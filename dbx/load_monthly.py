"""Replay history into Delta one month per commit-group, so time travel reproduces what the CRM held on any date."""
import json, time
from dbsql import sql, FQ, CAT, SCH

V = f"/Volumes/{CAT}/{SCH}/raw"
rf = lambda f: f"read_files('{V}/{f}.parquet', format => 'parquet')"
sql(f"DROP TABLE IF EXISTS {FQ}.decisions", rows=False); sql(f"DROP TABLE IF EXISTS {FQ}.outcomes", rows=False)
sql(f"""CREATE TABLE {FQ}.decisions TBLPROPERTIES (delta.enableChangeDataFeed = true)
        COMMENT 'Discount decisions as the CRM holds them; facts are EDITED after decisions (churn_high, competitor). Use VERSION AS OF for point-in-time.'
        AS SELECT * FROM {rf('decisions')} WHERE 1 = 0""", rows=False)
sql(f"""CREATE TABLE {FQ}.outcomes COMMENT 'Renewal outcomes, appended only when known (month + 12 * term)'
        AS SELECT * FROM {rf('outcomes')} WHERE 1 = 0""", rows=False)
versions = {}; t0 = time.time()
for m in range(48):
    sql(f"INSERT INTO {FQ}.decisions SELECT * FROM {rf('decisions')} WHERE month = {m}", rows=False)
    for field in ["churn_high", "competitor"]:
        sql(f"""MERGE INTO {FQ}.decisions d USING (SELECT deal_id, value FROM {rf('edits')} WHERE edit_month = {m} AND field = '{field}') e
                ON d.deal_id = e.deal_id WHEN MATCHED THEN UPDATE SET {field} = e.value""", rows=False)
    sql(f"INSERT INTO {FQ}.outcomes SELECT * FROM {rf('outcomes')} WHERE known_month = {m}", rows=False)
    dv = int(sql(f"DESCRIBE HISTORY {FQ}.decisions LIMIT 1")[0]["version"]); ov = int(sql(f"DESCRIBE HISTORY {FQ}.outcomes LIMIT 1")[0]["version"])
    versions[m] = dict(decisions=dv, outcomes=ov)
    print(m, versions[m], round(time.time() - t0), "s", flush=True)
sql(f"DROP TABLE IF EXISTS {FQ}.month_versions", rows=False)
sql(f"CREATE TABLE {FQ}.month_versions (month INT, decisions_version BIGINT, outcomes_version BIGINT) COMMENT 'Delta version at the END of each month'", rows=False)
sql(f"INSERT INTO {FQ}.month_versions VALUES " + ",".join(f"({m},{v['decisions']},{v['outcomes']})" for m, v in versions.items()), rows=False)
json.dump(versions, open("month_versions.json", "w"), indent=1)
print("done", round(time.time() - t0), "s")
