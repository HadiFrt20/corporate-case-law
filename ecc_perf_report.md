`mine_beam` is now **8.5× faster** (2.31s → 0.27s on one hard-world window) and its output is identical. All 16 tests pass, and nothing is committed.

**The 13 minutes didn't reproduce.** On this machine the full `--seed 7 --miner beam --world hard` run took **40.7s** before any change, not ~13 min, and `mine_beam` was about 60% of it, not almost all. The rest is mostly the 37 HistGradientBoosting fits (about 14s). If you saw 13 minutes, it was probably something about how that run was launched (thread settings, other runs at the same time) rather than the miner itself.

**Timings** (`OMP_NUM_THREADS=2`)

| | Before | After |
|---|---|---|
| `mine_beam`, one hard window (seed 7, month 36, 25,062 rows) | 2.31s | 0.27s |
| `mine_beam`, all 12 windows | 26.2s | ≈3.3s (estimated from the per-window time) |
| Full run, `python3 ccl_sim.py --seed 7 --miner beam --world hard --out /tmp/x.json` | 40.7s | 17.2s (19.1s through the CLI) |

The full-run result JSON is byte-identical before and after, and so is the holdings output for the benchmark window.

**What changed** (only in `ccl_sim.py`, and only the parts you allowed)
- **Literals:** each literal's mask is built once per call into a single boolean matrix (72 × rows), instead of a dict of separate arrays.
- **One-off setup per greedy rule:** the code restricts to the still-open rows and puts each row into a discount bin relative to the caps.
- **Scoring candidates:** the old code sorted rows by discount for every candidate (about 145k sorts per run). Now one matrix multiply per parent gives every child's counts per bin at once, and the counts per cap follow from running totals. Sort order within equal discounts never affected the result, so the counts come out the same.
- **`_best_cap`:** now evaluates all candidates of a parent in one vectorised pass, with the same gain formula and the same tie-breaking.
- **Ranking:** the original's two Python sorts are reproduced exactly, including how ties are ordered. The best rule is still picked from the top 5 with the same strict `>` comparison.
- **Beam entries:** each one stores the open-row indices it covers, so children are evaluated only on those rows.
- **New private helpers:** `_beam_caps`, `_cap_bins`, `_score_children`. `generic_literals` is unchanged, as are `fires`, `literal`, every other function and constant, and the CLI.

**Tests:** `OMP_NUM_THREADS=1 python3 -m pytest -q tests` gives **16 passed in 14.3s**. The new file `tests/test_beam_equivalence.py` holds a frozen copy of the old `mine_beam`, `_best_cap` and `generic_literals` as written before my edit, not imported. It checks, for both worlds on `make_firm(np.random.default_rng(3), 25000, 0.35)`:
- the new output matches the reference exactly (full dicts, same order);
- `generic_literals` is unchanged;
- outputs still match with three non-default parameter sets (`beam=5`; `min_prec=.85, min_support=30`; `max_lits=2, max_rules=4`). I added this check beyond what you asked.

I also checked the test can fail: with a narrower beam or lower `min_prec`, the hard world gives different holdings. The easy world gives the same holdings under those changes, so on its own it's a weaker check.

Two other things in the working tree: a `dbx/` directory appeared during the session and I didn't create it. `ecc_perf.err` and `ecc_perf_report.md` were already there and are empty. My scratch scripts are in `/tmp/beambench/`.
