"""runs_v5/*.json -> summary_v5.json + RESULTS_v5.md. Every variant reported; mean and 95% CI over seeds; paired CCL-minus-baseline
differences; fidelity incl. stricter rules at any discount; over-breadth (false exception approvals). No hand-typed numbers."""
import glob, json, os, sys, itertools
import numpy as np
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import ccl_sim as C

RUN_DIR = os.environ.get("CCL_RUN_DIR", "runs_v51")
runs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(HERE, RUN_DIR, "*.json")))]
KEY = ("world", "rogue_effect", "law_ref", "miner", "adm_months", "bad_renew")
seen = set()
for r in runs:  # fail closed on duplicates
    k = tuple(r[x] for x in KEY) + (r["seed"],); assert k not in seen, f"duplicate run {k}"; seen.add(k)
# fail closed on completeness: the expected manifest (every configuration x every seed) and ONE code version
SEEDS = [7, 11, 23, 31, 47]
expected = {(w, e, l, m, a, 0.35, s) for w in ["easy", "hard"] for e in ["segment", "exception"] for l in ["global", "scoped"]
            for (m, a) in [("beam", 2), ("beam", 4), ("beam_power", 4)] for s in SEEDS}
expected |= {("easy", e, l, "beam", 2, b, s) for e in ["segment", "exception"] for l in ["global", "scoped"] for b in [0.55, 0.70, 0.85] for s in SEEDS}
missing, extra = expected - seen, seen - expected
assert not missing and not extra, f"manifest mismatch: missing {sorted(missing)[:5]} extra {sorted(extra)[:5]}"
shas = {r.get("code_sha") for r in runs}; assert len(shas) == 1 and None not in shas, f"runs come from different or missing code versions: {shas}"
CODE_SHA = shas.pop()
assert CODE_SHA == C.CODE_SHA, f"runs were produced by ccl_sim {CODE_SHA} but this aggregator imports {C.CODE_SHA} (fidelity is recomputed with the imported code)"
METHODS = [("statute", "policy"), ("gbm_monthly", "GBM"), ("gbm_uplift", "GBM+renewal veto"), ("gbm_tlearner", "GBM+T-learner"), ("ccl", "CCL"), ("ccl_goodlaw", "CCL+outcome screen")]


def ci(x):
    x = np.asarray(x, float); m = x.mean()
    if len(x) < 2: return m, np.nan, np.nan
    h = stats.t.ppf(.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)); return m, m - h, m + h


def holdings_from_sql(hs):
    out = []
    for h in hs:
        conds, verdict = h["sql"].split("  => "); kind = "loosen" if verdict == "APPROVE" else "tighten"
        out.append(dict(id=h["id"], kind=kind, lits=conds.split(" AND "), cap=1e9 if kind == "loosen" else -1e9))
    return out


def rule_metrics(r):
    """fidelity per hidden rule (stricter rule scored at ANY discount) + system-level false exception approvals, month-36 law"""
    C.set_world(r["world"]); C.ROGUE_EFFECT = r["rogue_effect"]
    fresh = C.make_firm(np.random.default_rng(r["seed"] + 1000), 60000, r["bad_renew"], month=C.TEST_START - 1)
    pred, _ = C.apply(holdings_from_sql(r["snapshots"]["36"]["holdings"]), fresh, None)
    t_over = C.TIGHT[1](fresh).values & (fresh.disc.values > C.TIGHT[2]); out = {}
    for name, f_, cap in C.LOOSEN:
        a = f_(fresh).values & ~fresh.statute.values & (fresh.disc.values <= C.cap_of(cap, fresh)) & ~t_over
        out[name] = float(pred[a].mean()) if a.sum() else np.nan
    a = t_over; out[C.TIGHT[0]] = float((~pred[a]).mean())
    if r["world"] == "hard":
        name, f_, cap = C.LOOSEN[0]
        a = f_(fresh).values & (fresh.segment.values != "ENT") & ~fresh.statute.values & (fresh.disc.values <= C.cap_of(cap, fresh)) & ~t_over
        out["H1b >1M branch (non-ENT)"] = float(pred[a].mean())
    above = ~fresh.statute.values
    out["_false_exception_approvals"] = float((pred & above & ~fresh.truth.values).sum() / above.sum())   # over-breadth
    out["_missed_exceptions"] = float((~pred & above & fresh.truth.values).sum() / above.sum())
    C.ROGUE_EFFECT = "segment"
    return out


