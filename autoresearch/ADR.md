# Architecture decision records: CCL autoresearch

Project-scoped ADRs for the autoresearch loop (the CCL project's own ADRs stay in `docs/ADR.md`; ADR-043 there
points here). Numbered AR-NNN. Later records supersede earlier ones where noted.

## AR-001 · Adopt karpathy/autoresearch's structure (2026-10-22)

**Context.** CCL v5.1 lost to case-level black boxes once every method saw the same outcome information. Progress so
far came from one agent editing many files, with metrics redefined along the way (see `WORKLOG.md` of the parent
project), which made it hard to tell research progress from moving goalposts.

**Decision.** Same shape as karpathy/autoresearch: one frozen harness (`harness.py`, like `prepare.py`), one file the
agent edits (`method.py`, like `train.py`), instructions for the agent in `program.md`, one scalar metric, a fixed
budget per run, keep or discard by git commit, results in an untracked `results.tsv`. The human edits `program.md` and
the harness; the agent edits only `method.py`.

**Consequences.** Every result is comparable across the run because the harness and its code hash are fixed;
baselines are cached per harness and simulator hash. About 20 s per experiment on 14 cores.

**Status.** Accepted.

## AR-002 · What the method may see, and how it may decide (2026-10-22)

**Context.** The v5 review loop found an information gap (baselines saw no outcomes) and leaks are the easiest way
to fake progress in this setup.

**Decision.** The method receives a view of rows with month < m only; the ground-truth columns (`truth`,
`good_decision`, `binding`, `harmful_if_approved`, `harm_oracle`) are dropped; `renewed` is masked to the rows in
`ccl_sim.outcome_rows` (approved, decided before m, term ended before m) and an `outcome_known` flag is added. The
method is never told the world, the rogue effect or the seed. It returns a law; the harness decides with the frozen
`ccl_sim.apply`. Form gates: at most 15 holdings, at most 4 conditions each, valid literals or a compiled AST,
numeric caps. Violations make the whole run invalid.

**Consequences.** No model can act at decision time; the only way to score is with readable rules. Known open
question for review: `method.py` may monkeypatch `ccl_sim` functions (it replaces `generic_literals`); the harness
re-sets world globals after each call but does not restore patched functions.

**Status.** Accepted; monkeypatch policy under review (see AR-007).

## AR-003 · Metric: CCL minus the best case-level black box (2026-10-22)

**Decision.** `score_pts` = mean over the 12 dev configurations (easy, hard) x (exception, segment) x seeds (7, 11, 23)
of (CCL agreement with the harm-aware oracle minus the best of GBM, GBM + renewal veto, GBM + T-learner), in points.
The baselines use the same outcome rows and are computed by the harness, not by the agent. Also reported:
worst gap, harmful approvals, false rejections, mean rule count. Simplicity criterion: fewer rules and less code win
ties; honesty criterion: every change must be a policy a firm could state.

**Consequences.** 0 means CCL ties the best black box. Agreement with a threshold oracle is not policy value.

**Status.** Accepted.

## AR-004 · Holdout policy (2026-10-22)

**Decision.** Holdout = unseen seeds (101, 202) for the two dev worlds plus an unseen "alt" world (different hidden rules,
a different stricter rule, a rogue approver in another segment), both rogue effects. Run only every 5 kept commits and
at the end; never used to keep or discard; error analysis only on dev configurations.

**Status.** Accepted.

## AR-005 · Overruling precedents (2026-10-22)

**Context.** Baseline error analysis: in the exception world, harm leaked through overlapping rules that pass a
rule-level outcome screen (1.6% to 1.9% harmful approvals).

**Decision.** A stricter-law holding (REJECT above policy) for a population of one or two literals whose above-policy
approvals renew at least 0.20 worse than the same population's in-policy approvals (z <= -3, at least 40 known outcomes
each side), only if the contrast also holds (at least half the drop) in every refinement of the population by any
other literal, with at least 20 known outcomes per side. At most 3 per month, greedy by z.

