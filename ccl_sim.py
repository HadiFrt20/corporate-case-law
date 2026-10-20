"""Corporate Case Law (CCL) falsification test, v2.

Synthetic firm: a written policy (max 15% discount) plus planted tacit rules, 4% decision noise.
CCL mines holdings from the residual of the policy, admits them by point-in-time replay, and filters
"bad law" using downstream outcomes that only become known after the contract term ends.

v2 fixes (from the ECC python-review, 2026-10-19):
  1. report CCL with and without the bad-law filter, and score every method against the
     policy-consistent truth (what a well-run firm decides: no rogue rule, no noise) as well as
     against the actual logged decisions
  2. renewal outcomes are only visible at month + 12 * term (no future leakage); 48-month horizon
  3. rule recovery scored on a FRESH sample, effect masks use the binding cap (R3 override respected)
  4. round-number deal-size literals, so a "> 500k" rule is reachable
  + regression-safe admission, decay tracked on a rule that is mined then retired, miner recorded in output
"""
import argparse, json
from itertools import combinations
import numpy as np, pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import HistGradientBoostingClassifier

STATUTE_CAP, NOISE, MONTHS, TEST_START = 15.0, 0.04, 48, 36
CAT, BOOL, NUM = ["segment", "region"], ["renewal", "quarter_end", "competitor", "churn_high"], ["term", "size_k", "disc"]
LOOSEN = [  # planted tacit rules: name, mask, cap
    ("R1 renewal+3yr+quarter-end <=25% (retired at month 40)", lambda d: d.renewal & (d.term == 3) & d.quarter_end & (d.month < 40), 25),
    ("R2 enterprise vs competitor <=30%", lambda d: (d.segment == "ENT") & d.competitor, 30),
    ("R4 churn-risk renewal <=22%", lambda d: d.churn_high & d.renewal, 22),
    ("R5 deal > 500k <=20%", lambda d: d.size_k > 500, 20),
    ("R6 UK vs competitor <=28% (from month 24)", lambda d: (d.region == "UK") & d.competitor & (d.month >= 24), 28),
    ("R7 US mid-market rogue approver <=35% (bad outcomes)", lambda d: (d.region == "US") & (d.segment == "MM"), 35),
]
TIGHT = ("R3 Germany SMB stricter >10% rejected", lambda d: (d.region == "DE") & (d.segment == "SMB"), 10)
ROGUE = LOOSEN[-1][0]
EASY = (LOOSEN, TIGHT)
# v3 "hard world": hidden rules OUTSIDE the v2 miner's shape (OR, term-scaled caps, odd threshold, unused field, negation)
HARD_LOOSEN = [
    ("H1 enterprise OR deal > 1M <=30% (OR-rule)", lambda d: (d.segment == "ENT") | (d.size_k > 1000), 30),
    ("H2 renewal 2-3yr: cap 15+3*term, +5 if churn risk (interaction)", lambda d: d.renewal & (d.term >= 2), lambda d: 15 + 3 * d.term.values + 5 * d.churn_high.values),
    ("H3 deal > 340k <=20% (odd threshold)", lambda d: d.size_k > 340, 20),
    ("H4 customer tenure >= 11y <=22% (field unused in v2)", lambda d: d.tenure_y >= 11, 22),
    ("H5 competitor outside France <=26% (negation)", lambda d: d.competitor & (d.region != "FR"), 26),
    ("H6 US mid-market rogue approver <=35% (bad outcomes)", lambda d: (d.region == "US") & (d.segment == "MM"), 35),
]
HARD = (HARD_LOOSEN, TIGHT)
WORLD = "easy"
def set_world(w):
    global LOOSEN, TIGHT, ROGUE, WORLD
    assert w in {"easy", "hard"}, w
    LOOSEN, TIGHT = EASY if w == "easy" else HARD; ROGUE = LOOSEN[-1][0]; WORLD = w
def cap_of(c, d):
    return np.asarray(c(d), float) if callable(c) else np.full(len(d), float(c))