S = {"n_runs": len(runs), "configs": []}
groups = {}
for r in runs: groups.setdefault(tuple(r[x] for x in KEY), []).append(r)
for k in sorted(groups, key=str):
    rs = sorted(groups[k], key=lambda r: r["seed"]); g = dict(zip(KEY, k)); g["seeds"] = [r["seed"] for r in rs]
    for metric in ["vs_actual", "vs_harm_oracle", "harmful_approvals", "nonharmful_false_approvals", "false_rejections"]:
        g[metric] = {m: ci([r["accuracy"][m][metric] for r in rs]) for m, _ in METHODS}
        g[metric + "_diff"] = {m: ci([r["accuracy"]["ccl_goodlaw"][metric] - r["accuracy"][m][metric] for r in rs]) for m, _ in METHODS if m != "ccl_goodlaw"}
    if k[-1] == 0.35:
        rm = [rule_metrics(r) for r in rs]
        g["rules"] = {n: ci([x[n] for x in rm]) for n in rm[0]}
        g["rules_range"] = {n: (float(np.mean([x[n] for x in rm])), float(np.min([x[n] for x in rm])), float(np.max([x[n] for x in rm]))) for n in rm[0]}
        g["recovered"] = ci([sum(v.get("overlap_recovered", False) for v in r["snapshots"]["36"]["recovery"].values()) for r in rs])
        g["flagged_share"] = ci([np.mean([l["rogue_flagged"] for l in r["log"]]) for r in rs])
    S["configs"].append(g)
S["code_sha"] = CODE_SHA; S["run_dir"] = RUN_DIR
json.dump(S, open(os.path.join(HERE, "summary_v5.json"), "w"), indent=1, default=float)

f = lambda t: f"{t[0]:.3f} [{t[1]:.3f}, {t[2]:.3f}]"
fd = lambda t: f"{t[0]*100:+.2f} [{t[1]*100:+.2f}, {t[2]*100:+.2f}]"
L = [f"# CCL v5.1 results (auto-generated by aggregate_v5.py from {RUN_DIR}/*.json)", "",
     f"Runs: {len(runs)} from `{RUN_DIR}/` (manifest-validated: every configuration x seeds {SEEDS}; one code version `{CODE_SHA}`). Variants reuse the same seeds, so these are not independent worlds.",
     "Where shown, intervals are pointwise 95% Student-t intervals across five seed-level values (full-precision run metrics); some tables show means only.",
     "Fidelity, a bounded share, is shown as mean [min, max] over seeds. These exploratory intervals do not account for development-time selection,",
     "multiple comparisons, or uncertainty over independently specified worlds.",
     "`vs_harm_oracle` measures agreement with the simulator's noiseless firm-rule decisions after vetoing designated rogue-bound exceptions whose configured",
     "renewal-probability drop meets the 0.20 harm threshold. It is a threshold-defined synthetic target, not a utility-optimal policy or a causal estimate.",
     "The CCL screen (`ccl_sim.good_law`), the renewal veto and the T-learner use the same eligibility: approved decisions before the month with outcomes known",
     "before it (`ccl_sim.outcome_rows`). The CCL outcome screen is an association screen, not a causal estimator.", ""]