**Consequences.** The naive version (no refinement check) over-blocked through Simpson confounding (dev -4.4). With the
check: harmful approvals 0% everywhere, hard/exception -3.1 to -1.3. In the segment world (the segment renews badly
either way) the contrast is near zero and no overrule fires. This is a rule-form, exact-refinement T-learner, not
causal identification.

**Status.** Accepted.

## AR-006 · Remove the rule-level outcome screen; strike overruled precedents (2026-10-22)

**Decision.** With overrules in place the v5 association screen is dropped (simpler, and better: -0.092 to -0.024). A
loosening holding whose above-policy cases all fall inside an overrule is removed (same decisions, -0.5 rules).

**Status.** Accepted.

## AR-007 · Open: monkeypatching the frozen simulator from method.py (2026-10-22)

**Context.** `method.py` replaces `ccl_sim.generic_literals` so the frozen miners see more candidate thresholds. It only
widens the candidate set (every rule still goes through the frozen `literal` / `fires` / `apply`), but the same
mechanism could replace `apply` itself in the worker process, which the gates would not catch.

**Decision pending** the Astra review: either forbid monkeypatching in `program.md` and have the harness verify that
`ccl_sim`'s callables are unchanged after each `build_law`, or copy the miner into `method.py`.

**Status.** Superseded by AR-009/AR-010 (monkeypatching removed; the method now runs in its own process).

## AR-008 · No moot court for mined rules; replay admission kept for untrusted proposals only (2026-10-22)

**Context.** Experiment 14 (an ablation) removed the replay admission step: mine on the full 12-month window and admit
every rule the miner returns (the miner already requires 90% precision and 30 cases). Dev -> +0.181 (every config
positive), holdout -0.071 -> +0.050.

**Decision.** Keep the ablation in the method. Record plainly that, in this simulator, the moot court cost accuracy for
mined rules: splitting 12 months into 8 for mining and 4 for replay starved rare rules of data. The moot court's other
role, keeping untrusted proposals (LLM-written rules, human edits) out of the law, is not exercised by this harness.

**Consequences.** CCL's "replay as the admission test" claim must be narrowed to untrusted proposals until a harness
test shows otherwise. Proposed harness change (human-owned): inject plausible-but-wrong candidate rules each month and
score whether the law admits them; that would let replay prove or lose its value inside the loop.

**Status.** Accepted (exploratory); supersedes the admission-window decisions of experiments 4 and 12 for mined rules.

## AR-009 · Harness v2: an enforced trust boundary (2026-10-22, after Astra review round 1)

**Context.** Astra (round 1, grade C+) showed the v1 boundary was procedural: the method ran in the harness process
(caller frames held the firm, seed and oracle), could monkeypatch `apply` / `outcome_rows`, the scorer passed
`approved` / `renewed` to the rule engine, AST holdings escaped the size gate, literals were not restricted to
decision fields, and baselines could be computed after the method had mutated the simulator.

**Decision.**
- The method runs in `runner.py`, a separate `python -I` process; for each month it receives a pickled view of
  `VIEW_COLS` only and returns plain JSON. Its mutations of `ccl_sim` stay in its own process.
- `validate()` accepts only `{kind, lits, cap}` holdings; literals must match a strict grammar over the nine deal fields
  (no approved, renewed, statute, month, disc or outcome literals); at most 15 holdings, 4 literals each, 45 overall;
  finite caps in range (loosen 15 to 60, tighten 0 to 15). No AST, no trees.
- Decisions are made by the harness's own `ccl_sim.apply` on decision-time columns only.
- Baselines are computed in workers that never import the method; added a compact-rule baseline (15-leaf tree) and
  that tree plus the renewal veto.
- Reported: 95% t-interval over configurations (optimistic: seeds are shared across worlds), false rejections, share of
  harmful cases caught, overrule count, literal count; a prespecified non-inferiority margin of -0.25 pts for the
  monitor and fresh panels.
