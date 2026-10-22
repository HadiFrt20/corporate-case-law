# Astra (databricks-gpt-6-astra) review of the autoresearch loop

Raw model output, unedited.

## Verdict

**Grade: B− for the research loop; D for the claim that CCL has established non-inferiority to case-level models.** The loop has improved materially from C+: the principal in-process leakage and executable-output loopholes are closed, consequential ablations were reported, a Goodhart failure was acknowledged, and the first fresh failure was not concealed.

**Yes—the process is now substantially honest about failure.** The worklog correctly says the clean test does not support “CCL ties or beats the black box.” But its proposed explanation—joint confounding missed by one-literal refinements—is still a hypothesis, not an established diagnosis.

**The single most valuable next step:** have the human freeze a **paired, detector-focused falsification experiment** comparing the locked method, no overrules, and one prespecified two-literal-refinement variant. Measure whether overrules actually cause the fresh false rejections, and whether the proposed fix reduces them without sacrificing near-threshold sensitivity. **Do this before another general optimization campaign or another fresh draw.**

*Scope: this is a static review of the supplied code and records, not an independently executed reproduction.*

---

## 1. Leakage: much better isolation, not a secure sandbox

### The ordinary data path is sound

- History is restricted to `month < m`; the view is constructed from an allowlist, not merely by dropping known secrets (`autoresearch/harness.py:75–81`).
- Renewal values are masked using eligibility computed **in the trusted process** (`harness.py:77–80`).
- Eligibility means approved, decided before \(m\), and contract ending strictly before \(m\) (`ccl_sim.py:462–465`).
- `outcome_known_month` is visible, but here it is just `month + 12 * term`, information already determined by the contract—not realized renewal information (`ccl_sim.py:102`).
- The runner reconstructs features from the sanitized view; it does not receive the harness’s full feature matrix (`autoresearch/runner.py:27–28`).
- Scoring receives only deal fields, discount and statute; the returned rules cannot name outcomes (`harness.py:37–42,119–122`).

**I see no ordinary route in the current method to unmasked future renewals or hidden row-level truth.**

### What remains exposed

The child imports the actual simulator (`runner.py:11`). That exposes:

- planted easy/hard rules and rogue populations;
- simulator constants and mechanisms;
- the default `WORLD`, `ROGUE_EFFECT`, and rule globals.

See `ccl_sim.py:25–50`.

These are **not synchronized to the current configuration**: the runner never calls `worlds.setup`. Thus `C.WORLD` is not a live channel revealing the harness’s selected world. Nevertheless, the library contains privileged simulator knowledge that a real firm would not have. The presence of `tenure_y` also identifies the easy/non-easy schema distinction (`ccl_sim.py:80`), although observing one’s own schema is legitimate.

Published dev/monitor seeds and world definitions remain readable (`harness.py:45–50`; `autoresearch/worlds.py:15–40`). Fresh runtime seeds improve protection against advance seed memorization (`harness.py:164–169`), but do not create an adversarial security boundary:

- the child has normal filesystem access under the same user;
- its module path reaches the repository;
- no read-only filesystem or OS-level process isolation is established;
- fresh draw identifiers are printed and may be accessible through run artifacts.

Consequently, **“separate address space and sanitized protocol” is supported; “the method cannot obtain the seed/world” is too absolute.** There is no evidence the supplied method exploits those routes.

---

## 2. Gates: no hidden executable model, but bounded rules are still a model

### The important holes are closed

The harness reconstructs holdings using only `kind`, copied literal strings and a finite numeric cap (`harness.py:56–72`). It enforces:

- ≤15 holdings;
- ≤4 population literals per holding;
- ≤45 population literals overall;
- a restricted grammar;
- bounded finite caps.

Scoring uses the parent process’s `apply`, whose literal execution is straightforward conjunction plus a discount threshold (`ccl_sim.py:150–153,342–349`). There is no returned callable, tree or AST that can execute a hidden predictor.

**Current `method.py` does not monkeypatch `generic_literals`.** It calls it and extends the candidate list locally, then passes literals to a copied miner (`method.py:23–34`). The premise in the question describes the old implementation.

