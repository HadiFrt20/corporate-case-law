# Astra (databricks-gpt-6-astra) review of the autoresearch loop

Raw model output, unedited.

## Verdict

**Overall grade: C+.** This is a substantially better *research process*, with a promising method improvement—but it is not yet an enforced, leakage-resistant autoresearch benchmark.

The strongest result is **closing most of the gap to three fixed GBM-based comparators on this simulator**, including improvement on additional seeds and an alternate planted-rule world. The weakest claims are “the method cannot see hidden information,” “only the frozen rule engine can decide,” and “every-refinement contrast detects harm.” The implementation does not establish those claims.

**I see no direct use of hidden truth or future outcomes in the submitted method.** I do see several ways an editable `method.py` could obtain them or bypass the rule restrictions. Those are harness defects, not evidence that the reported improvement was obtained dishonestly.

This is a source review of the supplied files and reported results, not an independent reproduction. `rulec.py` was not supplied, so compiler-specific guarantees cannot be verified.

---

## 1. Leakage: the ordinary view is mostly right; the execution boundary is not

### What is correctly implemented

- Historical rows are restricted to `month < m`, the five identified ground-truth columns are removed, and unavailable renewal outcomes are masked: **`autoresearch/harness.py:59–65`**.
- Outcome eligibility requires historical approval and contract completion **strictly before** the decision month: **`ccl_sim.py:462–465`**.
- `X` contains deal attributes, not approval labels, renewal outcomes, or hidden truth: **`ccl_sim.py:107–109`**.
- The submitted overrule method explicitly intersects both comparison groups with `outcome_known`: **`autoresearch/method.py:47–60`**. It does not mistake masked `False` values for observed failures.

**`outcome_known_month` is not intrinsically a leak here.** It is calculated as origination month plus contractual term, something the firm could know at origination: **`ccl_sim.py:102`**. Historical `approved` and `statute` are also legitimate training information.

### What remains accessible

| Route | Evidence | Assessment |
|---|---|---|
| **Hidden world and planted rules** | Harness configures `C` before importing/calling the method: **`harness.py:46–55, 110–115`**. `C.LOOSEN`, `C.TIGHT`, `C.ROGUE`, `C.WORLD`, and `C.ROGUE_EFFECT` expose simulator configuration: **`ccl_sim.py:25–50, 61–65`**. | Directly accessible. “Never told the world” is not an information boundary. In alt, `WORLD` says hard, but `LOOSEN/TIGHT` contain the alt rules. |
| **Seed, complete firm, future rows, oracle columns** | `world`, `effect`, `seed`, `df`, and `X` remain in the caller’s Python frame during `build_law`: **`harness.py:107–115`**. | Same-process Python introspection can access caller locals. No seed reconstruction is necessary. |
| **Future eligibility manipulation** | Method imports before the first `view_of`; later calls use `C.outcome_rows`: **`harness.py:111–115, 59–64`**. | A patch to `outcome_rows` can expose premature renewals. Setup does not restore that function. |
| **Outcome access during scoring** | The evaluator drops only `HIDDEN` before calling `apply`: **`harness.py:119–120`**. Thus current-month `approved` and unmasked `renewed` remain in the scoring dataframe. | Decision-time data is not restricted to decision-time features. This matters even without replacing `apply`, because literal fields are not allowlisted. |
| **Simulator source and public test configuration** | Dev/holdout seeds and alternate rules are in the readable harness: **`harness.py:32–42`**. | A procedural prohibition on reconstructing firms is useful, but it is not enforcement. |

The current method’s candidate generator uses normal deal fields, so **the submitted implementation does not appear to exploit the scoring-data leak**: **`method.py:22–28, 48–49`**, **`ccl_sim.py:129–140`**.

**Bottom line:** the view is sensible for a cooperative method. The claim that the method *cannot* access forbidden information is false.

---

## 2. Form gates: several substantive bypasses

### A. The `generic_literals` monkeypatch is benign in purpose, but exposes a real hole

