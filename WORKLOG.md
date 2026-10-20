# WORKLOG: CLM paper study → Corporate Case Law (CCL)

Decisions are in `docs/ADR.md`. Results come from `RESULTS.md` (auto-generated). Dates are 2026.

## 15 Oct: studying the CLM paper
- Fetched arXiv 2609.04377 (Avini & Trez, Unisinos / Care Intelligence, posted 03 Sep, 22 pp, cs.AI). Paper: https://arxiv.org/abs/2609.04377.
- Full read and critique are in `docs/CLM_PAPER_NOTES.md`. Verdict: good vocabulary and one buildable pattern (guarded generation), not evidence.
- Built Board 1 (12 zones) as a hand-drawn whiteboard (ADR-001). Three render-and-fix passes: arrow routing in zone 1, ring labels in zone 6, real-world label. Loaded in excalidraw.com in the isolated context (ADR-002).

## 16 Oct: guided tour, then the CCL idea
- The user asked for a step-by-step walk. Zoomed to zone 1 and explained it; the user then asked for it to run automatically.
- Injected a self-advancing tour of stops 2-12: narration panel, camera glide, timed self-test reveal (ADR-003). Caught a paper inconsistency while writing stop 7: §7.2 says stages 5-6 are "in design", but §7.3 says the hospital spec was "compiled into the four artifact types".
- The user asked for an original, untested, valid approach to corporate context on Databricks. Proposed **Corporate Case Law**: tacit = residual of policy, holdings as predicates, replay admission, appeals, outcome weighting, decay (ADR-004…007).
- Prior-art agent: verified the Solozobov arXiv IDs and found the Foundation Capital "Context graphs" essay myself (quote: "decision traces - the exceptions, overrides, precedents…"). The agent's "none" for appeals/decay is wrong (CBR 4R loop, concept drift). Its "70% novel" and patent suggestion were not adopted. Novelty narrowed to "CI/CD for corporate context" (ADR-016).
- **v1 simulation** (`v1/ccl_sim.py`): 60K decisions, 24 months, 7 planted rules, 4% noise, 3 seeds, miners tree / covering / schema. Reported: schema CCL 0.931 vs black box 0.954 vs policy 0.809 ("84% of gap"), 3/7 rules recovered exactly, rogue rule flagged 9/9. Later shown to be overstated (see 19 Oct).
- Built Board 2 (8 zones) to the right of Board 1 on the same canvas; combined file `whiteboard/combined.excalidraw`.

## 19 Oct: ECC install + review, then v2
- Installed `ecc@ecc` 2.2.3 at project scope, hooks `standard`, rules `common` + `python` (ADR-015). It adds about 33K tokens per session.
- Ran ECC `python-review` headless and read-only → `ecc_python_review.md`. Verified its main claims against the result files:
  - v1's 0.931 includes the rogue rule; with the filter it is 0.877 = 47% of the gap.
  - "9/9 flagged" is circular (planted 0.35 vs 0.85) and leaks the future (renewal read before the term ends).
  - Recovery was scored mostly on training months.
  - R5 was unreachable (quantile thresholds).
  - `run_seed7.json` duplicated `run_tree_7.json`.
  - Corrected the memory note.
- **v2** (`ccl_sim.py`), applying ADR-006…013:
  - 120K decisions over 48 months; outcomes visible only at month + 12·term.
  - Scored vs_actual and vs_good; fresh-sample recovery; round size literals; regression-safe admission; R1 retired at month 40 to test decay; miner recorded in output; `aggregate.py` generates the results.
