# Astra (databricks-gpt-6-astra) RE-REVIEW of v5, 2026-10-20

Raw model output, unedited.

## A. Verdict â five lines

1. **New grade: C, up from D:** substantial corrections and more honest reporting, but important implementation and evidence-integrity defects remain.
2. The equal-outcome-information comparison, revised HMDA interpretation, and genuinely later-period Databricks comparison are meaningful improvements.
3. **The READMEâs public claims are not yet fully supported:** its simulation ranking contradicts the results, and âappend-only registryâ contradicts explicit database updates.
4. The trusted compiler substantially reduces the original SQL-injection surface, but numeric validation, artifact integrity, merge admission, and end-to-end authorization remain incomplete.
5. Retain this as an exploratory prototype; do not mark the responseâs findings 5, 10, 11, 15, or 16 comprehensively fixed.

**Review scope:** Static review of the supplied code, tests, and reported resultsânot an execution or reproduction. Raw runs, database helpers, data-generation/loading code, report generators, and workspace audit records were not supplied. References below use the supplied source line numbers; document quotations are identified by section.

## B. Disposition of the 17 original findings

âResolvedâ can mean a misleading claim was withdrawn; it does not mean the originally proposed experiment has now been performed.

| # | Original finding | Disposition | Evidence |
|---|---|---|---|
| 1 | Unsupported black-box accuracy equivalence | **Partially resolved** | Tuned comparisons and paired intervals exist, but âequal toâ remains unjustified: HMDA reports â0.69, â0.04, â0.11 points; selection uses admission accuracy at `real/hmda/ccl_hmda.py:139â145`. |
| 2 | HMDA reference is not lender policy | **Resolved â interpretation only** | Explicitly acknowledged at `real/hmda/ccl_hmda.py:3â5`; learned-cutoff comparison implemented at `:111â112,146â150`. Actual lender-policy recovery remains untested. |
| 3 | Scoped association falsely called causal | **Partially resolved** | Public causal claim withdrawn, but tree rules still silently use the global reference under `LAW_REF="scoped"`: `ccl_sim.py:383â390`. |
| 4 | Author-defined oracle misrepresented as decision value | **Partially resolved** | Oracle now depends on mechanism/effect, `ccl_sim.py:95â100`; still a threshold-defined imitation target, without utility/regret, and the reported âdecompositionâ is incomplete. |
| 5 | Unsafe generated SQL and outcome-screen bypass | **Partially resolved** | Conditions are parsed and new rules screened, `dbx/ccl_on_dbx.py:134â149`; caps bypass the compiler and finite/domain validation, `:305â309`, `ccl_sim.py:162`. |
| 6 | Unequal outcome-information access | **Resolved â for displayed comparisons** | CCLâs history/approval/maturity restrictions match baseline eligibility: `ccl_sim.py:377â391,430â438,459â466`. However, CCL does **not** actually call the claimed shared helper. |
| 7 | Extensive exploratory selection | **Partially resolved** | Exploratory labeling is appropriate; five-seed intervals do not undo repeated development. No independent frozen evaluation is shown; aggregation has no expected-run manifest, `aggregate_v5.py:9â13,54â59`. |
| 8 | Hard world aligned with representation | **Not resolved** | Author-designed category/threshold rules remain, including the explicit 1,000-size literal: `ccl_sim.py:36â43,137`. |
| 9 | Rare-rule intervention changes standards, not only power | **Partially resolved** | `ccl_sim.py:326` still jointly changes support, precision target, and criterion; reported branch fidelity is **0.904 [0.682, 1.126]**, with false exception approvals **0.0012 â 0.0089**. |
| 10 | Confounded, admission-set point-in-time comparison | **Partially resolved** | The central repair is real: shared `verdict_of`, later months, `dbx/ccl_on_dbx.py:176â192,245â247`; uncertainty remains application-bootstrap uncertainty for one synthetic run, not robustness across worlds/edit processes. |
| 11 | Overstated immutability, registry auditability, and OBO | **Response is wrong** | âAppend-onlyâ is directly contradicted by `ON CONFLICT â¦ DO UPDATE` and subsequent updates: `dbx/ccl_on_dbx.py:100â103,159,254,288`. Second-principal SQL execution is not an end-to-end checker identity test. |
| 12 | HMDA cohort and feature timing | **Partially resolved** | Action assertion, flow reporting, and reduced-feature arm exist, `real/hmda/ccl_hmda.py:37â59`; acceptance selection, complete-case selection, and feature timing are not resolved. |
| 13 | Fairness audit and steward enforcement | **Partially resolved** | Final-system errors are now calculated, `real/hmda/ccl_hmda.py:89â101`; no blocking review state, uncertainty, intersectional analysis, or expert interpretation exists. |
| 14 | Small LLM demonstrations | **Partially resolved** | More cautious reporting and stricter judge, `dbx/ccl_on_dbx.py:284â290`; zero autonomous proposals/merges means those positive paths were not exercised in this run. |
| 15 | Attribution, regression, recovery, and fidelity gaps | **Partially resolved** | Simulator support/precision repair is real, `ccl_sim.py:351â371`; parity checks only decisions, `dbx/ccl_on_dbx.py:195â200`, and scoped tree screening, recovery action compatibility, and final registry statistics remain defective. |
| 16 | Correctness and reproducibility | **Partially resolved** | Single-class handling and configuration reset are implemented, `ccl_sim.py:52â64,286â295`; lossy serialization, future vocabulary, rounded run metrics, and absent completeness/hash validation remain, `:159â168,447,489â492`. |
| 17 | Unmeasured novelty/governance advantage | **Resolved â claims only** | README now says **âGovernance advantage: untested.â** No comparative governance or novelty evaluation has been supplied. |

