# Astra (databricks-gpt-6-astra) review, 2026-10-20

Prompt: aggressive-but-constructive full-project review; packet = docs, results, reports, core code (line-numbered). Raw model output below, unedited.

# Review

**Scope:** This is a static review of the supplied documents and code, not a reproduction. Several referenced artifactsâincluding the SQL/authentication helpers, injection harness, simulation snapshot, raw run logs, and additional testsâwere not supplied. Where those artifacts determine a claim, I mark the claim unverified rather than assuming the implementation.

## A. Verdict â five lines

1. **Established:** A working prototype can mine executable exception rules, select them by historical replay, and enforce the resulting decision function around an LLM.
2. **Not established:** Real-data accuracy equivalence, causal harm identification, superiority to strong uplift baselines, or measurable governance benefits.
3. **Headline problems:** HMDA uses an invalid approval-policy proxy; causal comparisons lack identification and equal outcome access; the point-in-time benefit is measured on admission data with unequal gates.
4. **Engineering assessment:** Useful demonstration, but unsafe generated SQL, unverified OBO, mutable law artifacts, and incomplete admission checks prevent a production-governance claim.
5. **Overall research grade: D:** Substantial implementation and unusually explicit correction history, but the central conclusions still exceed the design, measurements, and correctness guarantees.

---

## B. Findings ranked by severity

### 1. CRITICAL â âMatches black-box accuracyâ is unsupported even before examining the HMDA policy

**Evidence**

- `real/hmda/REPORT.md`: CCL power-aware versus GBM is **0.933 vs 0.940**, **0.931 vs 0.931**, and **0.933 vs 0.934**.
- Always-approve achieves **0.910 / 0.906 / 0.905**.
- The author acknowledges post-result variant selection, an untuned GBM, and no confidence intervals.
- `real/hmda/ccl_hmda.py:104â115` evaluates two CCL variants and one default GBM.

**Why it matters â claim 1**

The first year has a **0.7 percentage-point deficit**, not a demonstrated tie. Equality after rounding in another year is not equivalence. CCL improves on always-approve by only **2.3â2.8 points**; that may be useful, but overall accuracy hides whether it identifies denials or mostly reproduces approvals.

The yearly split is prospective in structure, but choosing the headline method after observing those years makes them development results, not an untouched confirmation set.

**Fix/test**

Freeze the variant and a noninferiority margin before acquiring new test data. Report paired prediction differences with uncertainty, denial precision/recall, balanced accuracy, false-approval/false-denial costs, and subgroup errors. Use temporal/lender clustering where applicableânot an independence assumption over all applications. Compare against tuned GBM and strong interpretable models under equal tuning budgets.

---

### 2. CRITICAL â The HMDA âstatuteâ is not the lenderâs approval policy

**Evidence**

- `real/hmda/ccl_hmda.py:3â4` explicitly acknowledges that the General QM DTI cap was replaced during the study period.
- Nevertheless, `:20,53` fixes the policy at `DTI <= 43` for every year.
- `docs/ADR.md`, ADR-028: âReal tacit rules are recovered.â
- `real/hmda/REPORT.md`: the principal rule is approval through 49% DTI, excluding TOTAL.

**Why it matters â claims 1 and 4**

A QM eligibility condition is **not an instruction to approve every qualifying mortgage**, and exceeding that condition does not universally prohibit lending. Other underwriting criteria, applicable QM routes, product eligibility, and changing regulation matter.

Consequently, the residual is not identified as âtacit corporate knowledge.â It combines:

- an incomplete and temporally misspecified reference policy;
- legitimate documented underwriting;
- omitted creditworthiness;
- process and reporting effects;
- potentially discretionary decisions.

The declining reference-policy accuracyâ**0.821 â 0.738**âcould substantially reflect reference-policy obsolescence rather than increasing value from tacit-rule discovery.

**Fix/test**

Rename this baseline a **43%-DTI heuristic** immediately. For an actual policy-residual study, obtain dated lender underwriting rules and product applicability, independently encode them, and validate their decisions with underwriting experts. Separately compare CCL against a simple learned DTI threshold and a time-varying policy baseline. Do not label a discrepancy âtacitâ without documentary or expert corroboration.

---

### 3. CRITICAL â âScoped is causally correctâ is false

