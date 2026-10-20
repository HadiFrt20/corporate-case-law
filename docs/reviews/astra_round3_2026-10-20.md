# Astra (databricks-gpt-6-astra) round-3 verification, 2026-10-20

Raw model output, unedited.

## Verdict: **C â substantial improvement, but not a B**

The reported numerical comparisons are now consistent. The remaining blockers are engineering guarantees that exceed what the code enforces, incomplete differential testing, and no independent evaluation.

**Scope:** static verification of the supplied files, not execution. Raw runs, HMDA implementation, database helpers/loading code and audit records were not supplied.

## 1. C1âC13 disposition

âResolvedâ may mean the claim was appropriately narrowed, not that the broader experiment was completed.

| Issue | Disposition | Evidence |
|---|---|---|
| **C1 Numerical README** | **Partially** | Numbers now match; âBest per settingâ silently maximizes over variants and only renewal 0.35 (`make_claims.py:12â19`). |
| **C2 Complete compiler** | **Partially** | Conditions are substantially hardened, but cap validation returns a potentially boundary-changing float (`rulec.py:123â131`); no SQL execution occurs in the purported AST parity unit test (`tests/test_rulec.py:64â69`). |
| **C3 Registry/artifact integrity** | **Partially** | Events replace mutable rows, but the trigger omits TRUNCATE and artifact verification is substring matching (`dbx/ccl_on_dbx.py:64â70,111â115`). |
| **C4 Merge contract** | **Response wrong** | Same-kind and no-loss checks are fixed; equality on observed mining/admission rows is **not** semantics-preserving compression (`dbx/ccl_on_dbx.py:164â172`). |
| **C5 Screening consistency** | **Response wrong** | Effective populations improved, but AST/literal scopes retain discount conditions while tree scopes remove them; CCL still does not call the helper (`ccl_sim.py:386â403`). |
| **C6 Attribution/parity/statistics** | **Partially** | Final statistics and isolated shadowing test are real; parity compares decisions and aggregate support only, not masks, precision, admission or screen results (`dbx/ccl_on_dbx.py:236â243,398â402`). |
| **C7 Recovery/fidelity** | **Partially** | Wrong-action credit fixed (`ccl_sim.py:437`); branch metric remains positive-case system approval, without exclusive-effect/negative controls (`aggregate_v5.py:47â54`). The promised explanatory label is absent from RESULTS. |
| **C8 Harm boundary/decomposition** | **Partially** | Third component and boundary test added (`ccl_sim.py:98,503`); oracle rounding, screen tolerance and strict baseline comparisons still implement different boundary conventions (`:418,495â496`). |
| **C9 Provenance/intervals** | **Partially** | Full-precision aggregate accuracy and manifest are improvements; homogeneous missing hashes pass, and loaded code need not match run code (`aggregate_v5.py:22â23,41â45`). |
| **C10 Point-in-time estimand** | **Resolved â wording only** | README/report correctly condition **+0.20 [+0.09,+0.33] points** on this one run; robustness remains untested. |
| **C11 Checker identity** | **Partially** | Same checker, identity equality, denial causes and final assertion now exist; cleanup revokes rather than restores prior grants and suppresses function-revoke failures (`dbx/ccl_on_dbx.py:259â289,432`). |
| **C12 HMDA inference** | **Resolved â reporting** | Report states retrospective selection, conditional **2,000** state-bootstrap resamples and **51** clusters; implementation changes cannot be independently checked without the HMDA source. |
| **C13 Reproducibility/audit outputs** | **Partially** | Race error rates and reason denominators published; future vocabulary and SQL-string reconstruction remain (`ccl_sim.py:472`; `aggregate_v5.py:33â37`). |

## 2. README evidence-block audit

### Numbers: **no transcription mismatch found**

- **Simulation:** recovery **7.0/7, 6.8â7.0/7**; veto **0.997/0.997**; T-learner **0.994/0.997**; screened CCL **0.996/0.963â0.970** all match RESULTS.
- Harm shares **1.7%â1.9% versus 0.0%** correctly round **0.0170â0.0193 versus 0.0000**.
- All displayed scoped-CCL-minus-T-learner point estimates and interval endpoints match. The easy-world **+0.70 [+0.47,+0.92]** occurs for two variants.
- **HMDA:** **43%, 49%, +0.01â+0.18**, and **â0.69/â0.04/â0.11** match. Only the 2021 GBM comparison interval excludes zero; GBM denial recall is higher in all three years.
- **Databricks:** **5,029**, zero mismatches before/after, months **36â38**, **+0.20 [+0.09,+0.33]**, permission sequence and `bad_law` control match its report.
- Exploratory/oracle/association qualifications, non-equivalence, non-OBO and untested governance are appropriate.