A child-local monkeypatch of `apply`, `fires`, or `generic_literals` cannot change the parent’s scorer. The `apply` patch regression test demonstrates the central case (`tests/test_autoresearch.py:55–64`). Such monkeypatching remains prohibited by the program; it is no longer the old scoring hole.

### What the gates do not establish

A 15-rule policy is still a case-level predictive model, albeit a constrained, inspectable one. Narrow numeric intervals and numerous small populations remain possible. That is not smuggling if they fit the declared representation.

Two qualifications matter:

1. **The cap is another decision condition.** “Four literals plus a discount cap” is accurate; “four conditions total” is not.
2. **Syntactic compactness is not demonstrated readability.** There is no gate for minimum coverage, redundancy, monthly churn, or human comprehension.

There are also smaller contract weaknesses:

- `validate()` does not literally reject all extra keys; it trusts the runner’s `other_keys` marker and reconstructs away everything else (`harness.py:62–70`; `runner.py:19–21`). This is safe against executable extras, but the “ONLY these keys accepted” description is inaccurate.
- Valid grammar can reference a missing field, such as `tenure_y` in the easy world. Application failures are not converted into a clean invalid-law result (`harness.py:117–128`).
- `MONTH_TIMEOUT_S` is declared but unused; `readline()` can block indefinitely (`harness.py:34,113–114`).

**The scoring representation is enforced. Runtime/resource containment and repository integrity are not.**

---

## 3. Metric validity and the actual empirical result

### The scalar is coherent—but narrow

Within each configuration, agreement is case-weighted across months. The best baseline is selected retrospectively, and configuration gaps are then equally averaged (`harness.py:135–144`).

That is a coherent benchmark statistic for a declared mixture of synthetic configurations. It does **not** estimate:

- financial policy value;
- causal benefit;
- performance against the best available machine-learning approach;
- performance at a typical real firm.

The oracle itself is a simulator-defined threshold rule (`ccl_sim.py:96–100`). Agreement treats errors symmetrically, regardless of deal value or harm severity.

Also, **the current dev panel has 16 configurations, not 12** (`harness.py:46–47`). `program.md` still describes the old objective. Documentation needs an explicit versioned result table rather than one continuing headline score.

### Baselines are fixed and information-fair, not competitively exhausted

The five baselines use frozen implementations and common known-outcome eligibility (`harness.py:84–97`). They are computed in the trusted worker, which never imports the method; their computation occurs after method calls, but child-local mutations cannot contaminate them (`harness.py:100–128`).

Limitations:

- CCL receives repeated experimental tuning; the GBM variants largely retain defaults.
- A 15-leaf tree is a useful compact-model comparator, but not complexity-matched to a 15-holding cap policy.
- The T-learner conditions on discount while dividing treatment arms by the discount threshold. Its counterfactual predictions therefore extrapolate across disjoint discount support (`ccl_sim.py:24,107–109`; `harness.py:91–96`).
- Retrospective winner selection favors the baselines, but does not make them comprehensive or equally optimized.

The proper description is **“best of five fixed baselines, selected retrospectively per configuration.”**

### What the results support

| Result | Defensible interpretation |
|---|---|
| Historical **+0.110 dev / −0.071 holdout** | Substantial improvement over the starting CCL implementation on nearby synthetic distributions; not demonstrated superiority or equivalence. |
| Current **+0.306 dev v2.1** | Performance on an adaptively expanded development panel. |
| Current **−0.032 monitor** | Descriptive performance on a repeatedly observed monitoring panel. |
| First fresh **−0.419 [−0.901, +0.063]** | **Non-inferiority was not established at the −0.25 margin.** |

The fresh result is not merely an inconvenient mean: **10 of 12 configuration gaps are negative**. All four segment configurations lose, and one no-harm near-threshold configuration loses approximately 1.38 points (`autoresearch/FRESH_run1_k16737199.txt:12–23`).

Conversely, the interval includes zero: **failure to establish non-inferiority is not proof of inferiority.**