**Evidence**

- `docs/ADR.md`, ADR-027: âScoped is causally correct.â
- `ccl_sim.py:338â355` computes an unadjusted renewal-rate difference.
- Treatment in the T-learner is exception approval versus in-policy approval (`:414â420`).
- `disc` is a model feature (`:23,88â90`), while exception status is determined by that same variableâs threshold.
- Both comparisons condition on actual approval.

**Why it matters â claim 2**

Restricting controls to a ruleâs population does not establish exchangeability, positivity, consistency, or a well-defined intervention.

In particular:

1. **No conditional overlap:** Given discount, exception status is deterministic. The T-learner predicts each arm outside that armâs discount support.
2. **Ambiguous intervention:** Are you comparing different discount offers, approval versus rejection, or an exception-policy regime? These are different causal questions.
3. **Selection:** Outcomes are observed among approved deals. Approval can depend on treatment and other determinants of renewal.
4. **Uncontrolled differences:** Term, customer risk, time, and other variables can differ within a holdingâs population.

The scoped filter is a subgroup association screen. It can behave correctly in the particular simulator without being a causal estimator.

**Fix/test**

Specify potential outcomes and the intervention first. For discount effects, randomize feasible offers or construct a design with defensible assignment and overlap. Use pretreatment covariates, evaluate propensity/support diagnostics, handle approval selection and outcome maturity, and report sensitivity to unmeasured confounding. Rename the current quantity `observed_renewal_difference`, not causal lift.

---

### 4. CRITICAL â The causal leaderboard rewards an author-defined target, not demonstrated decision value

**Evidence**

- `ccl_sim.py:69â78` defines `good_decision` by removing the designated rogue rule, regardless of the renewal-effect parameter.
- `:80â82` assigns renewal probabilities from the planted rogue identity.
- `RESULTS_causal.md`: at rogue renewal **0.85**, filtering correctly does nothing, yet CCL remains at **0.942** against `vs_good`.
- In the hard causal setting, the reported **0.985** accompanies only **47% âmonths flagged.â**

**Why it matters â claim 2**

The target declares the rogue rule wrong even under the **null outcome effect**. Thus `vs_good` is not an outcome-optimal policy target.

There is a second mismatch: in the exception-effect world, above-policy approvals in the rogue population can be harmful even when another legitimate rule also permits them. Removing only the rogue rule can retain those harmful approvals because `good_decision` preserves the other rules.

Renewal alone also omits margin, acquisition value, retention economics, and the consequences of rejection. Calling this target a âwell-run firmâ embeds an unsupported normative conclusion.

**Fix/test**

Rename it `agreement_with_nonrogue_rule_oracle`. Add potential outcomes for feasible actions and an explicit utility function. Evaluate policy value/regret against the utility-optimal policy, separately from rule imitation. Include null-harm and beneficial-exception cases where the optimal action changes. Decompose performance into rule discovery, filter sensitivity, false vetoes, and policy value; do not infer filter quality from final agreement alone.

---

### 5. CRITICAL â Generated SQL bypasses a real security boundary; outcome review can be bypassed too

**Evidence**

- LLM conditions are interpolated into executable expressions at `dbx/ccl_on_dbx.py:233â240,259â260`.
- `create_fn()` submits them through `CREATE OR REPLACE FUNCTION` at `:54â55`.
- The operator/column restriction exists only in a prompt.
- Outcome review occurs at `:170â187`, **before** LLM proposals and merges at `:224â266`.
- `sql_lit()` inserts string values without escaping at `:310â313`.

**Why it matters â claims 3 and 5**

Replay accuracy is not a SQL sandbox. The shown code does not enforce the promised expression language before privileged compilation. Whether a particular payload succeeds depends on SQL grammar and permissions, but the missing validation is definite.

An admitted LLM proposal also does not pass the outcome filter before becoming agent-visible. It can reintroduce harmful exceptions already removed from the law. The checker then faithfully enforces that contaminated law.

**Fix/test**

Accept a typed rule AST, not arbitrary SQL. Enforce allowed fields, operators, types, expression depth, finite bounds, and resource limits; compile it with a trusted compiler. Disallow subqueries and function calls unless explicitly approved. Parameterize values.

