"""Frozen evaluation harness v2 for CCL autoresearch. DO NOT MODIFY (the agent edits method.py only).

Trust boundary (AR-009, after Astra review round 1):
  - the method runs in a SEPARATE process (runner.py, python -I) and receives, for each decision month m, a pickled
    VIEW: rows with month < m, only the columns in VIEW_COLS, renewal outcomes only where knowable before m
    (ccl_sim.outcome_rows; elsewhere renewed = False, flag outcome_known). It never sees the firm, the seed, the world
    or this process's memory, and anything it does to ccl_sim stays in its own process.
  - it returns plain JSON holdings; validate() reconstructs ONLY {"kind", "lits", "cap"} from each holding (runner.py flags
    ast / conds holdings, which are rejected; any other key is dropped) whose literals match a
    strict grammar over the deal fields in FIELDS (no approved / renewed / statute / month / outcome fields), at most
    MAX_RULES holdings, MAX_LITS literals each, MAX_TOTAL_LITS overall, finite caps in range. No AST, no trees.
  - decisions are made HERE with this process's own ccl_sim.apply on decision-time columns only (DEC_COLS).
  - baselines are computed HERE, in processes that never import the method, and cached by harness/world/simulator hash.

Metric (dev panel: 32 configs since v4, AR-021; 16 in v2.1): score_pts = mean over the panel of (CCL agreement - best baseline agreement) * 100, with a 95% t-interval over
configurations (configurations share seeds across worlds, so the interval is optimistic). Baselines: GBM, GBM +
renewal veto, GBM + T-learner, a 15-leaf decision tree (a compact rule model), and that tree + the renewal veto,
selected RETROSPECTIVELY per configuration (the best of five fixed baselines, not the best possible black box).

Panels: dev (decide keep/discard), monitor (seen at checkpoints only), stress (harm-detector stress tests,
reported, never in the score), fresh (newly generated worlds and seeds drawn at run time; run ONCE per locked method).
Usage: python autoresearch/harness.py [--panel dev|monitor|stress|fresh]
"""
import argparse, hashlib, json, math, os, pickle, re, secrets, select, subprocess, sys, tempfile, time
os.environ.setdefault("OMP_NUM_THREADS", "1")
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path[:0] = [HERE, ROOT]
import ccl_sim as C
import worlds as WD
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.tree import DecisionTreeClassifier

MAX_RULES, MAX_LITS, MAX_TOTAL_LITS, MONTH_TIMEOUT_S = 15, 4, 45, 120
NI_MARGIN = -0.25   # prespecified non-inferiority margin (points) for monitor / fresh panels
HIDDEN = ["truth", "good_decision", "binding", "harmful_if_approved", "harm_oracle"]
FIELDS = {"segment": "cat", "region": "cat", "renewal": "bool", "quarter_end": "bool", "competitor": "bool", "churn_high": "bool",
          "term": "num", "size_k": "num", "tenure_y": "num"}
VIEW_COLS = ["month", "disc", "approved", "statute", "outcome_known_month", "renewed"] + list(FIELDS)
DEC_COLS = ["disc", "statute"] + list(FIELDS)
LIT_RES = [re.compile(r"^(segment|region) (=|!=) '([A-Z]{2,3})'$"), re.compile(r"^(NOT )?(renewal|quarter_end|competitor|churn_high)$"),
           re.compile(r"^(term|size_k|tenure_y) (>|<=|>=) (\d{1,5}(\.\d{1,2})?)$")]
CAP_RANGE = {"loosen": (15.0, 60.0), "tighten": (0.0, 15.0)}
P = lambda **k: dict(dict(bad_renew=0.35, stress=None), **k)
def _gen_dev(i, e):
    br = round(float(np.random.default_rng(700001 + i).uniform(0.35, 0.75)), 2) if e == "exception" else 0.35
    return P(world=f"gen:{700001 + i}", effect=e, seed=7001 + i, bad_renew=br)


