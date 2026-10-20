"""Equivalence guard for the optimised beam miner: the pre-optimisation mine_beam is frozen here verbatim
(with its _best_cap and generic_literals) and must produce identical holdings on fixed-seed data."""
import sys, os
import numpy as np
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ccl_sim as c


# ---------------- frozen reference (copied from ccl_sim.py before optimisation) ----------------
def generic_literals_reference(d):
    L = []
    for f in c.CAT:
        for v in sorted(d[f].unique()): L += [f"{f} = '{v}'", f"{f} != '{v}'"]
    for f in c.BOOL: L += [f, f"NOT {f}"]
    for f in ["term", "size_k", "tenure_y"]:
        if f not in d: continue
        qs = sorted({float(np.round(np.quantile(d[f], q))) for q in np.arange(.1, 1, .1)} | ({100, 250, 500, 1000} if f == "size_k" else set()))
        for x in qs: L += [f"{f} > {x:g}", f"{f} <= {x:g}"]
    return list(dict.fromkeys(L))


def _best_cap_reference(m, open_, disc, appr, kind, nlits, min_support, min_prec):
    idx = np.flatnonzero(m & open_)
    if len(idx) < min_support: return None
    caps = np.arange(16, 36, dtype=float) if kind == "loosen" else np.arange(5, 15, dtype=float)
    o = np.argsort(disc[idx]); ds = disc[idx][o]; good = (appr[idx][o] if kind == "loosen" else ~appr[idx][o]).astype(int)
    cg = np.concatenate([[0], np.cumsum(good)]); k = np.searchsorted(ds, caps, "right")
    n, g = (k, cg[k]) if kind == "loosen" else (len(ds) - k, cg[-1] - cg[k])
    ok = (n >= min_support) & (g >= min_prec * np.maximum(n, 1))
    if not ok.any(): return None
    gain = np.where(ok, 2 * g - n - 3 * nlits, -1e9); j = int(np.argmax(gain))
    return gain[j], caps[j], int(n[j]), g[j] / n[j]


def mine_beam_reference(d, min_support=60, min_prec=.9, max_rules=14, max_lits=3, beam=25):
    lits = generic_literals_reference(d); L = {l: c.literal(l, d) for l in lits}; disc, appr = d.disc.values, d.approved.values
    out = []; overridden = np.zeros(len(d), bool)
    for kind in ["tighten", "loosen"]:
        open_ = (~d.statute.values & ~overridden) if kind == "loosen" else d.statute.values.copy()
        for _ in range(max_rules):
            best, frontier = None, [((), np.ones(len(d), bool))]
            for depth in range(1, max_lits + 1):
                scored = []
                for combo, pm in frontier:
                    for l in lits:
                        if l in combo or (combo and l < combo[-1]): continue
                        m = pm & L[l]
                        if (m & open_).sum() < min_support: continue
                        r = _best_cap_reference(m, open_, disc, appr, kind, depth, min_support, min_prec)
                        purity = (appr if kind == "loosen" else ~appr)[m & open_].mean()
                        scored.append((r[0] if r else -1e9, purity, combo + (l,), m, r))
                scored.sort(key=lambda t: (t[0], t[1]), reverse=True)
                for gsc, _, combo, m, r in scored[:5]:
                    if r and (best is None or gsc > best[0]): best = (gsc, combo, r)
                frontier = [(c, m) for _, _, c, m, _ in sorted(scored, key=lambda t: t[1], reverse=True)[:beam]]
            if best is None or best[0] <= 0: break
            _, combo, (_, cap, n, prec) = best
            h = dict(kind=kind, lits=list(combo), cap=float(cap), support=n, train_prec=round(float(prec), 3))
            out.append(h); f = c.fires(h, d, None); open_ = open_ & ~f
            if kind == "tighten": overridden |= f
    return out


# ---------------- tests ----------------
def _firm(world):
    c.set_world(world)
    return c.make_firm(np.random.default_rng(3), 25000, 0.35)


def _key(hs):
    return [(h["kind"], tuple(h["lits"]), h["cap"], h["support"], h["train_prec"]) for h in hs]


@pytest.mark.parametrize("world", ["easy", "hard"])
def test_generic_literals_match_reference(world):
    d = _firm(world)
    assert c.generic_literals(d) == generic_literals_reference(d)


@pytest.mark.parametrize("world", ["easy", "hard"])
def test_mine_beam_matches_reference(world):
    d = _firm(world)
    expected = mine_beam_reference(d)
    actual = c.mine_beam(d)
    assert expected, "reference produced no holdings; the test would be vacuous"
    assert _key(actual) == _key(expected)
    assert actual == expected  # full dicts, same order, same types-by-equality


@pytest.mark.parametrize("world", ["easy", "hard"])
@pytest.mark.parametrize("kw", [dict(beam=5), dict(min_prec=.85, min_support=30), dict(max_lits=2, max_rules=4)])
def test_mine_beam_matches_reference_off_default_params(world, kw):
    d = _firm(world)
    assert c.mine_beam(d, **kw) == mine_beam_reference(d, **kw)
