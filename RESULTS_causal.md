> **SUPERSEDED by `RESULTS_v5.md`.** Kept for the record. Produced before the v5 fixes (equal outcome information for baselines, harm-aware oracle, canonical attribution, shadowing check); numbers and wording here (e.g. "vs_good", "exact", causal language) should not be quoted.

# Causal check: is the bad-law filter measuring the EXCEPTION's effect or the segment's? (auto-generated)

rogue effect: `segment` = the rogue approver's whole book renews badly (v1-v4); `exception` = only above-policy approvals renew badly (the discount causes churn).
bad-law reference: `global` = all policy approvals; `scoped` = policy approvals in the holding's own population (a within-population control, like a T-learner).

| world | rogue effect | reference | rogue renewal | months flagged | CCL+bad-law vs_good | GBM+renewal veto | GBM+T-learner |
|---|---|---|---|---|---|---|---|
| easy | exception | global | 0.35 | 100% | 0.999 | 0.990 | 0.980 |
| easy | exception | global | 0.55 | 100% | 0.999 | 0.976 | 0.966 |
| easy | exception | global | 0.7 | 0% | 0.942 | 0.951 | 0.950 |
| easy | exception | global | 0.85 | 0% | 0.942 | 0.939 | 0.936 |
| easy | exception | scoped | 0.35 | 100% | 0.999 | 0.990 | 0.980 |
| easy | exception | scoped | 0.55 | 100% | 0.999 | 0.976 | 0.966 |
| easy | exception | scoped | 0.7 | 0% | 0.942 | 0.951 | 0.950 |
| easy | exception | scoped | 0.85 | 0% | 0.942 | 0.939 | 0.936 |
| easy | segment | global | 0.35 | 100% | 0.999 | 0.991 | 0.949 |
| easy | segment | global | 0.55 | 100% | 0.999 | 0.975 | 0.947 |
| easy | segment | global | 0.7 | 0% | 0.942 | 0.950 | 0.943 |
| easy | segment | global | 0.85 | 0% | 0.942 | 0.939 | 0.936 |
| easy | segment | scoped | 0.35 | 0% | 0.942 | 0.991 | 0.949 |
| easy | segment | scoped | 0.55 | 0% | 0.942 | 0.975 | 0.947 |
| easy | segment | scoped | 0.7 | 0% | 0.942 | 0.950 | 0.943 |
| easy | segment | scoped | 0.85 | 0% | 0.942 | 0.939 | 0.936 |
| hard | exception | global | 0.35 | 47% | 0.985 | 0.974 | 0.962 |
| hard | exception | scoped | 0.35 | 47% | 0.985 | 0.974 | 0.962 |
| hard | segment | global | 0.35 | 47% | 0.985 | 0.976 | 0.949 |
| hard | segment | scoped | 0.35 | 0% | 0.967 | 0.976 | 0.949 |
