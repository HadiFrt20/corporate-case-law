# Response to Astra's review round 3 (record B+, loop B+, claims B)

| Finding | Status | Change |
|---|---|---|
| Pre-registration order consistent; path fix post-registration but infrastructural | ACCEPTED | disclosed in AR-014 / WORKLOG |
| Simulator not pinned by the manifests | ACKNOWLEDGED | AR-019: no commits to ccl_sim.py / rulec.py during the line (git evidence, CODE_SHA); pin in the next line |
| "never sees the seed, the world" too categorical | ACCEPTED | wording: the harness does not pass them through the protocol (AR-009 already says "not a sandbox") |
| Partial-line timeout, invalid-run cache writes, two CIs printed | OPEN | AR-019 |
| Both intervals contain -0.25 | FIXED | README (generated) and AR-018 corrections say so |
| Two looks disclosed, not controlled | ACCEPTED | both failed; a future line needs an alpha allocation |
| H2 falsified the remedy, not every joint-confounding account | FIXED (wording) | AR-018 corrections |
| Attribution is direct, not pipeline-level | FIXED (wording) | AR-018 corrections |
| AR-018 claim wording (best CCL, "at all", search adjustment scope) | FIXED | AR-018 corrections; README text derived from results |
| README generator hard-codes FAILED | FIXED | verdict derived from parsed results with an assertion against the registered rule |
| README "Nothing here is a confirmatory test" | FIXED | status paragraph rewritten |
