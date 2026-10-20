"""CCL on REAL decisions: one US lender's mortgage decisions (HMDA public LAR, 2018-2023). EXPLORATORY study.

reference = a fixed 43% debt-to-income HEURISTIC (approve iff DTI <= 43). It is NOT the lender's approval policy: the General QM
            43% cap is an eligibility condition, it was replaced by a price-based test from 2021 (mandatory Oct 2022), and real
            underwriting uses many criteria. Residual rules mined against it are predictive associations, not verified tacit policy.
decision  = action_taken 1 (originated) vs 3 (denied); asserted on the raw files (the download filtered actions_taken=1,3)
time      = activity year: mine on t-3..t-2, admit on t-1, test on t
protected = race / sex are EXCLUDED from mining; the audit evaluates the FINAL system's decisions per group
No outcomes and no credit scores exist in HMDA: the outcome screen cannot run and most within-heuristic denials are unexplainable.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import ccl_sim as C

LENDER = "6BYL5QZYBDK8S7L73M02"  # U.S. Bank National Association (public LEI)
YEARS = list(range(2018, 2024)); HEURISTIC_DTI = 43.0; B = 2000
DENIAL = {1: "debt-to-income", 2: "employment history", 3: "credit history", 4: "collateral", 5: "insufficient cash",
          6: "unverifiable information", 7: "application incomplete", 8: "mortgage insurance denied", 9: "other"}
AUS = {"1": "DU", "2": "LP", "3": "TOTAL", "4": "GUS", "5": "other", "6": "none", "7": "internal"}
GBM_GRID = [dict(max_depth=None, learning_rate=0.1, max_iter=100), dict(max_depth=6, learning_rate=0.05, max_iter=300),
            dict(max_depth=None, learning_rate=0.05, max_iter=300), dict(max_depth=4, learning_rate=0.1, max_iter=200)]


def dti(v):
    v = str(v); m = {"<20%": 15, "20%-<30%": 25, "30%-<36%": 33, "50%-60%": 55, ">60%": 65}
    if v in m: return float(m[v])
    try: return float(v)
    except ValueError: return np.nan


num = lambda s: pd.to_numeric(s, errors="coerce")


def load(year, flow):
    d = pd.read_csv(os.path.join(HERE, "raw", f"usb_{year}.csv"), low_memory=False, dtype=str)
    assert set(d.action_taken.unique()) <= {"1", "3"}, f"{year}: unexpected action codes {set(d.action_taken.unique())}"
    f = d[(d.loan_purpose == "1") & (d.loan_type == "1") & (d.lien_status == "1") & (d.occupancy_type == "1") &
          (d["open-end_line_of_credit"] == "2") & (d.reverse_mortgage == "2") & (d.business_or_commercial_purpose == "2")].copy()
    out = pd.DataFrame({
        "year": int(year), "approved": (f.action_taken == "1").values, "disc": f.debt_to_income_ratio.map(dti).values,
        "ltv": num(f.loan_to_value_ratio).values, "income_k": num(f.income).values, "loan_k": num(f.loan_amount).values / 1000,
        "value_k": num(f.property_value).values / 1000, "term_m": num(f.loan_term).values,
        "aus": f["aus-1"].map(AUS).fillna("other").values, "score_model": f.applicant_credit_score_type.fillna("na").values,
        "jumbo": (f.conforming_loan_limit == "NC").values, "state": f.state_code.fillna("na").values,
        "denial1": num(f["denial_reason-1"]).values, "race": f.derived_race.values, "sex": f.derived_sex.values})
    complete = out.disc.notna() & out.ltv.notna() & out.income_k.notna() & (out.income_k > 0)
    flow[year] = dict(raw=len(d), raw_approval=round(float((d.action_taken == "1").mean()), 4), cohort=len(out),
                      cohort_approval=round(float(out.approved.mean()), 4), complete=int(complete.sum()),
                      complete_approval=round(float(out.approved[complete].mean()), 4),
                      dropped_by_race={g: int(((~complete) & (out.race == g)).sum()) for g in out.race.value_counts().index[:4]})
    out = out[complete].reset_index(drop=True); out["statute"] = out.disc <= HEURISTIC_DTI
    return out


COLS_ALL = dict(cat=["aus", "score_model"], bool=["jumbo"], num=["ltv", "income_k", "loan_k", "value_k", "term_m"])
COLS_NOWF = dict(cat=[], bool=["jumbo"], num=["ltv", "income_k", "loan_k", "value_k", "term_m"])  # no workflow-sensitive fields


def X(d, wf=True):
    base = d[["disc", "ltv", "income_k", "loan_k", "value_k", "term_m", "jumbo"]].astype(float)
    return pd.concat([base, pd.get_dummies(d[["aus", "score_model"]]).astype(int)], axis=1) if wf else base


def configure(cols):
    C.STATUTE_CAP = HEURISTIC_DTI
    C.CAPS = {"loosen": np.array([44, 45, 46, 47, 48, 49, 55, 65], float), "tighten": np.array([15, 25, 33, 36, 38, 40, 42], float)}
    C.LIT_COLS = cols


def metrics(p, d):
    y = d.approved.values; p = np.asarray(p, bool); deny_p, deny_y = ~p, ~y
    tp = (deny_p & deny_y).sum()
    return dict(acc=float((p == y).mean()), bal_acc=float(((p & y).sum() / y.sum() + tp / deny_y.sum()) / 2),
                deny_precision=float(tp / deny_p.sum()) if deny_p.sum() else float("nan"), deny_recall=float(tp / deny_y.sum()))


def cluster_ci(pa, pb, d, label):
    """paired bootstrap over STATES (cluster), accuracy(a) - accuracy(b): pointwise 95% percentile interval, CONDITIONAL on the fitted and
    selected models (no training/selection uncertainty). Deterministic seed per comparison; cluster diagnostics returned."""
    rng = np.random.default_rng(int.from_bytes(label.encode()[:8].ljust(8, b"0"), "little") % (2 ** 32))
    y = d.approved.values; da = (np.asarray(pa, bool) == y).astype(float) - (np.asarray(pb, bool) == y).astype(float)
    st = d.state.values; groups = {s: np.flatnonzero(st == s) for s in np.unique(st)}; keys = list(groups); diffs = []
    for _ in range(B):
        idx = np.concatenate([groups[k] for k in rng.choice(keys, len(keys), replace=True)]); diffs.append(da[idx].mean())
    sizes = np.array([len(v) for v in groups.values()])
    return [float(da.mean()), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5)), dict(n_states=len(keys), largest_state_share=float(sizes.max() / sizes.sum()))]


def group_audit(p, d):
    """final-system decisions per race / sex group: approval rate, and errors vs the lender's own decisions"""
    out = {}; y = d.approved.values; p = np.asarray(p, bool)
    for col in ["race", "sex"]:
        rows = {}
        for g in d[col].value_counts().index:
            m = d[col].values == g
            if m.sum() < 200: continue
            rows[g] = dict(n=int(m.sum()), approval=round(float(p[m].mean()), 4), false_denial=round(float((~p[m] & y[m]).sum() / max(1, y[m].sum())), 4),
                           false_approval=round(float((p[m] & ~y[m]).sum() / max(1, (~y[m]).sum())), 4))
        ap = [v["approval"] for v in rows.values()]
        out[col] = dict(groups=rows, approval_ratio=round(min(ap) / max(ap), 3) if ap else None)
    return out


