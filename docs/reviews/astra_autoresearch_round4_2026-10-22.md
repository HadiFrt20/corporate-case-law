# Astra (databricks-gpt-6-astra) review of the autoresearch loop

Raw model output, unedited.

## Verdict

**The third test genuinely passes its registered numerical criterion. It does not establish that CCL matches black boxes generally, that the diagnosed fixes caused the improvement, or that the loop now controls research-wide optional stopping.**

The strongest improvement since round 3 is substantive: the candidate was locked before a fresh evaluation, the scoring distribution was not silently changed for that evaluation, the world-level interval clears the margin comfortably, and the two failures remain prominent. Adding generated worlds to development is legitimate distribution matching—not automatically leakage.

But several claims have outrun the evidence again:

- “Diagnosed the cause … fixed it” is stronger than the experiment establishes.
- “Line 2 is its own family” is not a defensible multiplicity policy for indefinitely continuing the same research question.
- The manifest pins much more, but **not everything**, and the execution environment is not a security sandbox.
- The new threshold test has a predictable sensitivity problem at the oracle’s boundary.
- The reported **94.1% harm caught is a macro-average**, not the fraction of all harmful cases caught.
- The confirmatory law averages **6.08 rules**, not “about 8.”

**Grades: record/loop B+; narrow synthetic non-inferiority claim B; broad “readable laws close the black-box gap” claim C−.** I would retain the record’s B+, not upgrade it merely because a test turned green.

### Audit scope

This is a static review of the supplied material, not a reproduction. `runner.py`, `worlds.py`, `ccl_sim.py`, `rulec.py`, the tests, and the actual `method.py` are absent. I can inspect the locked `m_line2.py` and the harness, but cannot independently verify their hashes, the feature construction, outcome eligibility, or the runner’s serialization. References below use the supplied line numbers; README wording is traceable to its generator.

---

## 1. Is the pass genuine—or an artefact?

### The registered pass is real

The registered statistic is implemented correctly in its essential structure:

- Average the two configuration gaps **within each world**.
- Compute a t-interval across those world averages.
- Pass only if the lower bound exceeds the manifest margin.

That is `autoresearch/harness.py:196–211`, not the configuration-level interval. The latter is now explicitly marked as non-primary (`harness.py:181–182`).

The reported **+0.030 [−0.116, +0.175]** therefore passes **−0.25**. It does **not** establish superiority. Nor is this merely “failure to reject a difference”: it is a positive non-inferiority result against a specified margin.

### Sharing a generator family is not test leakage

Development now includes eight generated worlds (`harness.py:47–55`); confirmation draws new world identifiers, firm seeds, and harm sizes after checking the manifest (`harness.py:220–234`).

This is legitimate if the target claim is:

> Generalization to new draws from this particular planted-rule generator.

It is not evidence of generalization to new mechanisms. You have moved from a partially out-of-distribution challenge to an explicitly **within-generator-family** test. That is an appropriate repair of development coverage, but a narrower scientific achievement than learning principles that transfer beyond the simulator.

The confirmatory distribution itself appears unchanged in the registered description. That matters: you changed training/development exposure, not the stated examination after seeing its answers.

### The margin remains lenient, but is not the sole reason this passes

A −0.25-point allowance is one additional error per 400 decisions. Against approximately 0.1%–0.3% baseline error, that permits approximately **1.8×–3.5×** the baseline error. “Two to three times” in the manifest is a rough and slightly flattering summary.

Nevertheless, the observed lower bound is −0.116:

- Passes −0.25.
- Would pass −0.12 under the same nominal interval.
- Would **not** pass −0.10.
- Does not establish a nonnegative gap.

The −0.12 observation is post hoc sensitivity analysis, not a second registered success.

### Three looks: the sensitivity calculation helps; the stopping policy does not solve the problem

AR-020 bounds each inner loop and each line. It leaves the **number of research lines unbounded**. “New diagnosis + new registration” can still become “continue until success.”

Calling line 2 a separate family does not reset the evidential history of the same overarching question. Nor does renaming the line erase AR-018’s earlier commitment against a third tweaked confirmatory test in the session. The reopening was disclosed and hypothesis-motivated; it was still reopening.

The reported three-test Bonferroni lower bound, **−0.152**, is useful and numerically plausible from the displayed interval. It suggests this result is not a fragile three-look false positive. But:

- It is retrospective.
- It does not establish a policy for future lines.
- It does not include the two earlier fresh evaluations if the scope is “every opportunity to claim non-inferiority.”
- Exact verification requires unrounded world-level results.

Also, a lower-bound decision using a **two-sided 95% interval** is effectively a one-sided 2.5% test, not a conventional one-sided 5% test. The manifest’s “alpha 0.05” wording should distinguish these.

**Bottom line:** accept the pass as qualified evidence. Reject the claim that AR-020 now makes indefinite claim-seeking statistically safe.

---

## 2. Leakage and the trust boundary

### What the visible code gets right

| Protection | Evidence | Assessment |
|---|---|---|
| Only historical rows | `harness.py:88–94` | Explicit `month < m`. |
| Allowlisted columns | `harness.py:39–42,91` | Stronger than merely dropping known hidden columns. |
| Unknown renewals masked | `harness.py:90–93` | Values become false; eligibility is separately marked. |
| Separate method process | `harness.py:129–138` | Removes ordinary access to harness frames and simulator globals. |
| Decision-time input restriction | `harness.py:149–150` | The rule engine receives only decision columns, plus `Xt`. |
| Locked method uses outcome eligibility | `m_line2.py:115,125` | Masked false outcomes are not treated as observed failures. |

There is **no visible oracle-column or future-row leak in the locked candidate**.

### What cannot be certified from this packet

1. **Outcome timing.**  
   Both masking and baseline training rely on `C.outcome_rows` (`harness.py:90,101`). Its implementation is absent. I cannot independently verify “approved, decision before m, term ended before m.”

2. **`outcome_known_month`.**  
   This column passes through even for not-yet-known outcomes (`harness.py:41,91`). That is harmless if it is a contractual maturity date knowable in advance. It is leakage if it encodes a realized future reporting delay, early termination, or other outcome-dependent event.

3. **Features and metadata.**  
   `WD.firm` constructs `X` (`harness.py:127`), and the absent runner constructs or supplies the candidate’s `X`. DataFrame indices and metadata are not explicitly sanitized by the visible view builder. Audit these as well as columns.

4. **Simulator globals.**  
   Importing `ccl_sim` in the child does not inherit the parent’s runtime world state under this subprocess arrangement. But the simulator’s source and default globals remain accessible. Whether those defaults expose planted knowledge requires the missing file.

### Isolation is not a sandbox

The subprocess has ordinary filesystem access under the invoking user (`harness.py:129–133`). `python -I` is Python import/environment isolation, not an OS security boundary.

A malicious method could potentially read published seeds, logs, caches, or other artifacts, or write files that the harness later consumes. Two concrete concerns:

- Confirmation loads an existing baseline cache if one happens to exist, even though it does not write confirm caches (`harness.py:242–252`).
- The manifest is read again for the final decision (`harness.py:256`), instead of using the already-validated in-memory object.

That second point is an avoidable integrity hole: a writable manifest could have its margin changed between validation and reporting.

**Finding:** good accidental-leakage protection; incomplete protection against an adversarial agent. There is no evidence the submitted candidate exploits these routes.

---

## 3. Gate loopholes and monkeypatching

### The alleged monkeypatch is obsolete in the supplied candidate

`m_line2.py:28` **calls** `C.generic_literals`; it does not replace it. The miner is copied locally and accepts literals explicitly (`m_line2.py:58–60`). AR-010 describes exactly this correction.

Do not keep reviewing the v1 monkeypatch as if it were present in the locked method.

Even if a method patched `apply` or `fires` in its own process, that would not directly alter the harness’s in-memory functions. Scoring happens in the parent worker using its own `C.apply` (`harness.py:147–150`). Patching shared files would be a different, filesystem-level attack.

### Can the law smuggle a case-level model?

The visible validation is meaningful:

- At most 15 rules.
- One to four literals per rule.
- At most 45 literals overall.
- Restricted fields and literal syntax.
- Finite caps in prescribed ranges.
- Output reconstructed into plain holdings.

See `harness.py:69–85`.

This prevents an arbitrary tree, AST, callable, or unrestricted predictor from being passed as the decision procedure. Fifteen tiny rules can overfit small regions, but they cannot encode an unlimited case-level lookup table under these restrictions.

However:

- These laws **are themselves case-level classifiers**. The defensible distinction is restricted, inspectable representation—not “no case-level model.”
- Form constraints do not guarantee interpretability, adequate support, stability, or coherent interactions.
- Caps have no precision restriction, though the finite fixed evaluator limits their practical use as an encoding channel.
- The literal regex uses `$` with `match`; use `fullmatch` for an exact grammar (`harness.py:43–44,80`).
- The final execution guarantee still depends on the absent `C.apply`, including whether it ever uses `Xt` for ordinary literal holdings.

The admission process should report unsupported rules and interacting or contradictory holdings even if those remain soft diagnostics rather than hard gates.

---

## 4. Metric and baselines: sound benchmark, misleading shorthand

### The metric is coherent

Within a configuration, decisions are weighted by monthly sample size; configurations are then weighted equally (`harness.py:172–178`). Confirmation weights worlds equally, with equal weight on exception and segment settings (`harness.py:201–206`).

That defines a legitimate synthetic estimand. It does not estimate value for an arbitrary real firm.

The stale “12 configurations” question is historical:

- Original: 12.
- v2.1: 16.
- Current development: **32** (`harness.py:53–55`).
- Confirmation: **24 worlds, 48 configurations**.

`program.md` still says 16 and calls zero “ties the best black box.” Update the executable research contract, not just the ADR.

### Retrospective best-of-five is not an unfair advantage for CCL

The comparator chooses the highest observed baseline agreement per configuration (`harness.py:173–174,203`). That makes it an oracle selector unavailable in deployment and tends to make CCL’s task harder, not easier.

But it is not “the best black box”:

- Two baselines are compact trees.
- All five are fixed configurations.
- The candidate receives repeated development optimization; the baselines do not.

The actual baselines are visible and fixed (`harness.py:97–110`): approval models use a 12-month window; outcome models use eligible observed outcomes. This is respectable information parity, subject to verifying `X` and `outcome_rows`. It is not equal tuning effort or representation parity. A 15-leaf tree is not automatically equivalent to 15 rules with at most four literals and 45 total.

### What +0.110 development / −0.071 holdout supported

At that historical checkpoint: a promising development improvement, followed by a small negative monitored generalization result. It did not establish non-inferiority, superiority, or transfer. Repeated checkpoint inspection also means that “holdout” subsequently became a monitor, correctly renamed in the record.

### Averages hide the important failure modes

From the rounded confirm_3 rows, the effect-specific gaps are approximately:

- **Exception:** +0.18 points.
- **Segment:** −0.11 points.

So the overall +0.030 is not uniform parity. Gains where fixed outcome baselines over-block offset losses elsewhere.

Moreover, the **94.1%** figure is the unweighted mean of per-configuration catch rates (`harness.py:175,179,186`). Two harm-bearing configurations catch only **44.0%** and **56.2%**. Report both:

- Macro-average catch across harm-bearing configurations.
- Pooled harmful cases caught / pooled harmful cases.
- Minimum and lower-tail catch.

Finally, false rejections and harmful approvals do not exhaust all errors. Some confirm_3 rows have substantial disagreement with little of either. Add **non-harmful but oracle-invalid approvals** as a separate error class.

---

## 5. Goodharting and the overrule detector

### Which changes plausibly transfer?

| Change | Judgment |
|---|---|
| Enumerating small-integer thresholds | Sensible general-purpose search; not inherently cheating because planted rules use integers. |
| Finer continuous quantiles | Plausible recall improvement, but selected after seeing generated-threshold failures. Valid within-family adaptation, not structural transfer evidence. |
| Support 30, beam 60 | Ordinary hyperparameter tuning. Neither number is a scientific discovery. |
| Error weight 2 | Plausible conservative mining bias, but tuned against this simulator’s accuracy metric—not a measured business error-cost ratio. |
| Removing replay admission | Supported for this mining pipeline; does not invalidate replay for untrusted proposals. |
| Refinement checks and search correction | Useful heuristics with clear failure modes; not causal identification. |
| Threshold z-cutoff −1 | A simulator-objective trade-off selected on development, not a validated safety threshold. |

Evidence: numeric-grid construction at `m_line2.py:25–35`; error-weighted gain at `38–46`; search settings at `21–22`; threshold test at `129–133`.

A firm being able to *state* a policy does not make its statistical justification sound. “Honesty criterion” is useful, but too permissive to prevent simulator-specific optimization.

### “Same population” does not mean comparable treatment groups

The detector compares observed approved deals above policy with observed approved deals inside policy (`m_line2.py:115–128`). It does not randomize discounting, establish exchangeability, or repair approval-selection bias.