def make_firm(rng, n, bad_renew, month=None):
    d = pd.DataFrame({
        "month": rng.integers(0, MONTHS, n) if month is None else np.full(n, month),
        "segment": rng.choice(["SMB", "MM", "ENT"], n, p=[.45, .35, .20]),
        "region": rng.choice(["FR", "DE", "UK", "US"], n),
        "term": rng.choice([1, 2, 3], n, p=[.5, .25, .25]),
        "renewal": rng.random(n) < .45, "quarter_end": rng.random(n) < .30,
        "competitor": rng.random(n) < .35, "churn_high": rng.random(n) < .25,
        "size_k": np.round(rng.lognormal(4.6, 1.0, n)), "disc": np.round(rng.uniform(5, 35, n), 1),
    })
    if WORLD == "hard": d["tenure_y"] = rng.integers(0, 16, n)
    d = d.sort_values("month").reset_index(drop=True)
    cap, cap_good = np.full(n, STATUTE_CAP), np.full(n, STATUTE_CAP)
    binding = np.array(["statute"] * n, dtype=object)
    for name, fn, c in LOOSEN:
        m = fn(d).values; cv = cap_of(c, d)
        up = m & (cv > cap); cap[up] = cv[up]; binding[up] = name
        if name != ROGUE: cap_good[m] = np.maximum(cap_good[m], cv[m])
    t = TIGHT[1](d).values; cap[t] = TIGHT[2]; cap_good[t] = TIGHT[2]; binding[t] = TIGHT[0]
    truth = d.disc.values <= cap
    d["approved"] = np.where(rng.random(n) < NOISE, ~truth, truth)
    d["good_decision"] = d.disc.values <= cap_good  # policy-consistent, noiseless: what a well-run firm decides
    d["binding"] = binding
    rogue = (binding == ROGUE) & d.approved.values
    d["renewed"] = rng.random(n) < np.where(rogue, bad_renew, 0.85)
    d["outcome_known_month"] = d.month + 12 * d.term  # renewal is only observable when the term ends
    d["statute"] = d.disc <= STATUTE_CAP
    return d


def features(d):
    extra = [c for c in ["tenure_y"] if c in d]
    return pd.concat([pd.get_dummies(d[CAT]).astype(int), d[BOOL].astype(int), d[NUM + extra]], axis=1)


SIZE_LITS = [100, 250, 500, 1000]
def literal(name, d):
    if " != '" in name: f, v = name.split(" != '"); return (d[f] != v.rstrip("'")).values
    if name.startswith("NOT "): return ~d[name[4:]].values.astype(bool)
    for op in [" >= ", " <= ", " > "]:
        if op in name and name.split(op)[0] in d and name.split(op)[0] not in ("term",) or (op in name and name.startswith("term") and name not in ("term >= 2",)):
            f, x = name.split(op); x = float(x)
            return (d[f] >= x).values if op == " >= " else (d[f] <= x).values if op == " <= " else (d[f] > x).values
    if " = '" in name: f, v = name.split(" = '"); return (d[f] == v.rstrip("'")).values
    if name == "term = 3": return (d.term == 3).values
    if name == "term >= 2": return (d.term >= 2).values
    if name.startswith("size_k > "): return (d.size_k > float(name.split("> ")[1])).values
    return d[name].values.astype(bool)
LITS = [f"segment = '{v}'" for v in ["SMB", "MM", "ENT"]] + [f"region = '{v}'" for v in ["FR", "DE", "UK", "US"]] + \
       ["term = 3", "term >= 2"] + BOOL + [f"size_k > {s}" for s in SIZE_LITS]


def generic_literals(d):
    """every condition a real miner would try: category = / !=, boolean / NOT, numeric > and <= at deciles + round sizes"""
    L = []
    for f in CAT:
        for v in sorted(d[f].unique()): L += [f"{f} = '{v}'", f"{f} != '{v}'"]
    for f in BOOL: L += [f, f"NOT {f}"]
    for f in ["term", "size_k", "tenure_y"]:
        if f not in d: continue
        qs = sorted({float(np.round(np.quantile(d[f], q))) for q in np.arange(.1, 1, .1)} | ({100, 250, 500, 1000} if f == "size_k" else set()))
        for x in qs: L += [f"{f} > {x:g}", f"{f} <= {x:g}"]
    return list(dict.fromkeys(L))


