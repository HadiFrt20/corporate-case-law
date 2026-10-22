"""The CCL method under research. THIS is the only file the autoresearch loop edits.

build_law(view, X, m) receives the past as the firm knew it at decision month m (rows with month < m,
no ground truth, renewal outcomes only where knowable before m: column outcome_known) and returns the law
for month m: a list of holdings in ccl_sim's rule schema, e.g.
  {"kind": "loosen", "lits": ["segment = 'ENT'", "competitor"], "cap": 30.0}
The frozen harness applies the law with ccl_sim.apply and scores it. The method is never told the world,
the rogue effect or the seed.

Baseline (v5.1 CCL): beam miner on months m-12..m-3, moot court on m-2..m-1, scoped outcome screen.
"""
import ccl_sim as C

MINER, ADM, LAW_REF = "beam", 2, "scoped"


def build_law(view, X, m):
    win = view.month >= m - 12
    mw, aw = win & (view.month < m - ADM), win & (view.month >= m - ADM)
    hs = C.moot_court(C.mine(view[mw], X[mw], MINER), view[aw], X[aw])
    C.LAW_REF = LAW_REF
    judged = C.good_law(hs, view, X, now=m)
    return [h for h in judged if h["outcome"] not in ("bad", "quarantined_no_controls")]
