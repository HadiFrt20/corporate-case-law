"""Corporate Case Law (CCL) falsification test on a synthetic firm with PLANTED tacit rules.

Question: can 'tacit knowledge = residual of written policy' be mined from decision exhaust,
admitted only via point-in-time replay, kept alive by decay, and filtered by outcome?
Baselines: statute only (= perfect RAG over the policy doc), gradient boosting (static + monthly retrain).
"""
import numpy as np, pandas as pd, json, sys
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import HistGradientBoostingClassifier

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 7
MINER_ARG = sys.argv[2] if len(sys.argv) > 2 else "covering"
rng = np.random.default_rng(SEED)
N, MONTHS, NOISE = 60000, 24, 0.04

# ---------------- synthetic firm ----------------
df = pd.DataFrame({
    "month": rng.integers(0, MONTHS, N),
    "segment": rng.choice(["SMB", "MM", "ENT"], N, p=[.45, .35, .20]),
    "region": rng.choice(["FR", "DE", "UK", "US"], N),
    "term": rng.choice([1, 2, 3], N, p=[.5, .25, .25]),
    "renewal": rng.random(N) < .45,
    "quarter_end": rng.random(N) < .30,
    "competitor": rng.random(N) < .35,
    "churn_high": rng.random(N) < .25,
    "size_k": np.round(rng.lognormal(4.6, 1.0, N)),
    "disc": np.round(rng.uniform(5, 35, N), 1),
}).sort_values("month").reset_index(drop=True)

STATUTE_CAP = 15.0  # written policy: "max discount 15%"
PLANTED = {  # hidden tacit rules: name -> (mask fn, cap)
    "R1 renewal+3yr+quarter-end -> 25% (retired month 18)": (lambda d: d.renewal & (d.term == 3) & d.quarter_end & (d.month < 18), 25),
    "R2 enterprise vs competitor -> 30%": (lambda d: (d.segment == "ENT") & d.competitor, 30),
    "R4 churn-risk renewal -> 22%": (lambda d: d.churn_high & d.renewal, 22),
    "R5 deal > 500k -> 20%": (lambda d: d.size_k > 500, 20),
    "R6 UK vs competitor -> 28% (new from month 12)": (lambda d: (d.region == "UK") & d.competitor & (d.month >= 12), 28),
    "R7 US mid-market rogue approver -> 35% (BAD outcomes)": (lambda d: (d.region == "US") & (d.segment == "MM"), 35),
}
TIGHT = ("R3 Germany SMB stricter -> 10%", lambda d: (d.region == "DE") & (d.segment == "SMB"), 10)

cap = np.full(N, STATUTE_CAP)
for name, (fn, c) in PLANTED.items():
    m = fn(df).values; cap[m] = np.maximum(cap[m], c)
tm = TIGHT[1](df).values; cap[tm] = TIGHT[2]
truth = df.disc.values <= cap
flip = rng.random(N) < NOISE
df["approved"] = np.where(flip, ~truth, truth)
r7 = PLANTED["R7 US mid-market rogue approver -> 35% (BAD outcomes)"][0](df).values & (df.disc.values > STATUTE_CAP)
df["renewed"] = rng.random(N) < np.where(r7 & df.approved.values, 0.35, 0.85)  # downstream outcome
df["statute"] = df.disc <= STATUTE_CAP

CAT = ["segment", "region"]; BOOL = ["renewal", "quarter_end", "competitor", "churn_high"]; NUM = ["term", "size_k", "disc"]
def X(d):
    return pd.concat([pd.get_dummies(d[CAT]).astype(int), d[BOOL].astype(int), d[NUM]], axis=1)
XALL = X(df); FEATS = list(XALL.columns); DF = df

# ---------------- CCL: mine holdings on the residual of the statute ----------------
def leaf_rules(tree, feats):
    t = tree.tree_; out = []
    def walk(n, conds):
        if t.children_left[n] == -1:
            v = t.value[n][0]; out.append((conds, v[1] / v.sum(), int(t.n_node_samples[n]))); return
        f, th = feats[t.feature[n]], t.threshold[n]
        walk(t.children_left[n], conds + [(f, "<=", th)]); walk(t.children_right[n], conds + [(f, ">", th)])
    walk(0, []); return out