PANELS = {
    "dev": [P(world=w, effect=e, seed=s) for w in ("easy", "hard") for e in ("exception", "segment") for s in (7, 11, 23)]
           + [P(world="hard", effect="exception", seed=s, bad_renew=b) for b in (0.60, 0.70) for s in (31, 47)]   # v2.1: harm near the threshold (AR-012)
           + [_gen_dev(i, e) for i in range(8) for e in ("exception", "segment")],   # v4: generated worlds, the confirm distribution's family (AR-021)
    "monitor": [P(world=w, effect=e, seed=s) for w in ("easy", "hard", "alt") for e in ("exception", "segment") for s in (101, 202)],
    "stress": [P(world="hard", effect="segment", seed=s, stress="confounded") for s in (7, 11)]
              + [P(world="hard", effect="exception", seed=s, bad_renew=b) for b in (0.70, 0.60) for s in (7, 11)],
    # detector falsification panel (AR-014): new seeds 501-503, frozen before any run
    "detector": [P(world="hard", effect="exception", seed=s, bad_renew=b) for b in (0.75, 0.70, 0.65, 0.60, 0.55) for s in (501, 502, 503)]
                + [P(world=w, effect="segment", seed=s) for w in ("hard", "gen:900001", "gen:900002") for s in (501, 502, 503)]
                + [P(world="hard", effect="segment", seed=s, stress="confounded") for s in (501, 502, 503)]
                + [P(world="hard", effect=e, seed=s, n=40000) for e in ("exception", "segment") for s in (501, 502, 503)],
}
SRC = "".join(open(os.path.join(HERE, f)).read() for f in ("harness.py", "worlds.py", "runner.py"))
HARNESS_SHA = hashlib.sha256(SRC.encode()).hexdigest()[:12]


def validate(law):
    """plain-data law -> (holdings, None) or (None, reason). The ONLY thing the method can hand back."""
    if not isinstance(law, list): return None, "law is not a list"
    if len(law) > MAX_RULES: return None, f"{len(law)} holdings > {MAX_RULES}"
    out, total = [], 0
    for i, h in enumerate(law):
        if not isinstance(h, dict) or h.get("other_keys"): return None, f"holding {i}: only lits/cap holdings are allowed"
        kind, lits, cap = h.get("kind"), h.get("lits"), h.get("cap")
        if kind not in CAP_RANGE: return None, f"holding {i}: kind {kind!r}"
        if not isinstance(lits, list) or not lits or len(lits) > MAX_LITS: return None, f"holding {i}: 1..{MAX_LITS} literals required"
        for l in lits:
            if not isinstance(l, str) or not any(r.match(l) for r in LIT_RES): return None, f"holding {i}: literal {l!r} not in the grammar"
        if not isinstance(cap, (int, float)) or not math.isfinite(cap) or not CAP_RANGE[kind][0] <= cap <= CAP_RANGE[kind][1]:
            return None, f"holding {i}: cap {cap!r} out of range for {kind}"
        total += len(lits); out.append({"id": f"L{i}", "kind": kind, "lits": list(lits), "cap": float(cap)})
    if total > MAX_TOTAL_LITS: return None, f"{total} literals > {MAX_TOTAL_LITS}"
    return out, None


def view_of(df, m):
    hist = (df.month < m).values
    known = C.outcome_rows(df, m).values[hist]
    v = df.loc[hist, [c for c in VIEW_COLS if c in df]].copy()
    v["renewed"] = v["renewed"].values & known
    v["outcome_known"] = known
    return v


def baselines(df, X, m):
    win = (df.month >= m - 12) & (df.month < m)
    gbm = HistGradientBoostingClassifier(random_state=0).fit(X[win], df.approved[win])
    tree = DecisionTreeClassifier(max_leaf_nodes=15, min_samples_leaf=30, random_state=0).fit(X[win], df.approved[win])
    kn = C.outcome_rows(df, m)
    renew_model = HistGradientBoostingClassifier(random_state=0).fit(X[kn], df.renewed[kn])
    ref = df.renewed[kn & df.statute].mean()
    t1 = HistGradientBoostingClassifier(random_state=0).fit(X[kn & ~df.statute], df.renewed[kn & ~df.statute])
    t0 = HistGradientBoostingClassifier(random_state=0).fit(X[kn & df.statute], df.renewed[kn & df.statute])
    te = (df.month == m).values; dt, Xt = df[te], X[te]
    exc = ~dt.statute.values; veto = exc & (renew_model.predict_proba(Xt)[:, 1] < ref - C.HARM_DROP)
    base, tb = gbm.predict(Xt).astype(bool), tree.predict(Xt).astype(bool)
    return {"gbm": base, "veto": base & ~veto, "tlearner": base & ~(exc & (t1.predict_proba(Xt)[:, 1] - t0.predict_proba(Xt)[:, 1] < -C.HARM_DROP)),
            "tree15": tb, "tree15_veto": tb & ~veto}


