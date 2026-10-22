"""The CCL method under research. THIS is the only file the autoresearch loop edits.

build_law(view, X, m) receives the past as the firm knew it at decision month m (rows with month < m,
no ground truth, renewal outcomes only where knowable before m: column outcome_known) and returns the law
for month m: a list of holdings in ccl_sim's rule schema, e.g.
  {"kind": "loosen", "lits": ["segment = 'ENT'", "competitor"], "cap": 30.0}
The frozen harness applies the law with ccl_sim.apply and scores it. The method is never told the world,
the rogue effect or the seed.

v5.1 CCL (beam miner on m-12..m-3, moot court on m-2..m-1, scoped outcome screen)
+ overruling precedents: a population whose above-policy approvals renew clearly worse than its own
  in-policy approvals gets a stricter-law holding (REJECT above policy).
"""
from itertools import combinations
import numpy as np
import ccl_sim as C

MINER, ADM, LAW_REF = "beam", 2, "scoped"
OVR_MIN_KNOWN, OVR_Z, OVR_MAX = 40, -3.0, 3


def overrules(view):
    """stricter-law holdings from outcomes: above-policy approvals vs in-policy approvals in the SAME population"""
    known, ren, st = view.outcome_known.values, view.renewed.values, view.statute.values
    lits = [l for l in C.generic_literals(view) if not l.startswith("disc")]
    masks = {l: C.literal(l, view) for l in lits}
    pops = [((l,), masks[l]) for l in lits] + [((a, b), masks[a] & masks[b]) for a, b in combinations(lits, 2)]
    out, taken = [], np.zeros(len(view), bool)
    for _ in range(OVR_MAX):
        best = None
        for ls, P in pops:
            a = known & P & ~st & ~taken; b = known & P & st
            na, nb = a.sum(), b.sum()
            if na < OVR_MIN_KNOWN or nb < OVR_MIN_KNOWN: continue
            pa, pb = ren[a].mean(), ren[b].mean(); lift = pa - pb
            if lift > -C.HARM_DROP: continue
            p = (ren[a].sum() + ren[b].sum()) / (na + nb); z = lift / np.sqrt(max(p * (1 - p) * (1 / na + 1 / nb), 1e-9))
            if z <= OVR_Z and (best is None or z < best[0]): best = (z, ls, P)
        if best is None: break
        out.append({"id": f"O{len(out)}", "kind": "tighten", "lits": list(best[1]), "cap": C.STATUTE_CAP, "support": int((best[2] & ~st).sum()), "outcome": "overrule"})
        taken |= best[2]
    return out


def build_law(view, X, m):
    win = view.month >= m - 12
    mw, aw = win & (view.month < m - ADM), win & (view.month >= m - ADM)
    hs = C.moot_court(C.mine(view[mw], X[mw], MINER), view[aw], X[aw])
    C.LAW_REF = LAW_REF
    judged = C.good_law(hs, view, X, now=m)
    law = [h for h in judged if h["outcome"] not in ("bad", "quarantined_no_controls")]
    return law + overrules(view)[: max(0, 15 - len(law))]
