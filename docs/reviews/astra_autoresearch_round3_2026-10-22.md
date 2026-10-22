# Astra (databricks-gpt-6-astra) review of the autoresearch loop

Raw model output, unedited.

# Round 3 review

**Bottom line: this is now a credible negative research result—not a successful non-inferiority result.** The strongest improvement since round 2 is that you committed to tests, reported failures, and stopped. The remaining problems are incomplete provenance enforcement, overstatements in the detector interpretation, and several claims that are broader than the experiments establish.

**Grades**
- **Research loop: B+**, up from B−.
- **Final claims as written: B.**
- **Final research record overall: B+.**
- **Non-inferiority: not established.** Continuing to assert it would deserve an F; explicitly abandoning it is good research practice.

**Audit scope:** I reviewed the supplied source and records, not a live repository. You did not supply `runner.py`, `worlds.py`, `ccl_sim.py`, the current `method.py`, the original frozen candidates, or the tests. Consequently, I can inspect the parent-side boundary and Bonferroni candidate, but cannot certify the full information boundary, calculate the committed hashes, inspect historical diffs, or independently reproduce the runs.

---

## 1. Pre-registration order: consistent, with an important verification limit

Reading the supplied log **oldest first**, the relevant sequence is:

| Order | Commit | Event | Assessment |
|---|---|---|---|
| 1 | `e6a9069` | AR-013 pauses optimization and commits to falsification followed by confirmation | Before the detector experiment |
| 2 | `0f04399` | Harness v3, frozen candidates, AR-014 pre-registration | Before recorded detector results |
| 3 | `54b885c` | Detector analysis script | Before recorded results; commit order cannot establish when someone first read output |
| 4 | `89f71ef` | Absolute-path infrastructure fix | **After detector pre-registration**, before successful recorded detector results |
| 5 | `6efd56f` | Detector results and confirm_1 manifest | Before recorded confirmatory result 1 |
| 6 | `914f007` | Confirmatory result 1: FAIL | No intervening commit shown |
| 7 | `e6a37f2` | Bonferroni candidate, development results, confirm_2 manifest | Before recorded confirmatory result 2 |
| 8 | `77eae3b` | Confirmatory result 2: FAIL; stop | No intervening commit shown |
| 9 | `9e1fc99` | README evidence update | After both failures |

### What this verifies

The **reported commit sequence is consistent with both confirmatory manifests preceding their results**. It shows no intervening commit between either manifest and its result. The Bonferroni change happened **between tests**, not after confirm_2 registration.

The detector’s path fix was a post-registration harness change. Its present implementation is narrowly infrastructural: resolve `--method` before entering the temporary working directory (`harness.py:200–201`, `113–115`). Disclosure of the failed attempt and repair is appropriate.

### What it does not verify

A log of commit subjects cannot prove:

- which files changed inside each commit;
- that no uncommitted edits existed during a run;
- that a run occurred only once;
- that results were unread before the analysis-script commit.

The runtime checks provide additional protection: the method and combined harness hash must match the manifest (`harness.py:203–206`). But there is a material omission:

> **The simulator is not pinned by either confirmatory manifest.**

`HARNESS_SHA` covers only `harness.py`, `worlds.py`, and `runner.py` (`harness.py:59–60`). `C.CODE_SHA` appears in the baseline cache filename (`221`), **not in the manifest verification**. A simulator change could alter the oracle, timing, helpers, or baselines without failing those checks. AR-013 explicitly required a simulator hash.

**Verdict:** registration order passes a documentary consistency check. “No method or harness changes between registration and execution” is supported by the supplied record and runtime checks, but not independently proven from this log. Full executable provenance remains incomplete.

---

## 2. Leakage: the parent-side view is substantially better; this is not a sandbox

### What the supplied code gets right

The parent constructs a **positive column allowlist**, rather than merely dropping known hidden columns:

- Allowed historical columns: `harness.py:39–42`.
- Only rows with `month < m`: `82–85`.
- Renewal values masked unless `C.outcome_rows(df, m)` says they are known: `84–87`.
- Only the view file path and month are sent over the protocol: `118–120`.
- Scoring receives decision-time columns rather than approval/outcome columns: `131–134`.

Thus `truth`, `good_decision`, `binding`, `harmful_if_approved`, and `harm_oracle` are not directly passed through the constructed view. A copy is made, so ordinary dataframe aliasing cannot expose the full parent dataframe.

The process is launched separately with `python -I`, a temporary working directory, and a restricted environment (`111–115`). The simulator instance imported by the candidate (`m_bonf.py:19`) is not the parent’s in-memory module.

**This closes the old ordinary monkeypatch/caller-frame route into parent scoring.**

### What remains unverified or exposed

1. **Outcome timing depends on missing code.**  
   The harness delegates eligibility to `C.outcome_rows` (`84`). Without that implementation and the handcrafted test, I cannot certify “approved, decided before m, term ended before m.” The masking logic is correct *conditional on that eligibility function being correct*.

2. **`outcome_known_month` is exposed before the outcome is known.**  
   It is in `VIEW_COLS` (`41`). This is acceptable if it is a contractual schedule derivable at decision time. It leaks future information if it is the realized reporting/closure date. The generator must establish which.

3. **The child still imports simulator source.**  
   That can expose planted rules, defaults, generator code, and public seeds. Separate memory prevents inheritance of the active parent world; it does not make simulator knowledge unavailable. The current candidate does not visibly read planted rules, but the full import/global behavior cannot be audited without the missing files.

4. **The execution environment is not security-isolated.**  
   `python -I` is not a filesystem, network, or OS-process sandbox (`114–115`). A malicious candidate may read repository files, caches, redirected output, or modify shared files if permissions allow. Fresh random seeds reduce advance tuning; they do not by themselves enforce seed secrecy.

5. **Point-in-time validity of all deal fields is assumed.**  
   The view filters rows by month, but contains no visible versioned/as-of reconstruction (`82–88`). That can be perfectly valid for an immutable simulator, but does not establish safety against backfilled real-firm attributes.

**Verdict:** good isolation against accidental in-process leakage; incomplete enforcement against an adversarial method. The opening promise that the method “never sees … the seed, the world” is too categorical (`harness.py:4–7`). Prefer: **“The harness does not pass them through the method protocol.”**

---

## 3. Gate loopholes: constrained rules really are enforced, subject to trusted execution

The parent validates:

- At most 15 holdings (`harness.py:65–66`);
- One to four literals per holding (`72`);
- A restricted grammar over nine deal fields (`39–44`, `73–74`);
- Finite, bounded caps (`75–76`);
- At most 45 literals overall (`77–78`);
- A reconstructed plain-data law, with parent-generated identifiers (`77`).

Scoring uses the parent’s `C.apply` (`133`). There is no path in the shown grammar to submit Python, an arbitrary model object, an AST, or an outcome-reading predicate.

### Can many tiny rules smuggle a case-level model?

They can construct a **small rule-based classifier**. That is the stated representation, not a loophole.

Fifteen rules and 45 literals cannot encode an unrestricted case-level model, although narrow numeric intervals can still memorize a few small populations. The gates enforce syntactic size, **not**:

- minimum out-of-sample support;
- meaningful coverage;
- stability;
- nonredundancy;
- human comprehensibility.

Also, “four conditions” should always mean **four feature literals plus the discount/cap comparison**, not four atomic predicates total.

### What about `generic_literals` monkeypatching?

The supplied final candidate does **not** monkeypatch it. It calls `C.generic_literals` and adds thresholds locally (`m_bonf.py:25–31`), then uses a copied miner that accepts literals explicitly (`34–36`).

Therefore:

