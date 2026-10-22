# Worklog: CCL autoresearch

Chronological. Every experiment gets an entry: hypothesis, change, result, decision, and anything that went wrong.
Numbers come from `results.tsv` / `holdout.tsv` (untracked) and `RUN_*.md` snapshots.

## 2026-10-22 · setup

- Read karpathy/autoresearch (README, program.md). Mapped it to CCL (AR-001 to AR-004).
- Timed one hard/exception run of `ccl_sim.py`: 20 s. 12 dev configs in parallel on 14 cores: 16 s per experiment
  after baselines are cached.
- Baseline (`7b5b94b`, v5.1 CCL: beam miner, admission 2 months, scoped screen): dev -1.141, worst -3.244
  (hard/exception/23), harmful 0.50%, 6.68 rules. Reproduces the published v5.1 picture (hard/exception about -3).
- Holdout baseline: -0.836 (alt world -0.26 to -0.69).

## 2026-10-22 · experiments 1 to 13 (run oct22)

| # | commit | hypothesis | dev score | rules | decision |
|---|---|---|---|---|---|
| 1 | c3bd236 | overrule exceptions that renew worse than in-policy deals of the same population | -4.415 | 7.69 | discard: Simpson confounding ("region = US" mixes the rogue MM book with healthy segments) |
| 2 | 84f96fe | same, but the contrast must hold in every refinement | -0.655 | 7.22 | keep: harm 0% everywhere |
| 3 | acf8b75 | every threshold for small integer fields | -0.411 | 7.19 | keep: "tenure >= 11" stateable |
| 4 | cca8fe4 | admission window 4 months | -0.182 | 7.19 | keep: true rules stop dropping out of the law |
| 5 | 0bf4d69 | power-aware beam miner | -0.290 | 7.56 | discard |
| 6 | 7fc7232 | beam min_support 40 | -0.147 | 7.35 | keep |
| 7 | 531478d | beam width 60 | -0.092 | 7.55 | keep: churn branch of the interaction rule found |
| 8 | 0056e3f | drop the rule-level outcome screen | -0.024 | 8.19 | keep: simpler |
| 9 | eda0170 | strike precedents inside an overrule | -0.024 | 7.69 | keep: same decisions, fewer rules |
| 10 | a3618e4 | beam min_support 30 | +0.110 | 8.37 | keep: first dev score above 0 |
| 11 | 1fe5367 | up to 4 conditions per rule | +0.112 | 8.38 | discard: +0.002 for longer rules |
| 12 | a021963 | admission window 6 months | -0.058 | 7.67 | discard |
| 13 | 1b01ba6 | 18-month history window | -0.408 | 8.62 | discard: retired rule lingers |

Holdout checkpoints: 531478d -0.180; a3618e4 -0.071. Harmful approvals 0% in every holdout config.

What went wrong: experiment 1's first run crashed (holdings without an `id`); a safety hook flagged a combined
grep-and-commit command twice, so edits and commits now run as separate steps.

## 2026-10-22 · experiment 14 (ablation that was kept)

| # | commit | hypothesis | dev score | rules | decision |
|---|---|---|---|---|---|
| 14 | e3a50cd | ablation: drop the moot court, mine on the full 12-month window, admit every mined rule | +0.181 | 8.77 | keep: all 12 dev configs positive; holdout -0.071 to +0.050 (first positive), alt world ties or beats |

This undercuts "replay as an admission test" for MINED rules in this simulator: a high-precision miner on 12 months beats
mining on 8 and replaying on 4. It says nothing about untrusted proposals (LLM-written rules), which this harness never
injects; see AR-008.

## 2026-10-22 · Astra review round 1 (C+) and harness v2

- Review: `docs/reviews/astra_autoresearch_round1_2026-10-22.md` (the raw stream was decoded as latin-1; repaired to
  UTF-8 once, text otherwise unedited). Response: `docs/reviews/response_autoresearch_round1_2026-10-22.md`.
- Built harness v2 (AR-009): separate method process, plain-data law, strict literal grammar, decision-time columns,
  clean baselines plus a compact-tree baseline, CIs, false rejections, monitor / stress / fresh panels.