def fires(h, d, Xd):
    """raw firing mask of a holding (before restricting to the population it is allowed to change)"""
    if "lits" in h:
        m = np.ones(len(d), bool)
        for l in h["lits"]: m &= literal(l, d)
        return m & ((d.disc.values <= h["cap"]) if h["kind"] == "loosen" else (d.disc.values > h["cap"]))
    m = np.ones(len(d), bool)
    for f, op, th in h["conds"]: m &= (Xd[f].values <= th) if op == "<=" else (Xd[f].values > th)
    return m


def scope(h, d):
    """loosening holdings may only change policy rejections; stricter law (tightening) overrides ANY approval,
    including one granted by a loosening holding (v3 fix: v2 let loosening approvals escape the stricter rule)"""
    return ~d.statute.values if h["kind"] == "loosen" else np.ones(len(d), bool)


def to_sql(h):
    if "lits" in h:
        op = "<=" if h["kind"] == "loosen" else ">"
        bound = [] if abs(h["cap"]) >= 1e8 else [f"disc {op} {h['cap']:.0f}"]  # rebuilt holdings carry disc bounds as literals
        return " AND ".join(h["lits"] + bound) + ("  => APPROVE" if h["kind"] == "loosen" else "  => REJECT")
    parts = []
    for f, op, th in h["conds"]:
        if f.split("_")[0] in CAT and f not in NUM: parts.append(f"{f.split('_', 1)[0]} {'!=' if op == '<=' else '='} '{f.split('_', 1)[1]}'")
        elif f in BOOL: parts.append(("NOT " if op == "<=" else "") + f)
        else: parts.append(f"{f} {op} {th:.1f}")
    return " AND ".join(parts) + ("  => APPROVE" if h["kind"] == "loosen" else "  => REJECT")


# ---------------- miners ----------------
def mine_schema(d, min_support=60, min_prec=.9, max_rules=12, max_lits=3):
    """schema-guided subgroup search: WHEN <conjunction of literals> THEN cap = c, greedy cover of the residual"""
    L = {l: literal(l, d) for l in LITS}; disc, appr = d.disc.values, d.approved.values
    combos = [c for k in range(1, max_lits + 1) for c in combinations(LITS, k)]
    masks = []
    for c in combos:
        m = np.ones(len(d), bool)
        for l in c: m &= L[l]
        masks.append(m)
    out = []
    overridden = np.zeros(len(d), bool)  # cases a stricter (tightening) holding already decides
    for kind in ["tighten", "loosen"]:  # stricter law first: loosening precision ignores cases it can never decide
        open_ = (~d.statute.values & ~overridden) if kind == "loosen" else d.statute.values.copy()
        caps = np.arange(16, 36, dtype=float) if kind == "loosen" else np.arange(5, 15, dtype=float)
        for _ in range(max_rules):
            best = None
            for c, m in zip(combos, masks):
                idx = np.flatnonzero(m & open_)
                if len(idx) < min_support: continue
                o = np.argsort(disc[idx]); ds = disc[idx][o]; good = (appr[idx][o] if kind == "loosen" else ~appr[idx][o]).astype(int)
                cg = np.concatenate([[0], np.cumsum(good)])
                if kind == "loosen":
                    k = np.searchsorted(ds, caps, "right"); n = k; g = cg[k]
                else:
                    k = np.searchsorted(ds, caps, "right"); n = len(ds) - k; g = cg[-1] - cg[k]
                ok = (n >= min_support) & (g >= min_prec * np.maximum(n, 1))
                if not ok.any(): continue
                gain = np.where(ok, 2 * g - n - 3 * len(c), -1e9); j = int(np.argmax(gain))
                if best is None or gain[j] > best[0]: best = (gain[j], c, caps[j], int(n[j]), g[j] / n[j])
            if best is None or best[0] <= 0: break
            _, c, cap, n, prec = best
            h = dict(kind=kind, lits=list(c), cap=float(cap), support=n, train_prec=round(float(prec), 3))
            out.append(h); f = fires(h, d, None); open_ = open_ & ~f
            if kind == "tighten": overridden |= f & ~d.statute.values | lit_only(h, d) & (d.disc.values > h["cap"])
    return out