The patch at **`method.py:31`** changes training search, not the submitted decision semantics. Expanding candidate thresholds is an acceptable research operation.

**Doing it by mutating the supposedly frozen simulator is not an acceptable trust boundary.**

After each method call, `setup` resets selected configuration, not functions: **`harness.py:115–120`**, **`ccl_sim.py:53–65`**. The same mechanism can replace:

- `C.apply`, so an arbitrary case-level model decides;
- `C.fires`, `C.literal`, or `C.scope`, so apparently simple rules execute different semantics;
- `C.to_sql`, so the printed explanation differs from execution;
- `C.outcome_rows`, contaminating both views and uncached baselines.

The gate and scorer themselves resolve these mutable functions: **`harness.py:80, 87, 120`**.

**Recommendation:** preserve the richer candidate search, but copy the miner into `method.py`, or have the human provide an explicit candidate-list parameter. Do not permit monkeypatching the evaluator. Callable identity checks are useful diagnostics, but not a substitute for process isolation.

### B. AST rules bypass the advertised condition limit

For AST holdings, the gate only calls `rulec.to_sql`: **`harness.py:73–76`**. It does not count:

- predicates;
- Boolean branches;
- nodes or depth;
- arithmetic complexity;
- total law description length.

The `<=4` check applies only to `lits` and `conds`: **`harness.py:78, 85`**.

If the compiler accepts sufficiently large Boolean expressions, a decision tree could be represented as one AST holding. **I cannot determine the compiler’s internal restrictions without `rulec.py`; the harness itself does not enforce this budget.**

### C. “Valid literal” does not mean “permitted decision field”

`C.literal` accepts generic dataframe columns, including Boolean columns through its fallback: **`ccl_sim.py:113–124`**. The gate checks whether the literal evaluates on a sample, not whether its field is permitted: **`harness.py:79–81`**.

Consequently, current-month `approved` or `renewed` can be used as rule conditions at evaluation, because they remain in the scoring dataframe. Fifteen short rules are no protection against a rule that reads an outcome.

### D. Other schema and semantic weaknesses

- Numeric cap validation exists only in the literal branch and merely attempts `float(...)`: **`harness.py:82–85`**. There is no finite-value/range validation.
- `conds` receives no explicit feature/operator/type validation before SQL rendering. Execution treats every operator other than `<=` as `>`: **`ccl_sim.py:155`**.
- Rule objects are not restricted to inert, exact-type JSON structures. Python subclasses or custom objects can carry executable behavior.
- SQL is rendered, not independently replayed. Literal caps execute at their actual precision but print rounded to integers: **`ccl_sim.py:153, 173–174`**. A fractional cap can therefore produce a misleading explanation.
- Fifteen ordinary conjunctions are a legitimate bounded rule model, not inherently “smuggling.” But count alone does not establish readability, adequate support, or stability.

**Required boundary:** serialized plain-data law → independent trusted validator → independent trusted evaluator, with decision-time input restricted to an explicit feature allowlist.

---

## 3. Metric validity: useful benchmark score, narrower than “best black box”

### The arithmetic is reasonable

The harness first case-weights months within each configuration, then equally weights configurations: **`harness.py:149–152`**. That is a defensible macro-average **if the twelve configurations are the intended benchmark distribution**.

It is not an estimate for a real firm population. The easy/hard and exception/segment weights are arbitrary design choices.

### Baselines are fixed, but “best” means best of three implementations

The comparators are:

1. approval GBM;
2. that GBM plus an absolute renewal veto;
3. that GBM plus a T-learner veto.

They use fixed default `HistGradientBoostingClassifier` settings and shared outcome eligibility: **`harness.py:92–104`**.

That corrects the previous information disadvantage. Nevertheless:

- CCL receives repeated development effort; the baseline hyperparameters, calibration, windows, and outcome estimators do not.
- All three share the same underlying approval GBM.
- There is no competitively tuned baseline suite or stronger outcome-aware challenger.