def read_line(proc, timeout):
    """one protocol line within `timeout` seconds overall, or None (a partial line without newline times out too)"""
    fd, buf, end = proc.stdout.fileno(), b"", time.time() + timeout
    while b"\n" not in buf:
        left = end - time.time()
        if left <= 0 or not select.select([fd], [], [], left)[0]: return None
        chunk = os.read(fd, 65536)
        if not chunk: return buf.decode() if buf else ""
        buf += chunk
    return buf.split(b"\n", 1)[0].decode() + "\n"


def eval_config(cfg, need_base, method_path=None):
    t_start = time.time()
    df, X = WD.firm(cfg)
    res = dict(cfg=cfg, agree=[], harmful=[], harm_cases=[], blocked_harm=[], false_rej=[], rules=[], lits=[], overrules=[], n=[], violation=None, base={})
    env = {"PATH": os.environ.get("PATH", ""), "OMP_NUM_THREADS": "1", "HOME": os.environ.get("HOME", "")}
    if method_path: env["AR_METHOD"] = method_path
    with tempfile.TemporaryDirectory() as tmp:
        proc = subprocess.Popen([sys.executable, "-I", os.path.join(HERE, "runner.py")], cwd=tmp, env=env,   # binary pipes: read_line
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            for m in range(C.TEST_START, C.MONTHS):
                p = os.path.join(tmp, f"view_{m}.pkl")
                with open(p, "wb") as f: pickle.dump(view_of(df, m), f)
                proc.stdin.write((json.dumps({"path": p, "m": m}) + "\n").encode()); proc.stdin.flush()
                line = read_line(proc, MONTH_TIMEOUT_S); os.remove(p)
                if line is None: res["violation"] = f"month {m}: method timeout after {MONTH_TIMEOUT_S}s"; break
                rep = json.loads(line) if line else {"error": "runner died"}
                if "error" in rep: res["violation"] = f"month {m}: method error {rep['error']}"; break
                law, err = validate(rep["law"])
                if err: res["violation"] = f"month {m}: {err}"; break
                missing = sorted({re.split(r"[ =!<>]", l.replace("NOT ", ""))[0] for h in law for l in h["lits"]} - set(df.columns))
                if missing: res["violation"] = f"month {m}: literal on a field not available in this world: {missing}"; break
                WD.setup(cfg)
                te = (df.month == m).values; dt, Xt = df[te], X[te]
                dcols = dt[[c for c in DEC_COLS if c in dt]]
                pred = np.asarray(C.apply(law, dcols, Xt)[0], bool)
                orc, harm = dt.harm_oracle.values, dt.harmful_if_approved.values
                ovr = [h for h in law if h["kind"] == "tighten" and h["cap"] == C.STATUTE_CAP]
                pred0 = np.asarray(C.apply([h for h in law if h not in ovr], dcols, Xt)[0], bool) if ovr else pred
                changed = pred0 & ~pred                                        # approvals the overrules turned into rejections
                res.setdefault("ovr_false_rej", []).append(int((changed & orc).sum())); res.setdefault("ovr_prevented", []).append(int((changed & harm).sum()))
                res.setdefault("all_false_rej_n", []).append(int((~pred & orc).sum())); res.setdefault("ovr_pops", []).append([" AND ".join(h["lits"]) for h in ovr])
                res["agree"].append(float((pred == orc).mean())); res["harmful"].append(float((pred & harm).mean()))
                res["harm_cases"].append(int(harm.sum())); res["blocked_harm"].append(int((~pred & harm).sum()))
                res["false_rej"].append(float((~pred & orc).mean())); res["rules"].append(len(law)); res["lits"].append(sum(len(h["lits"]) for h in law))
                res["overrules"].append(sum(h["kind"] == "tighten" and h["cap"] == C.STATUTE_CAP for h in law)); res["n"].append(int(te.sum()))
                if need_base:
                    for k, b in baselines(df, X, m).items(): res["base"].setdefault(k, []).append(float((b == orc).mean()))
        finally:
            proc.kill()
    res["seconds"] = time.time() - t_start
    return res


def summarize(out, cache, panel):
    rows = []
    for r in out:
        w = r["n"]; ccl = float(np.average(r["agree"], weights=w)); b = cache[json.dumps(r["cfg"], sort_keys=True)]
        bk = max(b, key=b.get); hc = sum(r["harm_cases"])
        rows.append(dict(cfg=r["cfg"], ccl=ccl, bk=bk, bv=b[bk], gap=(ccl - b[bk]) * 100, harmful=float(np.average(r["harmful"], weights=w)) * 100,
                         catch=(sum(r["blocked_harm"]) / hc * 100) if hc else None, false_rej=float(np.average(r["false_rej"], weights=w)) * 100,
                         rules=float(np.mean(r["rules"])), lits=float(np.mean(r["lits"])), ovr=float(np.mean(r["overrules"]))))
    g = np.array([x["gap"] for x in rows]); n = len(g)
    half = 0 if n < 2 else __import__('scipy.stats', fromlist=['t']).t.ppf(0.975, n - 1) * g.std(ddof=1) / math.sqrt(n)
    catches = [x["catch"] for x in rows if x["catch"] is not None]
    print("---")
    note = "  (config-level, NOT the registered analysis: see confirm_world_gap)" if panel == "confirm" else ""
    print(f"score_pts:        {g.mean():+.3f}  [95% CI {g.mean() - half:+.3f}, {g.mean() + half:+.3f}]{note}")
    print(f"worst_gap_pts:    {g.min():+.3f}  ({rows[int(g.argmin())]['cfg']['world']}/{rows[int(g.argmin())]['cfg']['effect']}/{rows[int(g.argmin())]['cfg']['seed']})")
    if panel in ("monitor", "fresh"): print(f"non_inferior:     {'yes' if g.mean() - half > NI_MARGIN else 'no'} (lower CI vs margin {NI_MARGIN})")
    print(f"harmful_appr_pct: {np.mean([x['harmful'] for x in rows]):.3f}")
    print(f"harm_caught_pct:  {np.mean(catches):.1f}" if catches else "harm_caught_pct:  n/a (no harmful cases)")
    print(f"false_rej_pct:    {np.mean([x['false_rej'] for x in rows]):.3f}")
    print(f"rules_mean:       {np.mean([x['rules'] for x in rows]):.2f}  (literals {np.mean([x['lits'] for x in rows]):.1f}, overrules {np.mean([x['ovr'] for x in rows]):.2f})")
    print(f"panel:            {panel} ({n} configs)")
    for x in rows:
        c = x["cfg"]; tag = f"{c['world']:6s} {c['effect']:9s} s{c['seed']:<6d}" + (f" br{c['bad_renew']}" if c["bad_renew"] != 0.35 else "") + (f" {c['stress']}" if c["stress"] else "") + (f" n{c['n'] // 1000}k" if c.get("n") else "")
        print(f"  {tag:38s} ccl {x['ccl']:.4f}  best {x['bk']:11s} {x['bv']:.4f}  gap {x['gap']:+6.2f}  harmful {x['harmful']:5.2f}%  "
              f"caught {('%5.1f%%' % x['catch']) if x['catch'] is not None else '  n/a '}  false_rej {x['false_rej']:5.2f}%  rules {x['rules']:4.1f}  ovr {x['ovr']:.1f}")


def confirm_summary(out, cache, man):
    """pre-registered inference (AR-015): one gap per WORLD (mean of its exception and segment configs), t-interval over
    worlds; success iff the lower 95% bound exceeds the margin"""
    from collections import defaultdict
    per = defaultdict(list)
    for r in out:
        b = cache[json.dumps(r["cfg"], sort_keys=True)]; ccl = float(np.average(r["agree"], weights=r["n"]))
        per[r["cfg"]["world"]].append((ccl - max(b.values())) * 100)
    g = np.array([np.mean(v) for v in per.values()]); n = len(g)
    from scipy import stats
    half = stats.t.ppf(0.975, n - 1) * g.std(ddof=1) / math.sqrt(n)
    lo = g.mean() - half
    print(f"confirm_world_gap: {g.mean():+.3f}  [95% CI {lo:+.3f}, {g.mean() + half:+.3f}] over {n} independent worlds")
    print(f"confirm_margin:    {man['margin_pts']}")
    print(f"confirm_result:    {'PASS' if lo > man['margin_pts'] else 'FAIL'} (pre-registered: lower bound > margin)")
    print(f"worlds_negative:   {int((g < 0).sum())} of {n}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--panel", default="dev", choices=["dev", "monitor", "stress", "fresh", "detector", "confirm"])
    ap.add_argument("--manifest", default=None, help="confirm panel: committed pre-registration manifest (AR-013)")
    ap.add_argument("--dump", default=None, help="write per-config raw results as JSON (detector panel)")
    ap.add_argument("--method", default=None, help="path to a method file (tests); default autoresearch/method.py"); a = ap.parse_args()
    if a.method: a.method = os.path.abspath(a.method)   # the runner starts in a temp dir (bug found on the first detector run)
    if a.panel == "confirm":
        man = json.load(open(a.manifest)); mp = os.path.join(ROOT, man["method"])
        sha = hashlib.sha256(open(mp, "rb").read()).hexdigest()
        if sha != man["method_sha256"]: print("status: manifest method hash mismatch"); return
        if HARNESS_SHA != man["harness_sha"]: print("status: manifest harness hash mismatch"); return
        if "simulator_sha" in man and C.CODE_SHA != man["simulator_sha"]: print("status: manifest simulator hash mismatch"); return
        if "rulec_sha256" in man and hashlib.sha256(open(os.path.join(ROOT, "rulec.py"), "rb").read()).hexdigest() != man["rulec_sha256"]:
            print("status: manifest compiler hash mismatch"); return
        k = secrets.randbits(30); rr = np.random.default_rng(k); a.method = mp
        panel = []
        for i in range(man["n_worlds"]):
            br = round(float(rr.uniform(*man["harm_bad_renew_range"])), 2)
            panel += [P(world=f"gen:{k + i}", effect="exception", seed=k % 100000 + 3000 + i, bad_renew=br),
                      P(world=f"gen:{k + i}", effect="segment", seed=k % 100000 + 3000 + i)]
        print(f"confirm draw: k={k} manifest={a.manifest}")
    elif a.panel == "fresh":
        k = secrets.randbits(30)    # drawn now: nobody, including the agent, has seen these worlds or seeds
        panel = [P(world=f"gen:{k + i}", effect=e, seed=k % 100000 + 1000 + i) for i in range(4) for e in ("exception", "segment")]
        rr = np.random.default_rng(k)   # v2.1: plus harm of random size around the threshold (drop 0.10 to 0.30)
        panel += [P(world=f"gen:{k + 4 + i}", effect="exception", seed=k % 100000 + 2000 + i, bad_renew=round(float(rr.uniform(0.55, 0.75)), 2)) for i in range(4)]
        print(f"fresh draw: k={k}")
    else: panel = PANELS[a.panel]
    cache_p = os.path.join(HERE, f"baselines_{a.panel}_{HARNESS_SHA}_{C.CODE_SHA}.json")
    cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=min(len(panel), os.cpu_count() or 4)) as ex:
        futs = [ex.submit(eval_config, c, json.dumps(c, sort_keys=True) not in cache, a.method) for c in panel]
        out = [f.result() for f in futs]
    viol = [r["violation"] for r in out if r["violation"]]
    for r in out:
        if r["base"] and not r["violation"] and len(r["n"]) == C.MONTHS - C.TEST_START:
            cache[json.dumps(r["cfg"], sort_keys=True)] = {k: float(np.average(v, weights=r["n"])) for k, v in r["base"].items()}
    if a.panel not in ("fresh", "confirm"): json.dump(cache, open(cache_p, "w"))
    if a.dump: json.dump([dict(r, base_cached=cache.get(json.dumps(r["cfg"], sort_keys=True))) for r in out], open(a.dump, "w"))
    if viol: print("---\nstatus:           invalid\nviolation:       ", viol[0], "\nscore_pts:        nan"); return
    summarize(out, cache, a.panel)
    if a.panel == "confirm": confirm_summary(out, cache, json.load(open(a.manifest)))
    print(f"seconds:          {time.time() - t0:.1f}")


if __name__ == "__main__":
    main()
