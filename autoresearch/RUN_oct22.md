# autoresearch run oct22

Branch autoresearch/oct22, harness autoresearch/harness.py (frozen), method autoresearch/method.py. Metric: mean over 12 dev configs of (CCL - best case-level black box) in points; decisions made only by the frozen rule engine, at most 15 rules of at most 4 conditions.

## Dev log (results.tsv)

```
commit   score_pts  worst_gap  rules_mean  status   description
7b5b94b  -1.141     -3.244     6.68        keep     baseline: v5.1 CCL (beam, adm 2, scoped screen)
c3bd236  -4.415     -10.384    7.69        discard  overrule precedents, naive same-population contrast: harm 0% but Simpson confounding over-blocks (easy/segment -10)
84f96fe  -0.655     -1.612     7.22        keep     overrule only if contrast holds in every refinement: harm 0%, hard/exception -3.1 -> -1.3
acf8b75  -0.411     -1.009     7.19        keep     every threshold for small integer fields (tenure >= 11 now stateable)
cca8fe4  -0.182     -0.533     7.19        keep     admission window 4 months (true rules stop dropping out)
0bf4d69  -0.290     -1.049     7.56        discard  power-aware beam miner: more rules, worse in hard world
7fc7232  -0.147     -0.506     7.35        keep     beam min_support 40 (rarer exceptions mineable)
531478d  -0.092     -0.360     7.55        keep     beam width 60 (interaction rule's churn branch found)
0056e3f  -0.024     -0.323     8.19        keep     drop the rule-level outcome screen: simpler, overrules handle harm (+0.6 rules: overruled precedents linger)
eda0170  -0.024     -0.323     7.69        keep     strike precedents fully inside an overrule: same decisions, -0.5 rules
a3618e4  +0.110     -0.163     8.37        keep     beam min_support 30 (rare OR branch: deals > 1M)
1fe5367  +0.112     -0.163     8.38        discard  up to 4 conditions per rule: +0.002 for longer rules (simplicity)
a021963  -0.058     -0.396     7.67        discard  admission window 6 months: mining window too short
1b01ba6  -0.408     -1.046     8.62        discard  18-month window: stale rules (retired R1) linger
```

## Holdout checkpoints (unseen seeds 101, 202 + unseen alt world; never used to decide)

```
commit   score_pts  worst_gap  rules_mean  note
7b5b94b  -0.836     -3.243     6.03        baseline
531478d  -0.180     -0.849     6.77        checkpoint after 5 keeps
a3618e4  -0.071     -0.576     7.33        early check: first dev score above 0
```

## Final holdout per config (a3618e4)

```
  easy  exception s101  ccl 0.9992  best veto     0.9974  gap  +0.17  harmful  0.00%  rules  6.5
  easy  exception s202  ccl 0.9993  best veto     0.9967  gap  +0.26  harmful  0.00%  rules  6.5
  easy  segment   s101  ccl 0.9992  best gbm      0.9976  gap  +0.16  harmful  0.00%  rules  6.5
  easy  segment   s202  ccl 0.9976  best gbm      0.9968  gap  +0.08  harmful  0.00%  rules  6.6
  hard  exception s101  ccl 0.9937  best veto     0.9980  gap  -0.43  harmful  0.00%  rules  9.6
  hard  exception s202  ccl 0.9964  best veto     0.9975  gap  -0.11  harmful  0.00%  rules  9.8
  hard  segment   s101  ccl 0.9923  best gbm      0.9980  gap  -0.58  harmful  0.00%  rules 10.2
  hard  segment   s202  ccl 0.9964  best gbm      0.9976  gap  -0.12  harmful  0.00%  rules  9.8
  alt   exception s101  ccl 0.9983  best veto     0.9989  gap  -0.06  harmful  0.00%  rules  5.4
  alt   exception s202  ccl 0.9977  best veto     0.9982  gap  -0.06  harmful  0.00%  rules  5.3
  alt   segment   s101  ccl 0.9983  best gbm      0.9989  gap  -0.06  harmful  0.00%  rules  5.4
  alt   segment   s202  ccl 0.9971  best gbm      0.9982  gap  -0.11  harmful  0.00%  rules  6.2
```