Thus the accurate phrase is **“best of three fixed GBM-based baselines,” not “best case-level black box.”**

There is also a disadvantage to the baselines: the winner is chosen using **test-oracle agreement within each configuration**, rather than a deployable validation-based selection procedure: **`harness.py:149–150`**. This is a useful retrospective comparator, but its selection privilege should be disclosed.

### A specific T-learner problem

`statute` is determined by discount, and discount is included in `X`: **`ccl_sim.py:103, 109`**. The treatment/control models are trained on opposite sides of the discount threshold and evaluated on the same above-policy cases: **`harness.py:99–104`**.

That makes the control prediction an extrapolation outside its observed discount range. This is not a well-supported causal counterfactual merely because it is called a T-learner.

### Caching is not fully trustworthy yet

On a cache miss, baselines run after the editable method in the same process: **`harness.py:115–125`**. Module mutations can therefore contaminate the reference scores. The cache key includes harness and simulator hashes, but not method state, dependency versions, or compiler code: **`harness.py:133–143`**.

Compute baselines in a clean trusted process, and record complete provenance.

### What the reported numbers support

- Dev improved from **−1.141 to +0.110 percentage points**.
- Holdout improved from **−0.836 to −0.071 points**.
- That is a **1.251-point dev improvement and 0.765-point holdout improvement** over the starting CCL implementation.

This is meaningful evidence of progress **within the simulator**.

But:

- +0.110 is a small adaptively selected development advantage.
- −0.071 means the final method **does not beat the benchmark on the reported holdout average**.
- All four alt configurations remain negative; easy configurations win, hard configurations lose.
- There are no uncertainty estimates or prespecified noninferiority margins.
- The configurations are not twelve independent worlds: seeds are reused across related scenarios.

The holdout improved at every reported checkpoint, so this is **not** evidence of “dev rises while holdout collapses.” It is evidence of improvement with a remaining generalization gap.

### Holdout quality

Fresh seeds test resampling within the same DGP. Alt adds some structural variation, but still consists of short planted rules and the same outcome mechanism.

Furthermore, repeated checkpoints—and an early check triggered by the first positive dev result—make this a **monitoring set**, not an untouched final test. Even without explicit keep/discard decisions, seeing results can influence subsequent hypotheses or stopping. Publicly available alt rules are not genuinely hidden from the research agent.

Finally, agreement is not policy value. Zero harmful approvals is insufficient because rejecting everything also achieves it. The harness records false rejections but does not print them in its summary: **`harness.py:123, 151–160`**. Harm percentages use **all cases** as denominator, and segment configurations have zero oracle harm by construction: **`harness.py:122`**, **`ccl_sim.py:98–100`**.

---

## 4. Goodharting: plausible mechanisms, simulator-specific optimization

The experiment log is unusually candid about which planted branches improved. That candor is good; those explanations also limit the generalization claim.

| Kept change | Transferable rationale | Simulator-specific concern |
|---|---|---|
| Every integer threshold for term/tenure | Reasonable generic treatment of low-cardinality integers. | Explicitly unlocks planted `tenure >= 11`: **`method.py:25–27`**, **`ccl_sim.py:41`**. Only two named fields receive this treatment. |
| Admission window four months | More reliable replay evidence. | Tuned against this firm size, noise level, and retirement schedule: **`method.py:18, 69–71`**, **`ccl_sim.py:26`**. No universal reason for four. |
| Support 30 | Better detection of rare but legitimate exceptions. | Selected partly to recover the `>1M` OR branch: **`method.py:18`**, **`ccl_sim.py:38`**. Thirty observations is not a portable confidence standard. |
| Beam 60 | More thorough interaction search. | Selected for the planted churn interaction: **`ccl_sim.py:39`**. More search also increases selection risk. |
| Refinement check | Sensible defense against broad heterogeneous populations. | Tailored to a simulator where relevant confounders are simple, observed, and expressible as literals. |
| Drop rule-level outcome screen | Removes redundant machinery under the current overrules. | Unknown safety outside this very strong-signal harm mechanism. |
| Strike overruled precedents | Potentially useful legal simplification. | The implementation proves containment only on historical observations—not logically or on future cases. |

