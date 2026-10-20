# Corporate Case Law (CCL)

An exploratory research prototype: mine exception rules ("holdings") from the gap between a written policy and logged decisions,
admit a rule only if replaying past decisions on point-in-time facts improves accuracy, screen rules against outcomes known at the
time, and let an agent decide only through executable, checkable rules. Started from a critical study of the CLM paper
(arXiv 2609.04377, notes in `docs/CLM_PAPER_NOTES.md`).

**Status: exploratory.** Metrics, thresholds, simulator worlds and miners were developed while looking at results (see
`WORKLOG.md` and `docs/reviews/`). Nothing here is a confirmatory test.

## What the evidence supports (v5.1, after two external reviews; generated from the result files by `make_claims.py`)

<!-- CLAIMS:BEGIN -->
- **Simulation** (`RESULTS_v5.md`; exploratory runs, five seeds per configuration, manifest-validated): month-36 laws achieve mean thresholded-overlap recovery of 7.0/7 planted rules in the easy world and 6.8-7.0/7 in the hard world; this is not exact structural recovery. The displayed outcome comparisons (CCL's screen, renewal veto, T-learner) share one eligibility rule (`ccl_sim.outcome_rows`). At rogue renewal 0.35 in the exception-effect world, the renewal veto scores 0.997 (easy) and 0.997 (hard), the T-learner 0.994 and 0.997, and screened CCL 0.995-0.996 and 0.963-0.970; in the hard world CCL approves harmful cases in 1.7%-1.9% of decisions vs 0.0% for the case-level veto, consistent with harmful cases remaining covered by overlapping rules that pass the rule-level association screen. In the segment-effect world, scoped CCL substantially reduces the false blocking of the global screen and the veto; scoped CCL minus T-learner, by miner/admission window: beam/2 +0.59 [+0.33, +0.86]; beam/4 +0.60 [+0.37, +0.84]; beam_power/4 +0.60 [+0.37, +0.84] pts (easy) and beam/2 -1.13 [-1.41, -0.85]; beam/4 -0.84 [-1.23, -0.45]; beam_power/4 -1.30 [-1.92, -0.69] pts (hard). Highest observed mean at rogue renewal 0.35 among the displayed variants (exact maximum; not a significance claim; near-ties are within the paired intervals in `RESULTS_v5.md`): easy/exception: GBM+renewal veto; hard/exception: GBM+renewal veto; easy/segment (scoped): CCL; hard/segment (scoped): GBM. No method is best in every setting; the effect-size sweep in `RESULTS_v5.md` changes the ordering further. These are agreement rates with a threshold-defined synthetic oracle, not estimates of causal policy value.
- **Real decisions** (`real/hmda/REPORT.md`, one US lender, HMDA 2018-2023, mined against a fixed 43% DTI heuristic that is not the lender's policy): CCL's observed accuracy is +0.01 to +0.18 percentage points relative to a learned DTI cutoff of 49%. Relative to the tuned GBM, its differences are -0.69 (2021), -0.04 (2022), -0.11 (2023); the conditional state-cluster bootstrap intervals exclude zero only in 2021. These results do not establish equivalence. GBM has higher denial recall in all three years. Mined rules are predictive associations, not verified tacit policy.
- **Databricks build** (`dbx/REPORT.md`, one synthetic run): month-end Delta reconstruction under a delayed-edit simulator; hash-named UC functions whose stored body and ordered signature are checked exactly (tamper tests detected an added clause and swapped parameters; 9 active functions verified, 0 failures); a trusted compiler (`rulec.py`) for proposed conditions and caps; Lakebase branches isolating trial registry records while replay runs in DBSQL; an event log (`law_events`) whose triggers block UPDATE, DELETE and TRUNCATE (TRUNCATE verified blocked; ownership/DDL lockdown not demonstrated); Python/SQL agreement: 0 decision mismatches in 5029 admission cases before the LLM steps and 0 after them, with 0 rules whose per-case decided mask differs; a control merge (exact union of two admitted rules) ended as `admitted`; 0 LLM-generated proposals and 0 LLM-proposed merges were admitted, so no LLM-authored law was activated; a deterministic control merge (built from mined rules) exercised the merge activation path. The point-in-time contrast (same admission function, untouched months [36, 37, 38]) is +0.20 pts [+0.09, +0.33], a paired decision-bootstrap interval conditional on this run's laws and simulated edits. The same checker run under a second principal: all identity assertions passed (denied before grant, works after grant, denied with one function withheld, denied after revoke); this is not end-user OBO token passthrough. A control re-proposal of a screened rule ended as `bad_law`.
- **Governance advantage: untested.** CCL produces compact executable rules that support inspection, testing and controlled deployment; whether that beats an explained black box in practice has not been measured.
<!-- CLAIMS:END -->

| File | What |
|---|---|
| `WORKLOG.md` | chronological log, including every mistake and correction |
| `docs/ADR.md` | method and design decisions (later ADRs supersede earlier ones where noted) |
| `docs/reviews/` | external model reviews (Astra) and the responses |
| `RESULTS_v5.md` / `summary_v5.json` | current simulation results (`aggregate_v5.py` over `runs_v51/`; `runs_v5/` = superseded first v5 grid) |
| `RESULTS.md`, `RESULTS_v3.md`, `RESULTS_v4.md`, `RESULTS_causal.md`, `v1/` | SUPERSEDED earlier results, kept for the record |
| `ccl_sim.py` | simulator, miners, moot court, outcome screen, baselines (`--world`, `--miner`, `--rogue-effect`, `--law-ref`, `--adm-months`) |
| `real/hmda/` | real-decision study (raw data gitignored; download recipe in `WORKLOG.md`) |
| `rulec.py` | trusted rule compiler (AST, bounds, cap validation; the same AST is evaluated in Python and emitted as SQL) |
| `dbx/` | Databricks build (`ccl_on_dbx.py`, Lakebase helpers) and `REPORT.md` |
| `tests/` | leakage invariance, attribution, shadowing, compiler adversarial and boundary cases, beam equivalence, smoke |
| `whiteboard/` | the two Excalidraw boards (numbers read from result files) |
| `ecc_python_review.md` | an earlier ECC code review that triggered v2 |

Reproduce the simulation:
```bash
OMP_NUM_THREADS=1 python3 -m pytest -q tests
OMP_NUM_THREADS=2 xargs -P 6 -L 1 python3 ccl_sim.py < runs_v51/jobs_main.txt
OMP_NUM_THREADS=2 xargs -P 6 -L 1 python3 ccl_sim.py < runs_v51/jobs_sweep.txt
python3 aggregate_v5.py && python3 make_claims.py
```
The Databricks build needs `CCL_DATABRICKS_PROFILE`, `CCL_WAREHOUSE_ID` and `CCL_CATALOG` for your own workspace.
