"""Standalone integrity check of the LATEST run's law (no pipeline re-run): every active rule function's body AND signature are
verified exactly; a signature-tamper function (two BOOLEAN parameters swapped, identical body) must be rejected."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.dirname(HERE))
import lb
from dbsql import sql, FQ
from ccl_on_dbx import verify_fn, COLS, EXPECTED_SIG
with lb.connect() as c:
    run = c.execute("SELECT run_id FROM law_events ORDER BY seq DESC LIMIT 1").fetchone()[0]
    rows = c.execute("SELECT id, fn_name, sql_text, status FROM law_current WHERE run_id=%s AND status IN ('admitted', 'superseded') ORDER BY id", [run]).fetchall()
res = dict(run_id=run, checked=[], failures=[])
for hid, f, body, st in rows:
    try: verify_fn(f, body); res["checked"].append(hid)
    except RuntimeError as e: res["failures"].append(dict(id=hid, error=str(e)[:200]))
# signature tamper: swap two same-typed BOOLEAN parameters (renewal <-> quarter_end) and keep the exact body of a real rule
hid, f, body, _ = rows[0]
swapped = list(EXPECTED_SIG); i, j = 3, 4; swapped[i], swapped[j] = swapped[j], swapped[i]
tam = f"{FQ}.h_sigtamper_{run.lower()}"
sql(f"CREATE OR REPLACE FUNCTION {tam}({', '.join(f'{n} {t}' for n, t in swapped)}) RETURNS BOOLEAN RETURN {body}", rows=False)
try: verify_fn(tam, body); res["signature_tamper"] = "NOT DETECTED"
except RuntimeError as e: res["signature_tamper"] = "detected"
sql(f"DROP FUNCTION IF EXISTS {tam}", rows=False)
json.dump(res, open(os.path.join(HERE, "integrity_check.json"), "w"), indent=1)
print({k: (v if not isinstance(v, list) else len(v)) for k, v in res.items()})
assert not res["failures"] and res["signature_tamper"] == "detected"
