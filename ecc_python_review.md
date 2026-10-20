I've finished reading both files and the run JSONs; here is the write-up.

# CCL review: `ccl_sim.py` + `whiteboard/ccl_board.py`

**Bottom line:** I found no direct leak of test-month data in the online loop. Mining, admission, outcome checks and GBM training all use months `< m`, and the test month `m` is only used for scoring. But three problems change what the reported numbers mean: the headline CCL accuracy includes the rogue rule, the "bad law" filter reads renewal outcomes that wouldn't exist yet, and the rule-recovery metric is measured mostly on training data. Below, ① = changes a reported number or claim, ② = metric definition or reproducibility, ③ = code quality.

I read the code and checked the saved `run_*.json` files against `RESULTS.md` and the board. I did not run ruff, mypy or black; on a script this size they would mostly report formatting.

## ① Correctness: affects reported results

**1. The headline CCL number (0.931) includes the rogue approver rule**
- **Where:** `ccl_sim.py:215`; board `ccl_board.py:136,143`
- **Why it matters:** `res["ccl"]` uses all admitted holdings, including the US mid-market ≤35% rule that gets flagged as bad law. The board says "the black box COPIES the rogue approver" next to a CCL bar that copies it too. With the bad-law filter applied (`ccl_goodlaw`), schema CCL drops to about **0.877** (0.879 / 0.8745 / 0.8785 across the three seeds). That is about 47% of the gap closed, not 84%.
- **Fix:** either show `ccl_goodlaw` as the headline, or show both bars. Judging "gap closed" against a GBM that is fit to the same rogue labels needs a caveat either way. A cleaner option is to score both against the policy-consistent truth, excluding R7.

**2. The bad-law filter uses renewal outcomes from the future**
- **Where:** `ccl_sim.py:49, 192-196, 208`
- **Why it matters:** `good_law` reads `renewed` for deals from the last month. In reality a renewal outcome only exists after the 1–3 year contract term (`term`). Your own board says outcomes are "never visible to replay" (`ccl_board.py:91`). On top of that, the effect is planted at 0.35 vs 0.85 against a −0.2 threshold, so "flagged 9/9 runs" can't come out any other way.
- **Fix:** delay outcome availability, e.g. `renewed` is known only at `month + 12*term`, so `good_law` only sees deals with `month + 12*term < m`. That will likely leave nothing to check inside a 24-month sim, which is the honest result. Also add a sweep on outcome effect size (0.85 → 0.75 / 0.65) to show where flagging breaks down.

**3. Rule recovery is scored mostly on the training data**
- **Where:** `ccl_sim.py:220-222`
- **Why it matters:** holdings are mined on months 11–20 and admitted on 21–22, but coverage and purity are computed on months 12–23. Only month 23 is out-of-sample, so purity is inflated for holdings that partly fit noise. This feeds the "3 of 7 recovered" claim.
- **Fix:** score on month 23 only. Better: since the rules are planted, generate a large fresh sample from the same process and score `final` on that.

**4. The "effect" masks ignore that the Germany SMB rule (R3) overrides everything**
- **Where:** `ccl_sim.py:224-226` vs `41-44`
- **Why it matters:** in the ground truth, R3 sets the cap to 10% for Germany SMB even when a loosening rule applies. `effect()` still counts those Germany SMB cases as targets for R1/R4/R5, but a correct holding can never cover them, since they are rejected. So coverage for those rules is capped at about 0.89 and understated.
- **Fix:** build the effect from what actually decides the case:
  ```python
  e = m & (disc > STATUTE_CAP) & (disc <= c) & ~TIGHT[1](dl).values
  ```
  Even better, also require that this rule is the binding cap.

**5. Board numbers are copied by hand and partly from a single seed**
- **Where:** `ccl_board.py:128, 136, 144, 146`
- **Why it matters:** "8 readable rules" is the seed 7/23 count; seed 11 has 7. The "support 912 · precision 0.984" and "−0.48" figures are seed 7 only. Nothing ties the board to the result files, so they will drift the next time you re-run.
- **Fix:** load the `run_schema_*.json` files in the board script, then compute means and pick a labelled example seed there.

## ② Metric definitions and reproducibility

