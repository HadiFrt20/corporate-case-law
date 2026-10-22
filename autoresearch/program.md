# autoresearch for Corporate Case Law

Adapted from karpathy/autoresearch: an agent edits one file, a frozen harness scores it, keep or discard, repeat.

## The research question

CCL v5.1 lost to case-level black boxes once every method saw the same outcome information
(hard world: -2.8 points against GBM + renewal veto; harm leaked through overlapping rules that a
rule-level outcome screen cannot see). The question for this loop:

> Can a law made only of readable, executable rules close the gap to the best case-level black box?

## Files

- `autoresearch/harness.py`, `runner.py`, `worlds.py`: FROZEN (harness v2, AR-009). The harness builds the firms, sends
  your method a view of the past in a separate process, validates the plain-data law you return, decides with its own
  rule engine and scores against the harm-aware oracle. Do not modify.
- `ccl_sim.py`, `rulec.py`: FROZEN. You may import and call helpers, or copy a function into `method.py` and change
  the copy. Do not monkeypatch them (it has no effect on scoring anyway: your process is not the harness's).
- `autoresearch/method.py`: THE ONLY FILE YOU EDIT. `build_law(view, X, m)` returns the law for month m.
- `autoresearch/results.tsv`: experiment log (untracked).
- `autoresearch/monitor.tsv`, `stress.tsv`, `fresh.tsv`: panel logs (untracked).
- `autoresearch/WORKLOG.md`, `autoresearch/ADR.md`: this project's own records (tracked).

## Rules of the game

What you CAN do: anything inside `method.py`. Mining, admission, outcome screening, rule merging, carve-outs,
overruling, decay, new literals built from the allowed fields, thresholds, windows.

What you CANNOT do:
- modify the harness, the simulator, the rule engine or the compiler
- install packages
- decide anything at decision time with a model: the harness applies your law with `ccl_sim.apply`, so your
  only output is a list of rules
- break the form gates: at most 15 holdings of the form {kind, lits, cap}, at most 4 literals each and 45 overall,
  literals only over the deal fields (segment, region, renewal, quarter_end, competitor, churn_high, term, size_k,
  tenure_y), finite caps in range
- use information the firm did not have: the view already hides it; do not try to reconstruct hidden columns
  from the simulator's code or random seeds (that is cheating, not research)
- look at the monitor, stress or fresh panels to choose what to keep

**The goal: the highest `score_pts`** (mean over the 16 dev configurations, since harness v2.1, of CCL minus
the best of five fixed baselines selected retrospectively per configuration, in points). 0 means CCL ties the best black box; positive means it beats it.

**Simplicity criterion** (as in the original): all else equal, simpler is better, and fewer rules is better.
A +0.02 gain that adds 40 lines or 4 rules is probably not worth it. Equal score with less code or fewer
rules is a win. Report `rules_mean` with every result.

**Honesty criterion** (added for this domain): a change must be justifiable as a policy a firm could state
("an exception whose approvals renew badly against comparable in-policy deals is overruled"). If you can only
explain a gain by a quirk of the simulator, discard it and say so in the description.

## Running

```
python3 autoresearch/harness.py --panel dev > autoresearch/run.log 2>&1
grep "^score_pts:\|^false_rej\|^rules_mean:\|^status:" autoresearch/run.log
```
A run takes about 45 seconds (baselines are cached). If `status: invalid` appears, the law broke a gate.

## Logging

`results.tsv`, tab-separated, header: `commit	score_pts	worst_gap	rules_mean	status	description`
status is `keep`, `discard`, `invalid` or `crash`.

Every 5 kept commits, run the monitor and stress panels and append to `monitor.tsv` / `stress.tsv`
(`--panel monitor`, `--panel stress`). The monitor has unseen seeds and an alt world; it is seen repeatedly, so it is
not a clean test. The stress panel tests the harm detector (below / above threshold, non-causal confounding).
Run `--panel fresh` ONCE per locked method (it draws new worlds and seeds at run time) and log it to `fresh.tsv`.
If dev improves while monitor or fresh fall, you are overfitting the simulator: say so.

## Logging and decisions (this project's own records)

- `autoresearch/WORKLOG.md`: after EVERY experiment, add a row (number, commit, hypothesis, dev score, rules,
  decision and why). Record crashes and mistakes too.
- `autoresearch/ADR.md`: when a kept change alters the method's design (a new mechanism, a removed one, a policy
  for the loop itself), add an AR-NNN record: context, decision, consequences, status. Parameter tweaks go in the
  worklog only.
- Commit the worklog and ADR updates with the experiment they describe (results.tsv stays untracked).

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

## Current state (2026-10-22)

Line 1 STOPPED (AR-018: two confirmatory tests failed). Line 2 (AR-021: mining recall) is OPEN under the stopping
policy AR-020: at most 12 experiments or 4 consecutive discards, then lock and run ONE confirmatory test.