The t-interval is appropriately disclosed as optimistic, but remains inadequate for a confirmatory claim: configurations share firms/seeds, worlds are paired across effects, and development scores are selected through repeated experimentation (`harness.py:14–19,143–149,165–168`). Use independent generated-world clusters and a prespecified inferential procedure.

The −0.25-point margin also needs substantive justification: against baselines making only a few tenths of a percent errors, this margin can permit a large relative increase in error.

---

## 4. Goodharting and transferability

### Changes visibly motivated by planted structure

- **Integer thresholds:** generally sensible, but the recorded justification explicitly targets the planted `tenure >= 11` rule (`method.py:23–29`; `ccl_sim.py:41`).
- **Support 30:** the worklog describes recovering the rare >1M branch, matching the planted hard-world disjunction (`method.py:19`; `ccl_sim.py:38`).
- **Beam 60:** selected because the planted churn interaction became discoverable (`ccl_sim.py:39`; WORKLOG, experiments 6–10).
- **Refinement screening:** introduced after a particular Simpson-confounding failure; its utility is plausible, but its specification was tuned within the simulator.
- **Full-threshold refinement checking:** the clearest Goodhart. Large planted dev effects made an overly stringent test look harmless; near-threshold stress exposed lost sensitivity.

The parameter-neighborhood experiments are useful: they weaken a “single lucky parameter value” explanation. They do not establish transfer outside these rule templates.

### Changes with stronger general justification

- point-in-time outcome eligibility;
- explicit, bounded executable policy artifacts;
- considering integer thresholds systematically;
- comparing within populations rather than against one global renewal mean;
- pruning only through logical implication;
- removing a replay split when it demonstrably starves a miner of data.

But the last point must remain narrow: replay was ablated for mined rules, not tested as a defense against untrusted proposals.

The fresh generator still samples familiar forms—conjunctions, integer-tenure thresholds, size thresholds, and segment×region rogue populations (`worlds.py:26–40`). This is fresh sampling **within a known simulator family**, not broad external validity.

A further transfer limitation: this is a fixed logged-data backtest. The firm is generated once and CCL’s decisions do not change subsequent approvals or observed outcomes (`harness.py:102–128`). Deployment would change the future data distribution.

### Was the response to Goodhart honest?

Mostly yes. Expanding dev after discovering a missing regime is legitimate exploratory research, provided old and new scores are separated—which AR-012 does.

However, “the repair was justified a priori by power” must not imply it was independent of the observed failure. **The statistical rationale can be principled while the choice to introduce it remains adaptive.** Likewise, stress ceased being untouched once it prompted redesign.

---

## 5. Overruling: a useful association heuristic, not a validated harm detector

### The description now overstates what the implementation requires

The method header says the contrast holds “in every one-literal refinement” (`method.py:10–11`). That is no longer the test.

Current behavior is:

1. Require an aggregate observed drop ≥0.20 and a z-statistic against zero ≤−3.
2. Examine one-literal refinements and complements.
3. Skip cells with fewer than 20 observations in either arm.
4. Reject the population only when a refinement significantly contradicts the threshold (`method.py:63–76,88–94`).

Thus it **passes unless sufficiently strong counterevidence appears**. It does not demonstrate ≥0.20 harm in every refinement.

### Principal failure modes

**Multiple search and reuse.** All single literals and pairs are searched, the most extreme eligible z-statistic is selected, up to three overrules are added, and this repeats monthly (`method.py:83–97`). Thousands of correlated hypotheses and repeated observations invalidate a simple “z=−3 is strong evidence” interpretation. The point-drop threshold and refinement tests complicate the error rate; they do not provide search-adjusted control.

**Wrong null for the substantive threshold.** The aggregate z-test is against zero, not against a drop of 0.20. A significant negative association plus a point estimate below −0.20 does not establish that the true drop exceeds the harm threshold (`method.py:91–94`).

**Small cells become permission.** Skipped refinements contribute no objection. A population can pass with little informative refinement evidence. Adding two-literal refinements may exacerbate this unless “insufficient evidence” gets an explicit treatment.

**Marginal refinement is not joint adjustment.** One-at-a-time splits cannot generally remove interactions among confounders. Segment×region rogue populations in generated worlds make this concern especially plausible (`worlds.py:36–37`), but the fresh table alone does not prove this caused the errors.

