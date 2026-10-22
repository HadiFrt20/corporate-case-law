# Response to Astra's review of the autoresearch loop (round 2, grade B-)

| Finding | Status | Change / evidence |
|---|---|---|
| Child imports the real simulator (planted easy/hard rules readable) | PARTIAL (accepted) | not a sandbox; prohibited in program.md; the fresh panel generates worlds at run time. |
| Seeds, worlds and draw ids readable on disk | PARTIAL | unchanged; noted in AR-009. |
| "Four conditions" is really four literals plus a cap | FIXED (wording) | program.md and harness docstring say literals + cap. |
| validate() does not literally reject all extra keys | FIXED (wording) | docstring: it reconstructs only kind / lits / cap, flags ast / conds, drops other keys. |
| A literal on a field missing in the world crashes | FIXED | harness turns it into a violation; test `test_law_on_a_missing_field_is_invalid_not_a_crash`. |
| MONTH_TIMEOUT_S unused; readline can hang | FIXED | select-based timeout; test `test_hanging_method_times_out`. |
| Dev panel is 16 configs; program.md stale | FIXED | program.md and harness docstring updated. |
| Baselines: fixed, retrospective, T-learner extrapolates | ACKNOWLEDGED | wording "best of five fixed baselines, selected retrospectively"; competitive tuning open (AR-013 follow-up). |
| CI over configs is not confirmatory; margin unjustified | OPEN -> AR-013 | confirmatory test will cluster by world and justify the margin before the run. |
| Goodhart record: the fix was adaptive even if principled | ACCEPTED | AR-012 wording kept; this table notes it. |
| Overrule description overstates the test | FIXED | method.py docstring now states the actual rule (z vs zero, skipped cells do not object). |
| Search multiplicity, wrong null (vs 0, not vs 0.20), small cells as permission, marginal refinement | OPEN -> AR-013 | the falsification experiment measures false-overrule rates and power before any change. |
| GC leak probe defective; positive control only covered frames | FIXED | probe inspects pandas Index safely; positive control now covers the GC route on its own. |
| Outcome-timing test used the code under test as oracle | FIXED | `test_outcome_timing_handcrafted`. |
| Untested: 45-literal boundary, end-to-end AST rejection, timeouts, malformed protocol, pruning / exclusion fixes | MOSTLY FIXED | boundary, AST and timeout tests added; pruning / symmetric-exclusion unit tests still open. |
| Do not draw another fresh panel before a frozen falsification experiment | DISCLOSED | fresh run 2 had already been launched before the review was read; logged as such (WORKLOG). No further draws until AR-013 step 2. |