## C. Remaining and newly exposed issues

### HIGH â 1. The READMEâs principal simulation conclusion is numerically wrong

The revised narrative appears to have been written from a remembered conclusion rather than the regenerated tables.

- **Easy, exception, beam/2:** veto **0.997**, T-learner **0.994**, screened CCL **0.996**ânot veto and T-learner both 0.997.
- Screened CCL minus T-learner is **+0.15 [+0.06, +0.24] points**.
- **Easy, segment, scoped:** CCL **0.999** versus T-learner **0.992**; paired difference **+0.69 [+0.45, +0.94] points**.
- **Hard, segment:** ordinary GBM **0.998**, T-learner **0.995**. The T-learner is not the best method there either.
- The hard exception range omits `beam_power/4`: CCL is **0.963â0.970**, not 0.967â0.970.
- The sweep at renewal **0.55** further contradicts an unconditional âCCL does not win.â

These are the supplied `RESULTS_v5.md` tables; paired differences are computed at `aggregate_v5.py:57â59`.

**Fix:** Replace the README paragraph as specified below. Generate numerical claims from a declared comparison specification. Do not declare an âacross worldsâ winner without specifying world weights, variants, and the aggregate estimand.

---

### HIGH â 2. Compiler validation stops before the complete executable rule

The condition parser is a substantial security improvement. It is not yet a complete trusted rule compiler.

**Concrete holes:**

1. **Cap bypass:** proposals use `float(p["cap"])` without finite/range validation, then append the cap outside `compile_rule`: `dbx/ccl_on_dbx.py:305â309,134â140`.
2. **A large cap silently removes the bound:** `ccl_sim.py:162` omits bounds whenever `abs(cap) >= 1e8`. An infinite cap also satisfies this condition. An internal serialization sentinel is therefore reachable through external proposals.
3. **Numeric overflow:** an arbitrarily long digit token passes the grammar; `float(...)` can produce infinity: `dbx/rulec.py:11,54`.
4. **Silent numeric changes:** `:g` defaults to six significant digits. For example, a condition containing `disc <= 30.00001` is emitted as `disc <= 30`. Caps are separately rounded to integers by `ccl_sim.py:162`.
5. **Input/resource bounds are incomplete:** the token-count limit is checked after tokenization, and neither source length nor numeric-literal length is bounded: `dbx/rulec.py:18â26`.
6. **Cross-runtime representation is broken for admitted proposals:** the compiler output is stored as a single parenthesized `lits` entry, `dbx/ccl_on_dbx.py:135`. `ccl_sim.literal()` cannot generally evaluate these nested Boolean expressions, `ccl_sim.py:112â123`. The current parity test runs **before** proposals and merges.

The supplied compiler suite contains four valid cases, fifteen rejected cases, and one string-escaping testânot twenty adversarial rejection cases: `tests/test_rulec.py:8â41`.

**Fix:** Validate a complete typed rule object, including action and cap. Require finite, domain-appropriate numbers; eliminate externally reachable sentinels; preserve numeric values exactly; bound bytes, tokens, and depth. Use the same AST for Python evaluation, SQL emission, hashing, and storage. Test thresholds immediately below/at/above each boundary and repeat parity after proposals and merges.