- Panels: dev (decides), monitor (the former holdout; seen at checkpoints, so not a clean test), stress (harm-detector
  tests, never in the score), fresh (worlds generated from templates with a generator seed drawn at run time;
  run once per locked method).
- 27 adversarial tests (`tests/test_autoresearch.py`): forbidden fields, malformed laws, hidden columns, outcome
  masking, a method that monkeypatches `apply` (no effect on scoring), a method that searches caller frames and the
  garbage collector for the firm or oracle (finds nothing; a positive control in-process does find it), a law that
  reads outcomes (invalid), method crashes (reported).

**Consequences.** The v1 result reproduces under v2: dev +0.181 [+0.147, +0.214]. Still not a sandbox: the method can
read files on disk (the harness, the simulator) and could regenerate firms from published seeds; that remains
prohibited in `program.md` and is the reason the fresh panel draws its seeds at run time.

**Status.** Accepted.

## AR-010 · Method fixes from review round 1 (2026-10-22)

**Decision.** (1) The beam miner is copied into `method.py` and takes its candidate literals as an argument (no
monkeypatching). (2) A loosening precedent is struck only when an overrule's literals are a subset of its own
(logical implication: it can never decide differently), instead of containment on past rows. (3) Overrules are
chosen to fit the rule budget first, and precedents are struck only against the overrules actually kept. (4) In the
sequential overrule search both arms exclude rows already overruled (the v1 code excluded them from one arm only).

**Consequences.** Same dev score as before (+0.181): these were correctness fixes, not gains.

**Status.** Accepted.

## AR-011 · Stress findings: what the overrule detector can and cannot do (2026-10-22)

**Context.** Stress panel (harness v2): effect below the 0.20 threshold (renewal 0.85 vs 0.70), just above (0.85 vs 0.60),
and a non-causal confound (weak customers get bigger discounts and renew badly whether or not approved).

**Findings.** Below threshold: no overrule fires (correct); the veto and T-learner over-block (0.990 / 0.986 vs CCL
0.999). Just above: CCL catches 91.5% and 100% of harmful cases, +0.36 and +1.34 pts vs the best baseline. Confounded:
CCL is fooled (false rejections 2.4% to 2.6%, -2.2 to -2.4 pts vs plain GBM), but so is every outcome-aware method
(veto 0.913 to 0.919, T-learner 0.971 to 0.974, CCL 0.973 to 0.975); only methods that ignore outcomes are unaffected.

**Decision.** State the limitation plainly: overruling is an observational association rule with a refinement check;
it cannot detect confounding by unobserved customer quality. Do not claim causal harm detection.

**Status.** Accepted.

## AR-012 · A Goodhart caught at the checkpoint; statistical refinement test; dev panel v2.1 (2026-10-22)

**Context.** Experiment 16 required every one-literal refinement to show the full 0.20 drop. It improved dev (+0.181 to
+0.184) because every harmful dev world had a 0.50 drop. The stress checkpoint then showed it catching 38% of harmful
cases at a 0.25 drop (one config 0%, 6% harmful approvals). The metric rewarded a check that destroys sensitivity
near the threshold.

**Decision.** (1) Replace the point-estimate check with a statistical one: reject a population only if some refinement
shows significant evidence (z > 2) that its drop is smaller than the threshold. Justification is a priori (power in
small cells), not the stress number. (2) Fix the dev panel, a human-owned harness change: add hard-world exception
configs with renewal 0.60 and 0.70 (drops 0.25 and 0.15) on new seeds 31 and 47 (16 dev configs). (3) Widen the
unrun fresh panel with four generated worlds whose harm size is drawn at run time (drops 0.10 to 0.30). (4) Re-score
both candidates on dev v2.1: exp 16 +0.193 (worst -1.276, 93.8% caught), exp 19 +0.306 (worst -0.196, 100% caught).
Keep exp 19.

**Consequences.** Dev v2.1 scores are not comparable with v1/v2 rows. The stress panel has been looked at; its
near-threshold configs now duplicate dev in kind (on other seeds) and only its confounded configs remain informative
as a check. The fresh panel is the clean test.

**Status.** Accepted.