def fires(conds, Xd):
    if isinstance(conds, dict):  # schema holding
        d = DF.loc[Xd.index]; m = lit_mask(conds["lits"], d)
        return m & ((d.disc.values <= conds["cap"]) if conds["kind"] == "loosen" else (d.disc.values > conds["cap"]))
    m = np.ones(len(Xd), bool)
    for f, op, th in conds: m &= (Xd[f].values <= th) if op == "<=" else (Xd[f].values > th)
    return m

def to_sql(conds):
    if isinstance(conds, dict):
        op = "<=" if conds["kind"] == "loosen" else ">"
        return " AND ".join(conds["lits"] + [f"disc {op} {conds['cap']:.0f}"]) + ("  => APPROVE" if conds["kind"] == "loosen" else "  => REJECT")
    parts = []
    for f, op, th in conds:
        if f.split("_")[0] in CAT and f not in NUM: parts.append(f"{f.split('_',1)[0]} {'!=' if op=='<=' else '='} '{f.split('_',1)[1]}'")
        elif f in BOOL: parts.append(f"{'NOT ' if op=='<=' else ''}{f}")
        else: parts.append(f"{f} {op} {th:.1f}")
    return " AND ".join(parts)

MINER = MINER_ARG
def simplify(conds):
    lo, hi, rest = {}, {}, []
    for f, op, th in conds:
        if f in NUM:
            if op == ">": lo[f] = max(lo.get(f, -1e18), th)
            else: hi[f] = min(hi.get(f, 1e18), th)
        elif (f, op, th) not in rest: rest.append((f, op, th))
    return rest + [(f, ">", v) for f, v in lo.items()] + [(f, "<=", v) for f, v in hi.items()]

def mine(d, Xd, min_support=60, min_prec=.85, max_rules=15):
    if MINER == "schema":
        return [dict(kind=h["kind"], conds=dict(kind=h["kind"], lits=h["lits"], cap=h["cap"]), train_prec=h["train_prec"], support=h["support"]) for h in mine_schema(d)]
    """sequential covering on the statute residual: take the best rule, remove what it covers, repeat"""
    hs = []
    for kind, pop0, label in [("loosen", ~d.statute.values, d.approved.values), ("tighten", d.statute.values, ~d.approved.values)]:
        pop = pop0.copy()
        for _ in range(max_rules):
            if pop.sum() < 200 or label[pop].sum() < min_support: break
            depth = 5 if MINER == "tree" else 3
            tr = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=min_support, random_state=0).fit(Xd[pop], label[pop])
            leaves = [(c, p, n) for c, p, n in leaf_rules(tr, FEATS) if p >= min_prec and n >= min_support]
            if not leaves: break
            if MINER == "tree":
                hs += [dict(kind=kind, conds=simplify(c), train_prec=round(float(p), 3), support=n) for c, p, n in leaves]; break
            c, p, n = max(leaves, key=lambda l: l[2] * l[1])
            c = simplify(c); hs.append(dict(kind=kind, conds=c, train_prec=round(float(p), 3), support=n))
            pop &= ~fires(c, Xd)
    return hs

from itertools import combinations
def literals(d):
    L = {}
    for v in ["SMB", "MM", "ENT"]: L[f"segment = '{v}'"] = (d.segment == v).values
    for v in ["FR", "DE", "UK", "US"]: L[f"region = '{v}'"] = (d.region == v).values
    L["term = 3"] = (d.term == 3).values; L["term >= 2"] = (d.term >= 2).values
    for b in BOOL: L[b] = d[b].values.astype(bool)
    for q in [0.9, 0.95, 0.975]:
        th = float(np.quantile(d.size_k, q)); L[f"size_k > {th:.0f}"] = (d.size_k > th).values
    return L