**Selection and non-identification.** Both arms contain only historically approved deals with matured outcomes. Approval selection, customer quality, calendar time and outcome-delay composition can differ. Above-policy versus in-policy is not randomized treatment. Unobserved confounding cannot be solved merely by enumerating more literals.

**Segment versus exception behavior.** In an adequately controlled population, a segment-wide low renewal rate should appear in both arms; exception-specific harm should not. Broad populations, differing mixtures and small cells break that intuition. Fresh segment losses are exactly the kind of negative-control warning this detector needed.

**Time mismatch.** Mining uses 12 recent months, while overrules use all matured history (`method.py:101–104`). That may improve power but can retain obsolete outcome associations.

**Bottom line:** promising observational screening with demonstrated failure modes—not causal harm detection, and not yet a calibrated automatic veto.

---

## 6. Round-1 findings: adjudication

The response document lists 21 findings. Here is my assessment of each, against the current code and subsequent records.

| Round-1 finding | Status | Evidence / remaining limitation |
|---|---|---|
| Same-process frames expose firm, seed and oracle | **Resolved** | Separate interpreter and sanitized request path: `harness.py:107–113`; `runner.py:24–28`. This resolves the original in-process route, not all OS-level access. |
| Method can patch `outcome_rows` before view construction | **Resolved** | Eligibility is computed in the trusted process: `harness.py:75–80`; child mutation regression: `tests:55–64`. |
| Scorer passes current approvals/renewals to `apply` | **Resolved** | `DEC_COLS` and restricted literals: `harness.py:37–42,121`. |
| Seeds and alternative rules readable on disk | **Partially** | Runtime fresh draws help; repository access and published panels remain: `harness.py:45–50,164–169`; `worlds.py:15–40`. |
| `generic_literals` monkeypatch | **Resolved** | Local candidate expansion and copied miner: `method.py:23–34`. |
| AST escapes condition limits | **Resolved** | Runner flags AST/conds; harness reconstructs only literal holdings: `runner.py:19–21`; `harness.py:62–71`. |
| Literals unrestricted to decision fields | **Resolved** | Strict grammar: `harness.py:37–42,67`; negative tests: `tests:17–21`. |
| Caps, condition objects, SQL rounding | **Resolved for this loop** | Finite bounded caps and normalized holdings: `harness.py:68–70`. SQL is not the scoring path; its rendering is not thereby repaired. |
| “Best black box” is only fixed GBM variants | **Partially** | Five fixed baselines now exist: `harness.py:84–97`. Competitive tuning and consistent wording remain absent. |
| Baseline winner selected by test-oracle agreement | **Not changed; disclosed** | Still `max(b, key=b.get)`: `harness.py:138–140`. Acceptable as a retrospective benchmark if labeled. |
| T-learner extrapolates across discount threshold | **Not resolved** | Discount remains a feature and arms remain threshold-separated: `ccl_sim.py:24,109`; `harness.py:91–96`. |
| Baselines contaminated by method mutations | **Resolved for in-memory mutations** | Trusted worker never imports method; child isolation: `harness.py:107–128`. Shared-disk integrity remains procedural. |
| Missing uncertainty, NI margin and false rejections | **Partially** | All are reported: `harness.py:35,143–152`. Dependence-aware uncertainty and a justified margin remain open. |
| Holdout has become monitoring data | **Resolved in designation/protocol** | Monitor/fresh distinction implemented: `harness.py:18–19,164–170`. Fresh run 1 was actually performed and retained. |
| Tuning to planted rules | **Partially** | Neighborhoods and fresh testing were performed; fresh failed. The threat is measured, not eliminated. |
| Historical-containment pruning and pruning before truncation | **Resolved** | Logical-subset pruning against the selected overrules: `method.py:105–109`. |
| Overrule detector is an association heuristic | **Partially** | Limitation acknowledged and stressed; statistical calibration, skipped cells and joint confounding remain: `method.py:63–97`. |
| Asymmetric exclusion of already-overruled rows | **Resolved** | Both arms exclude `taken`, including refinement arms: `method.py:70,88`. |
| Harm-detector stress tests | **Partially** | First set implemented: `harness.py:49–50`; `worlds.py:57–62`. Coverage remains limited and threshold tests informed development. |
| Discovery/confirmation split | **Partially** | Experiment 15 tried it and reported degradation. Current method still searches and assesses on the same outcomes: `method.py:79–97`. One unsuccessful split does not resolve search bias. |
| Ablations and parameter neighborhoods | **Resolved as an initial experimental request** | WORKLOG experiments 14, 17 and 18 report them. They should now be repeated for the materially changed locked detector. |