Two additional code-level concerns deserve fixes:

1. **Historical containment is not semantic redundancy.**  
   Removal uses observed firing masks: **`method.py:75–77`**. The comment “its decisions cannot change” is too strong. A future case can satisfy a deleted precedent but not the overrule.

2. **Pruning occurs before overrule truncation.**  
   Precedents are removed using *all* computed overrules, then only a prefix of those overrules is returned: **`method.py:76–78`**. Under budget pressure, a precedent may be removed because of an overrule absent from the final law.

Also, the benchmark already favors compact-rule methods: hidden policies are compact rules, approvals have only 4% noise, and the miner’s integer cap grid closely matches planted caps: **`ccl_sim.py:22–43, 227`**. Success here is not yet success against messy organizational decision-making.

---

## 5. Overruling precedents: promising association screen, not a sound causal harm detector

### What it actually does

It searches one- and two-literal populations, compares observed renewals among approved above-policy and in-policy deals, requires:

- at least 40 observed outcomes per arm;
- estimated drop at least 0.20;
- pooled z-score at most −3;
- no sufficiently populated one-literal refinement whose estimated drop is less than 0.10;

then greedily selects up to three populations: **`method.py:32–64`**.

That is a reasonable exploratory subgroup procedure. The failed naive version and improved refinement version provide useful evidence that **heterogeneity matters**.

### Why “every refinement” and “no Simpson effect” overstate it

**1. It checks only one additional literal at a time.**  
The implementation tests `P & Q` and `P & ~Q`: **`method.py:37–41`**. It does not examine every intersection of additional literals. Joint confounding can survive all these marginal checks.

**2. Small cells are skipped, not passed.**  
If either arm has fewer than 20 outcomes, the refinement imposes no constraint. `homogeneous` returns `True` if nothing disqualifies the population: **`method.py:41–42`**. Sparse regions therefore generate apparent robustness through missing evidence.

**3. The refinement requirement is weaker than the main harm threshold.**  
A 0.10 estimated drop passes refinements even though the claimed harm threshold is 0.20. No confidence bound establishes a minimum 0.20 effect.

**4. Search-adjusted uncertainty is absent.**  
With approximately 1,800 tested populations, a one-sided z≤−3 cutoff alone would yield roughly 2.4 exceedances under an idealized independent null. That is not the actual false-overrule rate—the effect-size requirement, correlations, and refinement filter matter—but it illustrates why the nominal z-score is not a post-search significance guarantee.

Selection repeats monthly on overlapping data and greedily selects the most extreme surviving z-score: **`method.py:52–64`**. This requires empirical null calibration or independent confirmation.

**5. “Same population” does not establish exchangeability.**  
The arms differ in discount, historical approval selection, potentially unobserved customer quality, and anything not balanced by the literals. Both arms contain only approved deals. The procedure does not estimate the effect of approval versus rejection.

**6. Outcome maturity changes the population.**  
Overrules use all available history, while decision mining uses the recent twelve months: **`method.py:69–72`**. Long-term contracts contribute much later. Neither calendar-time balance nor a temporal refinement is built into the ordinary literal generator: **`ccl_sim.py:132–139`**.

**7. Sequential selection changes the comparison asymmetrically.**  
Previously selected populations are excluded from the above-policy arm, but not the in-policy arm: **`method.py:40, 55, 64`**. Later contrasts are no longer straightforward comparisons of identically restricted populations.

**8. Generalization beyond observed approvals is aggressive.**  
An overrule rejects all above-policy deals in the selected population, not merely the discount range and cohorts supporting the contrast: **`method.py:63`**, **`ccl_sim.py:150–153`**.

### Why these particular worlds are accommodating

The simulator gives a large **0.50 renewal-probability difference**—0.85 versus 0.35—against a 0.20 threshold: **`harness.py:30, 55`**, **`ccl_sim.py:94–102`**. The harmful population is simple and observed.