## AR-013 · Stop optimizing; pre-commit a falsification experiment, then one confirmatory test (2026-10-22)

**Context.** Two fresh draws failed non-inferiority (-0.419, -0.042). Astra round 2: the process is now honest about
failure, but the diagnosis (joint confounding behind the false rejections) is a hypothesis, and further fresh draws per
revised method would be optional stopping.

**Decision.** The optimization loop pauses. Next, in this order, all human-owned and frozen before any result is seen:
1. **Paired falsification experiment** on a new `--panel detector` (controlled worlds: causal exception harm,
   segment-only, joint segment x region confounding, unobserved confounding, small cells; harm drops 0.10, 0.15, 0.20,
   0.25, 0.30), comparing three frozen methods on identical firms: ar-locked-2, the same miner with no overrules, and
   the one-literal-refinement variant (ar-locked-1). Per overrule, log the population, its evidence, skipped
   refinements, decisions changed, harmful approvals prevented and valid approvals rejected. Question: do overrules
   cause the fresh false rejections, and does the two-literal check reduce them without losing power near 0.20?
2. **One confirmatory evaluation**, pre-registered in a manifest committed before the run: method hash, harness hash,
   simulator hash, number of generated worlds (at least 24, independent world clusters), harm-size distribution, the
   margin and its justification, inference by world cluster (not configuration), success criterion, and the rule that
   every draw is reported whatever it shows. No method change between the manifest and the run.

**Consequences.** No claim of non-inferiority until step 2 passes. Fresh runs 1 and 2 remain in the record as failures.

**Status.** Accepted.

## AR-014 · Pre-registered detector falsification experiment (2026-10-22, written BEFORE any run)

**Frozen.** Harness v3 (`--panel detector`, 33 configs on new seeds 501 to 503): hard-world causal exception harm at
drops 0.10, 0.15, 0.20, 0.25, 0.30 (renewal 0.75 to 0.55); segment-only worlds (hard, gen:900001, gen:900002);
unobserved confounding (hard, confounded); small cells (hard, 40,000 deals, both effects). Per month the harness
attributes decisions to overrules (approvals the law minus its overrules would grant but the law rejects). Three
frozen methods in `autoresearch/candidates/`: `m_twolit.py` (ar-locked-2), `m_onelit.py` (ar-locked-1), `m_noovr.py`
(ar-locked-2 with overrules switched off).

**Hypotheses and criteria.** "No-harm configs" = segment-only, confounded, and causal drops 0.10 / 0.15 (below the 0.20
threshold, so the oracle calls nothing harmful).
- H1 (cause): for `m_twolit` in no-harm configs, at least 50% of false rejections are attributable to overrules.
- H2 (fix): `m_twolit` vs `m_onelit`: overrule-attributable false rejections in no-harm configs fall by at least 30%,
  AND the share of harmful cases caught at drops 0.25 / 0.30 falls by at most 5 points.
- H3 (net value): `m_twolit` mean score over the whole detector panel exceeds `m_noovr`.

**Selection rule for the confirmatory test (AR-015).** The candidate with the highest detector-panel score_pts; if
within 0.02 of another, the one with fewer rules on average. Applied mechanically; no method edits after this record.

**Status.** Accepted (frozen before running).

### AR-014 result (2026-10-22, analysis script committed before results were read)

| | two-literal (ar-locked-2) | one-literal (ar-locked-1) | no overrules |
|---|---|---|---|
| detector score_pts | -0.020 | -0.020 | -1.584 |
| harm caught, drops 0.25 / 0.30 | 100% | 100% | 0% |
| no-harm false rejections (count) | 2,763 | 2,771 | 692 |
| of which caused by overrules | 2,071 (75.0%) | 2,079 (75.0%) | 0 |

