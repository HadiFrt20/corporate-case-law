"""Thin DBSQL helper (statement execution API) on the personal fe-vm; runs as the calling user (OBO by construction)."""
import time
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

import os
# configure your own workspace: CCL_DATABRICKS_PROFILE (a ~/.databrickscfg profile), CCL_WAREHOUSE_ID, CCL_CATALOG
W = WorkspaceClient(profile=os.environ["CCL_DATABRICKS_PROFILE"])
WH, CAT, SCH = os.environ["CCL_WAREHOUSE_ID"], os.environ["CCL_CATALOG"], os.environ.get("CCL_SCHEMA", "ccl")
FQ = f"{CAT}.{SCH}"


def sql(q, rows=True):
    r = W.statement_execution.execute_statement(statement=q, warehouse_id=WH, wait_timeout="50s")
    while r.status.state in (StatementState.PENDING, StatementState.RUNNING):
        time.sleep(1); r = W.statement_execution.get_statement(r.statement_id)
    if r.status.state != StatementState.SUCCEEDED: raise RuntimeError(f"{r.status.error.message if r.status.error else r.status.state}\n{q[:400]}")
    if not rows or not r.result: return []
    out = list(r.result.data_array or []); chunk = r.result
    while chunk.next_chunk_index is not None:
        chunk = W.statement_execution.get_statement_result_chunk_n(r.statement_id, chunk.next_chunk_index); out += chunk.data_array or []
    cols = [c.name for c in r.manifest.schema.columns]
    return [dict(zip(cols, x)) for x in out]