Make **every** new or modified rule pass the complete admission, outcome, authorization, and steward pipeline before activation. Add adversarial compiler tests and a test where an LLM proposal recreates the removed rogue rule.

---

### 6. HIGH â Outcome-information access is unequal across CCL and the purported âfairestâ baselines

**Evidence**

- CCLâs filter receives **all earlier history**: `ccl_sim.py:401â402`.
- Renewal veto and T-learner receive a trailing **24-month window**: `:407â416`.
- Outcomes mature after `12 * term` months: `:83`.
- Known outcomes require `< m`, not `<= m`.

**Why it matters â claim 2**

Within that 24-month window, **no two- or three-year contract outcomes can be observed** under these boundaries. The renewal baselines learn from one-year contracts only, then predict renewal effects for longer contracts. CCL can use older matured outcomes, including longer-term contracts.

âSame outcome informationâ is therefore false at the row level. Using the same threshold is not an equal-information comparison.

The label models also use different histories: CCL reserves admission months, while the monthly GBM trains on the whole trailing window. These choices may be reasonable, but their effects must be separated.

**Fix/test**

Provide every outcome method exactly the same eligible rows, covariates, availability times, and censoring rules. Add ablations for full-history versus rolling-history outcome estimation. Tune T/S/X/DR-style learners and the simple veto on development data, but only after repairing the causal design; more sophisticated learners cannot fix nonidentification.

---

### 7. HIGH â The project has an extensive garden of forking paths, not confirmatory falsification

**Evidence**

- Recovery changed after results: ADR-012 and ADR-021.
- Hard-world tenure changed from seven to eleven years after observing coverage: `WORKLOG.md`, v3 section.
- Miners, thresholds, support requirements, admission windows, references, and causal worlds changed across versions.
- The simulator was changed after the uplift baseline exposed the original causal mismatch.
- Three simulation seeds are repeatedly reused.
- `ccl_sim.py:325â334` adaptively admits multiple candidates against the same admission set.

**Why it matters â claims 1, 2, and 6**

These are legitimate development activities. They do not preserve a prespecified kill test. Disclosure is necessary, but disclosure does not restore confirmatory validity.

Fresh synthetic rows from the same repeatedly inspected generator address sampling overfit, not researcher overfit to that generator. A Wilson interval on a selected candidateâs training precision likewise does not control false discoveries across the search.

**Fix/test**

Declare all existing results exploratory. Freeze code, generator families, metrics, thresholds, stopping rules, and model-selection budgets. Obtain untouched worlds/data from an independent evaluator. Report all variants rather than only the best variant for each target.

Save paired predictions and full-precision metrics. Use simulation-world/seed-level uncertainty and cluster-aware real-data intervals. Predefine the multiple-comparison family or use simultaneous intervals for headline comparisons.

---

### 8. HIGH â The âhard worldâ remains closely aligned with the rule representation

**Evidence**

- `ccl_sim.py:57â67` generates most features independently; discount is uniform and decision noise is independent.
- Hard rules remain combinations of category predicates, thresholds, and caps (`:36â42`).
- Multiple holdings can implement OR, and a small finite number of term/churn cases can approximate the interaction.
- Round-size literals still explicitly include **1000** (`:119`).

**Why it matters â claims 2, 4, and 6**

The hard world is harder than the schema minerâs original literal list, but not convincingly outside the final systemâs representational family. A set of conjunction rules is already a disjunction. The author controls both the challenge and the search vocabulary.

Enterprise decisions also involve correlated covariates, repeated customers and approvers, endogenous offers, missing information, changing incentives, and selective outcome observation. Those structures are largely absent.

**Fix/test**

Have an independent team generate hidden policies and decision processes after code freeze. Include correlated features, smooth effects, high-order interactions, latent confounding, missingness, repeated entities, selection, and abrupt/gradual drift. Include worlds where the correct conclusion is âno stable ruleâ or âinsufficient evidence,â rather than forcing every world to contain recoverable holdings.

---

### 9. HIGH â The rare-rule result changes the acceptance standard, not just statistical power

**Evidence**

