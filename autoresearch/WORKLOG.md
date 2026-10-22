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