It can fail through:

- Unobserved customer quality.
- Poor overlap between in-policy and above-policy deals.
- Confounding involving omitted or higher-order features.
- Calendar drift and outcome censoring.
- Selection into approval and into observed renewal.
- Genuine heterogeneous effects that the uniform-population test rejects.

Segment worlds are a useful negative control: low renewal alone should not imply exception-caused harm. Passing that control does not establish causality.

### “Every refinement” remains false

The implementation:

- Tests a finite literal dictionary and selected categorical/boolean pairs.
- Skips small cells (`m_line2.py:105–106`).
- Skips certain overlapping refinements (`101–102`).
- Accepts when no tested refinement significantly contradicts the threshold (`108–110`).

That is **absence of detected contradiction**, not proof that every refinement shows harm. The candidate docstring at `12–13` still overstates the procedure.

### Bonferroni is partial protection

`m_line2.py:120` adjusts the zero-effect z-cutoff by the number of candidate populations. This is useful, and dependence between populations does not itself invalidate Bonferroni.

But it does not establish end-to-end error control:

- Wald/normal approximations can be poor in small or extreme cells.
- Up to three sequential searches reuse adaptively modified data (`122–136`).
- Monthly searches reuse overlapping historical data.
- The adjusted test is against **zero**, whereas the oracle’s relevant boundary is **0.20**.
- The threshold-specific test is only z ≤ −1, without corresponding search adjustment.

Do not call the resulting law a statistically certified set of harmful populations.

### The new boundary-power problem is mathematical, not mysterious

The new condition is:

\[
(\widehat{p}_{above}-\widehat{p}_{inside}+0.20)/SE \le -1.
\]

That is `m_line2.py:131–133`.

For a fixed, well-behaved contrast whose true drop is exactly 0.20, the centered statistic is approximately standard normal. Its probability of passing this condition is approximately **15.9%**, before other restrictions—not 50%, and not something that tends to 100% merely by increasing sample size.

Adaptive population search and overlapping rules make whole-law catch rates different, but the basic boundary-power problem is unavoidable under this test.

Also, confirmation rounds renewal probabilities to two decimals (`harness.py:231`). Exact-boundary worlds therefore have nonzero sampling probability; they are not a measure-zero curiosity.

**The scientific decision needed:** should exactly 0.20 be treated as harmful with high sensitivity, or should intervention require evidence of an effect meaningfully larger than 0.20? The current oracle and detector encode different answers.

---

## 6. Manifest and generated README audit

### Manifest: substantially better, not complete

The harness checks:

- Candidate SHA-256.
- Aggregate harness hash covering `harness.py`, `worlds.py`, and `runner.py`.
- Simulator `CODE_SHA`.
- Compiler SHA-256.

Evidence: `harness.py:65–66,221–227`.

Important qualifications:

1. Simulator and compiler checks are **optional if their keys are absent**. Require them in a versioned confirmatory schema.
2. The simulator hash’s coverage cannot be verified without its definition.
3. Python, NumPy, SciPy, pandas, scikit-learn, and numerical/runtime dependencies are not pinned.
4. Transitive candidate dependencies are not comprehensively enumerated.
5. Baseline cache contents are not authenticated.
6. Registration chronology is supported by the supplied commit order, but the harness does not enforce one run or registration-before-run.
7. The final manifest reread is unnecessary and unsafe.
8. Full-precision raw outputs are not shown here; the text summaries are insufficient for exact independent statistical reconstruction.

The robust reader does fix the partial-line blocking problem (`harness.py:113–122`). It still lacks an output-size bound, uses wall-clock rather than monotonic time, and `proc.kill()` does not itself manage descendant processes or reap the child (`163–164`). These are remaining operational issues, not reasons to invalidate this particular result.

### README: the numbers are generated; the causal story is hand-written

Good:

- The generator reads the **world-level** result (`make_claims.py:67–71`).
- It asserts consistency between the printed result and the margin (`73`).
- It preserves both failures and correctly distinguishes non-inferiority from superiority (`82–90`).

Problems:

**1. Unsupported causal diagnosis.**  
“Diagnosed the cause … fixed it” is hard-coded at `make_claims.py:87–88`. Three changes were selected, the development panel changed, and confirmation used different worlds. That does not isolate causes.

Replace with:

> “Targeted hypothesized mining-recall and overrule-selection failures, improved on the revised development panel, and passed a fresh same-family evaluation.”