- `ccl_sim.py:306`: support changes **60 â 25**, while raw precision **0.9** becomes Wilson lower bound **0.8**.
- `WORKLOG.md`: the missing branch had purity around **0.8**.
- `RESULTS_v4.md`: branch fidelity **0.52 â 1.00**, but logged accuracy **0.929 â 0.914**, filtered target accuracy **0.980 â 0.970**, and recovery **6.7/7 â 6.0/7**.

**Why it matters â claim 6**

This is not an isolated power intervention. It changes support, the precision estimand/criterion, and the validation horizon. A population precision near 0.8 will not satisfy a fixed 0.9 requirement merely with more data; an exactly 0.8 observed precision also cannot have a finite-sample Wilson lower bound at least 0.8.

The result may be useful, but ârecovered through powerâ overstates the diagnosis.

Furthermore, branch fidelity measures decisions on branch-positive cases, including approvals justified by other rules. It does not establish that the branch itself was identified.

**Fix/test**

Run a factorial study varying sample size, support floor, precision target, Wilson versus raw scoring, and admission length independently. Keep the underlying acceptable error rate fixed for the power comparison. Evaluate exclusive branch cases, nearby negative controls, false approvals, total utility, and complexity. Report a trade-off frontier, not a single ârecoveryâ success.

---

### 10. HIGH â The point-in-time accuracy benefit is confounded and evaluated on the admission set

**Evidence**

- `dbx/ccl_on_dbx.py:158â169` evaluates both laws on `ADM_SRC`.
- The as-decided law is selected using that same source at `:110â115`.
- The today-table contrast at `:163â165` checks only improvement and candidate support; it omits the precision/regression checks used by the main procedure.
- `dbx/gen_data.py:53â55` deliberately injects later edits.
- `as_decided()` uses month-end versions (`dbx/ccl_on_dbx.py:27â29`).

**Why it matters â claim 5**

The **+0.28-point** result is neither an independent test result nor a clean point-in-time ablation. It changes both data provenance and the admission procedure.

The **11.6% changed-facts rate** is a property of the constructed edit process and selected mining interval, not evidence about production CRM revision prevalence.

Month-end state equals decision-time state only because this simulator delays edits into later months. In production, edits within the decision month, late ingestion, corrections, and policy-version changes break that equivalence.

**Fix/test**

Use identical mining and admission code in both arms and evaluate on untouched subsequent decisions. Implement event-time/availability-time reconstruction or immutable decision snapshots. Add within-month edits, late arrivals, corrections, schema changes, and historical policy versions. Report accuracy differences with paired uncertainty across seeds, edit regimes, and decision months.

---

### 11. HIGH â Lakebase branching and SQL API execution do not establish governed deployment or OBO

**Evidence**

- Replay runs in DBSQL; branches contain registry records: ADR-023.
- UC functions are globally created/replaced at `dbx/ccl_on_dbx.py:54â55,105,131`.
- Registry tables are truncated on each run (`:140`).
- Branches expire after seven days (`:104`).
- Checker execution uses the imported `sql()` helper (`:286`); no requesting-user credential propagation is shown.
- ADR-025 calls this âOBO by construction.â

**Why it matters â claims 3 and 5**

The branch isolates a copy of registry state, **not the executable law or replay environment**. The benefit over a transactionally isolated candidate record or append-only trial log has not been measured.

SQL API use does not itself prove OBO. Authentication could be the developerâs identity or a service principal. The supplied code cannot establish requester-level authorization.

A mutable UC function plus a registry row is also not an immutable, reproducible law version. Truncation and short-lived branches weaken the audit narrative.

**Fix/test**

Demonstrate two callers with different entitlements and verify effective identity in audit logs, denied execution, row/column restrictions, and absence of privileged fallback.

Version law artifacts by immutable IDs/hashes. Record exact data versions, policy versions, compiler version, credentialsâ effective principal, and trial results. Use atomic activation and rollback. Compare branching against ordinary transaction/append-only designs on isolation failures, operational cost, latency, and audit recovery.

---

### 12. HIGH â HMDA cohort construction and feature timing require an audit before interpretation

**Evidence**

- The documented target is action **1 versus 3**.
- `real/hmda/ccl_hmda.py:40â43` does not filter `action_taken` to `{1,3}`; it labels every non-1 record false.
- The supplied code does not establish whether upstream downloads already perform that filtering.
- Complete cases are selected at `:52`.
- AUS and score-model fields are used at `:47,57â62`.
- Annual public records do not provide decision-time feature snapshots.