def lit_only(h, d):
    m = np.ones(len(d), bool)
    for l in h["lits"]: m &= literal(l, d)
    return m


def _beam_caps(kind):
    return np.arange(16, 36, dtype=float) if kind == "loosen" else np.arange(5, 15, dtype=float)


def _cap_bins(disc, good, caps):
    """one-hot row -> discount bin (all cases, then good cases); bin b holds caps[b-1] < disc <= caps[b]"""
    n, nb = len(disc), len(caps) + 1; b = np.searchsorted(caps, disc, "left")
    W = np.zeros((n, 2 * nb), np.float32 if n < 2 ** 24 else np.float64)  # float32 sums of 0/1 are exact below 2**24
    W[np.arange(n), b] = 1; W[np.flatnonzero(good), nb + b[good]] = 1
    return W


def _best_cap(n_le, g_le, n_tot, g_tot, kind, nlits, min_support, min_prec):
    """vectorised over candidates: n_le / g_le[i, j] = cases / good cases of candidate i with disc <= caps[j].
    returns (gain, cap index, n, g, has_cap) per candidate, first-best cap on ties as np.argmax"""
    n, g = (n_le, g_le) if kind == "loosen" else (n_tot[:, None] - n_le, g_tot[:, None] - g_le)
    ok = (n >= min_support) & (g >= min_prec * np.maximum(n, 1))
    gain = np.where(ok, 2 * g - n - 3 * nlits, -1e9); j = gain.argmax(1); r = np.arange(len(j))
    return gain[r, j], j, n[r, j], g[r, j], ok.any(1)


def _score_children(Lf, W, rows, cand, depth, kind, min_support, min_prec):
    """score parent AND lit for every candidate lit at once: per-bin counts from one matmul, no sort per candidate"""
    H = np.rint(Lf[np.ix_(cand, rows)] @ W[rows]).astype(np.int64); nb = W.shape[1] // 2
    n_tot, g_tot = H[:, :nb].sum(1), H[:, nb:].sum(1); keep = n_tot >= min_support
    H, n_tot, g_tot = H[keep], n_tot[keep], g_tot[keep]
    gain, j, n, g, has = _best_cap(H[:, :nb - 1].cumsum(1), H[:, nb:-1].cumsum(1), n_tot, g_tot, kind, depth, min_support, min_prec)
    return cand[keep], np.where(has, gain, -1e9), j, n, g, has, g_tot / n_tot


def mine_beam(d, min_support=60, min_prec=.9, max_rules=14, max_lits=3, beam=25):
    """beam-search subgroup discovery over GENERIC literals built from the data (no hand-picked schema)"""
    lits = generic_literals(d); Lm = np.array([literal(l, d) for l in lits]); disc, appr = d.disc.values, d.approved.values
    after = [np.array([j for j, b in enumerate(lits) if b > a], int) for a in lits]  # combos grow in increasing string order
    out = []; overridden = np.zeros(len(d), bool)
    for kind in ["tighten", "loosen"]:
        open_ = (~d.statute.values & ~overridden) if kind == "loosen" else d.statute.values.copy()
        caps, good = _beam_caps(kind), (appr if kind == "loosen" else ~appr)
        for _ in range(max_rules):
            rows = np.flatnonzero(open_); Lo = Lm[:, rows]; W = _cap_bins(disc[rows], good[rows], caps); Lf = Lo.astype(W.dtype)
            best, frontier = None, [((), np.arange(len(rows)))]  # (combo of lit indices, open rows it covers)
            for depth in range(1, max_lits + 1):
                parts = [(p, _score_children(Lf, W, pr, after[combo[-1]] if combo else np.arange(len(lits)), depth, kind, min_support, min_prec))
                         for p, (combo, pr) in enumerate(frontier) if not combo or len(after[combo[-1]])]
                if not parts: break
                pid = np.concatenate([np.full(len(s[0]), p) for p, s in parts])
                lit, gain, j, n, g, has, pur = (np.concatenate(a) for a in zip(*(s for _, s in parts)))
                order = np.lexsort((-pur, -gain))  # stable: (gain, purity) descending, ties keep generation order
                for i in order[:5]:
                    if has[i] and (best is None or gain[i] > best[0]):
                        best = (gain[i], frontier[pid[i]][0] + (lit[i],), caps[j[i]], int(n[i]), g[i] / n[i])
                top = order[np.argsort(-pur[order], kind="stable")][:beam]
                frontier = [(frontier[pid[i]][0] + (lit[i],), frontier[pid[i]][1][Lo[lit[i], frontier[pid[i]][1]]]) for i in top]
            if best is None or best[0] <= 0: break
            _, combo, cap, n, prec = best
            h = dict(kind=kind, lits=[lits[k] for k in combo], cap=float(cap), support=n, train_prec=round(float(prec), 3))
            out.append(h); f = fires(h, d, None); open_ = open_ & ~f
            if kind == "tighten": overridden |= f
    return out


