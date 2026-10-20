# Response to Astra round 4 (2026-10-20)

| Item | Status | Evidence |
|---|---|---|
| Winner tolerance | FIXED | `make_claims.py`: exact maximum, with a pointer to the paired intervals for near-ties. |
| False LLM provenance | FIXED | Merge/proposal provenance derived from source tags; README states no LLM-authored law was activated. |
| "Avoids" false blocking | FIXED | "Substantially reduces". |
| Shared helper scope | FIXED | Restricted to the displayed comparisons (screen, veto, T-learner); `gbm_outcome` is not displayed. |
| HIGH signature not verified | FIXED | `verify_fn` checks ordered parameter names/types and return type; `dbx/integrity_check.json`: 9/9 pass, signature tamper detected. |
| MED null contract asymmetry | NOT FIXED | Python rejects nulls; SQL three-valued logic is not mirrored. Generated data has no nulls; documented as open. |
| MED cap repr check wording | ACKNOWLEDGED | Two-decimal restriction prevents boundary crossing; `Decimal(repr())` is a round-trip check, not proof of exact binary representation. |