I do **not** infer that arbitrary SQL execution remains demonstrated. The verified defects are incomplete validation and semantic alteration.

---

### HIGH â 3. The registry is mutable, and content-addressed names do not establish immutable artifacts

The âappend-onlyâ claim is false:

- Upserts overwrite existing rows: `dbx/ccl_on_dbx.py:100â103`.
- Merge status overwrites earlier state: `:158â159`.
- Outcome status and rationale overwrite earlier state: `:254,288`.

`law_trials` is append-oriented in the shown code; `law` is not. Keeping different runs is not the same as preserving every state transition.

Artifact integrity is also weaker than claimed:

- The function name uses only **40 bits** of SHA-1: `:54â57`.
- `CREATE FUNCTION IF NOT EXISTS` trusts any existing object under that name without checking its body: `:60â62`.
- Signature, compiler version, and execution semantics are not included in the hash.
- Code choosing not to replace a function does not prevent its owner from replacing or dropping it.

**Fix:** Use an append-only event log with a derived current-state view. Hash a versioned canonical artifact including signature and compiler semantics using full SHA-256. Verify existing definitions against the expected artifact and enforce restrictive ownership/DDL privileges. Add atomic law-version activation and rollback.

---

### HIGH â 4. Merge admission violates its own contract and can invalidate previously screened law

`verdict_of()` says a merge âmay not lose anyâ accuracy, but permits a loss of **0.001**, i.e. **0.10 percentage points**: `dbx/ccl_on_dbx.py:117â125`.

More importantly:

- Replacement IDs are filtered for membership, but their action kinds are not checked.
- The merged action is copied from the first replacement: `:322â326`.
- No equivalence between the replacement expression and the original union is enforced.
- Only the candidate is outcome-screened: `:146â149`.
- Changing/removing tightening rules can expose approval populations belonging to other rules, whose screening is not repeated.
- `screen()` has no tightening-rule exemption and evaluates historical exception approvals even for a tightening candidate: `:165â172`.

Thus âmergeâ can mean an unverified policy rewrite with tolerated regression.

**Fix:** Distinguish **semantics-preserving compression** from **policy change**. For compression, require same-kind replacements and prove AST equivalence or exhaustively test a suitable finite domain. For policy changes, enforce the declared accuracy condition and rerun admission statistics and screening for the entire resulting law. Give tightening rules an explicit, appropriate outcome-review contract.

---

### HIGH â 5. Outcome screening is still representation-dependent and inconsistent between runtimes

Three different notions of a ruleâs population remain:

- `effective()` excludes tightening overrides but credits every overlapping same-kind rule: `ccl_sim.py:341â348`.
- Python `good_law()` uses raw firing/scope masks, **not** `effective()`: `:391`.
- SQL `screen()` excludes tightening overrides: `dbx/ccl_on_dbx.py:167â170`.

Therefore the Python and SQL screens can disagree even with identical rows and rules.

Also, scoped tree/covering rules still fall through to the global reference at `ccl_sim.py:383â390`. The old representation-specific fallback has not been fixed.

Pending outcomes are retained as active law, `ccl_sim.py:456`; new database proposals are blocked only when status is `"bad"`, `dbx/ccl_on_dbx.py:146â149`. That may be an exploratory policy, but **pending is not evidence of safety**.

**Fix:** Define one action/scope AST and one outcome population specification. Implement representation-independent controls and report unsupported scope explicitly. Decide whether pending means active, restricted, or quarantined, and expose that decision publicly. Differential-test screen statuses, sample counts, and statisticsânot just predictions.

**Important credit:** Despite not calling `outcome_rows()`, CCL currently applies equivalent historical eligibility restrictions to the displayed simulation methods. The information-gap repair is substantively real. Centralize the helper now so it stays repaired.

---

### HIGH â 6. âCanonical attributionâ is not unique attribution, and parity does not validate admission

`effective()` is order-independent because overlapping rules each receive credit for the same cases. `apply()` citations remain last-firing-rule dependent: `ccl_sim.py:331â348`.

That is a defensible **coverage** convention, but not a unique explanation of which rule caused a decision. It can also hide weak incremental scope: a candidate can overlap many correctly decided incumbent cases and add a much less precise new region while satisfying overall rule precision and improving accuracy slightly.

The Databricks parity check only compares final Boolean predictions: `dbx/ccl_on_dbx.py:195â200`. It does not compare:

- citations;
- per-rule masks, support, or precision;
- admission/shadowing verdicts;
- outcome-screen decisions.