**Why it matters â claim 1**

If raw downloads contain other action codes, the implemented target is not originated-versus-denied. Even if downloads are correct, this is an unasserted external dependency.

Origination is not identical to an approval decision: excluding approved-but-not-accepted applications selects on borrower acceptance. Complete-case filtering can further change approval rates and group composition.

AUS and score-model reporting may reflect workflow or decision-dependent availability. They are not proven leaked features, but their decision-time availability has not been established. TOTAL is an FHA scorecard appearing in a conventional-loan cohort; that requires investigation, not a business-rule interpretation by default.

**Fix/test**

Assert allowed action codes and publish a cohort-flow table by year, action, missingness, and protected group. Include approved-but-not-accepted applications when appropriate to the estimand. Audit feature availability and reporting codes with an HMDA specialist. Repeat results without workflow-sensitive fields and with missingness retained rather than silently dropping records.

---

### 13. HIGH â The fairness audit neither establishes fairness nor enforces steward review

**Evidence**

- `real/hmda/ccl_hmda.py:71â84` uses lowest/highest firing rates over at most four groups and denominators of at least 100.
- For tightening, its denominator is **in-policy cases**, although tightening applies to all cases (`:74` versus `ccl_sim.py:138`).
- Only race and sex are loaded/audited (`:50,76`), despite broader protected-attribute claims.
- Accuracy is computed before audit output, and no rule is excluded or routed by audit result (`:105â109`).
- `because()` uses only the first denial reason among denied covered applications (`:87â91`).

**Why it matters â claims 1 and 3**

A symmetric ratio of burden rates is not the ordinary four-fifths selection-rate calculation. The four-fifths heuristic is also not a general mortgage fair-lending determination.

Excluding protected attributes does not remove proxy discrimination. Restricting to common groups can hide harms to smaller groups. Per-rule firing rates do not measure the final systemâs effective decisions after overrides.

The claim that failing rules âgo to steward reviewâ describes an intended workflow, not the supplied implementation. Reported accuracy still includes them.

Denial-code frequencies describe recorded explanations among selected denials; they do not prove why the rule is valid.

**Fix/test**

Define the fairness estimand and evaluate final decisions, effective rule contributions, approval/denial errors, and uncertainty. Include all relevant groups and intersections, reporting âinsufficient evidenceâ where necessary. Have fair-lending experts specify appropriate analyses.

Implement an actual review state that blocks activation, then report both unrestricted research accuracy and deployable-law accuracy. Label denial codes as descriptive provenance, with missingness and denominator disclosure.

---

### 14. HIGH â The LLM results are small demonstrations with an accommodating evaluator

**Evidence**

- Synthetic notes contain planted reasons frequently: `dbx/gen_data.py:16â42`.
- Rationales are judged by an LLM against a hidden reason chosen through maximum overlap (`dbx/ccl_on_dbx.py:191â218`).
- `dbx/REPORT.md` acknowledges that a mixed rationale was accepted.
- Nine rationales, three proposals, one seed, one decision month.
- Models and warnings are changed together in the injection comparison.
- `dbx/ccl_on_dbx.py:295â296` sets the final decision to executable law on disagreement.

**Why it matters â claims 3 and 5**

â9/9â measures semantic matching to a small set of templated reasons, not faithful explanation of real organizational decisions. There is no blinded human reference, judge calibration, or unsupported-claim measure.

â0/3 admittedâ demonstrates rejection of those proposals. It does not show that the gate rejects bad proposals while admitting good ones.

âZero wrong shippedâ means zero deviations from the chosen law under this harness. That is structurally expected from fallback and does not establish that the law is correct or the system secure. Even under independent identical trials, zero failures in ten trials leaves a one-sided 95% upper failure bound of approximately **26%**.

**Fix/test**

Use blinded expert-labelled real or independently generated notes, multiple model runs, calibrated independent judges, contradictory evidence, and unsupported-rationale scoring. Include both valid and invalid proposal controls.

For injection, factorially vary model and warning. Test retrieval contamination, malicious facts, tool-output injection, compiler abuse, unauthorized citations, outages, and registry changes. Measure law compliance, factual/explanatory correctness, authorization, and actual decision quality separately.

---

