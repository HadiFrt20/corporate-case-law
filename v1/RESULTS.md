# CCL falsification v1 (synthetic firm, 60K deals, 7 planted tacit rules, 4% noise, online months 18-23, 3 seeds)

| miner | statute only | CCL | GBM monthly | gap closed | rules recovered (cov>=.6, purity>=.8) | rogue rule flagged as bad law |
|---|---|---|---|---|---|---|
| tree | 0.809 | 0.911 | 0.954 | 71% | 0.7/7 | 3/3 |
| covering | 0.809 | 0.901 | 0.954 | 63% | 2.7/7 | 3/3 |
| schema | 0.809 | 0.931 | 0.954 | 84% | 3.0/7 | 3/3 |

Not tested yet: LLM rationale + consolidation of sibling holdings, decay (R1 never mined), real data.