The Python simulator recomputes final precision correctly. The database registry does not update all incumbent replay statistics after later admissions: candidate-only writes occur at `:152,156`.

The shadowing regression test is also weak: its broad tightening candidate can already fail accuracy/precision, so rejection does not isolate the new shadowing guard: `tests/test_v5.py:49â54`.

**Fix:** Name the current metric âoverlapping effective coverage.â Separately measure incremental decision changes and define a deterministic citation policy. Add differential admission tests and a shadowing fixture that passes every other gate. Publish final-law statistics, not admission-time remnants.

---

### HIGH â 7. Recovery can credit a rule with the wrong action

`recovery()` compares firing masks without requiring the candidate action to match the planted action: `ccl_sim.py:405â418`.

A tightening rule covering the rogue exception region can therefore receive overlap credit for an **approval** rule. This is a general metric defect, even if the supplied beam runs do not happen to exploit it.

Furthermore, branch fidelity remains positive-case **system** agreement: `aggregate_v5.py:37â44`. Approval through another rule counts as success. Adding overall overbreadth does not establish recovery of the specific rare branch.

**Fix:** Require action compatibility for recovery. Report structural/semantic overlap separately from final-system behavior. For each branch, score exclusive-effect positives, nearby negatives, and errors on its complement.

---

### MEDIUM â 8. Harm scoring is improved, but the threshold and âdecompositionâ need repair

The oracle now correctly changes between the supplied harmful and null worlds: `ccl_sim.py:95â100`. That fixes an important original defect.

Remaining issues:

- It is still an author-chosen **renewal-drop threshold**, not an economically optimal policy.
- At the exact boundary, binary floating-point matters: `0.85 - 0.65` is slightly below `0.20`, so the documented `>= 0.20` condition can classify the boundary incorrectly.
- The screen uses strict `< -max_drop`, while the oracle defines harm using `>= HARM_DROP`: `:97,394`.
- âHarmful approvals / false rejectionsâ is not a complete error decomposition. It omits approvals that violate the oracle but are not designated harmful.

For example, hard `beam_power/4` has approximately **3.7%** oracle disagreement, versus **1.93% + 1.03% = 2.96%** from the two displayed components.

**Fix:** Declare threshold-boundary semantics and test them numerically. Add `nonharmful_false_approvals = pred & ~oracle & ~harmful`; verify that all mutually exclusive error components sum to total error. Keep âoracle agreementâ separate from policy value.

---

### MEDIUM â 9. Simulation CIs are paired correctly, but provenance and presentation overstate them

**What is correct:** `aggregate_v5.py:57â59` computes within-run CCL-minus-baseline differences and then a t-interval across seeds. It does not incorrectly subtract marginal interval endpoints.

**What remains wrong or weak:**

- Inputs have already been rounded to four decimals: `ccl_sim.py:489â491`. A paired difference can consequently have up to **0.01 percentage points** of rounding error.
- Five-seed t-intervals are fragile and pointwise. They do not cover researcher selection or the many comparisons.
- The interval **[0.682, 1.126]** exposes the poor bounded-metric approximation.
- âAll values â¦ with a 95% t-intervalâ is false: several tables emit means only, `aggregate_v5.py:88â96`.
- Duplicate rejection is not completeness validation. Missing seeds/configurations and incompatible code versions can pass: `:9â13,54â56`.
- The 180 runs are not 180 independent experimental worlds. Variants reuse seeds.

**Fix:** Store full-precision metrics, prediction/count artifacts, complete configuration and code hashes. Validate an explicit expected manifest and seed set. Label intervals pointwise and conditional on the developed generator; use more independent seeds and suitable bounded-metric summaries. Do not merely clip the current upper endpoint and call the uncertainty problem solved.

---

### MEDIUM â 10. The point-in-time comparison is repaired, but its CI has a narrow estimand

`court_offline()` really does call the same admission function, and months 36â38 are not used for mining/admission: `dbx/ccl_on_dbx.py:106â108,176â183,245â247`. This is not the old admission-set comparison.

However, `paired()` resamples individual decisions: `:186â192`. It conditions on the particular selected laws, single generated history, and edit realization. It does not quantify uncertainty from mining/admission, edit regimes, or temporal deployment.

Application-level pairing is **not inherently invalid** in an independent-row simulator. The problem is interpreting its interval as general evidence of a point-in-time benefit.