### 15. HIGH â âRegression-safe,â âexact recovery,â and fidelity contain consequential implementation gaps

| Issue | Evidence | Concrete fix/test |
|---|---|---|
| **Existing rules can escape regression checking** when their effective support drops below 15. | `ccl_sim.py:329â332` checks precision only when `m.sum() >= min_n`; only the candidate must meet support. | Treat insufficient support as an explicit unresolved state, not a passed guarantee. Test a candidate that leaves an incumbent with a tiny, entirely wrong effective scope. |
| **Recorded precision becomes stale** after later candidates change attribution. | `ccl_sim.py:334` records precision at admission only. | Recompute final effective support and precision for every rule after every accepted change and at publication. |
| **Python and SQL admission semantics differ.** Python assigns overlapping same-kind cases to the last firing rule; SQL counts them for every firing rule. | `ccl_sim.py:314â317` versus `dbx/ccl_on_dbx.py:68â76`. | Specify canonical attribution and add differential tests comparing predictions, citations, support, precision, and admission verdicts. |
| **Scoped control silently becomes global** if scoped controls are scarce; tree rules never get scoped controls. | `ccl_sim.py:346â351`. | Return `pending_no_comparable_controls`; implement representation-independent scope. Test a high-risk subgroup with insufficient controls. |
| **âExactâ is not exact.** It accepts coverage â¥0.6 and purity â¥0.8. | `ccl_sim.py:378â379`; `RESULTS_v3.md` includes `size_k > 355` for a planted `>340` rule. | Rename to thresholded overlap recovery. Add structural equivalence where meaningful and semantic error over positive and negative cases. |
| **Recovery chooses maximum coverageÃpurity**, which can select a failing candidate even when another passes both thresholds. | `ccl_sim.py:378â379`. | Compute recovery as âany candidate meets both thresholdsâ; report best overlap separately. Add a two-candidate counterexample test. |
| **Tightening fidelity excludes above-policy cases**, precisely where the historical override bug mattered. | `aggregate_v4.py:33â34` includes `& fresh.statute.values`. | Score all applicable tightening cases and add above-policy conflict tests. |
| **Positive-case fidelity cannot detect overbroad rules.** | `aggregate_v4.py:30â38`; tenure `>9` obtains fidelity 1.00 for truth `>=11`. | Add rule-specific false-positive rates, exclusive-effect cases, and decision disagreement on the complement. |

These are not cosmetic issues. They affect claims 3, 5, and 6 and the interpretation of the recovery tables.

---

### 16. MEDIUM â Additional correctness and reproducibility defects should be fixed before another results release

| Issue | Evidence | Concrete fix/test |
|---|---|---|
| **Single-class tree leaves can crash.** | `ccl_sim.py:272` accesses `v[1]`; a fitted classifier can have only one class. | Read `tree.classes_` and handle single-class fits. Test all-positive and all-negative mining populations. |
| **SQL serialization is potentially lossy.** | `ccl_sim.py:144,150` rounds caps/thresholds; `aggregate_v4.py:14` parses by splitting `" AND "`. | Store a typed AST with full precision. Property-test AST â Python/SQL/serialized AST on threshold boundaries and nested expressions. |
| **Mutable globals contaminate subsequent experiments.** | HMDA changes `STATUTE_CAP`, `CAPS`, and `LIT_COLS` at `real/hmda/ccl_hmda.py:65â68`; `set_world()` does not reset them. | Pass immutable experiment configuration. Run HMDA and simulation in both orders in one process and require identical results. |
| **Aggregation can mix incompatible runs or count duplicates.** | `aggregate_v4.py:42,50,63` does not validate unique seeds/configurations or group by causal effect/reference. | Require a run manifest, complete configuration hash, expected seeds, and duplicate rejection. Fail closed on mixed runs. |
| **The outcome-leakage smoke test does not test leakage.** | `tests/test_smoke.py:13â15` checks generated timestamps only. | Mutate all future outcomes and require current rules, flags, and predictions to remain unchanged. Do the same for future facts and labels. |
| **Default preprocessing sees future category vocabulary.** | `ccl_sim.py:390` builds dummies before temporal splitting. | Fit encoders on historical data only and handle unseen categories explicitly. This is limited transductive leakage, not evidence of label leakage. |
| **Documentation and reproducibility instructions are stale.** | README references six tests and v2 commands against current code; the worklog mentions additional tests not supplied. | Publish an exact environment lock, data checksums, immutable code/run hashes, current commands, and executable report-generation tests. |