def mine_schema(d, min_support=60, min_prec=.9, max_rules=12, max_lits=3):
    """schema-guided subgroup search: holdings have the firm's own shape  WHEN <conjunction> THEN cap = c"""
    L = literals(d); names = list(L); disc = d.disc.values; appr = d.approved.values; hs = []
    combos = [c for k in range(1, max_lits + 1) for c in combinations(range(len(names)), k)]
    masks = []
    for c in combos:
        m = np.ones(len(d), bool)
        for i in c: m &= L[names[i]]
        masks.append(m)
    for kind in ["loosen", "tighten"]:
        open_ = (~d.statute.values) if kind == "loosen" else d.statute.values
        caps = np.arange(16, 36) if kind == "loosen" else np.arange(5, 15)
        for _ in range(max_rules):
            best = None
            for c, m in zip(combos, masks):
                mm = m & open_
                if mm.sum() < min_support: continue
                for cap in caps:
                    h = mm & ((disc <= cap) if kind == "loosen" else (disc > cap))
                    n = h.sum()
                    if n < min_support: continue
                    good = (appr[h] if kind == "loosen" else ~appr[h]).sum()
                    if good / n < min_prec: continue
                    gain = 2 * good - n - 3 * len(c)  # net accuracy gain vs statute, small length penalty
                    if best is None or gain > best[0]: best = (gain, c, cap, n, good / n, h)
            if best is None or best[0] <= 0: break
            gain, c, cap, n, prec, h = best
            hs.append(dict(kind=kind, lits=[names[i] for i in c], cap=float(cap), support=int(n), train_prec=round(float(prec), 3)))
            open_ = open_ & ~h
    return hs

def lit_mask(lits, d):
    L = literals(d) if not hasattr(d, "_L") else d._L
    m = np.ones(len(d), bool)
    for l in lits:
        if l.startswith("size_k > "): m &= (d.size_k > float(l.split("> ")[1])).values
        else: m &= literals_one(l, d)
    return m

def literals_one(l, d):
    if " = '" in l: f, v = l.split(" = '"); return (d[f] == v.rstrip("'")).values
    if l == "term = 3": return (d.term == 3).values
    if l == "term >= 2": return (d.term >= 2).values
    return d[l].values.astype(bool)

def apply(hs, d, Xd):
    pred = d.statute.values.copy(); cite = np.array(["statute"] * len(d), dtype=object)
    for i, h in enumerate(hs):
        m = fires(h["conds"], Xd) & (d.statute.values if h["kind"] == "tighten" else ~d.statute.values)
        pred[m] = h["kind"] == "loosen"; cite[m] = f"H{i}"
    return pred, cite

def moot_court(cands, d, Xd, min_prec=.8):
    """admit a holding only if point-in-time replay on the admission window improves accuracy (greedy, regression-safe)"""
    admitted = []; base = (apply(admitted, d, Xd)[0] == d.approved.values).mean()
    for h in sorted(cands, key=lambda h: -h["support"]):
        m = fires(h["conds"], Xd) & (d.statute.values if h["kind"] == "tighten" else ~d.statute.values)
        if m.sum() < 15: continue
        prec = (d.approved.values[m] == (h["kind"] == "loosen")).mean()
        acc = (apply(admitted + [h], d, Xd)[0] == d.approved.values).mean()
        if prec >= min_prec and acc > base: admitted.append(dict(h, replay_prec=round(float(prec), 3))); base = acc
    return admitted

def good_law(hs, d, Xd, max_drop=.2):
    """outcome weighting: a loosening holding whose approvals renew much worse than statute-approved deals is 'bad law'"""
    ref = d.renewed.values[d.statute.values & d.approved.values].mean(); good, bad = [], []
    for h in hs:
        m = fires(h["conds"], Xd) & ~d.statute.values & d.approved.values
        lift = d.renewed.values[m].mean() - ref if m.sum() else 0
        (bad if h["kind"] == "loosen" and lift < -max_drop else good).append(dict(h, outcome_lift=round(float(lift), 3)))
    return good, bad