**Fix:** Label the interval conditional. Repeat the complete two-arm pipeline across seeds, edit regimes, and decision periods; bootstrap independent run units or use an appropriate hierarchical analysis. Supply the generation/loading code so within-month and availability-time claims can be audited.

---

### MEDIUM â 11. The identity test demonstrates a permission sequence, not checker credential propagation

The separate SDK client executes a SQL statement as the second principal: `dbx/ccl_on_dbx.py:203â218`. That is useful.

But the actual checker uses the imported global `sql()` helper: `:345`. No user credential is passed through that path in the supplied code. The second-principal test does not invoke the checker.

Additional weaknesses:

- Failed statements are not asserted to be authorization failures.
- Results are logged rather than enforced as test assertions.
- Permissions are changed without `try/finally` or restoration of prior grants.
- Top-level exceptions are converted to a logged error: `:362â363`.

**Fix:** Make the checker accept an explicit authenticated execution context. Invoke the same checker under both principals; assert returned identity and specific denial causes. Verify audit records and no privileged fallback. Restore permissions safely.

---

### MEDIUM â 12. HMDA bootstrap and selection are improvements, not confirmatory inference

The cluster bootstrap is genuinely paired and resamples whole states: `real/hmda/ccl_hmda.py:80â86`. Keeping all applications from each sampled state is appropriate for the stated application-weighted ratio statistic; this is not an obvious weighting bug.

Its limitations need to be stated:

- It conditions on already fitted and selected models; no training or model-selection uncertainty is included.
- State exchangeability is assumed, not established. Shared lender/year shocks are not captured.
- The number and size concentration of clusters are not reported.
- Five hundred resamples give relatively noisy percentile endpoints.
- There is no adjustment for selecting among/reporting multiple comparisons.
- The global RNG makes intervals depend on call order.

The selection code itself does **not** choose the variant using test-year labels: `:139â145`. But the variants, selection procedure, and study were developed after those years had been examined. âChosen in advanceâ and the code comment âpre-specifiedâ overstate the chronology. Admission data also serve both sequential rule admission and variant selection; this can encourage validation overfitting without being direct test-label leakage.

**Fix:** Describe this as retrospective, admission-selected evaluation. Use deterministic comparison-specific bootstrap seeds, publish cluster diagnostics, and increase resamples. For future inference, freeze the entire pipeline, use nested temporal development, and evaluate independently acquired future data. Report conditional prediction uncertainty separately from full-pipeline uncertainty.

---

### LOW â 13. Reproducibility and audit outputs still omit important qualifications

- Future category vocabulary is still constructed before simulation splitting: `ccl_sim.py:447`.
- Fidelity reconstructs rules by splitting pretty-printed SQL on `" AND "`: `aggregate_v5.py:23â27`.
- The HMDA report shows group approval ratios but omits the final-system error rates that the code computes: `real/hmda/ccl_hmda.py:97â100`.
- Denial-reason proportions normalize only over nonmissing mapped reasons, without showing that denominator: `:104â108`.

**Fix:** Fit historical encoders, store ASTs rather than parse display strings, publish group error tables with uncertainty, and disclose reason-code missingness and denominators.

## D. Exact public wording replacements

These changes should be made in the report generators as well as the generated files.

### README â replace the simulation bullet

> **Simulation** (`RESULTS_v5.md`; 180 exploratory runs using five seeds per configuration): month-36 laws achieve mean thresholded-overlap recovery of 7/7 planted rules in the easy world and 6.8â7/7 in the hard world; this is not exact structural recovery. The displayed outcome methods use equivalent historical outcome-eligibility restrictions. At rogue renewal 0.35 in the exception-effect world, the renewal veto scores about 0.997, the T-learner 0.994 in the easy world and 0.997 in the hard world, and screened CCL 0.996 and 0.963â0.970 respectively. In the segment-effect world, scoped CCL avoids the false blocking seen with the global screen and veto; it outperforms the T-learner in the easy world but underperforms it in the hard world. No method is best in every displayed setting. These are oracle-agreement results, not estimates of causal policy value.

### README â replace the real-decision comparison sentence

> CCLâs observed accuracy is 0.01â0.18 percentage points above a learned DTI cutoff of 49%. Relative to the tuned GBM, its differences are â0.69 points in 2021, â0.04 in 2022, and â0.11 in 2023; the reported conditional state-cluster bootstrap intervals exclude zero only in 2021. These results do not establish equivalence. GBM has higher denial recall in all three years.

### README â replace the Databricks bullet