- **H1 supported**: overrules cause 75% of the false rejections in no-harm worlds.
- **H2 NOT supported**: two-literal refinements cut overrule false rejections by 0.4% (target 30%). The joint-confounding
  diagnosis of the fresh failures is **falsified**. The false overrules sit on thin numeric tails that change month to
  month (`term > 2 AND tenure_y <= 0`, `size_k <= 28 AND tenure_y <= 1`, `size_k > 1000 AND ...`): a multiple-testing
  failure over ~1,800 candidate populations per month, as Astra round 2 predicted. In the confounded worlds the
  overrule hits a plausible segment x region cell, as designed: not detectable from these data.
- **H3 supported**: overrules are worth their errors on this panel (-0.020 vs -1.584).
- At exactly the threshold (drop 0.20) only 17% to 59% of harmful cases are caught: about coin-flip power at a cutoff.
- **Selection** (pre-registered rule): two-literal (tied within 0.02 with one-literal, fewer rules) -> `m_twolit.py`.
- Infrastructure bug on the first attempt: the harness passed the candidate path relative to the repo while the runner
  starts in a temp dir; every config died at month 36 with no result. Fixed (absolute path, regression test) and re-run.

## AR-015 · Confirmatory test 1, pre-registered (2026-10-22, committed BEFORE the run)

**Decision.** Manifest `autoresearch/manifests/confirm_1.json`: method `candidates/m_twolit.py` (hash pinned, selected by
the AR-014 rule), harness hash pinned, 24 generated worlds drawn at run time, each with an exception config (harm size
drawn per world, renewal 0.35 to 0.75: drops 0.10 to 0.50) and a segment config; per-world gap; two-sided 95% t-interval
over worlds; margin -0.25 pts with its (lenient) justification; PASS iff the lower bound exceeds the margin; one run,
reported whatever it shows.

**Status.** Accepted (frozen).

### AR-015 result: confirmatory test 1 FAILED (2026-10-22)

Draw k = 1068663073, 24 independent generated worlds, 48 configs, output verbatim in `autoresearch/CONFIRM_1.txt`.
**Per-world gap -0.373 pts [95% CI -0.603, -0.142]; 22 of 24 worlds negative; FAIL** (lower bound below -0.25). The whole
interval is below zero: on these synthetic worlds, the locked CCL is measurably worse than the best of five fixed
baselines (selected retrospectively per configuration), by about 0.37 points (about 1 extra error in 270 decisions).
Harm caught 91.0%, false rejections 0.49%. Consistent with AR-014: overrules on thin numeric tails over-block.

**Consequence.** The claim "CCL ties or beats case-level models" is refuted for this simulator family. What survives:
compact, auditable laws that catch most causal harm, at a measured accuracy cost.

## AR-016 · Search-adjusted overrules (Bonferroni) (2026-10-22)

**Context.** AR-014 located the false overrules on thin numeric tails: a multiple-testing failure. Confirmatory test 1
failed (AR-015).

**Decision.** Candidate `candidates/m_bonf.py` = `m_twolit` with the overrule cutoff `z <= min(-3, Phi^-1(0.05 / n))`, n =
populations tested that month (about z <= -4.4). Nothing else changed.

**Evidence (dev and the now-diagnostic detector panel).** Dev +0.360 [+0.054, +0.667], every dev config positive
(worst +0.020), false rejections 0.052% (was 0.094%). Detector +0.073 (was -0.020); overrule-caused false rejections
outside the confounded worlds 566 -> 0; the 1,505 left are all in the unobserved-confounding worlds; harm caught
83.5% (was 83.6%).

**Status.** Accepted as the candidate for confirmatory test 2.

## AR-017 · Confirmatory test 2, pre-registered (2026-10-22, committed BEFORE the run)

Manifest `autoresearch/manifests/confirm_2.json`: same protocol as AR-015 (24 new worlds drawn at run time, per-world
inference, margin -0.25, PASS iff the lower bound exceeds the margin, one run, reported whatever it shows), method
`candidates/m_bonf.py` with its hash pinned. This is the second confirmatory test of the line: whatever it shows,
both results are reported together, and a pass would be read with that multiplicity in mind (two looks).

**Status.** Accepted (frozen).

### AR-017 result: confirmatory test 2 FAILED (2026-10-22)

