"""Build the hard-world decision log as a CRM would actually hold it: decisions + deal-desk comments,
LATER EDITS to facts (churn flag, competitor flag), and renewal OUTCOMES that arrive at month + 12*term."""
import numpy as np, pandas as pd, os
import _sim_snapshot as S

HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "data"); os.makedirs(OUT, exist_ok=True)
REASONS = {  # ground-truth "because" per hidden rule (never shown to the LLM)
    "H1": "strategic account: enterprise logo or a 1M+ deal",
    "H2": "multi-year renewal commitment: discount scales with contract term, more if churn risk",
    "H3": "volume: large deal size justifies a moderate discount",
    "H4": "loyalty: long-tenure customer",
    "H5": "competitive displacement outside France (France has separate pricing)",
    "H6": "none given (rogue approver: vague 'my call' notes)",
    "R3": "Germany SMB margin floor set by regional finance",
}
TEMPLATES = {
    "H1": ["strategic logo, exec sponsor wants this one", "flagship enterprise account, worth the margin", "board-level deal, $1M+ ACV, approve",
           "big strategic deal, signing this matters more than margin", "enterprise reference customer, approved"],
    "H2": ["3y renewal commit, longer term earns more discount", "multi-year renewal, discount scaled to term", "they extend 2 years, ok given term",
           "renewal at risk of churn, multi-year lock-in worth it", "term commitment justifies it"],
    "H3": ["volume deal, size justifies it", "large footprint, discount ok at this size", "big order volume, approve moderate discount"],
    "H4": ["customer with us for 12 years, loyalty discount", "long-standing customer, tenure earns it", "loyal account since forever, approve"],
    "H5": ["competing against the incumbent in DE, need to win", "bake-off vs competitor in UK, match their price", "displacement deal vs competitor (US)",
           "competitive situation, not France so standard competitive grid applies"],
    "H6": ["my call", "keep them happy", "approved, I know this account", "fine", "ok go"],
    "R3": ["DE SMB margin floor, regional finance says no", "below the Germany SMB floor, rejected", "regional finance: SMB Germany max 10%"],
    "generic": ["standard approval", "within policy", "ok", "approved per guidelines", "no issues"],
    "reject": ["over policy, rejected", "too deep, no justification", "declined, above 15%", "not approved"],
}
KEY = {name: name.split(" ")[0] for name, _, _ in S.HARD_LOOSEN} | {S.TIGHT[0]: "R3"}


def comment(rng, binding, approved, statute):
    k = KEY.get(binding, None)
    if k == "R3" and not approved: pool = TEMPLATES["R3"]
    elif approved and not statute and k: pool = TEMPLATES[k]
    elif approved: pool = TEMPLATES["generic"]
    else: pool = TEMPLATES["reject"]
    r = rng.random()
    if r < 0.25: pool = TEMPLATES["generic"] if approved else TEMPLATES["reject"]  # lazy notes
    elif r < 0.33 and approved and not statute: pool = TEMPLATES[rng.choice(list(REASONS))]  # misleading note
    return pool[rng.integers(len(pool))]


def main(seed=7):
    S.set_world("hard")
    d = S.make_firm(np.random.default_rng(seed), 120000, 0.35)
    rng = np.random.default_rng(seed + 99)
    d.insert(0, "deal_id", np.arange(1, len(d) + 1))
    d["decided_at"] = pd.Timestamp("2023-01-01") + pd.to_timedelta(d.month * 30 + rng.integers(0, 28, len(d)), unit="D")
    d["comment"] = [comment(rng, b, a, s) for b, a, s in zip(d.binding, d.approved, d.statute)]
    # later edits: CRM fields change AFTER the decision (facts as of the decision differ from today's table)
    e1 = d.sample(frac=0.08, random_state=seed); e1 = pd.DataFrame(dict(deal_id=e1.deal_id, edit_month=e1.month + 2, field="churn_high", value=~e1.churn_high))
    e2 = d[d.competitor].sample(frac=0.10, random_state=seed + 1); e2 = pd.DataFrame(dict(deal_id=e2.deal_id, edit_month=e2.month + 1, field="competitor", value=False))
    edits = pd.concat([e1, e2]); edits = edits[edits.edit_month < S.MONTHS]
    outcomes = d[d.approved][["deal_id", "outcome_known_month", "renewed"]].rename(columns={"outcome_known_month": "known_month"})
    outcomes = outcomes[outcomes.known_month < S.MONTHS]
    cols = ["deal_id", "month", "decided_at", "segment", "region", "term", "renewal", "quarter_end", "competitor", "churn_high",
            "size_k", "tenure_y", "disc", "approved", "comment"]
    d[cols].to_parquet(os.path.join(OUT, "decisions.parquet"), index=False, coerce_timestamps="us", allow_truncated_timestamps=True)
    edits.to_parquet(os.path.join(OUT, "edits.parquet"), index=False)
    outcomes.to_parquet(os.path.join(OUT, "outcomes.parquet"), index=False)
    d[["deal_id", "binding", "good_decision", "statute"]].to_parquet(os.path.join(OUT, "truth_local_only.parquet"), index=False)  # never uploaded
    print(len(d), "decisions,", len(edits), "edits,", len(outcomes), "outcomes known by month 47")
    print(d.comment.value_counts().head(5).to_dict())


if __name__ == "__main__":
    main()
