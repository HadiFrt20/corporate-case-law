"""Lakebase (autoscaling) helpers for the CCL law registry: OAuth token, connect, branch per candidate."""
import json, subprocess, time
import psycopg

import os
PROFILE, PROJECT = os.environ["CCL_DATABRICKS_PROFILE"], "projects/" + os.environ.get("CCL_LAKEBASE_PROJECT", "ccl-law")
DB = "databricks_postgres"
_USER = None
def user():
    """Lakebase OAuth login = the calling workspace user"""
    global _USER
    if _USER is None: _USER = cli("current-user", "me")["userName"]
    return _USER


def cli(*args):
    out = subprocess.run(["databricks", "-p", PROFILE, *args, "-o", "json"], capture_output=True, text=True)
    if out.returncode: raise RuntimeError(out.stderr[-800:])
    return json.loads(out.stdout) if out.stdout.strip() else {}


def endpoint(branch="production"):
    eps = cli("postgres", "list-endpoints", f"{PROJECT}/branches/{branch}")
    return eps[0] if isinstance(eps, list) and eps else None


def connect(branch="production", autocommit=True):
    ep = endpoint(branch)
    tok = cli("postgres", "generate-database-credential", ep["name"])["token"]
    return psycopg.connect(host=ep["status"]["hosts"]["host"], port=5432, dbname=DB, user=user(), password=tok,
                           sslmode="require", connect_timeout=30, autocommit=autocommit)


def create_branch(branch_id, ttl="86400s"):
    t0 = time.time()
    cli("postgres", "create-branch", PROJECT, branch_id, "--ttl", ttl)
    while endpoint(branch_id) is None or endpoint(branch_id)["status"].get("current_state") != "ACTIVE":
        if time.time() - t0 > 600: raise TimeoutError(branch_id)
        time.sleep(3)
    return time.time() - t0


def delete_branch(branch_id):
    cli("postgres", "delete-branch", f"{PROJECT}/branches/{branch_id}")


def release_compute(branch_id):
    """keep the branch (the audit record of the trial) but disable its compute: active endpoints are capped per project
    and read-write endpoints cannot be deleted"""
    ep = endpoint(branch_id)
    if ep: cli("postgres", "update-endpoint", ep["name"], "spec.disabled", "--json", '{"spec":{"disabled":true}}')
