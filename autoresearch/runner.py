"""Untrusted host for method.py (AR-009). Runs in its own process, started by the harness with `python -I`.

Protocol: one JSON request per line on stdin {"path": <pickled view>, "m": <month>}; one JSON reply per line on the
ORIGINAL stdout {"law": [...]} or {"error": "..."}. This process never sees the firm, the seed, the world, the oracle,
or the harness's memory; whatever it does to ccl_sim stays in this process. Only plain data comes back.
"""
import importlib.util, json, os, pickle, sys

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT]
import ccl_sim as C

out = os.fdopen(os.dup(1), "w"); sys.stdout = sys.stderr      # method prints cannot corrupt the protocol
path = os.environ.get("AR_METHOD", os.path.join(HERE, "method.py"))
spec = importlib.util.spec_from_file_location("method", path); method = importlib.util.module_from_spec(spec)
sys.modules["method"] = method; spec.loader.exec_module(method)


def plain(h):
    return {"kind": h.get("kind"), "lits": list(h.get("lits", [])) if "lits" in h else None,
            "cap": float(h["cap"]) if "cap" in h else None, "other_keys": sorted(set(h) & {"ast", "conds"})}


for line in sys.stdin:
    req = json.loads(line)
    try:
        with open(req["path"], "rb") as f: v = pickle.load(f)
        law = method.build_law(v, C.features(v), int(req["m"]))
        rep = {"law": [plain(h) for h in law]}
    except Exception as e:
        rep = {"error": f"{type(e).__name__}: {e}"}
    out.write(json.dumps(rep) + "\n"); out.flush()