def leaf_rules(tree, feats):
    t = tree.tree_; out = []
    def walk(n, conds):
        if t.children_left[n] == -1:
            v = t.value[n][0]; out.append((conds, v[1] / v.sum(), int(t.n_node_samples[n]))); return
        f, th = feats[t.feature[n]], t.threshold[n]
        walk(t.children_left[n], conds + [(f, "<=", th)]); walk(t.children_right[n], conds + [(f, ">", th)])
    walk(0, []); return out


def simplify(conds):
    lo, hi, rest = {}, {}, []
    for f, op, th in conds:
        if f in NUM: (lo.__setitem__(f, max(lo.get(f, -1e18), th)) if op == ">" else hi.__setitem__(f, min(hi.get(f, 1e18), th)))
        elif (f, op, th) not in rest: rest.append((f, op, th))
    return rest + [(f, ">", v) for f, v in lo.items()] + [(f, "<=", v) for f, v in hi.items()]


def mine_tree(d, Xd, covering, min_support=60, min_prec=.85, max_rules=15):
    """tree: all pure leaves of one depth-5 tree; covering: best leaf of a depth-3 tree, remove covered, repeat"""
    out = []; feats = list(Xd.columns)
    for kind, pop0, label in [("loosen", ~d.statute.values, d.approved.values), ("tighten", d.statute.values, ~d.approved.values)]:
        pop = pop0.copy()
        for _ in range(max_rules if covering else 1):
            if pop.sum() < 200 or label[pop].sum() < min_support: break
            tr = DecisionTreeClassifier(max_depth=3 if covering else 5, min_samples_leaf=min_support, random_state=0).fit(Xd[pop], label[pop])
            leaves = [(simplify(c), p, n) for c, p, n in leaf_rules(tr, feats) if p >= min_prec and n >= min_support]
            if not leaves: break
            pick = [max(leaves, key=lambda l: l[2] * l[1])] if covering else leaves
            for c, p, n in pick:
                h = dict(kind=kind, conds=c, support=n, train_prec=round(float(p), 3)); out.append(h)
                pop &= ~fires(h, d, Xd)
    return out


def mine(d, Xd, miner):
    if miner == "schema": return mine_schema(d)
    if miner == "beam": return mine_beam(d)
    return mine_tree(d, Xd, covering=(miner == "covering"))


# ---------------- apply, moot court, good law ----------------
def apply(hs, d, Xd):
    """statute by default; loosening holdings may approve, tightening holdings (stricter law) win last"""
    pred = d.statute.values.copy(); cite = np.array(["statute"] * len(d), dtype=object)
    for kind in ["loosen", "tighten"]:
        for h in hs:
            if h["kind"] != kind: continue
            m = fires(h, d, Xd) & scope(h, d); pred[m] = kind == "loosen"; cite[m] = h["id"]
    return pred, cite