**2. The assertion uses rounded output and a hard-coded margin.**  
`make_claims.py:69–73` should consume full-precision machine-readable results and their registered manifest, not reconstruct the decision from three-decimal text.

**3. Attribution needs a scope qualifier.**  
The 75% figure refers to the frozen detector candidate and deletion-based attribution, not an identified causal contribution of overrules in the current method (`make_claims.py:81–82`; `harness.py:152–156`).

**4. “About 8 rules” is not the confirmatory result.**  
AR-023 should say **6.08 mean rules on confirm_3**, or explicitly identify another panel.

**5. Current-method description is muddled.**  
The README opens with replay admission, then retracts it for the tested methods. Lead with the method actually evaluated.

Generated prose is valuable protection against transcription errors. It is not protection against unsupported interpretation.

---

## 7. What should come next—ranked

### 1. Paired factorial diagnosis on an explicitly diagnostic panel

Run the old locked candidate and all combinations of:

- Fine numeric grid.
- Error weighting.
- Threshold-aware overrules.

Use identical worlds and firms. Decompose mining errors, false overrules, missed harm, and other invalid approvals.

This directly tests “diagnosed and fixed,” currently the largest unsupported claim. Existing confirm worlds may be used **as diagnostic data**, openly relabeled; do not count that reuse as new confirmation.

### 2. Freeze the research-wide claim protocol

Before another claim-bearing run:

- Define the research family and total testing budget or alpha-spending rule.
- Log human interruption as the reason when stopping before budget/plateau.
- Require mandatory manifest fields and an immutable validated manifest object.
- Freeze the environment, disable confirm-cache reuse, and save full-precision results and law traces.
- Separate research registration from evaluator access.

AR-020 is useful project management, not yet a complete inferential stopping policy.

### 3. Run a boundary-and-selection benchmark

Predefine dense effects around 0.20, null worlds, small cells, rare populations, delayed outcomes, and drift. Report false-overrule probability per month and per simulated firm, detection delay, subgroup catch, and both macro/pooled harm metrics.

Do not “fix” this by putting more boundary worlds in dev alone. First decide what the threshold means operationally.

### 4. Give baselines comparable tuning and representation access

Tune competing baselines on development only, with comparable search budgets. Include a policy-aware residual model and a compact rule learner under genuinely comparable complexity limits.

Retain retrospective best-of-five as a secondary benchmark; add a deployable comparator selected without test outcomes.

### 5. Test genuinely new mechanisms

Freeze external generator families: smooth rather than rule-planted effects, higher-order interactions, measurement error, missingness, policy-dependent observation, unobserved confounding, and behavioral feedback.

That is the next meaningful simulator transfer test—not another batch from the same template family.

### 6. Real longitudinal and governance evaluation

Move to a shadow evaluation with genuinely point-in-time features and outcomes. Separately measure whether compact laws improve auditability, correction speed, consistency, and controlled change compared with an explained black box.

Predictive parity cannot stand in for a governance advantage.

---

## Grades and honest claim today

| Item | Grade | Reason |
|---|---:|---|
| Research record and loop | **B+** | Strong disclosure, real boundary improvements, locked fresh evaluation; incomplete global stopping and provenance control. |
| Narrow synthetic non-inferiority claim | **B** | Supported by the registered statistic, conditional on implementation and sampling assumptions; narrow family and lenient margin. |
| “The fixes explain the improvement” | **C−** | Plausible and development-supported, but not isolated by paired experiments. |
| General black-box parity or real-firm transfer | **D** | Not established. |
| Causal harm detection or governance superiority | **F as affirmative claims** | The project appropriately disclaims them. |

**What may honestly be claimed today:** A locked CCL candidate producing a mean of 6.08 executable rules passed a pre-registered non-inferiority evaluation on 24 newly generated worlds from the same planted-rule family now represented in development. Its mean agreement difference from the retrospectively selected best of five fixed baselines was +0.030 percentage points, with a world-level 95% t-interval of [−0.116, +0.175], clearing the registered −0.25-point margin but not establishing superiority. Two earlier locked candidates failed their confirmatory tests. The current candidate achieved 94.1% macro-average harm catch across harm-bearing configurations, with substantial failures in some near-threshold worlds. These results support compact-rule competitiveness within this synthetic benchmark—not causal identification, the proven diagnosis of earlier failures, parity with tuned black boxes generally, real-firm transfer, or a measured governance advantage.