for world in ["easy", "hard"]:
    L += [f"## {world} world, rogue renewal 0.35", "", "| rogue effect | screen ref | miner/adm | " + " | ".join(n for _, n in METHODS) + " |", "|---|---|---|" + "---|" * len(METHODS)]
    for g in [g for g in S["configs"] if g["world"] == world and g["bad_renew"] == 0.35]:
        L.append(f"| {g['rogue_effect']} | {g['law_ref']} | {g['miner']}/{g['adm_months']} | " + " | ".join(f(g["vs_harm_oracle"][m]) for m, _ in METHODS) + " |")
    L += ["", "Paired difference, CCL+outcome screen minus baseline (percentage points, vs_harm_oracle):", "",
          "| rogue effect | screen ref | miner/adm | vs policy | vs GBM | vs GBM+renewal veto | vs GBM+T-learner | vs CCL (no screen) |", "|---|---|---|---|---|---|---|---|"]
    for g in [g for g in S["configs"] if g["world"] == world and g["bad_renew"] == 0.35]:
        d = g["vs_harm_oracle_diff"]
        L.append(f"| {g['rogue_effect']} | {g['law_ref']} | {g['miner']}/{g['adm_months']} | {fd(d['statute'])} | {fd(d['gbm_monthly'])} | {fd(d['gbm_uplift'])} | {fd(d['gbm_tlearner'])} | {fd(d['ccl'])} |")
    L += ["", "Decomposition (share of all decisions): harmful approvals / false rejections, and agreement with the logged decisions:", "",
          "| rogue effect | screen ref | miner/adm | CCL+screen harmful appr. | nonharmful false appr. | false rej. | GBM+veto harmful | T-learner harmful | CCL+screen vs logged | GBM vs logged |", "|---|---|---|---|---|---|---|---|---|---|"]
    for g in [g for g in S["configs"] if g["world"] == world and g["bad_renew"] == 0.35]:
        L.append(f"| {g['rogue_effect']} | {g['law_ref']} | {g['miner']}/{g['adm_months']} | {g['harmful_approvals']['ccl_goodlaw'][0]:.4f} | {g['nonharmful_false_approvals']['ccl_goodlaw'][0]:.4f} | "
                 f"{g['false_rejections']['ccl_goodlaw'][0]:.4f} | {g['harmful_approvals']['gbm_uplift'][0]:.4f} | {g['harmful_approvals']['gbm_tlearner'][0]:.4f} | {f(g['vs_actual']['ccl_goodlaw'])} | {f(g['vs_actual']['gbm_monthly'])} |")
    L += ["", "Rule recovery and fidelity (month-36 law, fresh sample; stricter rule scored at any discount):", "",
          "| rogue effect | screen ref | miner/adm | rules overlap-recovered | false exception approvals | missed exceptions | rogue flagged (share of months) |" + (" >1M branch fidelity |" if world == "hard" else ""),
          "|---|---|---|---|---|---|---|" + ("---|" if world == "hard" else "")]
    for g in [g for g in S["configs"] if g["world"] == world and g["bad_renew"] == 0.35]:
        ru = g["rules"]
        L.append(f"| {g['rogue_effect']} | {g['law_ref']} | {g['miner']}/{g['adm_months']} | {g['recovered'][0]:.1f}/7 | {ru['_false_exception_approvals'][0]:.4f} | {ru['_missed_exceptions'][0]:.4f} | {g['flagged_share'][0]:.0%} |"
                 + (" {:.2f} [{:.2f}, {:.2f}] |".format(*g["rules_range"]["H1b >1M branch (non-ENT)"]) if world == "hard" else ""))
    L.append("")
L += ["## Effect-size sweep (easy world, beam/2), vs_harm_oracle", "", "| rogue effect | screen ref | rogue renewal | " + " | ".join(n for _, n in METHODS) + " |", "|---|---|---|" + "---|" * len(METHODS)]
for g in [g for g in S["configs"] if g["world"] == "easy" and g["miner"] == "beam" and g["adm_months"] == 2]:
    L.append(f"| {g['rogue_effect']} | {g['law_ref']} | {g['bad_renew']} | " + " | ".join(f(g["vs_harm_oracle"][m]) for m, _ in METHODS) + " |")
open(os.path.join(HERE, "RESULTS_v5.md"), "w").write("\n".join(L) + "\n"); print(len(L), "lines")
