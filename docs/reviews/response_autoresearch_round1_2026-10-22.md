# Response to Astra's review of the autoresearch loop (round 1, grade C+)

| Finding | Status | Change / evidence |
|---|---|---|
| 1. Method runs in the harness process: caller frames hold firm, seed, oracle; ccl_sim globals expose the world | FIXED | `runner.py`: separate `python -I` process per configuration, pickled view only (AR-009). Test: a method that searches `inspect.stack()` and `gc` for the firm finds nothing; the same probe in-process does (positive control). |
| 1. `outcome_rows` patchable before `view_of` | FIXED | the view is built in the harness process; a method that patches `outcome_rows` and `apply` has no effect on scoring (test). |
| 1. Scorer passes current `approved` / `renewed` to `apply` | FIXED | `DEC_COLS` only (deal fields, disc, statute), and the literal grammar forbids those fields anyway. |
| 1. Seeds and alt rules readable on disk | PARTIAL | still readable (not a sandbox); prohibited in `program.md`; the new fresh panel draws worlds and seeds at run time. |
| 2A. Monkeypatching `generic_literals` | FIXED | miner copied into `method.py` with literals passed in (AR-010); AR-007 closed. |
| 2B. AST holdings escape the condition limit | FIXED | only `{kind, lits, cap}` holdings are accepted; AST / conds rejected (test). |
| 2C. Literals not restricted to decision fields | FIXED | strict grammar over nine deal fields (tests for approved, renewed, statute, outcome_known, month, disc, injection-like strings). |
| 2D. Caps, conds, rule objects, SQL rounding | FIXED / N.A. | finite caps in range; conds removed; plain JSON only; SQL rendering is not used by the loop. |
| 3. "Best black box" means best of 3 fixed GBM variants | FIXED (wording) / PARTIAL | added a 15-leaf tree and tree + veto baselines; the claim is now "best of five fixed baselines"; competitively tuned baselines not done. |
| 3. Baseline winner chosen by test-oracle agreement | KEPT, DISCLOSED | the comparator is retrospective (it favours the baselines). |
| 3. T-learner extrapolates across the discount threshold | ACKNOWLEDGED | kept as specified in v5 for comparability; noted. |
| 3. Baselines computed after the method mutated the simulator | FIXED | baselines computed in workers that never import the method. |
| 3. No uncertainty, no non-inferiority margin, false rejections hidden | FIXED | 95% t-interval over configs (flagged as optimistic), margin -0.25 pts for monitor / fresh, false rejections and harm caught printed. |
| 3. Holdout became a monitoring set | ACCEPTED | renamed `monitor`; a `fresh` panel (generated worlds, seeds drawn at run time) runs once per locked method. |
| 4. Kept changes may be tuned to the planted rules | OPEN | to be tested by the fresh panel and parameter neighbourhoods (next experiments). |
| 4. Striking by historical containment; pruning before truncation | FIXED | strike only by logical implication; choose overrules that fit first (AR-010). |
| 5. Overrule detector is an association heuristic | ACCEPTED | wording changed to "refinement-screened observational overrule"; stress panel shows it is fooled by unobserved confounding like every outcome-aware method (AR-011). One-literal refinements only, small cells skipped, no search-adjusted error control: open, next experiments. |
| 5. Asymmetric exclusion of overruled rows | FIXED | both arms exclude them (AR-010). |
| 6.3 Stress tests for the harm detector | DONE (first set) | below / above threshold and non-causal confounding (AR-011). |
| 6.4 Discovery / confirmation split for overrules | OPEN | next experiment. |
| 6.6 Ablations and neighbourhoods | STARTED | the moot-court ablation (AR-008); neighbourhoods next. |