### Tests: valuable, but two claims need correction

The suite genuinely tests forbidden fields, basic form violations, view masking, child-local monkeypatching and explicit method exceptions.

However:

1. **The GC leakage probe is defective.**  
   `list(getattr(o, "columns", []) or [])` truth-tests a pandas `Index`, ordinarily raises an ambiguity error, and is then skipped (`tests/test_autoresearch.py:73–76`). The positive control only exercises stack-name detection, not GC detection (`tests:93–107`). So the claim that the GC probe is validated is unsupported.

2. **Outcome timing is not independently checked.**  
   The view test uses `C.outcome_rows` as its expected answer (`tests:46–47`). Add handcrafted cases for rejected deals, future decisions, maturity exactly at \(m\), and maturity immediately before \(m\).

Also add the untested **45-total-literal boundary**, end-to-end AST/conds rejection, missing-field handling, hangs/timeouts, malformed protocol output, and tests for the logical-pruning and symmetric-exclusion fixes.

---

## 7. Ranked next steps

### 1. Diagnose and falsify the overrule mechanism

Human freezes a paired experiment:

- locked method;
- same miner with no overrules;
- same miner with one prespecified two-literal-refinement implementation.

Use controlled causal, segment-only, joint-confounding and small-cell worlds across harm sizes near 0.20. Record, per overrule:

- selected population and evidence;
- refinement coverage and skipped cells;
- decisions changed;
- harmful approvals prevented;
- additional oracle-valid approvals rejected.

Treat fresh run 1 as diagnostic data now. **Do not assume its false rejections all come from overrules.**

### 2. Precommit the next confirmatory evaluation

Before looking again, freeze method/harness hashes, independent world draws, sample size, margin, clustering, stopping rule and success criteria. Retain every draw and failure. “One fresh draw per revised method until one passes” is still optional stopping unless the entire sequence is accounted for.

### 3. Calibrate search, uncertainty and abstention

Evaluate null-world false-overrule rates and near-threshold power. Test confirmation/cross-fitting or search-adjusted procedures. Define what happens when refinements lack support; do not silently interpret missing evidence as homogeneity.

### 4. Strengthen baseline competition

Tune baselines on development data under a declared budget; add a comparator with the same rule/cap language or deployable model-selection procedure. Keep the retrospective best-of-five score as a separate benchmark.

### 5. Harden reproducibility and boundaries

Fix the GC test, enforce timeouts, isolate filesystem permissions where needed, and emit immutable manifests containing method, harness, simulator, dependencies, panel specification and draw identifiers. Update stale “12 configs,” “every refinement,” and “best black box” wording.

### 6. Broaden external-validity tests

Vary drift, outcome delays, sample size, feature dependence, latent confounding and policy-induced feedback. Eventually test on real retrospective firm data with an explicit identification and deployment plan—not merely another permutation of planted rule templates.

---

## What may honestly be claimed today

CCL’s autoresearch loop now enforces a bounded literal-rule output format across a separate-process boundary and has produced substantial development-set improvements over its starting implementation against five fixed synthetic-data baselines. Its observational overrule mechanism can prevent harmful approvals, but can also reject legitimate business through confounding and insufficiently informative refinements. The project has disclosed a Goodhart failure and its first locked-method fresh evaluation, which failed the prespecified non-inferiority criterion: −0.419 percentage points, reported 95% interval [−0.901, +0.063]. **Neither general non-inferiority, causal harm detection, nor real-firm transfer has been established. The credible achievement is a more falsifiable and candid research process—not yet a successful replacement for case-level models.**