The present smoke tests establish a few useful invariants. They do not establish end-to-end leakage resistance, SQL/Python equivalence, security, or production correctness.

---

### 17. MEDIUM â Novelty and âlasting governance advantageâ remain hypotheses

**Evidence**

- ADR-016 names CBR, concept drift, and decision-trace/context work.
- ADR-006 calls replay admission âthe defensible novelty.â
- The implementation mostly combines residual classification, subgroup discovery, validation-set selection, outcome screening, and executable rules.
- Decay is implemented principally through rolling re-mining; an appeals process and outcome-weighted precedent mechanism are not demonstrated.

**Why it matters â claims 3 and 4**

The combination may be a useful systems contribution. It has not been established as a novel methodology. Historical replay acceptance resembles validation gates, championâchallenger deployment, policy-as-code testing, and rule-system maintenance.

Executable form provides **affordances** for governance. It does not demonstrate that users understand rules better, catch mistakes faster, make fewer harmful decisions, or achieve better accountability. A short rule set can still be misleading, overbroad, unstable, or unauthorized.

**Fix/test**

Build a prior-art matrix against subgroup discovery, rule learning, case-based reasoning, policy mining, model deployment gates, temporal feature reconstruction, and agent guardrails. Distinguish conceptual overlap, implementation difference, and measured benefit.

Ablate residual mining, replay admission, outcome screening, and executable enforcement. Run a blinded governance-task study against rule lists, interpretable models, and black-box-plus-explanation systems. Measure defect detection, review time, correct scope understanding, rollback success, and audit completeness.

---

## C. Claims to retract or reword

Use these sentences verbatim unless new evidence supports stronger wording.

### Real-data accuracy

> âIn an exploratory study of one lenderâs selected HMDA records, the post-selected power-aware CCL variant achieved accuracy of 0.933, 0.931, and 0.933, versus 0.940, 0.931, and 0.934 for an untuned GBM; equivalence and generalization have not been established.â

### HMDA policy and tacit knowledge

> âThe HMDA experiment mines deviations from a fixed 43%-DTI heuristic, not from a validated, historically accurate lender approval policy; the resulting rules are predictive associations, not verified tacit underwriting policy.â

### Causal superiority

> âOn author-designed simulations, CCLâs outcome screen achieved higher agreement with a nonrogue-rule oracle than the implemented renewal-veto and T-learner baselines; these comparisons do not establish causal identification or superiority to strong, equally informed causal baselines.â

### Scoped bad-law filtering

> âThe scoped filter compares observed renewal rates within a rule-defined population; it is an association screen and requires additional identification assumptions or experimental evidence for a causal interpretation.â

### Governance advantage

> âCCL produces compact executable rules that support inspection, testing, and controlled deployment, but comparative readability, governance effectiveness, and operational safety have not yet been measured.â

### Novelty

> âWe propose and implement a combination of policy-residual rule mining, historical replay selection, outcome screening, and executable agent constraints; its novelty relative to existing rule-learning and deployment-governance systems remains to be established.â

### Point-in-time result

> âIn one synthetic run with deliberately injected later edits, as-decided reconstruction changed the mined rules; the reported 0.28-percentage-point difference was measured on admission data under unequal admission procedures and is not an unbiased estimate of future benefit.â

### Lakebase and OBO

> âLakebase branches isolate trial registry records while DBSQL performs replay; the supplied implementation does not establish isolation of executable law artifacts or requesting-user OBO authorization.â

### LLM evaluation

> âAn LLM judge accepted nine rationales derived from synthetic templated notes, and replay rejected three LLM proposals; these small tests do not establish rationale faithfulness or proposal utility.â

### Injection protection

> âIn the tested scenarios, deterministic fallback prevented final decisions from differing from the configured executable law; broader security, authorization, and correctness of that law were not established.â

### Rare-rule recovery

> âA combined change to support thresholds, precision criteria, and admission-window length raised positive-case agreement on the rare branch from 0.52 to 1.00, while reducing overall accuracy; this does not isolate a statistical-power explanation or prove exact branch recovery.â