- Method fixes (AR-010). Re-ran: dev +0.181 [95% CI +0.147, +0.214], identical to v1; monitor +0.052 [-0.040, +0.144],
  non-inferior at the -0.25 margin; stress panel (AR-011).
- Tests: 27 adversarial harness tests; full suite 106 passed.
- Mistakes: harness v2 first run crashed (decision columns included `tenure_y` in the easy world); the first leak probe
  crashed on objects whose `columns` attribute is not iterable; added a positive control so the probe's silence means
  something. A safety hook mistook a Python one-liner for a kubectl command; read the cache file directly instead.

## 2026-10-22 · experiments 15 to 19 on harness v2, and the dev panel fix (v2.1)

| # | commit | hypothesis | dev score | rules | decision |
|---|---|---|---|---|---|
| 15 | d0f0baa | overrule discovery on older outcomes, confirmation on newer (multiple-testing guard) | +0.129 | 8.81 | discard: half the data per stage, small refinements skipped, more false overrules (easy/segment s7 -0.56) |
| 16 | 08c36ca | refinements must show the full 0.20 drop, not half | +0.184 | 8.75 | keep: small gain, worst case +0.097, fewer overrules |
| 17 | 08c36ca | sensitivity: min_support 25/35, beam 40/80 | +0.180 to +0.184 | 8.72 to 8.75 | flat neighbourhood: not knife-edge |
| 18 | 08c36ca | ablations: minus overrules / minus integer thresholds / minus refinement check / plus moot court | -2.787 / -0.043 / -3.755 / +0.113 | | overruling with the refinement check is the core of the gain |
| ckpt | 08c36ca | monitor + stress after exp 16 | monitor +0.081 | | STRESS: harm just above threshold caught 38% (was 96%): exp 16 is a Goodhart, see AR-012 |
| 19 | 5ce0e00 | statistical refinement test: reject a population only on significant evidence a refinement's drop is below 0.20 | +0.121 (dev v2) / +0.306 (dev v2.1) | 9.34 | keep: on the corrected dev panel it beats exp 16 (+0.193, 93.8% caught) |

What happened at the checkpoint: experiment 16 (refinements must show the full 0.20 drop) was kept on dev (+0.184), then
the stress panel showed it catching only 38% of harmful cases when the true drop is 0.25 (was 96%). Dev had only 0.50
drops, so the stricter point estimate cost nothing there and vetoed real effects near the threshold through sampling
noise. Fix for a reason stated in advance (power), not because of the stress number: a statistical refinement test
(experiment 19). The dev panel itself was defective (no near-threshold harm), so harness v2.1 adds 4 near-threshold
configs on new seeds (31, 47) and widens the still-unrun fresh panel with harms of random size; both candidates were
re-scored on dev v2.1. The stress panel has now been looked at and is no longer a clean test of threshold sensitivity;
the fresh panel is.
Mistakes: a zsh loop did not word-split its parameter pairs (all four sensitivity runs invalid; rows removed, rerun
with explicit splitting); a safety hook mistook a Python one-liner for kubectl again (read the file instead).

## 2026-10-22 · locked method ar-locked-1 (exp 19): monitor and FRESH run 1

- Monitor: -0.032 [95% CI -0.169, +0.106], non-inferior at -0.25 (worst easy/segment/202 -0.412), harm caught 100%.
- **Fresh run 1** (draw k = 16737199, 12 configs, 4 generated worlds x 2 effects + 4 with random near-threshold harm;
  run once, output kept verbatim in `FRESH_run1_k16737199.txt`): **-0.419 [-0.901, +0.063], NOT non-inferior**.
  Harm caught 97%, harmful approvals 0.10%, but false rejections 0.71% on average (up to 1.44%) with overrules firing
  in segment worlds that contain no causal harm (up to 2.2 per month). One near-threshold world won big (+1.53, where
  the black boxes over-block), one missed harm (81.9% caught).
- Reading: the clean test does not support "CCL ties or beats the black box". The over-blocking is consistent with
  Astra round 1, point 5.1 (refinements by one literal miss confounders defined by two literals jointly, e.g. a rogue
  approver = segment x region). Next: two-literal refinements (proposed by the review BEFORE this run), judged on dev,
  then a NEW fresh draw; every fresh run is logged here so the adaptivity stays visible.

