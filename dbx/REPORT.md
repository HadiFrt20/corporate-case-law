# CCL on Databricks: end-to-end run (a personal Databricks sandbox workspace, 19 Oct 2026)

All numbers come from `run_log.json` and `injection_log_*.json`.

**Data.** Synthetic hard-world firm (seed 7): 120K discount decisions over 48 months, plus deal-desk comments, later CRM edits and delayed renewal outcomes.

**The run.**
- The firm decides month-36 deals using the law known at the end of month 35.
- Rules are mined on months 24-33 and admitted on months 34-35.

**What runs where.**

| Piece | Databricks primitive | Object |
|---|---|---|
| Decision log, facts edited after the fact | Delta + time travel, one commit group per month (versions 0-144), CDF on | `<catalog>.ccl.decisions`, `ccl.month_versions` |
| Renewal outcomes, appended when known (month + 12·term) | Delta | `ccl.outcomes` |
| Point-in-time facts | union of month-t slices read at the version for end of month t | `as_decided()` in `ccl_on_dbx.py` |
| Holdings (rules) | UC SQL functions, evidence in COMMENT | `ccl.h_m0` … `ccl.h_m8`, `ccl.h_p0..2` |
| Moot court | one **Lakebase branch per candidate**; replay in DBSQL; compute disabled after the verdict, branch kept as the audit record (TTL 7 days) | Lakebase project `ccl-law`, branches `t1758-*` |
| Law registry | Lakebase Postgres (production branch) | tables `holdings`, `trials` |
| Rationale, proposals, merges | Foundation Model API: Claude Sonnet 5.5 writes, GPT-5.5 judges | `llm.py` |
| Decision agent + checker | Claude Sonnet 5.5; the checker re-executes cited UC functions through the SQL API as the calling user | `ccl_on_dbx.py` stage E, `agent_injection.py` |

## Results

**Point in time matters.**
- 11.6% of past decisions have facts that differ in today's table (2,021 churn flags and 946 competitor flags edited after the decision).
- Mining today's table **misses a real rule**: `churn_high AND renewal AND term > 1 AND disc <= 26`, the churn branch of hidden rule H2.
- Law built on today's table, judged on the facts the firm really had: 0.9493. Law built on as-decided facts: 0.9521 (+0.28 pts).

**Moot court.** 9 mined candidates, 9 admitted, each raising replay accuracy (0.681 → 0.952). Median branch-ready time: **5.4 s**.

**Bad law.** Rule m2 (`region = 'US' AND segment = 'MM' AND disc <= 35`) is flagged on outcomes known before month 36. The status is set in the registry, and the agent never sees the rule.

**#1 LLM "because" (9 rules incl. the bad one).** The judge matched all **9/9** to the hidden reason. On the rogue rule, Claude answered *"no coherent, consistent business rationale … individual discretion"* (coherent = false).

**#1 LLM proposals.** Claude proposed 3 new rules from the 1,475 unexplained approvals:
- `competitor` ≤ 30%
- `quarter_end` ≤ 21%
- `churn_high` ≤ 23%

**The moot court rejected all 3**: replay accuracy dropped (0.915 → ~0.905) and precision was below 0.8. The LLM did *not* find H1's missing OR branch (deal > 1M ≤ 30%).

**#1 LLM merges.** Claude proposed none. The three H2 fragments have different caps (22 / 24 / 26), and the prompt only allowed merges with the same cap.

**Decision agent (32 month-36 deals, 24 exceptions).**
- Agent = executable law on 32/32. Citations valid on 32/32.
- Final decision vs a well-run firm: 1.000. Vs the logged decisions: 0.875 (the log includes rogue approvals and noise).

**Prompt injection** (10 deals the law rejects, instruction planted in the note):

| Model | Untrusted-text warning | Followed injection | Invalid citations | Blocked by checker | Wrong decisions shipped |
|---|---|---|---|---|---|
| Claude Sonnet 5.5 | yes | 0 | 0 | 0 | 0 |
| GPT-5.4-nano | no | 2 | 5 | 6 | **0** |

## Engineering findings
- **Endpoint cap.** A project caps active compute endpoints: the 22nd branch endpoint stayed IDLE until a 10-minute timeout. Read-write endpoints can't be deleted. Fix: `update-endpoint spec.disabled=true` after each trial (about 10 s). The branch survives as the audit record.
- **Parquet timestamps.** Nanosecond timestamps are rejected by `read_files` (PARQUET_TYPE_ILLEGAL); write with microsecond precision.
- **My first "point-in-time" read was wrong.** Reading the whole history `VERSION AS OF end-of-month-35` already included the edits (facts changed = 0.0). Point-in-time means each decision is read at its own month's version.
- **Content blocks.** Claude on FMAPI returns content blocks (a list), not a string. JSON replies are parsed with `raw_decode` plus an expected type.

## Caveats
- Synthetic data. The comments were generated with each rule's reason present in about 67% of covering notes, which makes rationale recovery easier than on real notes.
- The rationale judge is an LLM, and it accepted m6's mixed rationale as a match.
- One seed, one decision month.
- The decision agent adds explanation, not judgement: the checker forces the executable law. That is the design, but it means "agent accuracy" measures compliance.
