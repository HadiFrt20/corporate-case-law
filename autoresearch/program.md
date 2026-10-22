# autoresearch for Corporate Case Law

Adapted from karpathy/autoresearch: an agent edits one file, a frozen harness scores it, keep or discard, repeat.

## The research question

CCL v5.1 lost to case-level black boxes once every method saw the same outcome information
(hard world: -2.8 points against GBM + renewal veto; harm leaked through overlapping rules that a
rule-level outcome screen cannot see). The question for this loop:

> Can a law made only of readable, executable rules close the gap to the best case-level black box?

## Files

- `autoresearch/harness.py`: FROZEN. Builds the firms, hides ground truth, applies the law with the frozen
  rule engine, scores against the harm-aware oracle, enforces the form gates. Do not modify.
- `ccl_sim.py`, `rulec.py`: FROZEN. The simulator, the rule language (`literal`, `fires`, `apply`, `to_sql`) and
  the trusted compiler. Do not modify. You may import and call anything in them, or copy a function into
  `method.py` and change the copy.
- `autoresearch/method.py`: THE ONLY FILE YOU EDIT. `build_law(view, X, m)` returns the law for month m.
- `autoresearch/results.tsv`: experiment log (untracked).
- `autoresearch/holdout.tsv`: holdout checkpoints (untracked).

## Rules of the game

What you CAN do: anything inside `method.py`. Mining, admission, outcome screening, rule merging, carve-outs,
overruling, decay, new literals built from the allowed fields, thresholds, windows.

What you CANNOT do:
- modify the harness, the simulator, the rule engine or the compiler
- install packages
- decide anything at decision time with a model: the harness applies your law with `ccl_sim.apply`, so your
  only output is a list of rules
- break the form gates: at most 15 holdings, at most 4 conditions each, valid literals or AST, numeric caps
- use information the firm did not have: the view already hides it; do not try to reconstruct hidden columns
  from the simulator's code or random seeds (that is cheating, not research)
- look at the holdout to choose what to keep

**The goal: the highest `score_pts`** (mean over the 12 dev configurations of CCL minus the best case-level
baseline, in points). 0 means CCL ties the best black box; positive means it beats it.

**Simplicity criterion** (as in the original): all else equal, simpler is better, and fewer rules is better.
A +0.02 gain that adds 40 lines or 4 rules is probably not worth it. Equal score with less code or fewer
rules is a win. Report `rules_mean` with every result.

**Honesty criterion** (added for this domain): a change must be justifiable as a policy a firm could state
("an exception whose approvals renew badly against comparable in-policy deals is overruled"). If you can only
explain a gain by a quirk of the simulator, discard it and say so in the description.

## Running

```
python3 autoresearch/harness.py > autoresearch/run.log 2>&1
grep "^score_pts:\|^rules_mean:\|^status:" autoresearch/run.log
```
A run takes about 20 seconds (baselines are cached). If `status: invalid` appears, the law broke a gate.

## Logging

`results.tsv`, tab-separated, header: `commit	score_pts	worst_gap	rules_mean	status	description`
status is `keep`, `discard`, `invalid` or `crash`.

Every 5 kept commits, and at the end, run the holdout once and append to `holdout.tsv`:
`python3 autoresearch/harness.py --holdout > autoresearch/holdout.log 2>&1`.
The holdout has unseen seeds and an unseen world (different rule shapes, a different stricter rule, a rogue
approver in another segment). If dev improves while holdout falls, you are overfitting the simulator: say so.

## The loop

On branch `autoresearch/<tag>`:
1. form a hypothesis, write it down in one line
2. edit `method.py`, `git commit`
3. run the harness, read the summary
4. log to `results.tsv`
5. if `score_pts` improved (or equal and simpler), keep the commit; otherwise `git reset --hard HEAD~1`
6. repeat

Do not stop to ask whether to continue. When out of ideas, re-read the per-configuration lines: they say
where the law loses (harmful approvals = leaked harm; false rejections = over-blocking).
