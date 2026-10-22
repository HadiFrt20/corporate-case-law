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

**Status.** Proposed.
