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
