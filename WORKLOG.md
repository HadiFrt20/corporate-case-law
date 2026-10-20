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