- Bugs found during v2 (mine, not the reviewer's):
  1. The miner checked loosening precision before accounting for the stricter Germany rule → R4/R5 looked impure. Fix: mine tightening first (ADR-011).
  2. The outcome-aware black box trained on 12 months, where no outcome is known yet → it scored identically to the plain one. Fix: a 24-month window (ADR-010).
  3. The recovery metric used binding-rule semantics, so word-for-word correct holdings scored 0. Fix: "rule applies" semantics, disclosed as post hoc (ADR-012).
- The first v2 grid (before fixes 1-2) is kept in `runs_prefix/`. The final grid, 18 runs = 3 seeds × 3 miners + schema × outcome sweep {0.55, 0.70, 0.85}, is in `runs/`.
- **v2 results** (schema miner, mean of 3 seeds; full tables in RESULTS.md):

  | | statute | GBM | GBM+outcomes | CCL | CCL+bad-law filter |
  |---|---|---|---|---|---|
  | vs_actual | 0.805 | 0.958 | 0.953 | 0.955 | 0.902 |
  | vs_good | 0.888 | 0.941 | 0.936 | 0.938 | 0.994 |

  - Rule recovery: 6.7/7 word for word (tree miner 0.7/7, covering 3.3/7).
  - Bad law flagged from the first test month at renewal 0.35 and 0.55; not flagged at 0.70 (threshold 0.20); no false flag at 0.85 (null).
  - The R1 holding is admitted months 36-40 and dropped at month 41 (retired at 40).
  - Kill rule: +15.0 pts and 6.7/7 → survives (synthetic only).
- Board 2 zones 5, 6 and 8 now read `summary.json` (ADR-013). Reloaded in excalidraw.
- Ops: the browser-automation tool lost its own Chrome instance; restarted it in a fresh isolated context and reloaded the board.

## Open caveats (carry with every quote of the numbers)
1. Synthetic data only.
2. Planted rules share the miner's shape (conjunction + cap). The next experiment breaks this.
3. The recovery metric was changed after seeing results (justified, disclosed).
4. The outcome-aware baseline is naive relabelling; an uplift model is missing.
5. "vs_good" is defined by the simulator.

## Next (as of v2)
1. Hidden rules outside the miner's shape: OR rules, interactions, odd thresholds, rules split across two literals the schema doesn't have.
2. An LLM writes the "because" from justification text and merges fragments.
3. Real decision data (pricing approvals / claims / refunds) on sandbox workspace: Delta time travel replay, Lakebase branch per candidate, UC functions as holdings.

## 19 Oct (later): v3: hard world + fair black box
- Committed v2 to a local git repo (`git init`, no remote) so v3 is diffable. Added `tests/test_smoke.py` (6 fixed-seed tests, all passing).
- **Hard world** (ADR-017): hidden rules outside the v2 miner's shape:
  - H1 OR rule (enterprise OR deal > 1M)
  - H2 term-scaled cap (15+3·term, +5 if churn risk)
  - H3 odd threshold (> 340k)
  - H4 a field v2 never used (customer tenure >= 11y; first tried >= 7y, which covered 56% of deals, so tightened)
  - H5 negation (competitor outside France)
  - plus the same rogue and Germany rules
- **Beam miner** (ADR-018): generic literals built from every column (= / != categories, booleans and NOT, numeric deciles plus round sizes), beam search to depth 3.
- **Fairest black box** (ADR-019): GBM plus a renewal model that vetoes exceptions predicted to renew >= 0.20 worse. Same outcome information and threshold as the bad-law filter, no rules.
- **Bug found by error analysis** (ADR-020): the stricter Germany holding could only override cases inside the policy, so loosening holdings (e.g. "competitor outside France <= 26%") approved German SMB deals above 15%. That caused 1,345 false approvals on one fresh sample. It was also present in v2, with lower impact. Fix: stricter law overrides any approval, plus a regression test. The first v3 grid was killed and re-run.
- Recovery check redone so the stricter rule applies at any discount. Added **rule fidelity** (share of each hidden rule's cases decided like the rule) because "exact" was too lenient for approximated rules (ADR-021). Recovery is recomputed from the stored SQL in `aggregate_v3.py`.
- 33 runs in `runs_v3/` → `summary_v3.json`, `RESULTS_v3.md`. Board 2 zones 6 and 8 now read v3. Reloaded in excalidraw.
- **v3 results** (beam miner, mean of 3 seeds):

  | | policy | GBM | GBM+renewal veto | CCL | CCL+bad-law |
  |---|---|---|---|---|---|
  | hard vs_actual | 0.691 | 0.958 | 0.903 | 0.929 | 0.905 |
  | hard vs_good | 0.747 | 0.957 | 0.976 | 0.958 | 0.980 |
  | easy vs_actual | 0.805 | 0.958 | 0.903 | 0.959 | 0.907 |
  | easy vs_good | 0.888 | 0.941 | 0.991 | 0.942 | 0.999 |

  - Hard world, beam: 6.7/7 rules found. Decisions match the hidden rules 95% of the time. The v2 hand-picked miner gets 3.7/7, tree 0.3/7.
  - Weak spots: the OR rule keeps one branch; the negation rule is 85% faithful; the tenure rule is 80% covered. The beam miner takes about 13 minutes per run.
  - Kill rule (hard world): +23.8 pts over policy, 6.7/7 → survives.
- **Verdict:** the v2 claim "beats the black box" does not survive a fair baseline. With the same outcome information and threshold, a black box matches CCL on the well-run target (easy 0.991 vs 0.999; hard 0.976 vs 0.980) and beats it on the logged decisions in the hard world (0.958 vs 0.929). CCL's real edge is the **form**: about 8 readable, executable, testable, governed rules, plus a named "bad law", at roughly equal accuracy.

## Next (updated)
1. An LLM writes the "because" from justification text and merges OR branches.
2. Real decision data on sandbox workspace: time-travel replay, a Lakebase branch per candidate, UC functions as holdings, OBO checker.
3. Speed up the beam miner (13 min/run) before real volumes.

## 19 Oct (evening): "go ahead, ECC on 1, 2, 3"
- **#3 speed (ECC `performance-optimizer`, headless):** `mine_beam` vectorised, 8.5× faster per window (2.31 s → 0.27 s); full hard-world run 40.7 s → 19.9 s. Frozen-reference equivalence tests added (16 tests pass). I verified independently that holdings are identical at both snapshots against the v3 grid. ECC corrected my "13 min per run": that number came from 7 runs contending for threads (sys 1188 s), not from the miner.
- **#2 Databricks build** (`dbx/`, a personal Databricks sandbox workspace): Delta decisions loaded month by month (versions 0-144, edits after decisions, outcomes when known), UC functions as holdings, Lakebase project `ccl-law` with one branch per candidate, law registry in Lakebase, DBSQL replay, FMAPI Claude/GPT. Full write-up in `dbx/REPORT.md`.
- **#1 LLM:** rationale 9/9 matched (rogue rule flagged incoherent); 3 LLM-proposed rules, all rejected by the moot court; no merges.
- **Agent:** 32/32 matched the executable law. Injection test: Sonnet 0/10 followed; gpt-5.4-nano without a warning followed 2/10 with 5 invalid citations; the checker blocked 6 and shipped 0 wrong decisions.
- Bugs and gotchas (all in REPORT.md):
  - nanosecond parquet timestamps;
  - my first point-in-time read included later edits (facts changed 0.0) → fixed with per-decision version slices (11.6% changed);
  - FMAPI content blocks;
  - an injection test that selected 0 deals;
  - the Lakebase active-endpoint cap → disable compute after each trial; read-write endpoints can't be deleted.

## 20 Oct: public repo + four follow-ups
- Published as **github.com/HadiFrt20/corporate-case-law** (public, single clean commit, HadiFrt20 noreply author). Before publishing: workspace identifiers moved to env vars (`CCL_DATABRICKS_PROFILE`, `CCL_WAREHOUSE_ID`, `CCL_CATALOG`), internal references removed, ECC rule files and logs untracked, boards made self-contained. The private local history stays on the local `master` branch.
- **#3 the missing OR branch (deals > 1M):** a power problem, not a blind spot (~7 qualifying deals per month; purity ~0.8 against the 0.9 bar; under 15 cases in a 2-month admission window). Two fixes: Wilson-lower-bound mining (`beam_power`: support 25, LB >= 0.8) and a 4-month admission window (`--adm-months 4`). Branch fidelity: v3 0.52; longer admission only 0.50; power-aware only 0.72; **both 1.00**. Cost: extra admitted rules (logged accuracy 0.929 → 0.914). Best overall well-run-target result: longer admission only (0.985). Correction: I first said "longer admission alone gives 0.72"; it is power-aware alone that gives 0.72.
- **#4 proper uplift baseline:** a T-learner (exception-approved vs policy-approved renewal models, veto when tau < -0.20) did WORSE than the simple veto. Diagnosis: my simulator made the rogue approver's whole book renew badly, including in-policy deals, so the discount was not causal. Added `--rogue-effect exception` (only above-policy approvals renew badly) and a scoped bad-law reference (`--law-ref scoped`: policy approvals in the holding's own population). Result (`RESULTS_causal.md`): when the exception causes churn, CCL's filter 0.999 vs renewal veto 0.990 vs T-learner 0.980 (easy), 0.985 vs 0.974 vs 0.962 (hard); when the segment churns anyway, the scoped filter correctly stays quiet. v3's "a fair black box ties CCL" came from a correlational simulator.
- **#2 real decisions:** one US lender (U.S. Bank, public LEI), HMDA 2018-2023, about 222K conventional purchase applications; statute = QM 43% DTI cap; yearly replay. CCL (power-aware) 0.933/0.931/0.933 vs black box 0.940/0.931/0.934 vs always-approve ~0.91. Mined tacit rule: approve up to 49% DTI unless underwritten by TOTAL; stricter rule: jumbo with LTV > 90 rejected, "because" = collateral 66-75% of denial codes; both stricter rules fail the four-fifths fairness audit, so they go to steward review. A research agent recommended COMPAS; rejected (no logged decisions against a written policy; unsupported claims). Full table: `real/hmda/REPORT.md`.
- **#1 Board 2:** zones 9 (Databricks run), 10 (real lender), 11 (rare rules + causal check), all read from result files.

## 20 Oct (afternoon): Astra review → v5 fixes (all re-run)
- Astra (`databricks-gpt-6-astra`) reviewed the whole repo: grade D, `docs/reviews/astra_review_2026-10-20.md`. I verified its key claims before acting; the most damaging one was confirmed: the uplift baselines trained on a 24-month window in which **0** two- or three-year renewal outcomes were knowable, while CCL's screen used all history (3,200 two-year outcomes). My "same outcome information" claim was false.
- **Simulator fixes** (`ccl_sim.py`, tests in `tests/test_v5.py`):
  - one `outcome_rows()` used by every outcome-aware method;
  - a harm-aware oracle that depends on the causal mechanism and effect size (`vs_good` renamed `vs_nonrogue_oracle`, kept as legacy);
  - harmful-approval and false-rejection decomposition;
  - canonical order-independent attribution shared with the SQL replay;
  - shadowed incumbents block admission;
  - final precision recomputed;
  - scoped screen returns `pending_no_controls` instead of silently falling back;
  - `exact` → `overlap_recovered` (any qualifying candidate);
  - single-class tree leaves;
  - `reset_config()` isolates dataset configuration;
  - `step()` refactor with leakage-invariance tests (future rows and not-yet-known outcomes changed → identical law).
- A job-script bug on my side (zsh does not word-split variables) silently produced 120 failed runs on the first launch; rerun with explicit loops. 180 runs, 5 seeds.
- **v5 simulation result:** with equal information CCL's outcome screen does NOT beat case-level baselines. Exception-causes-harm world: veto / T-learner 0.997 vs CCL 0.996 (easy) and 0.967-0.970 (hard), because harm routed through other overlapping rules escapes a rule-level screen (1.7-1.9% harmful approvals). Segment world: the scoped screen is correct (no flag), the global screen and the veto wrongly block; the T-learner is best across both worlds. The earlier "beats uplift baselines" margin came from the information gap.
- **HMDA fixes:**
  - "43% DTI heuristic" naming;
  - action-code assertion and cohort-flow table;
  - group audit on the final system's decisions;
  - tuned GBM (4-config grid chosen on the admission year);
  - learned single DTI cutoff baseline;
  - CCL variant chosen in advance by admission-year accuracy;
  - state-clustered paired bootstrap CIs;
  - balanced accuracy and denial recall;
  - a no-workflow-fields run.

  Result: the learned cutoff is 49 every year and CCL is within +0.01 to +0.18 pts of it; CCL minus tuned GBM is -0.69 [-0.88, -0.50] (2021), and the 2022/2023 CIs include 0; GBM detects denials better.
- **Databricks fixes:**
  - `dbx/rulec.py` trusted compiler (20 adversarial tests);
  - LLM-origin rules go through compiler → moot court → outcome screen before activation (control: the re-proposed rogue rule was admitted on accuracy, then blocked as bad law);
  - content-addressed immutable UC functions;
  - append-only registry with data and compiler versions;
  - one admission rule shared by both point-in-time arms, judged on untouched months 36-38;
  - Python/SQL parity check;
  - identity-scoped execution test with a second principal;
  - escaped SQL literals.

  Result: point-in-time +0.20 pts [+0.09, +0.33]; parity 0/5,029; strict judge 7/9; LLM returned no proposals this run (empty reply).
- **HMDA download recipe:** `curl -sL --compressed "https://ffiec.cfpb.gov/v2/data-browser-api/view/csv?years=<YEAR>&leis=6BYL5QZYBDK8S7L73M02&actions_taken=1,3" -o real/hmda/raw/usb_<YEAR>.csv` for 2018-2023. At most 2 filters; follow redirects.

## 20 Oct (evening): Astra re-review (grade D → C) → round-2 fixes
- Re-review: `docs/reviews/astra_rereview_2026-10-20.md`. It verified the core repairs (information gap, fair point-in-time contrast, compiler) and found, among others:
  - **my README simulation paragraph was numerically wrong**, written from memory rather than from `RESULTS_v5.md`;
  - "append-only registry" was false (upserts and updates);
  - compiler holes (caps, overflow, rounding, bounds);
  - merges tolerating a 0.1-point loss;
  - Python/SQL screen populations differing;
  - recovery ignoring the action;
  - the harm-threshold float boundary;
  - an incomplete error decomposition;
  - an identity test that never invoked the checker.

  All confirmed against code and tables before fixing.
- **Fixes:**
  - **Simulator:** `good_law` uses `effective()` (same population as SQL), scoped controls for tree rules (`rule_population`), inclusive harm boundary, recovery requires the same action, full-precision run metrics with `code_sha`, `nonharmful_false_approvals` so the components sum to total error, "overlapping effective coverage" naming.
  - **Compiler:** `rulec.py` moved to the root as `rulec-2`: AST shared by Python evaluation and SQL emission, exact decimals, length/token/depth/digit bounds, per-column domains, `validate_cap`.
  - **Databricks:** `law_events` append-only enforced by a trigger plus a `law_current` view; SHA-256 function names with body verification; merges must be decision-equivalent and of one action kind, with no accuracy loss; whole-law re-screen after LLM admissions; tightening rules not outcome-screened; parity on decisions AND per-rule support, before and after the LLM steps; final-stats events; one `check()` run under the owner and a second principal, with asserted denials and grants revoked in `finally`.
  - **HMDA:** "retrospective, admission-selected" wording; per-comparison deterministic seeds; 2,000 resamples; cluster diagnostics; group error tables; denial-reason denominators.
  - **README evidence block** now GENERATED by `make_claims.py` from the result files.
- **Process mistake (mine):** I edited `ccl_sim.py` while the v5.1 grid was running. I stopped the grid, cleared its runs, and relaunched after the code was final. The aggregator now fails closed on a manifest (every configuration × seed) and on a single `code_sha`.
- New tests: a shadowing fixture that passes every other gate, recovery action, boundary, error-sum, scoped tree screen, screen population; compiler bound and cap tests.

## 20 Oct (late): Astra round 3 (stays C; no number mismatches in the generated README) → round-3 fixes
- `docs/reviews/astra_round3_2026-10-20.md`: all README numbers matched the tables. The remaining issues were guarantees stated more strongly than the code enforced. Fixes:
  - **Function verification:** exact comparison of the stored routine body from `information_schema.routines` (was a substring test); a tamper test (`OR true` appended) must be detected.
  - **Registry:** a TRUNCATE-blocking trigger, verified live.
  - **Merges:** built as the exact OR of the parts' ASTs (`rulec.union`); the LLM only picks ids. A CONTROL merge of two admitted rules exercises activation of compiled law and post-merge parity.
  - **Parity:** per-rule case-by-case masks.
  - **Scope:** AST and literal scopes strip top-level bounds on the policy variable (ambiguous scope → no controls); scoped rules with no comparable controls are QUARANTINED, not active.
  - **Shared helper:** CCL's screen now literally calls `outcome_rows`.
  - **Compiler (`rulec-3`):** caps must be plain decimals with at most 2 decimals and exactly representable; a null/non-finite fact contract.
  - **Aggregator:** rejects missing hashes and requires the run hash to equal the imported simulator's hash.
  - **README wording:** "highest observed mean … not a significance claim", configuration-labelled paired differences, softened mechanism sentence.
- Grid re-run on the final simulator code (manifest + hash checks); Databricks pipeline re-run.

## 20 Oct (late): Astra round 4 → C+ (all README numbers re-verified)
- `docs/reviews/astra_round4_2026-10-20.md`. Fixes:
  - **README wording:** exact maximum for "highest observed mean" (no tolerance); shared-helper sentence restricted to the displayed comparisons; "substantially reduces" false blocking; corrected provenance (no LLM-authored law was activated; a deterministic control merge exercised the merge path; merge provenance derived from source).
  - **Signature verification:** ordered parameter names/types and return type from `information_schema` (`LONG` is normalised to `BIGINT`); standalone `dbx/integrity_check.py`: 9/9 active functions pass and a signature-tamper copy (two BOOLEAN parameters swapped) is detected.
  - My first integrity run reported 9/9 failures because of that type alias. The check's assertion caught it before any claim was made.
- **Still open:**
  - asymmetric null handling between Python and SQL (SQL three-valued logic is not mirrored);
  - dependency hashing beyond `ccl_sim.py`;
  - DDL ownership lockdown;
  - grants restored by revoke only;
  - independent evaluation.