Draw k = 894053617, 24 new worlds, output verbatim in `autoresearch/CONFIRM_2.txt`. **Per-world gap -0.374 pts [95% CI
-0.591, -0.157]; 21 of 24 worlds negative; FAIL.** False rejections fell (0.49% to 0.34%) but harm caught fell too
(91.0% to 87.8%); the gap did not move.

**Diagnosis (from the two confirm outputs, descriptive only).** Segment worlds in which no overrule ever fired still
lose 0.31 pts (confirm 2) and 0.46 pts (confirm 1) with 0.29% to 0.50% false rejections: the MINER misses legitimate
generated exceptions (generated size thresholds such as 420k, 650k, 900k fall between the decile + round-number grid;
the GBM baselines learn exact cut points). Exception worlds where the overrule did not fire lose about 0.9 to 1.0 pts:
missed harm near the threshold. Overrule false alarms were real (AR-014) but are not the main cause of the deficit.

## AR-018 · Stop this research line; what can be claimed (2026-10-22)

**Decision.** Two pre-registered confirmatory tests failed with intervals entirely below zero. The line stops here;
no third confirmatory test of a tweaked method in this session (that would be optional stopping across looks).

**What the evidence supports.**
- On planted-rule synthetic worlds, the best CCL found by the loop is worse than the best of five fixed case-level
  baselines (selected retrospectively) by about 0.37 points of agreement (95% CIs [-0.60, -0.14] and [-0.59, -0.16]).
- Overruling precedents are what make CCL catch causal harm at all (detector: 0% caught without them, 100% at drops of
  0.25 to 0.30), and search adjustment removes their false alarms except under unobserved confounding, which fools every
  outcome-aware method tested.
- The loop itself (frozen harness, isolated method, plain-data laws, adversarial tests, pre-registration, manifests,
  every failure kept) is the durable contribution.

**Not supported.** Non-inferiority, causal harm detection, transfer to real firms.

**Open hypotheses for a future line (each would need its own pre-registered test):** finer numeric threshold grids for
mining recall; overrule power near the threshold (sequential evidence across months instead of a single-month test).

**Status.** Accepted.

### AR-018 corrections after Astra round 3 (B+ for the record)

- "The best CCL found by the loop" -> **the two selected locked CCL candidates** (dev / detector selection does not show
  which candidate is best on the confirmatory distribution).
- Both intervals exclude zero **and both contain -0.25**: the deficit is real against this comparator, but a deficit
  larger than the margin is not established.
- "Overrules make CCL catch causal harm at all" -> on the detector panel, at drops of 0.25 to 0.30, overrules catch 100%
  vs 0% without them. "Search adjustment removes their false alarms" -> **on the inspected detector panel**, search
  adjustment eliminated the measured overrule-attributable false rejections outside the unobserved-confounding configs;
  confirm 2 still shows overrules firing in segment worlds.
- H2 falsified **this two-literal remedy**, not joint confounding in general; overrule attribution measures direct
  decision changes from deleting overrules from the final law (it does not restore struck precedents).
- Between-run differences (confirm 1 vs 2) are descriptive, not treatment effects; the "miner misses generated
  thresholds" diagnosis is a hypothesis.

## AR-019 · Provenance gaps acknowledged (2026-10-22)

**Context.** Round 3: the manifests pin method and harness hashes but not the simulator; the timeout can still block on
a partial line; invalid runs may write partial baseline caches; the confirmatory summary prints an approximate
configuration-level CI before the registered world-level one.

**Decision.** Recorded as open defects for the next line. Evidence for these runs: `ccl_sim.py` and `rulec.py` have no
commits since the autoresearch baseline (last change `eeedfa7`, 2026-10-20; `CODE_SHA aec5a5c78d96dc8a`, also in the
baseline cache file names). The registered result is the `confirm_world_gap` line, not the `score_pts` line.

**Status.** Accepted.

## AR-020 · When the loop stops (2026-10-22)

