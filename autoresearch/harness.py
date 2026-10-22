"""Frozen evaluation harness for CCL autoresearch. DO NOT MODIFY (the agent edits method.py only).

For every configuration (world, rogue effect, seed) and every decision month m in 36..47:
  1. the method sees a VIEW of the past: rows with month < m, ground-truth columns removed, and the renewal
     outcome present only where it was knowable before m (ccl_sim.outcome_rows); elsewhere renewed = False
  2. method.build_law(view, X_view, m) returns a law: a list of holdings in ccl_sim's rule schema
  3. the law must pass the form gates (<= MAX_RULES holdings, <= MAX_LITS conditions each, valid literals/AST)
  4. decisions for month m are made by the FROZEN rule engine ccl_sim.apply(law, ...); no model is allowed
     at decision time
  5. decisions are scored against the harm-aware oracle (approve what the firm's rules allow, except approvals
     that cause a renewal drop >= 0.20)

Metric: score_pts = mean over the panel of (CCL agreement - best case-level baseline agreement) * 100.
Baselines (GBM, GBM + renewal veto, GBM + T-learner) are computed here with the same outcome information
(ccl_sim.outcome_rows) and cached. Higher is better; 0 means CCL ties the best black box.

Usage: python autoresearch/harness.py              (dev panel; the loop decides keep/discard on this)
       python autoresearch/harness.py --holdout    (unseen seeds + an unseen world; NEVER used to decide)
"""
import argparse, hashlib, importlib, json, os, sys, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, ROOT]
import ccl_sim as C
from sklearn.ensemble import HistGradientBoostingClassifier

BAD_RENEW, MAX_RULES, MAX_LITS, BUDGET_S = 0.35, 15, 4, 600
HIDDEN = ["truth", "good_decision", "binding", "harmful_if_approved", "harm_oracle"]
DEV = [(w, e, s) for w in ("easy", "hard") for e in ("exception", "segment") for s in (7, 11, 23)]
HOLDOUT = [(w, e, s) for w in ("easy", "hard", "alt") for e in ("exception", "segment") for s in (101, 202)]
# a world the loop never sees: new rule shapes, a different stricter rule, a rogue approver in another segment
ALT_LOOSEN = [
    ("A1 mid-market vs competitor <=27", lambda d: (d.segment == "MM") & d.competitor, 27),
    ("A2 long-tenure renewal <=24", lambda d: d.renewal & (d.tenure_y >= 8), 24),
    ("A3 deal > 750k <=22", lambda d: d.size_k > 750, 22),
    ("A4 UK quarter-end <=21", lambda d: (d.region == "UK") & d.quarter_end, 21),
    ("A5 France enterprise rogue approver <=34 (bad outcomes)", lambda d: (d.region == "FR") & (d.segment == "ENT"), 34),
]
ALT_TIGHT = ("A0 US SMB stricter >9 rejected", lambda d: (d.region == "US") & (d.segment == "SMB"), 9)
HARNESS_SHA = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()[:12]


def setup(world, effect):
    C.ROGUE_EFFECT, C.LAW_REF = effect, "global"
    if world == "alt":
        C.set_world("hard"); C.LOOSEN, C.TIGHT, C.ROGUE = ALT_LOOSEN, ALT_TIGHT, ALT_LOOSEN[-1][0]
    else: C.set_world(world)


def firm(world, effect, seed):
    setup(world, effect)
    df = C.make_firm(np.random.default_rng(seed), 120000, BAD_RENEW)
    return df, C.features(df)


def view_of(df, X, m):
    hist = (df.month < m).values
    known = C.outcome_rows(df, m).values[hist]
    v = df[hist].drop(columns=HIDDEN).copy()
    v["renewed"] = v["renewed"].values & known          # outcome only where it was knowable before m
    v["outcome_known"] = known
    return v, X[hist]


def gate(law, sample):
    if not isinstance(law, list): return "law is not a list"
    if len(law) > MAX_RULES: return f"{len(law)} holdings > {MAX_RULES}"
    for h in law:
        if h.get("kind") not in ("loosen", "tighten"): return "holding without kind loosen/tighten"
        if "ast" in h:
            import rulec
            try: rulec.to_sql(h["ast"])
            except Exception as e: return f"invalid AST: {e}"
        elif "lits" in h:
            if len(h["lits"]) > MAX_LITS: return f"{len(h['lits'])} literals > {MAX_LITS}"
            for l in h["lits"]:
                try: C.literal(l, sample)
                except Exception as e: return f"invalid literal {l!r}: {e}"
            try: float(h["cap"])
            except Exception: return "holding without a numeric cap"
        elif "conds" in h:
            if len(h["conds"]) > MAX_LITS: return f"{len(h['conds'])} conditions > {MAX_LITS}"
        else: return "holding without lits/conds/ast"
        try: C.to_sql(h)
        except Exception as e: return f"to_sql failed: {e}"
    return None


