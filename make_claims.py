"""Generate the README evidence block from the result files (no hand-typed numbers). Writes between the CLAIMS markers."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
V5 = json.load(open(os.path.join(HERE, "summary_v5.json")))["configs"]
H = json.load(open(os.path.join(HERE, "real", "hmda", "results.json")))["tests"]
D = json.load(open(os.path.join(HERE, "dbx", "run_log.json")))["stages"]
NAMES = {"statute": "policy", "gbm_monthly": "GBM", "gbm_uplift": "GBM+renewal veto", "gbm_tlearner": "GBM+T-learner", "ccl": "CCL", "ccl_goodlaw": "CCL+outcome screen"}
sel = lambda **k: [g for g in V5 if all((abs(g[a] - b) < 1e-9 if isinstance(b, float) else g[a] == b) for a, b in k.items())]
rng = lambda xs, f="{:.3f}": f.format(min(xs)) if abs(max(xs) - min(xs)) < 5e-4 else f.format(min(xs)) + "-" + f.format(max(xs))
v = lambda gs, m: [g["vs_harm_oracle"][m][0] for g in gs]

E_ex = sel(world="easy", rogue_effect="exception", bad_renew=0.35); H_ex = sel(world="hard", rogue_effect="exception", bad_renew=0.35)
E_sg = sel(world="easy", rogue_effect="segment", law_ref="scoped", bad_renew=0.35); H_sg = sel(world="hard", rogue_effect="segment", law_ref="scoped", bad_renew=0.35)
rec_e = [g["recovered"][0] for g in sel(world="easy", bad_renew=0.35)]; rec_h = [g["recovered"][0] for g in sel(world="hard", bad_renew=0.35)]
d_tl = lambda gs: [g["vs_harm_oracle_diff"]["gbm_tlearner"] for g in gs]
fmt_d = lambda ds: "; ".join(sorted({f"{d[0]*100:+.2f} [{d[1]*100:+.2f}, {d[2]*100:+.2f}]" for d in ds}))
best = []
for name, gs in [("easy/exception", E_ex), ("hard/exception", H_ex), ("easy/segment (scoped)", E_sg), ("hard/segment (scoped)", H_sg)]:
    m = max(NAMES, key=lambda k: max(v(gs, k)))  # exact maximum, no tolerance
    best.append(f"{name}: {NAMES[m]}")
lab = lambda g: f"{g['miner']}/{g['adm_months']}"
d_lab = lambda gs: "; ".join(f"{lab(g)} {g['vs_harm_oracle_diff']['gbm_tlearner'][0]*100:+.2f} [{g['vs_harm_oracle_diff']['gbm_tlearner'][1]*100:+.2f}, {g['vs_harm_oracle_diff']['gbm_tlearner'][2]*100:+.2f}]" for g in sorted(gs, key=lab))
harm_ccl = [g["harmful_approvals"]["ccl_goodlaw"][0] for g in H_ex]; harm_veto = [g["harmful_approvals"]["gbm_uplift"][0] for g in H_ex]

sim = (f"- **Simulation** (`RESULTS_v5.md`; exploratory runs, five seeds per configuration, manifest-validated): month-36 laws achieve mean thresholded-overlap recovery of "
       f"{rng(rec_e, '{:.1f}')}/7 planted rules in the easy world and {rng(rec_h, '{:.1f}')}/7 in the hard world; this is not exact structural recovery. The displayed outcome comparisons "
       f"(CCL's screen, renewal veto, T-learner) share one eligibility rule (`ccl_sim.outcome_rows`). At rogue renewal 0.35 in the exception-effect world, the renewal veto scores {rng(v(E_ex, 'gbm_uplift'))} (easy) and "
       f"{rng(v(H_ex, 'gbm_uplift'))} (hard), the T-learner {rng(v(E_ex, 'gbm_tlearner'))} and {rng(v(H_ex, 'gbm_tlearner'))}, and screened CCL {rng(v(E_ex, 'ccl_goodlaw'))} "
       f"and {rng(v(H_ex, 'ccl_goodlaw'))}; in the hard world CCL approves harmful cases in {rng(harm_ccl, '{:.1%}')} of decisions vs {rng(harm_veto, '{:.1%}')} for the case-level veto, "
       f"consistent with harmful cases remaining covered by overlapping rules that pass the rule-level association screen. In the segment-effect world, scoped CCL substantially "
       f"reduces the false blocking of the global screen and the veto; scoped CCL minus T-learner, by miner/admission window: {d_lab(E_sg)} pts (easy) and {d_lab(H_sg)} pts (hard). "
       f"Highest observed mean at rogue renewal 0.35 among the displayed variants (exact maximum; not a significance claim; near-ties are within the paired intervals in `RESULTS_v5.md`): {'; '.join(best)}. No method is best in every setting; the "
       f"effect-size sweep in `RESULTS_v5.md` changes the ordering further. These are agreement rates with a threshold-defined synthetic oracle, not estimates of causal policy value.")
cut = H["2023"]["learned_threshold"]["threshold"]
dd = [H[t]["ci_ccl_selected_minus_learned_threshold"][0] * 100 for t in H]; dg = {t: H[t]["ci_ccl_selected_minus_gbm_tuned"] for t in H}
excl = [t for t, x in dg.items() if x[1] > 0 or x[2] < 0]
rec_hi = all(H[t]["gbm_tuned"]["deny_recall"] > H[t]["ccl_selected"]["deny_recall"] for t in H)
real = (f"- **Real decisions** (`real/hmda/REPORT.md`, one US lender, HMDA 2018-2023, mined against a fixed 43% DTI heuristic that is not the lender's policy): "
        f"CCL's observed accuracy is {min(dd):+.2f} to {max(dd):+.2f} percentage points relative to a learned DTI cutoff of {cut:g}%. Relative to the tuned GBM, its differences are "
        + ", ".join(f"{dg[t][0]*100:+.2f} ({t})" for t in H) + f"; the conditional state-cluster bootstrap intervals exclude zero only in {', '.join(excl) or 'no year'}. "
        f"These results do not establish equivalence. GBM has higher denial recall in {'all three years' if rec_hi else 'some years'}. Mined rules are predictive associations, not verified tacit policy.")
pit = D["B_point_in_time"]["asof_minus_today_table"]; P = D["B_parity"]; F4 = D.get("F4_final", {}); G = D["G_identity"]
ctl = [p for p in D["F2_proposals"]["proposals"] if "CONTROL" in str(p.get("because"))]
IC = json.load(open(os.path.join(HERE, "dbx", "integrity_check.json")))
H_ = D.get("H_integrity", {}); M3 = D.get("F3_merges", {}).get("merges", [])
ctl_merge = next((m["verdict"] for m in M3 if str(m.get("because", "")).startswith("CONTROL") or m.get("id") == "g0"), None)
llm_admitted = sum(p["verdict"] == "admitted" for p in D["F2_proposals"]["proposals"] if "CONTROL" not in str(p.get("because")))
llm_merges = sum(m.get("verdict") == "admitted" for m in M3 if not str(m.get("because", "")).startswith("CONTROL") and m.get("id") != "g0")
dbx = (f"- **Databricks build** (`dbx/REPORT.md`, one synthetic run): month-end Delta reconstruction under a delayed-edit simulator; hash-named UC functions whose stored body "
       f"and ordered signature are checked exactly ({'tamper tests detected an added clause and swapped parameters' if H_.get('tampered_body') == 'detected' and IC.get('signature_tamper') == 'detected' else 'tamper tests incomplete'}; "
       f"{len(IC.get('checked', []))} active functions verified, {len(IC.get('failures', []))} failures); a trusted compiler (`rulec.py`) for "
       f"proposed conditions and caps; Lakebase branches isolating trial registry records while replay runs in DBSQL; an event log (`law_events`) whose triggers block UPDATE, "
       f"DELETE and TRUNCATE ({'TRUNCATE verified blocked' if str(H_.get('truncate', '')).startswith('blocked') else 'TRUNCATE not verified'}; ownership/DDL lockdown not demonstrated); "
       f"Python/SQL agreement: {P['python_vs_sql_mismatches']} decision mismatches in {P['cases']} admission cases before the LLM steps"
       + (f" and {F4.get('python_vs_sql_mismatches')} after them, with {len(F4.get('mask_mismatches', {}))} rules whose per-case decided mask differs" if F4 else "")
       + (f"; a control merge (exact union of two admitted rules) ended as `{ctl_merge}`" if ctl_merge else "")
       + (f"; {llm_admitted} LLM-generated proposals and {llm_merges} LLM-proposed merges were admitted, so no LLM-authored law was activated; a deterministic control merge "
          f"(built from mined rules) exercised the merge activation path. " if llm_admitted + llm_merges == 0 else f"; {llm_admitted} LLM-generated proposals and {llm_merges} LLM-proposed merges were admitted. ")
       + f"The point-in-time contrast (same admission function, untouched months {D['B_point_in_time']['test_months']}) is {pit['diff']*100:+.2f} pts [{pit['ci'][0]*100:+.2f}, {pit['ci'][1]*100:+.2f}], "
       f"a paired decision-bootstrap interval conditional on this run's laws and simulated edits. The same checker run under a second principal: "
       f"{'all identity assertions passed' if G.get('assertions_passed') else 'identity assertions FAILED'} (denied before grant, works after grant, denied with one function withheld, "
       f"denied after revoke); this is not end-user OBO token passthrough. "
       + (f"A control re-proposal of a screened rule ended as `{ctl[0]['verdict']}`." if ctl else ""))
gov = ("- **Governance advantage: untested.** CCL produces compact executable rules that support inspection, testing and controlled deployment; whether that beats an "
       "explained black box in practice has not been measured.")
import re as _re
import numpy as np
def _confirm(path):
    t = open(os.path.join(HERE, path)).read()
    m = _re.search(r"confirm_world_gap: ([+-][\d.]+)  \[95% CI ([+-][\d.]+), ([+-][\d.]+)\] over (\d+)", t)
    neg = _re.search(r"worlds_negative:\s+(\d+) of (\d+)", t); res = _re.search(r"confirm_result:\s+(\w+)", t)
    return dict(gap=float(m.group(1)), lo=float(m.group(2)), hi=float(m.group(3)), n=int(m.group(4)), neg=int(neg.group(1)), res=res.group(1))
c1, c2, c3 = _confirm("autoresearch/CONFIRM_1.txt"), _confirm("autoresearch/CONFIRM_2.txt"), _confirm("autoresearch/CONFIRM_3.txt")
for c in (c1, c2, c3): assert c["res"] in ("PASS", "FAIL") and (c["res"] == "PASS") == (c["lo"] > -0.25), c   # the verdict must match the registered rule
verdict = "FAILED" if c1["res"] == c2["res"] == "FAIL" else ("PASSED" if c1["res"] == c2["res"] == "PASS" else "split (one PASS, one FAIL)")
below0 = all(c["hi"] < 0 for c in (c1, c2)); in_margin = all(c["lo"] <= -0.25 <= c["hi"] for c in (c1, c2))
_t3 = open(os.path.join(HERE, "autoresearch", "CONFIRM_3.txt")).read()
_rows3 = [l for l in _t3.splitlines() if l.startswith("  gen")]
_g3 = lambda l: float(_re.search(r"gap\s+([+-][\d.]+)", l).group(1))
_c3 = sorted(float(x) for x in _re.findall(r"caught\s+([\d.]+)%", _t3))
X3 = dict(exc=float(np.mean([_g3(l) for l in _rows3 if l.split()[1] == "exception"])), seg=float(np.mean([_g3(l) for l in _rows3 if l.split()[1] == "segment"])),
          macro=float(_re.search(r"harm_caught_pct:\s+([\d.]+)", _t3).group(1)), cmin=_c3[:2], rules=float(_re.search(r"rules_mean:\s+([\d.]+)", _t3).group(1)))
DR = json.load(open(os.path.join(HERE, "autoresearch", "detector_result.json")))
st = DR["stats"]
auto = (f"- **Autoresearch loop** (`autoresearch/`, own `WORKLOG.md` and `ADR.md`; karpathy/autoresearch adapted: frozen harness, method in an isolated process, "
        f"plain-data laws, adversarial tests, pre-registered tests). The loop added overruling precedents (a stricter-law rule where above-policy approvals "
        f"renew at least 0.20 worse than comparable in-policy approvals). In the pre-registered detector experiment, overrules caught "
        f"{st['twolit']['caught_strong']:.0f}% of harmful cases at drops of 0.25 to 0.30 versus {st['noovr']['caught_strong']:.0f}% without them, and caused "
        f"{st['twolit']['nh_ovr_share']:.0%} of the false rejections in no-harm worlds. Line 1's **two pre-registered confirmatory tests on freshly generated worlds {verdict}** (the two selected locked candidates, each on 24 new worlds): "
        f"per-world gap to the best of five fixed baselines {c1['gap']:+.3f} pts [{c1['lo']:+.3f}, {c1['hi']:+.3f}] ({c1['neg']} of {c1['n']} worlds negative) and "
        f"{c2['gap']:+.3f} pts [{c2['lo']:+.3f}, {c2['hi']:+.3f}] ({c2['neg']} of {c2['n']} negative). "
        + ("Both intervals lie entirely below zero, so on these synthetic worlds the locked candidates are measurably worse than the retrospective "
           "best-of-five comparator; " if below0 else "") + ("both intervals also contain the -0.25 margin, so a deficit larger than the margin is not established. " if in_margin else "")
        + f"Line 2 (AR-021) then targeted the hypothesised causes (mining recall on generated thresholds; overrule false alarms near the threshold), improved on a "
          f"revised dev panel that contains generated worlds, and its single pre-registered confirmatory test on new draws from the SAME generator family "
          f"**{c3['res'] + 'ED' if c3['res'] == 'PASS' else c3['res']}**: per-world gap {c3['gap']:+.3f} pts "
          f"[{c3['lo']:+.3f}, {c3['hi']:+.3f}] over {c3['n']} new worlds ({c3['neg']} negative)"
          + (f", i.e. non-inferior at the -0.25 margin (a lenient one: up to about 2 to 3.5 times the best baseline's errors) to the retrospective best of five "
             f"fixed, untuned baselines; the interval contains zero, so not superior. The average hides a split: exception worlds {X3['exc']:+.2f} pts, segment "
             f"worlds {X3['seg']:+.2f} pts; harm caught {X3['macro']:.1f}% as a macro-average with two worlds at {X3['cmin'][0]:.0f}% and {X3['cmin'][1]:.0f}%; "
             f"{X3['rules']:.2f} rules on average. Which of the three line-2 changes caused the improvement is not isolated. " if c3['res'] == 'PASS' and c3['lo'] <= 0 <= c3['hi'] else ". ")
          + "Not established: superiority, causal harm detection under unobserved confounding, power for harm exactly at the threshold, transfer to real firms, "
          "any governance advantage (AR-023).")
block = "\n".join([sim, real, dbx, auto, gov])
R = open(os.path.join(HERE, "README.md")).read()
a, b = R.index("<!-- CLAIMS:BEGIN -->"), R.index("<!-- CLAIMS:END -->")
open(os.path.join(HERE, "README.md"), "w").write(R[:a] + "<!-- CLAIMS:BEGIN -->\n" + block + "\n" + R[b:])
print(block)
