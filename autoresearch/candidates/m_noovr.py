"""The CCL method under research. THIS is the only file the autoresearch loop edits.

build_law(view, X, m) receives the past as the firm knew it at decision month m (rows with month < m, deal fields,
approved, statute, outcome_known_month, renewed only where knowable before m: column outcome_known) and returns the
law for month m: a list of holdings {"kind": "loosen" | "tighten", "lits": [...], "cap": float}. It runs in its own
process (harness v2, AR-009); the harness validates the law and decides with its own rule engine.

Current method (AR-005, AR-006, AR-008, AR-010):
  - beam-search mining on the last 12 months (no moot court for mined rules)
  - overruling precedents: a stricter-law holding for a population whose above-policy approvals renew clearly worse
    than its own in-policy approvals, in every one-literal refinement of it
  - a loosening precedent is struck only when an overrule's literals are a subset of its own (logical implication:
    it can never decide differently on any case)
"""
from itertools import combinations
import numpy as np
import ccl_sim as C

MIN_SUPPORT, BEAM, MAX_RULES = 30, 60, 15
OVR_MIN_KNOWN, OVR_Z, OVR_MAX = 40, -3.0, 3


def literals(d):
    """decile thresholds, plus EVERY threshold for small integer fields (a real miner tries all of them)"""
    L = C.generic_literals(d)
    for f in ("term", "tenure_y"):
        if f in d and d[f].nunique() <= 20:
            for x in sorted(d[f].unique())[:-1]: L += [f"{f} > {x:g}", f"{f} <= {x:g}"]
    return list(dict.fromkeys(L))


def mine_beam(d, lits, min_support=60, min_prec=.9, max_rules=14, max_lits=3, beam=25):
    """ccl_sim.mine_beam with the candidate literals passed in (no monkeypatching the simulator, AR-007)"""
    Lm = np.array([C.literal(l, d) for l in lits]); disc, appr = d.disc.values, d.approved.values
    after = [np.array([j for j, b in enumerate(lits) if b > a], int) for a in lits]
    out = []; overridden = np.zeros(len(d), bool)
    for kind in ["tighten", "loosen"]:
        open_ = (~d.statute.values & ~overridden) if kind == "loosen" else d.statute.values.copy()
        caps, good = C._beam_caps(kind), (appr if kind == "loosen" else ~appr)
        for _ in range(max_rules):
            rows = np.flatnonzero(open_); Lo = Lm[:, rows]; W = C._cap_bins(disc[rows], good[rows], caps); Lf = Lo.astype(W.dtype)
            best, frontier = None, [((), np.arange(len(rows)))]
            for depth in range(1, max_lits + 1):
                parts = [(p, C._score_children(Lf, W, pr, after[combo[-1]] if combo else np.arange(len(lits)), depth, kind, min_support, min_prec))
                         for p, (combo, pr) in enumerate(frontier) if not combo or len(after[combo[-1]])]
                if not parts: break
                pid = np.concatenate([np.full(len(s[0]), p) for p, s in parts])
                lit, gain, j, n, g, has, pur = (np.concatenate(a) for a in zip(*(s for _, s in parts)))
                order = np.lexsort((-pur, -gain))
                for i in order[:5]:
                    if has[i] and (best is None or gain[i] > best[0]):
                        best = (gain[i], frontier[pid[i]][0] + (lit[i],), caps[j[i]], int(n[i]), g[i] / n[i])
                top = order[np.argsort(-pur[order], kind="stable")][:beam]
                frontier = [(frontier[pid[i]][0] + (lit[i],), frontier[pid[i]][1][Lo[lit[i], frontier[pid[i]][1]]]) for i in top]
            if best is None or best[0] <= 0: break
            _, combo, cap, n, prec = best
            h = dict(kind=kind, lits=[lits[k] for k in combo], cap=float(cap), support=n)
            out.append(h); f = C.fires(h, d, None); open_ = open_ & ~f
            if kind == "tighten": overridden |= f
    return out


def pair_refinements(view, lits):
    """conjunctions of two categorical / boolean literals (no negations, no thresholds): joint confounders such as a
    segment x region book are invisible to one-literal refinements (Astra round 1, point 5.1)"""
    base = [l for l in lits if (" = '" in l) or l in ("renewal", "quarter_end", "competitor", "churn_high")]
    m = {l: C.literal(l, view) for l in base}
    return {f"{a} AND {b}": m[a] & m[b] for a, b in combinations(base, 2) if a.split(" = ")[0] != b.split(" = ")[0]}


def homogeneous(ls, P, masks, known, ren, st, taken, min_n=20, z_fail=2.0):
    """compare like with like: reject the population if some one-literal refinement shows SIGNIFICANT evidence that its
    drop is smaller than the harm threshold (a statistical test, so sampling noise in small cells does not veto a real
    effect, and a heterogeneous population is still caught; AR-012)"""
    for q, Q in masks.items():
        if q in ls or any(part in ls for part in q.split(" AND ")): continue
        for side in (P & Q, P & ~Q):
            a = known & side & ~st & ~taken; b = known & side & st & ~taken
            na, nb = a.sum(), b.sum()
            if na < min_n or nb < min_n: continue
            pa, pb = ren[a].mean(), ren[b].mean()
            se = np.sqrt(max(pa * (1 - pa) / na + pb * (1 - pb) / nb, 1e-9))
            if (pa - pb + C.HARM_DROP) / se > z_fail: return False
    return True


def overrules(view, lits):
    """stricter-law holdings from outcomes: above-policy approvals vs in-policy approvals in the SAME population"""
    known, ren, st = view.outcome_known.values, view.renewed.values, view.statute.values
    masks = {l: C.literal(l, view) for l in lits}
    pops = [((l,), masks[l]) for l in lits] + [((a, b), masks[a] & masks[b]) for a, b in combinations(lits, 2)]
    refine = dict(masks, **pair_refinements(view, lits))
    out, taken = [], np.zeros(len(view), bool)
    for _ in range(OVR_MAX):
        best = None
        for ls, P in pops:
            a = known & P & ~st & ~taken; b = known & P & st & ~taken     # both arms exclude already-overruled rows
            na, nb = a.sum(), b.sum()
            if na < OVR_MIN_KNOWN or nb < OVR_MIN_KNOWN: continue
            lift = ren[a].mean() - ren[b].mean()
            if lift > -C.HARM_DROP: continue
            p = (ren[a].sum() + ren[b].sum()) / (na + nb); z = lift / np.sqrt(max(p * (1 - p) * (1 / na + 1 / nb), 1e-9))
            if z <= OVR_Z and (best is None or z < best[0]) and homogeneous(ls, P, refine, known, ren, st, taken): best = (z, ls, P)
        if best is None: break
        out.append({"kind": "tighten", "lits": list(best[1]), "cap": C.STATUTE_CAP})
        taken |= best[2]
    return out


def build_law(view, X, m):
    recent = view[view.month >= m - 12]
    hs = mine_beam(recent, literals(recent), min_support=MIN_SUPPORT, beam=BEAM)
    ovr_all = []   # CANDIDATE: no overrules
    for k in range(len(ovr_all), -1, -1):      # choose the overrules that fit FIRST, then strike only against those (AR-010)
        ovr = ovr_all[:k]
        law = [h for h in hs if not (h["kind"] == "loosen" and any(set(o["lits"]) <= set(h["lits"]) for o in ovr))] + ovr
        if len(law) <= MAX_RULES: return law
    return hs[:MAX_RULES]