**Context.** karpathy/autoresearch never stops on its own: it loops until a human interrupts. For a claim-making
research loop that is optional stopping: keep tweaking and re-testing until something passes.

**Decision.** Three levels of stopping.
- **Inner loop (experiments on dev):** stops after at most 12 experiments in a line, or after 4 consecutive discards
  (a plateau), or when the human interrupts. The kept method is then locked.
- **Line:** a line ends with exactly ONE pre-registered confirmatory test of the locked method on worlds drawn at run time,
  reported whatever it shows. No second confirmatory test inside a line.
- **Research:** a new line is allowed only if it targets a cause diagnosed in the previous line's records, starts with a
  new pre-registration, and uses fresh confirmatory worlds. Every line's result, pass or fail, stays in the README.

**Status.** Accepted.

## AR-021 · Line 2 pre-registration: mining recall (2026-10-22, committed BEFORE any line-2 result)

**Diagnosis carried over (AR-017, hypothesis).** In both confirmatory tests, segment worlds with no overrule still lost
0.3 to 0.5 pts: the miner misses legitimate exceptions in generated worlds. Line 1's dev panel contained no generated
worlds, so it never measured this.

**Harness v4 (human-owned, before running).** Dev panel = the 16 v2.1 configs + 16 generated-world configs (gen:700001 to
700008, exception with harm drawn per world, and segment); partial-line-safe timeout; baselines never cached from
invalid runs; manifests pin simulator and compiler hashes; the confirm summary labels the configuration-level CI as
not the registered analysis.

**Starting point.** `method.py` = `candidates/m_bonf.py` (line 1's final candidate), re-baselined on dev v4.

**Inner-loop budget.** At most 12 experiments or 4 consecutive discards. Keep / discard on dev v4 only.

**Confirmatory test (one).** Same protocol as AR-015 / AR-017 (24 new worlds, per-world t-interval, margin -0.25, PASS iff
the lower bound exceeds -0.25), with simulator and compiler hashes pinned. Line 2 is its own family: alpha 0.05 for this
single test; line 1's two failed tests are reported alongside, not pooled.

**Status.** Accepted (frozen).

## AR-022 · Line 2 inner loop result and confirm_3 pre-registration (2026-10-22, committed BEFORE the run)

**Inner loop (dev v4, 32 configs; stopped at 8 of 12 experiments after a flat sensitivity check).**

| # | change | dev | decision |
|---|---|---|---|
| base | m_bonf (line 1 final) | +0.144 | generated segment worlds -0.365 |
| 1 | 2.5%-quantile size thresholds | +0.234 | keep |
| 2 | CART-style threshold refinement | +0.100 | discard |
| 3 | miner precision 0.95 | +0.039 | discard |
| 4 | beam 100 | +0.234 | discard (same score, more compute) |
| 5 | error-weighted miner gain (errors cost 2x) | +0.305 | keep |
| 6 | error weight 3 | +0.307 | not adopted (flat) |
| 7 | overrule also needs z <= -1 against the threshold (not just against zero) | +0.326 | keep |
| 8 | sensitivity of 7 (-0.5 / -1.5) | +0.313 / +0.304 | flat; -1.5 loses harm detection |

Final dev +0.326 [+0.071, +0.581]; generated segment worlds -0.033; harm caught 100% on dev.
**Descriptive checks (not used to decide):** monitor +0.043 [-0.062, +0.149]; stress -0.337; detector -0.100 (line-1 final:
+0.073) with harm caught 75% (was 83.5%): requiring evidence that the drop EXCEEDS 0.20 misses harm sitting exactly at the
threshold. A real trade-off: fewer false alarms near the threshold, less power at it.

**Confirm_3.** Manifest `manifests/confirm_3.json`: method `candidates/m_line2.py` (hash pinned), harness, simulator
(`aec5a5c78d96dc8a`) and compiler hashes pinned; protocol as AR-015 (24 new worlds, per-world t-interval, margin -0.25, PASS iff the
lower bound exceeds -0.25, one run, reported whatever it shows).

**Status.** Accepted (frozen).