The segment world deliberately produces poor renewal without incremental above-policy harm; the exception world adds harm specifically above policy. This is a useful contrast, but much cleaner than real treatment selection.

**Call the method a refinement-screened observational overrule heuristic.** Do not call it causal identification, proof of safety, or a general solution to Simpson’s paradox.

---

## 6. What the human should change next, ranked by value

### 1. Enforce the trust boundary before running more optimization

- Separate generator/scorer and editable method into isolated processes.
- Send only serialized historical allowed data.
- Return only a strict plain-data law format.
- Restrict scorer inputs to decision-time features.
- Evaluate with trusted code unavailable for mutation.
- Block access to evaluator memory, hidden configuration, and privileged files.
- Add adversarial tests for hidden-column access, premature outcomes, function mutation, and oversized ASTs.

This protects every subsequent result.

### 2. Freeze this candidate and run a genuinely fresh evaluation

Use hidden seeds and newly generated rule worlds, with the method and baseline suite locked first. Report paired uncertainty across independent firms/worlds, subgroup gaps, exact error counts, and a prespecified noninferiority margin.

This most directly answers whether the reported improvement generalizes.

### 3. Stress-test the harm detector independently of rule mining

Prioritize:

- zero-effect worlds with observable and unobservable confounding;
- effects just below/above 0.20;
- sparse cells and poor overlap;
- joint confounders invisible to single-literal refinements;
- changing outcome mechanisms and delayed observations.

Measure false overrules, missed harmful populations, false rejections, and detection delay—not just overall accuracy.

### 4. Add discovery/confirmation separation for overrules

Discover populations on one historical partition and confirm on another, preferably respecting time. Compare search-adjusted or null-calibrated procedures, shrinkage, and explicit “insufficient evidence” states. Require stability before deployment.

### 5. Build a competitively developed baseline suite

Give comparators comparable development effort, fixed validation procedures, tuning budgets, and appropriate outcome-model features. Include compact trees/rule lists to distinguish “CCL architecture helps” from “a small rule model matches a rule-generated world.”

Retain the retrospective best-of-three score as a secondary benchmark.

### 6. Run ablations and parameter neighborhoods

Separately test the richer literals, admission window, beam width, support reduction, refinement check, removed screen, and pruning. Evaluate neighborhoods rather than selected points: does support 30 work broadly, or just unlock one planted branch?

Test pruning by logical implication or independent fresh-case equivalence, not observed-history containment alone.

### 7. Expand the objective and operational evidence

Report false rejections, nonharmful false approvals, conditional harm rates, per-group errors, law churn, minimum support, and total predicate count. Add independent SQL/Python equivalence checks and persist monthly laws.

Ultimately test on real longitudinal firm data in shadow mode. The present replay uses a fixed logged population; it does not simulate how changed approval policies alter future outcomes and available evidence.

---

## 7. Grades and an honest claim

| Component | Grade |
|---|---|
| Experimental discipline and transparent failure logging | **B** |
| Enforced leakage protection and form gates | **D** |
| Benchmark metric and comparator validity | **C+** |
| Evidence of simulator-level improvement | **B−** |
| Evidence for general harm detection or real-firm transfer | **D+** |
| **Overall loop and claims** | **C+** |

**What may honestly be claimed today:** On the supplied synthetic benchmark, an adaptively developed compact-rule method substantially improved over the starting CCL implementation, reducing its development deficit against the best of three fixed GBM-based baselines from 1.141 percentage points to a 0.110-point advantage, while reducing the reported holdout deficit from 0.836 to 0.071 points. The final method used about eight rules on average and reported no harmful approvals at the displayed precision. These results support compact rules as a competitive representation for these planted-rule worlds and refinement screening as a promising way to reduce overblocking. They do not establish superiority on fresh worlds, causal harm identification, real-firm safety or value, or an enforceably leakage-free autoresearch loop.