**6. The run JSON doesn't record which miner produced it, and a wrong miner name is silently accepted**
- **Where:** `ccl_sim.py:12, 86, 105, 235`
- **Evidence:** `run_seed7.json` has numbers identical to `run_tree_7.json`, even though the default miner is `covering`. It's a stale or mislabelled file, and only the filename says which miner was used. Any value other than `schema` or `tree` (e.g. a typo like `schemas`) silently runs covering.
- **Fix:** `assert MINER in {"covering","tree","schema"}`, add `miner=MINER` to `out`, and delete `run_seed7.json`.

**7. The "rules recovered" metric isn't in the code**
- **Where:** `RESULTS.md` (thresholds `cov≥.6, purity≥.8`) vs board (`ccl_board.py:149`, "found exactly")
- **Why it matters:** these are two different definitions, and the aggregation was done by hand.
- **Fix:** compute `recovered = cov>=.6 and purity>=.8` per rule inside the script, emit it, and generate `RESULTS.md` from the JSONs.

**8. Recovery matches each planted rule to one best holding**
- **Where:** `ccl_sim.py:232`
- **Why it matters:** a rule that is fully covered by 4 fragments (R4 split by region, as in the seed-7 schema run) scores as "not recovered".
- **Fix:** also report union coverage over all holdings with purity ≥ threshold. Keep "exact" as a separate, stricter metric.

**9. The schema miner can never find R5 exactly**
- **Where:** `ccl_sim.py:123-124`
- **Why it matters:** size thresholds come from quantiles (≈358 / 514 / 706 under lognormal(4.6, 1)), so a literal `> 500` can never appear. R5 can't count as "found exactly", which partly explains "2 missed".
- **Fix:** add round-number thresholds (100k / 250k / 500k / 1M), or acknowledge the limitation.

**10. The board claims "regression-safe" admission, but the code only checks overall accuracy**
- **Where:** `ccl_sim.py:186-187`
- **Why it matters:** the code checks that total accuracy goes up. It does not check that previously admitted holdings keep their precision, and later holdings overwrite earlier citations in `apply()` (line 176).
- **Fix:** recompute each admitted holding's precision on its effective (non-overwritten) mask after each admission, and reject the candidate if any drops below `min_prec`. Otherwise soften the board text (`ccl_board.py:95`).

**11. Smaller issues**
- `ccl_nodecay` (line 209) can't test decay, because R1 is never mined. You already note this, but the label still suggests it does.
- Monthly accuracies are averaged without weighting by month size (line 235). The effect is negligible at about 2.5k deals per month.

## ③ Code quality

**12. `lit_mask` does wasted work on every call** (`ccl_sim.py:159`)
`L = literals(d) ...` builds all literal masks and 3 quantiles, then never uses them, and `d._L` is never set. It runs on every `fires()` call and `moot_court` is O(k²) calls, so this is pure slowdown. Delete the line.

**13. `fires()` depends on a hidden global** (line 69)
It looks up rows through `DF.loc[Xd.index]`, which only works because `XALL` and `df` share an index. Pass `d` explicitly. `apply` and `moot_court` already have it.

**14. Structure and style in `ccl_sim.py`**
- The docstring in `mine()` (line 99) comes after code, so it isn't a docstring.
- `MINER` is a module-level global read inside functions.
- There is a mid-file import at line 116 and everything runs at import time, so nothing can be tested.
- Fix: put the experiment in `main(seed, miner)` with argparse, add a fixed-seed smoke test, and run `black`/`ruff`. The heavy `;` one-liners are fine for a scratch script but hurt review.

**15. `ccl_board.py` issues**
- `open()` is used without `with` (lines 178, 183); the write handle is never explicitly closed.
- `sys.path.insert` points at another project (line 4).
- `from exd import *` combined with assigning to `exd._seed` (line 7) mutates a module's private state.
- `E[-2]` (lines 69, 72) assumes `box()` always returns `[shape, text]`, which breaks silently if `exd` changes.
- Fix: use `with`, take the `exd` path from a parameter or env var, and use `box(...)[0]` explicitly.

## Suggested order

Fix 1 → 2 → 3 → 4 first, then re-run the 3 seeds × 3 miners. Items 1 and 2 will probably move the headline from "84% gap closed + rogue flagged 9/9" to roughly "~47% with bad-law filtering, and the filter isn't realistic within the time window". Under your own kill rule on the board ("KILL if CCL < policy + 10 pts OR fewer than 4 of 7 rules recovered"), the current 3/7 already triggers it, and corrected numbers for items 1 and 3 would strengthen that. Then add 6 and 7 so `RESULTS.md` and the board are generated from the JSONs rather than typed in by hand.
