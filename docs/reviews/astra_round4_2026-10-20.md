# Astra (databricks-gpt-6-astra) round-4 verification, 2026-10-20

Raw model output, unedited.

## Final verification â **C+**

**Scope:** static review of the supplied code and reports, not execution. Raw run artifacts, database metadata and HMDA implementation were not supplied.

### 1. Round-3 dispositions

âResolvedâ applies to the specific defect, not to production readiness.

| Item | Disposition and evidence |
|---|---|
| **HIGH artifact verification** | **Partially.** Exact normalized-body comparison replaces substring matching; tamper detected. Signature is still not inspected (`dbx/ccl_on_dbx.py:64â80`). |
| **HIGH merges** | **Resolved.** Same-kind merges are constructed as the OR of parsed constituent expressions, not accepted through sample equivalence (`dbx/ccl_on_dbx.py:174â176`); control `g0` admitted. |
| **HIGH scoped/pending** | **Resolved.** Discount bounds are removed conservatively; ambiguous scopes/no controls are quarantined and excluded (`ccl_sim.py:386â398,412â414,483`). Low-outcome-support âpendingâ remains active, explicitly disclosed. |
| **MED caps** | **Resolved for boundary crossing.** Two-decimal restriction prevents the reported near-15 collapse (`rulec.py:153â157`). However, `Decimal(repr(out))` does **not** establish exact binary representability (`:160`). |
| **MED null contract** | **Partially.** Python rejects referenced null/nonfinite facts (`rulec.py:108â114`); SQL emission has no corresponding rejection, and separately applied cap inputs are outside that validation. |
| **MED truncate/hashes** | **Partially.** TRUNCATE trigger and reported blocked test exist; missing/mismatched simulator hashes fail (`dbx/ccl_on_dbx.py:125â126`; `aggregate_v5.py:22â24`). Dependency hashing and ownership lockdown remain absent. |
| **README 1 â shared helper** | **Partially.** Displayed methods now share it (`ccl_sim.py:405,486`), but âall outcome-aware methodsâ also encompasses the undisplayed `gbm_outcome`, which uses different training eligibility (`:488â489`). |
| **README 2 â winners** | **Partially.** Setting/variant scope is explicit, but near-ties are called highest means using a **0.0005 tolerance** (`make_claims.py:19`). |
| **README 3 â paired labels** | **Resolved.** All six configuration-labelled differences and intervals match the rerun tables (`make_claims.py:21â22`). |
| **README 4 â mechanism** | **Resolved.** âConsistent withâ appropriately limits the inference (`make_claims.py:30`). |
| **README 5 â artifact wording** | **Resolved for body-only wording.** README claims a stored-body check, not complete artifact immutability; appended-clause test reports âdetected.â |
| **README 6 â append-only wording** | **Resolved.** README names UPDATE/DELETE/TRUNCATE protection and explicitly disclaims ownership/DDL lockdown; report confirms TRUNCATE blocked. |
| **README 7 â activated LLM law** | **Not.** The admitted control is compiler-constructed from mined rules, **not LLM-written law** (`dbx/ccl_on_dbx.py:176,402â409`). |

### 2. README evidence-block audit

**Numerical transcription checks pass:**

- Simulation: five seeds; month-36 recovery **7.0/7**, **6.8â7.0/7**; renewal **0.35**; veto **0.997/0.997**; T-learner **0.994/0.997**; screened CCL **0.995â0.996 / 0.963â0.970**.
- Harm shares **1.7%â1.9% versus 0.0%** correctly round **0.0170â0.0193 versus 0.0000**.
- Easy paired differences: **+0.59 [+0.33,+0.86]**, **+0.60 [+0.37,+0.84]**, **+0.60 [+0.37,+0.84]**. Hard: **â1.13 [â1.41,â0.85]**, **â0.84 [â1.23,â0.45]**, **â1.30 [â1.92,â0.69]**. All match by configuration.
- HMDA: one lender, **2018â2023**, **43%/49%**, **+0.01â+0.18 points**, **â0.69/â0.04/â0.11**; only the 2021 GBM-comparison interval excludes zero; denial-recall ordering matches.
- Databricks: **5,029**, zero decision/mask discrepancies, zero admitted LLM proposals, admitted control merge, months **[36,37,38]**, **+0.20 [+0.09,+0.33]**, identity sequence and `bad_law` control all match.

**Qualifier mismatches/overstatements:**

1. Hard/exception is **not an exact highest-mean tie**: paired differences show the veto approximately **0.04 points above** T-learner. Say âtied at three-decimal display precision,â or name the veto alone.
2. âLLM-written law â¦ through the control mergeâ is false provenance. Replace with: **âNo LLM-authored law was activated; a deterministic control merge exercised the merge activation path.â**
3. âScoped CCL avoids the false blockingâ overstates elimination: screening still reduces easy-segment accuracy by **0.10 points**, hard by approximately **0.03**. Say **âsubstantially reduces false blocking.â**
4. Restrict the shared-helper sentence to **the displayed outcome comparisons**.

The exploratory, threshold-oracle, noncausal, conditional-bootstrap, non-equivalence, non-OBO and untested-governance qualifications are supported.

### 3. Remaining/newly exposed code defects

- **HIGH â body-only verification misses altered signatures.** Reordering same-typed Boolean parameters can preserve the body while changing positional-call semantics. Verify ordered parameter names/types, return type and routine identity alongside the body; add a signature-tamper test (`dbx/ccl_on_dbx.py:64â80`).
- **MEDIUM â asymmetric null enforcement.** SQL can evaluate unknowns where Python raises; cap-only `disc` references bypass AST validation. Enforce one input contract before both runtimes, including cap columns, and execute NULL/NaN/infinity differential tests.
- **MEDIUM â generated provenance claim is unconditional.** Proposal counts exclude merge admissions, yet the generator always claims activation only through the control (`make_claims.py:45â54`). Record explicit source tags and derive wording from both proposal and merge outcomes.

### 4. Final assessment

The READMEâs **reported numerical evidence is now substantially supported**, and the engineering narrative is materially narrower and better tested. Nevertheless, inaccurate LLM provenance, tolerance-based winner wording and incomplete artifact/null contracts prevent an unqualified endorsement. Correct those claims and close the remaining verification gaps before presenting the README as fully verified. This is a credible exploratory demonstrationânot independent validation, evidence of causal policy value, or a production governance guarantee.