## 2026-10-22 · experiment 20, fresh run 2, Astra review round 2 (B-)

| # | commit | hypothesis | dev score | rules | decision |
|---|---|---|---|---|---|
| 20 | 8e11282 | two-literal refinements (categorical / boolean pairs) in the overrule check | +0.319 | 9.32 | keep (false rejections 0.106% to 0.094%); locked as ar-locked-2 |

- Monitor (ar-locked-2): +0.006 [-0.108, +0.121], non-inferior at -0.25.
- **Fresh run 2** (draw k = 940134736, output verbatim in `FRESH_run2_k940134736.txt`): **-0.042 [-0.676, +0.591], NOT
  non-inferior** (interval too wide). Harm caught 100%, harmful approvals 0%, false rejections 0.50% (run 1: 0.71%). Four
  segment worlds still lose 0.37 to 0.88 pts (over-blocking); three near-threshold worlds win +1.30 to +1.63 (the black
  boxes over-block there); one near-threshold world loses 1.35. Different worlds from run 1: the change is suggestive,
  not a measured improvement.
- **Disclosure:** fresh run 2 was launched before Astra round 2 had been read. Round 2 recommends against another fresh
  draw before a frozen falsification experiment and warns that "one fresh draw per revised method until one passes" is
  optional stopping. Two fresh draws have now been used; both are kept and both failed non-inferiority.
- Astra round 2 (`docs/reviews/astra_autoresearch_round2_2026-10-22.md`): B- for the loop, D for any non-inferiority
  claim. Defects it found and fixed here: the GC leak probe never actually inspected pandas objects (now fixed and
  covered by its own positive control); the outcome-timing test used the code under test as its oracle (now a
  handcrafted case); `MONTH_TIMEOUT_S` was unused (now enforced with select); a literal on a field missing in a world
  crashed instead of invalidating (now a violation); stale wording ("every refinement", "12 configs", "best black box").
  New tests: 32 harness tests, full suite 111 passed. Dev re-run after the harness changes: +0.319, unchanged.
- Response: `docs/reviews/response_autoresearch_round2_2026-10-22.md`. Next step pre-committed in AR-013.

## 2026-10-22 · AR-014 detector falsification experiment, then AR-015 manifest

- Harness v3: detector panel (33 configs, seeds 501 to 503), confirm panel driven by a committed manifest, per-overrule
  attribution of changed decisions. Candidates frozen in `candidates/` (one-literal, two-literal, no overrules).
- Pre-registration AR-014 committed (0f04399) before any run; analysis script committed (54b885c) before reading output.
- First detector attempt: all configs died (relative method path, runner cwd is a temp dir). Fixed in 89f71ef, test added.
- Results: H1 supported (75% of no-harm false rejections are overrules), H2 NOT supported (two-literal refinements: -0.4%),
  H3 supported (overrules net positive: -0.020 vs -1.584). False overrules = thin numeric tails = multiple testing.
- Selection by the pre-registered rule: `m_twolit.py`. Manifest `confirm_1.json` (AR-015) committed before the run.
- Not done on purpose: no method change in response to the H2 failure before the confirmatory run (that is the next
  iteration: search-adjusted overrules, AR-016 to come).

## 2026-10-22 · CONFIRMATORY TEST 1: FAIL

- `python3 autoresearch/harness.py --panel confirm --manifest autoresearch/manifests/confirm_1.json`, run once.
- Per-world gap **-0.373 [-0.603, -0.142]**, 22 of 24 worlds negative, **FAIL**; harm caught 91.0%, false rejections 0.49%.
- Recorded in AR-015. No change to the method or harness between the manifest commit (6efd56f) and the run.

## 2026-10-22 · AR-016 Bonferroni overrules; AR-017 confirm_2 manifest

- `candidates/m_bonf.py`: dev +0.360 (all positive), detector +0.073, overrule false rejections outside the confounded
  worlds 566 -> 0, harm caught unchanged (83.5%). Manifest `confirm_2.json` committed before the run.