def baselines(df, X, m):
    """the case-level black boxes, exactly as in ccl_sim.run (same outcome rows for every outcome-aware method)"""
    win = (df.month >= m - 12) & (df.month < m)
    gbm = HistGradientBoostingClassifier(random_state=0).fit(X[win], df.approved[win])
    kn = C.outcome_rows(df, m)
    renew_model = HistGradientBoostingClassifier(random_state=0).fit(X[kn], df.renewed[kn])
    ref = df.renewed[kn & df.statute].mean()
    t1 = HistGradientBoostingClassifier(random_state=0).fit(X[kn & ~df.statute], df.renewed[kn & ~df.statute])
    t0 = HistGradientBoostingClassifier(random_state=0).fit(X[kn & df.statute], df.renewed[kn & df.statute])
    te = (df.month == m).values; dt, Xt = df[te], X[te]
    base = gbm.predict(Xt).astype(bool); exc = ~dt.statute.values
    return {"gbm": base, "veto": base & ~(exc & (renew_model.predict_proba(Xt)[:, 1] < ref - C.HARM_DROP)),
            "tlearner": base & ~(exc & (t1.predict_proba(Xt)[:, 1] - t0.predict_proba(Xt)[:, 1] < -C.HARM_DROP))}


def eval_config(cfg, with_baselines):
    world, effect, seed = cfg
    t_start = time.time()
    df, X = firm(world, effect, seed)
    method = importlib.import_module("method")
    res = dict(cfg=list(cfg), agree=[], harmful=[], false_rej=[], rules=[], n=[], violation=None, base={})
    for m in range(C.TEST_START, C.MONTHS):
        v, Xv = view_of(df, X, m)
        law = method.build_law(v, Xv, m)
        setup(world, effect)                         # the method may not leave global state behind
        err = gate(law, v.head(50))
        if err: res["violation"] = f"month {m}: {err}"; break
        te = (df.month == m).values; dt, Xt = df[te], X[te]
        pred = np.asarray(C.apply(law, dt.drop(columns=HIDDEN), Xt)[0], bool)
        orc, harm = dt.harm_oracle.values, dt.harmful_if_approved.values
        res["agree"].append(float((pred == orc).mean())); res["harmful"].append(float((pred & harm).mean()))
        res["false_rej"].append(float((~pred & orc).mean())); res["rules"].append(len(law)); res["n"].append(int(te.sum()))
        if with_baselines:
            for k, p in baselines(df, X, m).items(): res["base"].setdefault(k, []).append(float((p == orc).mean()))
    res["seconds"] = time.time() - t_start
    return res


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--holdout", action="store_true"); a = ap.parse_args()
    panel = HOLDOUT if a.holdout else DEV
    cache_p = os.path.join(HERE, f"baselines_{'holdout' if a.holdout else 'dev'}_{HARNESS_SHA}_{C.CODE_SHA}.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=min(len(panel), os.cpu_count() or 4)) as ex:
        futs = [ex.submit(eval_config, tuple(c), json.dumps(list(c)) not in cache) for c in panel]
        out = [f.result(timeout=BUDGET_S) for f in futs]
    secs = time.time() - t0
    viol = [r["violation"] for r in out if r["violation"]]
    for r in out:
        if r["base"]: cache[json.dumps(r["cfg"])] = {k: float(np.average(v, weights=r["n"])) for k, v in r["base"].items()}
    json.dump(cache, open(cache_p, "w"))
    print("---")
    if viol:
        print("status:           invalid"); print("violation:       ", viol[0]); print("score_pts:        nan"); return
    rows, gaps = [], []
    for r in out:
        w = r["n"]; ccl = float(np.average(r["agree"], weights=w)); b = cache[json.dumps(r["cfg"])]
        best_k = max(b, key=b.get); gap = (ccl - b[best_k]) * 100; gaps.append(gap)
        rows.append((r["cfg"], ccl, best_k, b[best_k], gap, float(np.average(r["harmful"], weights=w)) * 100, float(np.mean(r["rules"]))))
    print(f"score_pts:        {np.mean(gaps):+.3f}")
    print(f"worst_gap_pts:    {min(gaps):+.3f}  ({'/'.join(map(str, rows[int(np.argmin(gaps))][0]))})")
    print(f"ccl_agree:        {np.mean([x[1] for x in rows]):.4f}")
    print(f"harmful_appr_pct: {np.mean([x[5] for x in rows]):.3f}")
    print(f"rules_mean:       {np.mean([x[6] for x in rows]):.2f}")
    print(f"panel:            {'holdout' if a.holdout else 'dev'} ({len(rows)} configs)")
    print(f"seconds:          {secs:.1f}")
    for cfg, ccl, bk, bv, gap, hp, nr in rows:
        print(f"  {cfg[0]:5s} {cfg[1]:9s} s{cfg[2]:<4d} ccl {ccl:.4f}  best {bk:8s} {bv:.4f}  gap {gap:+6.2f}  harmful {hp:5.2f}%  rules {nr:4.1f}")


if __name__ == "__main__":
    main()