def moot_court(cands, d, Xd, min_prec=.8, min_n=15):
    """admit a holding only if replay accuracy on the admission window rises AND every admitted holding keeps
    its precision on the cases it actually decides (regression-safe)"""
    admitted = []; y = d.approved.values; base = (apply(admitted, d, Xd)[0] == y).mean()
    for i, h in enumerate(sorted(cands, key=lambda h: -h["support"])):
        h = dict(h, id=f"H{i}")
        trial = admitted + [h]; pred, cite = apply(trial, d, Xd)
        acc = (pred == y).mean(); ok = acc > base
        for g in trial:
            m = cite == g["id"]
            if g is h and m.sum() < min_n: ok = False
            if m.sum() >= min_n and (pred[m] == y[m]).mean() < min_prec: ok = False
        if ok:
            m = cite == h["id"]; admitted.append(dict(h, replay_prec=round(float((pred[m] == y[m]).mean()), 3))); base = acc
    return admitted


def good_law(hs, hist, Xh, now, max_drop=.2, min_known=30):
    """outcome check using ONLY outcomes known before `now`: bad / good / pending (not enough known outcomes yet)"""
    known = hist.outcome_known_month.values < now
    ref_m = known & hist.statute.values & hist.approved.values
    ref = hist.renewed.values[ref_m].mean() if ref_m.sum() else np.nan
    out = []
    for h in hs:
        if h["kind"] == "tighten": out.append(dict(h, outcome="n/a", outcome_lift=None)); continue
        m = fires(h, hist, Xh) & scope(h, hist) & hist.approved.values & known
        if m.sum() < min_known or np.isnan(ref): out.append(dict(h, outcome="pending", outcome_lift=None, outcome_n=int(m.sum()))); continue
        lift = float(hist.renewed.values[m].mean() - ref)
        out.append(dict(h, outcome="bad" if lift < -max_drop else "good", outcome_lift=round(lift, 3), outcome_n=int(m.sum())))
    return out


# ---------------- recovery on a fresh sample ----------------
def recovery(hs, fresh, Xf, purity_min=.8, cov_min=.6):
    """a holding correctly states rule r if (almost) all cases it decides are cases where r APPLIES
    (r's conditions hold, discount within r's cap, not overridden by the stricter Germany rule)"""
    rec = {}
    t_over = TIGHT[1](fresh).values & (fresh.disc.values > TIGHT[2])
    hm = [(h, fires(h, fresh, Xf) & scope(h, fresh)) for h in hs]
    rules = [(n, fn, c, False) for n, fn, c in LOOSEN] + [(TIGHT[0], TIGHT[1], TIGHT[2], True)]
    for name, fn, c, tight in rules:
        r = fn(fresh).values
        cv = cap_of(c, fresh)
        applies = r & ((fresh.disc.values > cv) if tight else ~fresh.statute.values & (fresh.disc.values <= cv) & ~t_over)  # stricter law applies at any discount
        if applies.sum() == 0: rec[name] = dict(n_applies=0); continue
        best = dict(coverage=0.0, purity=0.0, holding=None); union = np.zeros(len(fresh), bool)
        for h, m in hm:
            decided = m & (~t_over if h["kind"] == "loosen" else True)
            if decided.sum() == 0: continue
            cov, pur = (applies & decided).sum() / applies.sum(), (applies & decided).sum() / decided.sum()
            if pur >= purity_min: union |= decided
            if cov * pur > best["coverage"] * best["purity"]: best = dict(coverage=round(float(cov), 3), purity=round(float(pur), 3), holding=to_sql(h))
        rec[name] = dict(n_applies=int(applies.sum()), **best, exact=bool(best["coverage"] >= cov_min and best["purity"] >= purity_min),
                         union_coverage=round(float((applies & union).sum() / applies.sum()), 3))
    return rec