- Historical in-process monkeypatching was a genuine hole.
- The shown implementation fixes it.
- Child-local monkeypatching would not ordinarily change parent scoring, but would still violate the current stated editing policy.
- I cannot certify the unsupplied current `method.py` has no patch.

### Remaining engineering problems

- **Timeout enforcement is incomplete.** `select` waits for readable bytes, then `readline()` can block indefinitely if the child writes a partial line without a newline (`harness.py:121–123`). A “sleep forever without output” test does not cover this.
- **The resource limit is per month, not visibly a fixed total compute budget.** There are no shown memory, output-size, or child-process limits.
- **End-to-end AST handling depends on the missing runner.** The parent reconstructs safe fields, which is protective, but the documented explicit rejection route relies on `other_keys` (`69`).
- Invalid runs may write partial baseline caches before the violation is handled (`227–232`). That is a latent comparability defect, even if it did not affect these runs.

**Verdict:** the rule-form gate is credible. The surrounding execution environment is not yet adversarially robust.

---

## 4. Metric and baselines: a valid benchmark score, not “the best black box”

### What the score actually measures

For each configuration, the code calculates:

\[
100\left(\text{CCL agreement}-\max_{b\in B}\text{baseline agreement}_b\right),
\]

then averages over configurations (`harness.py:155–164`).

This is coherent as a benchmark against a **retrospective upper envelope of five fixed methods**. It is not comparison with one deployable baseline-selection procedure.

The maximum uses evaluation-oracle accuracy. That makes the comparator deliberately demanding and can introduce finite-sample winner’s-curse effects. This is not concealed cheating because the estimand is disclosed; it just needs its precise name.

### Are baselines fair?

The visible setup is substantially fairer than the original:

- Approval learners use the previous 12 months (`91–94`).
- Outcome-aware baselines use `C.outcome_rows` (`95–99`).
- Five methods are fixed, including a compact tree (`93–104`).
- They execute in the parent worker, not the candidate’s process.

But “fair and fixed” does not mean “competitively optimized”:

- Default GBM settings are not a serious tuned-baseline search.
- The T-learner may extrapolate between poorly overlapping populations.
- A 15-leaf tree is compact, but not representation-matched to a 15-holding, 45-literal law.
- The construction of `X` is missing, so full feature parity cannot be verified.

### Twelve configurations is historical

Current dev is **16 configurations**, not 12 (`harness.py:48–49`). The extra four were added after seeing a failure mode. That is reasonable benchmark development, but it starts a new exploratory evaluation epoch—not a clean continuation of the old metric.

### What did +0.110 dev / −0.071 holdout support?

Only:

> A repeatedly optimized method slightly exceeded the retrospective comparator on the development panel and slightly underperformed it on the then-holdout panel.

It did not establish equivalence, non-inferiority, real-firm transfer, or robust simulator-family generalization. New seeds test sampling variation; one alternative planted-rule world gives limited structural variation. Repeatedly inspected holdouts become monitors.

### Agreement is still not policy value

The score rewards agreement with a threshold-defined synthetic oracle. It does not price:

- harmful approvals versus valid rejections;
- revenue or retention;
- subgroup effects;
- governance benefits;
- performance under policy-induced changes in observed outcomes.

These limitations should remain central, not footnotes.

---

## 5. Confirmatory inference: the primary calculation is right

The important code is `confirm_summary`, not the first displayed `score_pts` interval.

It:

1. Computes a decision-weighted accuracy within each configuration (`harness.py:184`);
2. Subtracts that configuration’s retrospective best baseline (`185`);
3. Averages the two configuration gaps within each world (`186`);
4. Uses a Student t interval over worlds (`187–190`);
5. Passes only if the lower bound exceeds the registered margin (`191–192`).

**This matches the registered primary analysis.** With 24 complete worlds, the degrees of freedom are 23. Pairing the exception and segment configurations within each world addresses the main pseudoreplication problem from round 2.

The reported outcomes are unambiguous:

| Test | World-level mean gap | 95% CI | NI result |
|---|---:|---:|---|
| 1 | −0.373 points | [−0.603, −0.142] | FAIL |
| 2 | −0.374 points | [−0.591, −0.157] | FAIL |

### Three qualifications matter

**First: both intervals exclude zero, but both contain −0.25.**

Therefore the evidence supports a negative mean gap against this comparator. It does **not** establish that the true deficit exceeds the non-inferiority margin. Failure to establish non-inferiority is not proof of inferiority beyond that margin.

**Second: the two tests evaluated different methods on different worlds.**

“False rejections fell” and “harm caught fell” are between-run descriptive differences, not measured Bonferroni treatment effects. You correctly call the diagnosis descriptive; apply that caution consistently to the metric comparisons too.

**Third: two looks were disclosed, not formally controlled.**

A statement that a pass would be “read with multiplicity in mind” is not a prespecified error-control procedure. Both failed, so this does not manufacture a success here. Future lines need an actual alpha allocation or a single final confirmation.

### Harden the inference implementation

`confirm_summary` does not assert:

- exactly the registered number of worlds;
- exactly one exception and one segment configuration per world;
- complete months and finite values;
- absence of duplicated configurations.

The construction currently supplies the intended design (`209–212`), but the analysis should validate it independently.

Also, suppress or clearly label the **configuration-level CI** on confirmatory runs. `summarize` prints one before the correct world-level interval (`233–234`), using an approximate critical-value table (`160–164`). Two prominent “95% CIs” for one result invite misuse.

---

## 6. Detector experiment: useful falsification, overconfident mechanism language

The analysis script implements the registered operational criteria:

- No-harm and strong-harm subsets: `detector_analysis.py:9–10`;
- H1 attribution share: `26–29`, `35`;
- H2 reduction and power condition: `36–37`;
- H3 net score comparison: `38`;
- Mechanical candidate selection: `43–45`.

The reported arithmetic checks out:

- \(2071/2763 \approx 75.0\%\);
- \(1-2071/2079 \approx 0.385\%\), nowhere near 30%;
- −0.020 exceeds −1.584;
- two-literal wins the tie-break on slightly fewer rules.

**H1 supported, H2 failed, H3 supported—on this panel and under these operational definitions.**

### But H2 did not falsify every joint-confounding diagnosis

It falsified the registered prediction that **this specific two-literal implementation** would reduce attributable false rejections by at least 30% without losing specified power.

That implementation considers a limited family of categorical/positive-boolean pairs (`m_bonf.py:65–70`), skips certain overlaps (`78`), and skips underpowered cells (`82`).

Failure of that remedy is not a general disproof that joint confounding contributed. Likewise, thin-tail examples plus a successful stronger cutoff are evidence consistent with multiplicity—not complete identification of the failure mechanism.

### Attribution is useful but narrower than “caused”

The harness removes overrules from the **already constructed final law**, then counts changed decisions (`harness.py:135–139`).

However, construction can already have removed loosening precedents because of those overrules (`m_bonf.py:118–120`). Deleting the overrules afterward does not restore those precedents.

Thus the attribution measures:

> Direct decision changes from deleting designated overrules from the final retained law.

It does not necessarily measure the total effect of running the whole pipeline with versus without overruling. The separate no-overrule candidate is the better pipeline-level intervention.

---

## 7. The harm detector remains a heuristic, including after Bonferroni

### The underlying idea is sensible

Comparing above-policy and in-policy approved deals within a population is better than comparing an exception population to a global renewal average. Refinement checks can reject obvious observed compositional differences.

That is a useful **observational screening heuristic**. It is not causal identification.

### The actual statistical test is weaker than the verbal description

The method requires:

- at least 40 observations per arm (`m_bonf.py:101–103`);
- observed renewal difference at least 0.20 (`104–105`);
- a pooled-proportion z-test against **zero difference** (`106`);
- no adequately populated refinement that significantly contradicts a 0.20 drop (`73–85`).