### Exact wording fixes still needed

1. **Shared helper:** replace  
   > âAll outcome-aware methods share one eligibility rule (`ccl_sim.outcome_rows`).â  
   with  
   > âThe displayed outcome comparisons use equivalent historical eligibility restrictions; CCL currently implements them separately from `outcome_rows`.â

2. **Winner scope and ties:** replace âBest per settingâ with  
   > âHighest observed mean at renewal 0.35 among the displayed variants (not a significance claim)â  
   and use **âCCL, with or without scoped screeningâ** for easy/segment. The unrestricted wording is misleading given the 0.55 sweep.

3. **Unlabelled paired differences:** explicitly map **beam/2, beam/4, beam_power/4** to easy **+0.69,+0.70,+0.70**, and hard **â1.10,â0.81,â1.27**, preserving their intervals. Sorting and deduplicating formatted numbers obscures configuration identity.

4. **Mechanism assertion:** replace âbecause harm routedâ¦â with  
   > âconsistent with harmful cases remaining covered by overlapping rules that pass the rule-level association screen.â  
   The aggregate tables alone do not establish the entire error-attribution mechanism.

5. **Artifact verification:** replace âverified against their expected bodyâ with  
   > âchecked using a normalized-text substring test; exact artifact verification is not yet implemented.â

6. **Append-only guarantee:** replace âdatabase-enforced append-only event logâ with  
   > âan event log with UPDATE/DELETE-blocking triggers; TRUNCATE protection and ownership lockdown are not demonstrated.â

7. **Post-LLM parity:** add  
   > âNo LLM proposal or merge was admitted, so these results do not exercise newly activated LLM-generated law.â

The compiler description is defensible only for this bounded, non-null demonstrationânot as a complete cross-runtime semantic guarantee. Governance wording needs no correction.

## 3. Newly introduced or newly exposed round-2 defects

### HIGH â Artifact âverificationâ accepts altered executable bodies

`dbx/ccl_on_dbx.py:69â70` searches all description values for a lowercased substring. A body containing the expected expression **followed by `OR true`** can pass. Lowercasing also erases meaningful string-literal differences.

**Fix:** extract the actual routine body and signature; compare a parsed, versioned canonical artifact exactly, preserving literal case. Add tampered-body tests and restrict replacement privileges.

### HIGH â Sample-equivalent merges can rewrite unobserved policy

An added condition covering no mining/admission rows passes `:171` yet changes future decisions. The new gate cannot substantiate âsemantics-preserving.â

**Fix:** construct the merged AST directly as the OR of referenced immutable ASTs. If arbitrary rewrites are allowed, classify them as policy changes, not compression, and evaluate accordingly.

### HIGH â New scoped AST path can turn bad evidence into active âpendingâ

`rule_population()` retains `disc > 15` in AST conditions but removes discount predicates from tree conditions. The former produces no in-policy controls and becomes active `pending_no_controls` (`ccl_sim.py:388â412,481`). Equivalent representations can receive different reviews.

**Fix:** separate population scope from action/discount bounds in the typed rule. Reject ambiguous scopes or quarantine unsupported-control rules rather than treating them as screened.

### MEDIUM â Cap validation can invalidate its own boundary check

`validate_cap("loosen", "15.0000000000000001")` passes Decimal validation but returns floating-point **15.0**. Tightening values just below 15 can similarly become 15.

**Fix:** bound cap length/scale and preserve canonical numeric semantics, or validate the final runtime representation too. Test representable neighbours of every boundary.

### MEDIUM â AST evaluation lacks a null contract

For example, Python `NaN != 30` is true; SQL `NULL != 30` is unknown. Boolean casting and negation create further differences (`rulec.py:112â116`).

**Fix:** reject null/nonfinite input facts consistently, or implement matching three-valued logic; differential-test against actual SQL.

### MEDIUM â New safeguards do not fully enforce their advertised guarantees

- UPDATE/DELETE triggers do not prevent **TRUNCATE**.
- `{None}` passes the single-hash check; fidelity is regenerated using currently imported simulator code regardless of run hash.

**Fix:** block TRUNCATE and restrict DDL privileges; require valid nonmissing hashes, verify executing code against them, and hash dependencies/configurationânot just one source file.

## 4. What would earn a B?

**The numerical README is supported; the complete engineering narrative is not yet.**

A **B** requires closing the high-severity defects, publishing genuine Python/SQL differential testsâincluding successful proposal/merge activation and screening/admission resultsâplus reproducible versioned artifacts. Then freeze the pipeline and obtain independent evaluation: independently authored worlds and new policy-grounded decisions, with predefined comparisons and safety criteria.

Another rerun of the same developed simulator and already-inspected HMDA years would not, by itself, earn that upgrade.