def because(h, d, eff):
    """recorded denial reasons on the denials a tightening holding decides: descriptive provenance with its denominator and missingness"""
    if h["kind"] != "tighten": return None
    m = eff[h["id"]] & ~d.approved.values
    r = pd.Series(d.denial1.values[m]).map(DENIAL); n_known = int(r.notna().sum())
    vc = r.value_counts(normalize=True)
    return dict(n_denials=int(m.sum()), n_with_reason=n_known, top={k: round(float(v), 3) for k, v in vc.head(3).items()})


def best_threshold(d):
    cs = np.arange(30, 66); return float(cs[np.argmax([((d.disc.values <= c) == d.approved.values).mean() for c in cs])])


def tuned_gbm(train, select, wf):
    xs = X(train, wf); scores = []
    for g in GBM_GRID:
        m = HistGradientBoostingClassifier(random_state=0, **g).fit(xs, train.approved)
        scores.append(((m.predict(X(select, wf).reindex(columns=xs.columns, fill_value=0)) == select.approved.values).mean()))
    return GBM_GRID[int(np.argmax(scores))]


def main():
    t0 = time.time(); flow = {}
    D = {y: load(y, flow) for y in YEARS}
    S = dict(lender=LENDER, cohort_flow=flow, residual_rate={y: round(float((d.approved != d.statute).mean()), 4) for y, d in D.items()}, tests={})
    for t in [2021, 2022, 2023]:
        mine = pd.concat([D[y] for y in YEARS if t - 3 <= y <= t - 2], ignore_index=True); adm, test = D[t - 1], D[t]
        hist = pd.concat([mine, adm], ignore_index=True); res = {}; preds = {}
        for wf, cols in [(True, COLS_ALL), (False, COLS_NOWF)]:
            configure(cols); tag = "" if wf else "_noworkflow"
            for miner in ["beam", "beam_power"]:
                hs = C.moot_court(C.mine(mine, None, miner), adm, None)
                p, cite = C.apply(hs, test, None); eff = C.effective(hs, adm, None); preds[miner + tag] = p
                adm_acc = float((C.apply(hs, adm, None)[0] == adm.approved.values).mean())
                res[miner + tag] = dict(**metrics(p, test), admission_acc=adm_acc, n_holdings=len(hs), cited=float((cite != "statute").mean()), audit=group_audit(p, test),
                                        holdings=[dict(id=h["id"], kind=h["kind"], sql=C.to_sql(h), support=h["support"], replay_prec=h["replay_prec"],
                                                       replay_n=h.get("replay_n"), because=because(h, adm, eff)) for h in hs])
            # implemented selection rule: the CCL variant with the higher ADMISSION-year accuracy (test labels never enter it; the rule itself
            # was chosen retrospectively, after these years had been examined)
            pick = max(["beam" + tag, "beam_power" + tag], key=lambda k: res[k]["admission_acc"]); res["ccl_selected" + tag] = dict(res[pick], variant=pick); preds["ccl_selected" + tag] = preds[pick]
            g = tuned_gbm(mine, adm, wf)
            gb = HistGradientBoostingClassifier(random_state=0, **g).fit(X(hist, wf), hist.approved)
            pg = gb.predict(X(test, wf).reindex(columns=X(hist, wf).columns, fill_value=0)); preds["gbm_tuned" + tag] = pg
            res["gbm_tuned" + tag] = dict(**metrics(pg, test), config=g, audit=group_audit(pg, test))
            res["ci_ccl_selected_minus_gbm_tuned" + tag] = cluster_ci(preds["ccl_selected" + tag], pg, test, f"{t}-gbm{tag}")
        c_ = best_threshold(hist); pt = test.disc.values <= c_
        res["learned_threshold"] = dict(**metrics(pt, test), threshold=c_, audit=group_audit(pt, test))
        res["heuristic_43"] = dict(**metrics(test.statute.values, test), audit=group_audit(test.statute.values, test))
        res["always_approve"] = dict(**metrics(np.ones(len(test), bool), test))
        res["ci_ccl_selected_minus_learned_threshold"] = cluster_ci(preds["ccl_selected"], pt, test, f"{t}-cutoff")
        S["tests"][t] = res
        print(t, {k: round(v["acc"], 4) for k, v in res.items() if isinstance(v, dict) and "acc" in v}, round(time.time() - t0), "s", flush=True)
    C.reset_config()
    json.dump(S, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