It does **not** establish with confidence that the true drop exceeds 0.20.

“Every refinement shows harm” is especially inaccurate:

- small cells do not object;
- nonsignificant evidence is treated as permission;
- only an enumerated refinement family is examined;
- selection and refinement use the same observations.

### Bonferroni: useful engineering change, incomplete statistical repair

The adjustment uses \(0.05/\text{number of populations}\) (`95–96`). Dependence among tests does not itself invalidate Bonferroni. The deeper limitations are:

1. **Wrong null for the harm threshold:** correction addresses evidence against zero, not evidence that harm exceeds 0.20.
2. **Adaptive repeat searches:** up to three rounds follow data-dependent population exclusions (`98–110`).
3. **Repeated months:** no visible across-month error allocation.
4. **Approximate tail probabilities:** small-cell pooled z-tests at roughly −4.4 need calibration.
5. **Unobserved confounding and selection:** adjusting search multiplicity cannot make approved-deal comparisons causal.
6. **Limited overlap:** the two arms may not contain genuinely comparable customers.

The experiment supports “this stricter cutoff reduced a measured class of detector-panel false positives.” It does not support “Bonferroni solved false overruling.”

### Segment versus exception worlds

Segment-only worlds are valuable negative controls: poor renewal need not imply discount-related harm. But broad segment populations can still contain different mixes of customer quality across approval arms. Refinements only partly address that.

Exception worlds are positive controls, but power depends on cell size, overlap, harm magnitude, and whether the candidate language can express the affected population.

---

## 8. Goodharting: the record now exposes it rather than hiding it

Several retained changes were demonstrably simulator-adaptive:

| Change | Assessment |
|---|---|
| Every integer threshold for tenure/term | Generalizable search technique, but its retained value was discovered against planted rules (`m_bonf.py:25–31`) |
| Minimum support 30 | Selected to recover rarer exceptions; not a generally justified reliability threshold (`21`) |
| Beam width 60 | Search-budget choice tuned to recover an interaction branch (`21`, `55`) |
| Full-drop refinement requirement | Clear Goodhart episode: favorable strong-harm dev score concealed near-threshold sensitivity loss |
| Statistical refinement check | Principled motivation, but still an adaptive response to inspected stress failures (`73–85`) |
| Removing moot court | Useful ablation; does not prove replay admission is generally useless |
| Bonferroni cutoff | Plausibly transferable statistical discipline; not yet a calibrated sequential procedure |

What plausibly transfers is the **architecture and disciplined testing**, not these parameter values: compact executable rules, isolated scoring, outcome eligibility, negative controls, ablation, explicit error attribution, and keeping failures.

The latest “miner misses generated thresholds” diagnosis is plausible, but still a hypothesis. Segment worlds losing with no overrules establishes that overrules cannot explain the entire deficit. It does not isolate threshold-grid resolution from precision gates, caps, support, search, rule budgets, or label noise.

---

## 9. AR-018 and the README: mostly right, but narrow three claims

### AR-018 claim 1: roughly 0.37-point deficit

**Supported for the two evaluated locked candidates and the registered generated-world distribution, against the retrospective five-baseline comparator.**

Replace “the best CCL found by the loop” with **“the two selected locked CCL candidates.”** Development/detector selection does not establish which candidate is truly best on the confirmatory distribution.

Also avoid wording that implies loss to every baseline individually.

### AR-018 claim 2: overrules catch harm and search adjustment removes false alarms

**Only partly supported as written.**

The 100% versus 0% detector ablation result is supported for the specified strong-harm cases. “Make CCL catch causal harm at all” is too universal: other configurations can reject harmful cases without an explicit overrule.

The search-adjustment result must be restricted to the diagnostic detector panel. Confirm_2 still shows nonzero overrule counts in multiple segment-only worlds. Those counts alone do not prove harmful decision changes, but they certainly do not establish universal disappearance of false alarms.