def run(seed, miner, bad_renew, world="easy"):
    assert miner in {"schema", "tree", "covering", "beam"}, miner
    set_world(world)
    rng = np.random.default_rng(seed)
    df = make_firm(rng, 120000, bad_renew); X = features(df)
    fresh = make_firm(np.random.default_rng(seed + 1000), 60000, bad_renew, month=TEST_START - 1); Xf = features(fresh)[X.columns]
    fresh_r1 = fresh  # month 35: R1 active, R6 active
    methods = ["statute", "gbm_static", "gbm_monthly", "gbm_outcome", "gbm_uplift", "ccl", "ccl_goodlaw"]
    acc = {k: {"actual": [], "good": [], "n": []} for k in methods}
    static = HistGradientBoostingClassifier(random_state=0).fit(X[df.month < TEST_START], df.approved[df.month < TEST_START])
    log, snapshots = [], {}
    r1_name = LOOSEN[0][0]
    for m in range(TEST_START, MONTHS):
        win = (df.month >= m - 12) & (df.month < m); mw = win & (df.month < m - 2); aw = win & (df.month >= m - 2)
        hs = moot_court(mine(df[mw], X[mw], miner), df[aw], X[aw])
        hist = df.month < m
        judged = good_law(hs, df[hist], X[hist], now=m)
        good = [h for h in judged if h["outcome"] != "bad"]
        gbm = HistGradientBoostingClassifier(random_state=0).fit(X[win], df.approved[win])
        # fairer baseline: a black box that also sees known outcomes (approved but known not to renew -> label "should reject")
        # outcomes inside the trailing 12 months are never known yet, so this baseline trains on 24 months of history
        known_bad = (df.outcome_known_month < m) & ~df.renewed; win24 = (df.month >= m - 24) & (df.month < m)
        gbm_o = HistGradientBoostingClassifier(random_state=0).fit(X[win24], (df.approved & ~known_bad)[win24])
        # strongest black box: same information and same 0.20 threshold as the bad-law filter, no rules.
        # a renewal model on approved deals with known outcomes vetoes exceptions predicted to renew >= 0.20 worse
        kn = win24 & (df.outcome_known_month < m) & df.approved
        renew_model = HistGradientBoostingClassifier(random_state=0).fit(X[kn], df.renewed[kn])
        ref_m = kn & df.statute; ref = df.renewed[ref_m].mean()
        te = (df.month == m).values; dt, Xt = df[te], X[te]
        preds = {"statute": dt.statute.values, "gbm_static": static.predict(Xt), "gbm_monthly": gbm.predict(Xt), "gbm_outcome": gbm_o.predict(Xt),
                 "gbm_uplift": (lambda base: base & ~(base & ~dt.statute.values & (renew_model.predict_proba(Xt)[:, 1] < ref - 0.2)))(gbm.predict(Xt).astype(bool)),
                 "ccl": apply(hs, dt, Xt)[0], "ccl_goodlaw": apply(good, dt, Xt)[0]}
        for k, p in preds.items():
            acc[k]["actual"].append(float((p == dt.approved.values).mean())); acc[k]["good"].append(float((p == dt.good_decision.values).mean())); acc[k]["n"].append(int(te.sum()))
        r1 = recovery(hs, fresh_r1, Xf)[r1_name]
        log.append(dict(month=m, admitted=len(hs), bad=sum(h["outcome"] == "bad" for h in judged), pending=sum(h["outcome"] == "pending" for h in judged),
                        r1_holding_admitted=r1["exact"], rogue_flagged=any(h["outcome"] == "bad" and recovery([h], fresh, Xf)[ROGUE]["purity"] >= .8 for h in judged)))
        if m in (TEST_START, MONTHS - 1):
            snapshots[m] = dict(recovery=recovery(hs, fresh, Xf),
                                holdings=[dict(id=h["id"], kind=h["kind"], sql=to_sql(h), support=h["support"], replay_prec=h["replay_prec"],
                                               outcome=h["outcome"], outcome_lift=h.get("outcome_lift")) for h in judged])
    wavg = lambda v, n: float(np.average(v, weights=n))
    return dict(seed=seed, miner=miner, bad_renew=bad_renew, world=world,
                accuracy={k: dict(vs_actual=round(wavg(a["actual"], a["n"]), 4), vs_good=round(wavg(a["good"], a["n"]), 4)) for k, a in acc.items()},
                per_month={k: [round(x, 3) for x in a["actual"]] for k, a in acc.items()}, log=log, snapshots=snapshots)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, default=7); ap.add_argument("--miner", default="schema")
    ap.add_argument("--bad-renew", type=float, default=0.35); ap.add_argument("--world", default="easy"); ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = run(a.seed, a.miner, a.bad_renew, a.world)
    with open(a.out, "w") as f: json.dump(res, f, indent=1)
    print(a.out, res["accuracy"]["ccl"], res["accuracy"]["ccl_goodlaw"])