# ---------------- online evaluation: months 18..23, trailing 12-month window ----------------
res = {k: [] for k in ["statute", "gbm_static", "gbm_monthly", "ccl_nodecay", "ccl", "ccl_goodlaw"]}
tr0 = df.month < 18
gbm_static = HistGradientBoostingClassifier(random_state=0).fit(XALL[tr0], df.approved[tr0])
frozen = None; log = []
for m in range(18, MONTHS):
    win = (df.month >= m - 12) & (df.month < m); mine_w = win & (df.month < m - 2); adm_w = win & (df.month >= m - 2)
    test = (df.month == m).values; dt, Xt = df[test], XALL[test]; y = dt.approved.values
    hs = moot_court(mine(df[mine_w], XALL[mine_w]), df[adm_w], XALL[adm_w])
    good, bad = good_law(hs, df[win], XALL[win])
    if frozen is None: frozen = hs  # CCL without decay/re-mining: holdings frozen at month 18
    gbm_m = HistGradientBoostingClassifier(random_state=0).fit(XALL[win], df.approved[win])
    res["statute"].append((dt.statute.values == y).mean())
    res["gbm_static"].append((gbm_static.predict(Xt) == y).mean())
    res["gbm_monthly"].append((gbm_m.predict(Xt) == y).mean())
    res["ccl_nodecay"].append((apply(frozen, dt, Xt)[0] == y).mean())
    p, cite = apply(hs, dt, Xt); res["ccl"].append((p == y).mean())
    res["ccl_goodlaw"].append((apply(good, dt, Xt)[0] == y).mean())
    log.append(dict(month=m, admitted=len(hs), bad_law=len(bad), cited_share=float((cite != "statute").mean())))

# ---------------- rule recovery: does any admitted holding flip the SAME cases as each planted rule? ----------------
last = df.month >= 12; dl, Xl = df[last], XALL[last]
win = (df.month >= 11) & (df.month < 23)
final = moot_court(mine(df[win & (df.month < 21)], XALL[win & (df.month < 21)]), df[win & (df.month >= 21)], XALL[win & (df.month >= 21)])
final_good, final_bad = good_law(final, df[win], XALL[win])
def effect(mask_fn, c, tighten=False):
    m = mask_fn(dl).values
    return m & ((dl.disc.values > c) & dl.statute.values if tighten else (dl.disc.values > STATUTE_CAP) & (dl.disc.values <= c))
recov = {}
hmasks = [(h, fires(h["conds"], Xl) & (dl.statute.values if h["kind"] == "tighten" else ~dl.statute.values)) for h in final]
planted = {**{k: (fn, c, False) for k, (fn, c) in PLANTED.items()}, TIGHT[0]: (TIGHT[1], TIGHT[2], True)}
for name, (fn, c, t) in planted.items():
    e = effect(fn, c, t)
    best = max(((e & hm).sum() / max(1, e.sum()), (e & hm).sum() / max(1, hm.sum()), to_sql(h["conds"]), any(b["conds"] == h["conds"] for b in final_bad)) for h, hm in hmasks) if hmasks else (0, 0, "", False)
    recov[name] = dict(coverage=round(float(best[0]), 2), purity=round(float(best[1]), 2), best_holding=best[2], flagged_bad_law=bool(best[3]))

out = dict(seed=SEED, accuracy_months_18_23={k: round(float(np.mean(v)), 4) for k, v in res.items()},
           per_month={k: [round(float(x), 3) for x in v] for k, v in res.items()}, log=log, recovery=recov,
           final_holdings=[dict(id=f"H{i}", kind=h["kind"], sql=to_sql(h["conds"]), support=h["support"], replay_prec=h["replay_prec"],
                                outcome_lift=next((g["outcome_lift"] for g in final_good + final_bad if g["conds"] == h["conds"]), None))
                           for i, h in enumerate(final)])
print(json.dumps(out, indent=1))
