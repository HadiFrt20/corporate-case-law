"""CCL on REAL decisions: one US lender's mortgage decisions (HMDA public LAR, 2018-2023).

statute   = the written Qualified Mortgage debt-to-income cap: approve iff DTI <= 43% (General QM; the cap was
            replaced by a price-based test from 2021, mandatory Oct 2022, so the written policy itself changes mid-history)
decision  = action_taken (1 originated vs 3 denied)
residual  = approvals above 43% DTI (tacit loosening) and denials at or below 43% (tacit tightening)
because   = HMDA denial-reason codes on the cases a tightening holding decides
time      = activity year (yearly replay: mine on t-3..t-2, admit on t-1, test on t)
protected = race / ethnicity / sex / age are EXCLUDED from mining and used only for a disparate-impact audit of each holding
No downstream outcome exists in HMDA, so the bad-law filter cannot run here; the fairness audit is the governance check.
"""
import json, os, sys, time
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(os.path.dirname(HERE)))
import ccl_sim as C

LENDER = "6BYL5QZYBDK8S7L73M02"  # U.S. Bank National Association (public LEI)
YEARS = list(range(2018, 2024)); QM_DTI = 43.0
DENIAL = {1: "debt-to-income", 2: "employment history", 3: "credit history", 4: "collateral", 5: "insufficient cash",
          6: "unverifiable information", 7: "application incomplete", 8: "mortgage insurance denied", 9: "other"}
AUS = {"1": "DU", "2": "LP", "3": "TOTAL", "4": "GUS", "5": "other", "6": "none", "7": "internal"}


def dti(v):
    v = str(v)
    m = {"<20%": 15, "20%-<30%": 25, "30%-<36%": 33, "50%-60%": 55, ">60%": 65}
    if v in m: return float(m[v])
    try: return float(v)
    except ValueError: return np.nan


def num(s):
    return pd.to_numeric(s, errors="coerce")


def load(year):
    d = pd.read_csv(os.path.join(HERE, "raw", f"usb_{year}.csv"), low_memory=False, dtype=str)
    f = d[(d.loan_purpose == "1") & (d.loan_type == "1") & (d.lien_status == "1") & (d.occupancy_type == "1") &
          (d["open-end_line_of_credit"] == "2") & (d.reverse_mortgage == "2") & (d.business_or_commercial_purpose == "2")].copy()
    out = pd.DataFrame({
        "year": int(year), "approved": (f.action_taken == "1").values,
        "disc": f.debt_to_income_ratio.map(dti).values,               # the policy variable (named disc so the CCL miner applies unchanged)
        "ltv": num(f.loan_to_value_ratio).values, "income_k": num(f.income).values, "loan_k": num(f.loan_amount).values / 1000,
        "value_k": num(f.property_value).values / 1000, "term_m": num(f.loan_term).values,
        "aus": f["aus-1"].map(AUS).fillna("other").values, "score_model": f.applicant_credit_score_type.fillna("na").values,
        "jumbo": (f.conforming_loan_limit == "NC").values, "state": f.state_code.fillna("na").values,
        "denial1": num(f["denial_reason-1"]).values,
        "race": f.derived_race.values, "sex": f.derived_sex.values,    # audit only, never mined
    })
    out = out[out.disc.notna() & out.ltv.notna() & out.income_k.notna() & (out.income_k > 0)]
    out["statute"] = out.disc <= QM_DTI
    return out.reset_index(drop=True)


MINE_COLS = dict(cat=["aus", "score_model"], bool=["jumbo"], num=["ltv", "income_k", "loan_k", "value_k", "term_m"])
FEATS = ["disc", "ltv", "income_k", "loan_k", "value_k", "term_m", "jumbo"]


def X(d):
    return pd.concat([d[FEATS].astype(float), pd.get_dummies(d[["aus", "score_model"]]).astype(int)], axis=1)


def configure():
    C.STATUTE_CAP = QM_DTI
    C.CAPS = {"loosen": np.array([44, 45, 46, 47, 48, 49, 55, 65], float), "tighten": np.array([15, 25, 33, 36, 38, 40, 42], float)}
    C.LIT_COLS = MINE_COLS


def audit(h, d):
    """four-fifths style check: does the holding's benefit (loosen) or burden (tighten) fall unevenly across race / sex groups?"""
    m = C.fires(h, d, None) & C.scope(h, d)
    pop = (~d.statute.values) if h["kind"] == "loosen" else d.statute.values
    res = {}
    for col in ["race", "sex"]:
        rows = {}
        for g in d[col].value_counts().index[:4]:
            gm = (d[col].values == g) & pop
            if gm.sum() >= 100: rows[g] = round(float((m & gm).sum() / gm.sum()), 4)
        if rows:
            hi, lo = max(rows.values()), min(rows.values())
            res[col] = dict(rates=rows, ratio=round(lo / hi, 3) if hi else None)
    return res


def because(h, d):
    if h["kind"] != "tighten": return None
    m = C.fires(h, d, None) & C.scope(h, d) & ~d.approved.values
    vc = pd.Series(d.denial1.values[m]).map(DENIAL).value_counts(normalize=True)
    return {k: round(float(v), 3) for k, v in vc.head(3).items()}


def main():
    configure(); t0 = time.time()
    D = {y: load(y) for y in YEARS}
    S = dict(lender=LENDER, rows={y: len(d) for y, d in D.items()}, approval_rate={y: round(float(d.approved.mean()), 4) for y, d in D.items()},
             residual_rate={y: round(float((d.approved != d.statute).mean()), 4) for y, d in D.items()}, tests={})
    print(S["rows"], S["residual_rate"], flush=True)
    for t in [2021, 2022, 2023]:
        mine = pd.concat([D[y] for y in YEARS if t - 3 <= y <= t - 2], ignore_index=True)
        adm, test = D[t - 1], D[t]
        res = {}
        for miner in ["beam", "beam_power"]:
            hs = C.moot_court(C.mine(mine, None, miner), adm, None)
            p, cite = C.apply(hs, test, None)
            res[miner] = dict(acc=round(float((p == test.approved.values).mean()), 4), n_holdings=len(hs), cited=round(float((cite != "statute").mean()), 4),
                              holdings=[dict(id=h["id"], kind=h["kind"], sql=C.to_sql(h), support=h["support"], replay_prec=h["replay_prec"],
                                             because=because(h, adm), audit=audit(h, adm)) for h in hs])
        hist = pd.concat([D[y] for y in YEARS if t - 3 <= y <= t - 1], ignore_index=True)
        gbm = HistGradientBoostingClassifier(random_state=0).fit(X(hist), hist.approved)
        xt = X(test).reindex(columns=X(hist).columns, fill_value=0)
        res["statute"] = dict(acc=round(float((test.statute.values == test.approved.values).mean()), 4))
        res["gbm"] = dict(acc=round(float((gbm.predict(xt) == test.approved.values).mean()), 4))
        res["always_approve"] = dict(acc=round(float(test.approved.mean()), 4))
        S["tests"][t] = res
        print(t, {k: v["acc"] for k, v in res.items()}, round(time.time() - t0), "s", flush=True)
    json.dump(S, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