Use:

> On the inspected detector panel, search adjustment eliminated measured overrule-attributable false rejections outside the unobserved-confounding configurations.

“All outcome-aware methods tested” also needs an explicit panel-specific scope.

### AR-018 claim 3: the loop is the durable contribution

**Reasonable as an engineering/research contribution.** Not evidence that this loop outperforms manual research or alternative optimization procedures. “Reusable evaluation and reporting infrastructure” is stronger and more defensible than an unmeasured general superiority claim.

### README generated claim

The numerical source is correct: `make_claims.py:67–71` parses **`confirm_world_gap`**, not the misleading configuration-level interval. It uses the detector result file for the ablation numbers (`73–80`).

But the generator parses `confirm_result` and then ignores it: **“Two … FAILED” and “measurably worse” are hard-coded** (`71`, `79–82`). Correct today; not safely generated logic.

Add assertions or derive the text from the results, bounds, manifests, and comparator definition.

Finally, the README still says **“Nothing here is a confirmatory test.”** That directly contradicts its new evidence block. Its opening replay-admission description also does not describe the autoresearch winner. These are small edits with large clarity benefits.

---

## 10. Next steps, ranked by value

**No more method tweaks under this stopped line.** The next work should be human-owned evaluation design.

1. **Complete the audit artifact and executable lock.**  
   Pin simulator/compiler/dependencies, record dirty-tree status and full source hashes, archive raw per-month outputs, and verify manifests against the run artifacts. Fix the partial-line timeout and invalid-run cache behavior.

2. **Run a paired mechanism decomposition—not another “fresh success” attempt.**  
   On common diagnostic worlds, compare frozen variants isolating:
   - numeric-threshold resolution;
   - support/precision/search constraints;
   - overrule behavior;
   - interactions between mining and overruling.  
   Predefine counterfactuals that restore struck precedents. Test the miner-recall explanation rather than promoting it immediately to fact.

3. **Calibrate the detector under the actual scientific null.**  
   Sweep effects densely around 0.20, including below-threshold effects; vary cell size, overlap, confounding, and months. Measure false-overrule rates and power for the full adaptive pipeline. Consider honest discovery/confirmation or sequential evidence with explicit error control.

4. **Redesign the comparator and target estimand.**  
   Keep the retrospective envelope as a stringent secondary benchmark. Add a baseline-selection strategy chosen using historical data only, tuned baselines, and a representation-matched interpretable competitor. Report per-baseline gaps and harm/rejection trade-offs.

5. **Broaden the human-frozen world family and deployment dynamics.**  
   Include rules outside the current grammar, continuous effects, missing and revised features, delayed/censored outcomes, drift, selective labels, and policy feedback. New random seeds within familiar templates are not enough.

6. **Test the claimed governance value.**  
   If compact rules justify accepting an accuracy cost, measure that benefit: review time, defect detection, edit reliability, stability, and controlled deployment. Inject untrusted proposals if replay admission remains a central claim.

A new confirmatory line should follow these diagnostic steps, with one prespecified candidate-selection procedure, a justified margin, a power calculation, and an explicit rule for multiple looks.

---

## What may honestly be claimed today

Corporate Case Law’s autoresearch loop produced compact executable rule systems and a useful observational overruling mechanism on planted-rule simulations. A pre-registered detector experiment found that overruling substantially improved strong-harm rejection but also generated most false rejections in its no-harm configurations; the proposed two-literal refinement did not deliver its registered improvement. Two subsequently registered evaluations of selected candidates on 24 newly generated worlds each failed to establish non-inferiority, with mean agreement deficits of about 0.37 percentage points against a retrospective best-of-five fixed-baseline comparator and world-level intervals entirely below zero. These results do not establish causal harm detection, real-firm transfer, or a governance advantage. The credible contribution today is the constrained-rule prototype, the increasingly disciplined evaluation infrastructure, and an honestly reported negative result—not parity with case-level models.