> **Databricks build** (`dbx/REPORT.md`, one synthetic run): month-end Delta reconstruction under a delayed-edit simulator; hash-named UC functions; a restricted compiler for proposed conditions; Lakebase branches isolating trial registry records while replay runs in DBSQL; run-preserving registry rows with mutable status and rationale fields; and zero Python/SQL decision mismatches on 5,029 admission cases before LLM proposals and merges. A separate second-principal SQL test demonstrates a grant/revoke sequence, not end-to-end checker credential propagation. One control re-proposal of a screened rule was blocked by the outcome screen.

### RESULTS_v5.md header â replace âAll values â¦â

> Where shown, intervals are pointwise 95% Student-t intervals across five seed-level values; several tables display means without intervals. Inputs are rounded run-level metrics. These exploratory intervals do not account for development-time selection, multiple comparisons, or uncertainty over independently specified worlds.

### RESULTS_v5.md header â replace the oracle definition

> `vs_harm_oracle` measures agreement with the simulatorâs noiseless firm-rule decisions after vetoing designated rogue-bound exceptions whose configured renewal-probability drop meets the 0.20 harm threshold. It is a threshold-defined synthetic target, not a utility-optimal policy or a causal estimate from the observed data.

### RESULTS_v5.md header â replace the shared-helper sentence

> CCLâs screen, renewal veto, and T-learner currently use equivalent eligibility restrictions: approved historical decisions with outcomes known before the decision month. The baselines call `outcome_rows`; CCL independently implements those restrictions.

### dbx/REPORT.md â replace âimmutable law artifactsâ

> Hash-named functions that this script does not replace; existing definitions are not verified, and infrastructure-enforced immutability has not been demonstrated.

### dbx/REPORT.md â replace the Registry rowâs description

> Lakebase Postgres registry keyed by run, with mutable law rows and appended trial records; the script preserves prior runs but updates status, outcome, and rationale fields within a run.

### dbx/REPORT.md â replace the Checker rowâs description

> The checker invokes UC functions through the configured SQL helper. A separate second-principal test exercises SQL permissions; propagation of that principal through the checker itself has not been demonstrated.

### dbx/REPORT.md â replace the point-in-time result bullet

> **Point-in-time contrast:** both arms use the same admission function and are evaluated on later months 36â38, comprising 7,379 decisions. In this synthetic run, accuracy is 0.9558 versus 0.9538, a difference of +0.20 points with a paired application-bootstrap interval of [+0.09, +0.33]. This interval conditions on the selected laws and generated history; it does not establish robustness across seeds, decision periods, or edit processes.

### real/hmda/REPORT.md â replace the selection sentence

> For each reported year, the implemented selection rule chooses between two CCL variants using admission-year accuracy and chooses GBM hyperparameters from four configurations using that same year. Test-year labels do not enter these selection functions, but the study and selection procedure were developed retrospectively after these years had been examined.

### real/hmda/REPORT.md â replace the CI sentence

> CIs are pointwise 95% percentile intervals from 500 paired state-cluster resamples of test predictions, conditional on the fitted and selected models. They do not include training/selection uncertainty or establish generalization to other lenders or years.

### real/hmda/REPORT.md â replace the bottom line

> **Bottom line:** in this selected cohort, a learned DTI cutoff of 49% comes within 0.01â0.18 percentage points of CCLâs observed accuracy. Tuned GBM has higher point-estimate accuracy and denial recall in all three years; the reported accuracy-difference interval excludes zero only in 2021. Neither model equivalence nor recovery of the lenderâs actual underwriting policy has been established.

## E. The three highest-value next steps

1. **Complete one canonical, testable law implementation.**  
   Typed AST; finite numeric validation; identical Python/SQL scope and outcome semantics; explicit merge contracts; full-law differential tests; immutable verified artifacts; append-only events and atomic activation. Exercise valid proposals and merges, not only a rejected rogue control.

2. **Make the evidence release internally consistent and reproducible.**  
   Correct the README ranking, publish full-precision paired artifacts, validate the 180-run manifest and hashes, repair recovery/action and error-decomposition metrics, and scope all CIs to their actual estimands. This is more valuable than another miner variant.

3. **Freeze the pipeline and obtain independent evidence.**  
   Use independently authored worlds and genuinely new, policy-grounded real decisions. Predeclare comparison weights, tuning budgets, utility or cost metrics, and deployment-safety criteria. The next credible upgrade in grade must come from independent evaluationânot another pass over the same generator and HMDA years.