---

## D. Five experiments that would most change my mind

**Freeze these criteria before execution. Do not modify them after seeing results.**

### 1. Independent, policy-grounded real-decision evaluation

**Design:** Obtain dated actual policies and decision-time records from at least three institutions or business units. Freeze CCL and tuning procedures before an independent evaluator releases future-period labels. Use equal tuning budgets for GBM and interpretable baselines.

**Pass:** In each domain, the simultaneous one-sided 95% lower bound for CCL minus the strongest baseline exceeds **â0.5 percentage points** in accuracy, while cost-weighted loss is no more than **5% worse**, and CCL beats policy-only on the preregistered primary metric.

**Fail:** Any domain misses those criteria. A pooled average must not hide failure in a domain.

### 2. Identified causal-policy evaluation

**Design:** Use randomized feasible discount offers, or an independently generated potential-outcome benchmark with known assignment and explicit utility. Include harmful, null, beneficial, confounded, and low-overlap settings. Give all estimators identical matured outcomes.

**Pass:** Against the strongest prespecified baseline, CCL has a positive simultaneous 95% lower bound on policy-value improvement in the primary harmful-effect setting; familywise false harmful-rule declarations are **â¤5%** in null settings; low-overlap cases trigger abstention rather than unsupported causal claims.

**Fail:** Superior oracle-label agreement without superior policy value does not count.

### 3. Blinded simulator and rare-rule stress test

**Design:** An independent team supplies at least 20 hidden world specifications, each with at least 30 seeds, after code freeze. Cross rare-rule prevalence with sample size, confounding, drift, and representational mismatch. Run the factorial threshold/window ablation.

**Pass:** At prespecified adequately powered sample sizes, exclusive rare-branch recall is **â¥0.90**, its nearby-negative false-approval rate is **â¤0.05**, and total accuracy is noninferior to standard CCL within **0.5 points**. Report success rates across all worlds, including non-rule worlds.

**Fail:** Positive-case fidelity of 1.00 accompanied by overapproval or aggregate degradation fails.

### 4. Corrected temporal and deployment-safety evaluation

**Design:** Identical point-in-time versus current-table pipelines, untouched future tests, realistic late/within-period edits, and production-like permissions. Add differential Python/SQL tests, AST fuzzing, concurrent promotion, rollback, credential expiry, and malicious proposal tests.

**Pass:** The claimed point-in-time benefit has a positive paired 95% lower bound on future performance under realistic edit regimes; no authorization bypass, unvalidated SQL execution, inconsistent activated law version, or silent unsafe fallback occurs in the preregistered fault suite.

**Fail:** Any security-critical failure fails the deployment claim, regardless of accuracy.

### 5. Governance-benefit randomized crossover study

**Design:** Blinded reviewers perform realistic approval, defect-detection, exception-scope, and rollback tasks using CCL versus a strong interpretable baseline and GBM with explanations. Include plausible but incorrect rules and misleading rationales.

**Pass:** CCL reduces median task time by **â¥20%**, with the lower 95% bound on critical-defect detection difference above **â2 percentage points**, and produces complete reproducible audit records for every activated rule.

**Fail:** Faster reviews with more missed critical defects, or better subjective readability without better task performance, do not establish a governance advantage.

---

## E. What is genuinely worth keeping

- **The separation of logged-decision imitation from a normative target.** Keep it, but name the simulator oracle honestly and add decision utility.
- **Delayed outcome availability.** This corrects a substantive earlier error; extend it into actual leakage-invariance tests.
- **Executable rules with deterministic enforcement.** This is a useful architecture when compilation, authorization, versioning, and activation are secured.
- **The explicit stricter-rule override and its regression test.** Expand this into cross-runtime property tests.
- **Point-in-time reconstruction as a first-class requirement.** The demonstration exposes a real engineering failure mode, despite the weak benefit estimate.
- **The correction log and retained negative results.** Preserve that transparency in a versioned public release with frozen experimental artifacts.

**Bottom line:** Keep the system prototype. Withdraw the equivalence, causal, and governance-superiority conclusions. The next credible advance is not another miner variant; it is an independently evaluated, policy-grounded experiment with identified outcomes and a defensible deployment boundary.