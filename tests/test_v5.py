"""v5 regression tests: one per fix from the Astra review (leakage, attribution, shadowing, controls, crashes, config, oracle)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ccl_sim as c


def firm(world="easy", n=30000, seed=2, bad=0.35, effect="segment"):
    c.set_world(world); c.ROGUE_EFFECT = effect
    return c.make_firm(np.random.default_rng(seed), n, bad)


def sig(hs, judged):
    return [(c.to_sql(h), h["replay_prec"]) for h in hs], [(c.to_sql(j), j["outcome"], j.get("outcome_lift")) for j in judged]


def test_step_ignores_everything_from_the_future():
    d = firm(n=40000); X = c.features(d); m = 36
    before = sig(*c.step(d, X, m, "beam"))
    fut = d.copy(); f = (fut.month >= m).values
    fut.loc[f, "approved"] = ~fut.loc[f, "approved"]; fut.loc[f, "renewed"] = ~fut.loc[f, "renewed"]
    fut.loc[f, "competitor"] = ~fut.loc[f, "competitor"]; fut.loc[f, "disc"] = 34.9
    after = sig(*c.step(fut, c.features(fut)[X.columns], m, "beam"))
    assert before == after


def test_step_ignores_outcomes_not_yet_known():
    d = firm(n=40000); X = c.features(d); m = 36
    before = sig(*c.step(d, X, m, "beam"))
    hid = d.copy(); unk = (hid.outcome_known_month >= m).values
    hid.loc[unk, "renewed"] = ~hid.loc[unk, "renewed"]
    assert sig(*c.step(hid, X, m, "beam")) == before


def test_outcome_rows_never_contain_unknown_outcomes():
    d = firm(n=20000); m = 36; r = c.outcome_rows(d, m).values
    assert r.sum() > 0 and (d.outcome_known_month.values[r] < m).all() and (d.month.values[r] < m).all()


def test_attribution_is_order_independent():
    d = firm(n=20000)
    hs = [dict(id="A", kind="loosen", lits=["competitor"], cap=30.0), dict(id="B", kind="loosen", lits=["segment = 'ENT'"], cap=30.0),
          dict(id="T", kind="tighten", lits=["region = 'DE'", "segment = 'SMB'"], cap=10.0)]
    e1, e2 = c.effective(hs, d, None), c.effective(list(reversed(hs)), d, None)
    assert all((e1[k] == e2[k]).all() for k in e1)
    assert not (e1["A"] & e1["T"]).any()  # stricter law removes cases from loosening attribution


def test_candidate_that_shadows_an_incumbent_is_rejected():
    d = firm(n=20000)
    incumbent = dict(kind="loosen", lits=["segment = 'ENT'", "competitor"], cap=30.0, support=500)
    shadow = dict(kind="tighten", lits=["segment = 'ENT'"], cap=5.0, support=400)  # would take over every ENT case
    adm = c.moot_court([incumbent, shadow], d, None)
    assert [h["kind"] for h in adm] == ["loosen"]


def test_scoped_screen_reports_missing_controls_instead_of_falling_back():
    d = firm(n=20000); c.LAW_REF = "scoped"
    d.loc[(d.region == "US") & d.statute, "approved"] = False  # the population has NO in-policy approved controls
    h = dict(id="X", kind="loosen", lits=["region = 'US'"], cap=30.0)
    out = c.good_law([h], d, None, now=48)
    c.LAW_REF = "global"
    assert out[0]["outcome"] == "quarantined_no_controls"


def test_tree_miner_survives_single_class_population():
    d = firm(n=5000); d["approved"] = True
    c.mine_tree(d, c.features(d), covering=True)  # used to IndexError on v[1]


def test_dataset_configuration_does_not_leak_into_simulation():
    c.STATUTE_CAP = 43.0; c.LIT_COLS = dict(cat=[], bool=[], num=[]); c.CAPS = {"loosen": np.array([44.0]), "tighten": np.array([20.0])}
    c.set_world("easy")
    assert c.STATUTE_CAP == 15.0 and c.LIT_COLS is None and c.CAPS["loosen"][0] == 16.0


def test_harm_oracle_depends_on_the_causal_mechanism():
    seg = firm(effect="segment", bad=0.35); assert not seg.harmful_if_approved.any()
    nul = firm(effect="exception", bad=0.85); assert not nul.harmful_if_approved.any()
    exc = firm(effect="exception", bad=0.35); h = exc.harmful_if_approved.values
    assert h.any() and (exc.disc.values[h] > 15).all() and not exc.harm_oracle.values[h].any()
    c.ROGUE_EFFECT = "segment"


def test_overlap_recovery_accepts_any_qualifying_candidate():
    fresh = firm(n=60000)
    good = dict(id="G", kind="loosen", lits=["segment = 'ENT'", "competitor"], cap=30.0)
    broad = dict(id="B", kind="loosen", lits=["competitor"], cap=30.0)
    rec = c.recovery([broad, good], fresh, None)["R2 enterprise vs competitor <=30%"]
    assert rec["overlap_recovered"]


# ---------------- round-2 tests (Astra re-review) ----------------
import pandas as pd


def _rows(n, **kw):
    base = dict(month=30, segment="SMB", region="FR", term=1, renewal=False, quarter_end=False, competitor=False, churn_high=False, size_k=100.0, disc=10.0, approved=True)
    base.update(kw); return pd.DataFrame([base] * n)


def test_shadowing_guard_alone_rejects_a_candidate_that_passes_every_other_gate():
    d = pd.concat([_rows(10, segment="MM", competitor=True, disc=20.0), _rows(10, segment="ENT", competitor=True, disc=20.0),
                   _rows(50, segment="ENT", disc=12.0, approved=False), _rows(100)], ignore_index=True)
    d["statute"] = d.disc <= 15; c.set_world("easy")
    inc = dict(kind="loosen", lits=["competitor"], cap=30.0, support=500)
    cand = dict(kind="tighten", lits=["segment = 'ENT'"], cap=10.0, support=400)
    # the candidate would pass the other gates: accuracy rises, precision 50/60 >= 0.8, 60 >= 15 decided cases
    p0, _ = c.apply([dict(inc, id="A")], d, None); p1, _ = c.apply([dict(inc, id="A"), dict(cand, id="T")], d, None)
    assert (p1 == d.approved.values).mean() > (p0 == d.approved.values).mean()
    eff = c.effective([dict(inc, id="A"), dict(cand, id="T")], d, None)
    assert eff["T"].sum() == 60 and (~d.approved.values[eff["T"]]).mean() >= 0.8 and eff["A"].sum() == 10
    adm = c.moot_court([inc, cand], d, None)
    assert [h["kind"] for h in adm] == ["loosen"]  # rejected ONLY because the incumbent drops from 20 to 10 decided cases


def test_recovery_requires_the_same_action():
    fresh = firm(n=60000)
    wrong_action = dict(id="T", kind="tighten", lits=["segment = 'ENT'", "competitor"], cap=5.0)
    assert not c.recovery([wrong_action], fresh, None)["R2 enterprise vs competitor <=30%"]["overlap_recovered"]


def test_harm_threshold_boundary_is_inclusive():
    d = firm(effect="exception", bad=0.65)  # 0.85 - 0.65 = 0.20 exactly: harmful by definition
    assert d.harmful_if_approved.any()
    c.ROGUE_EFFECT = "segment"


def test_error_components_sum_to_total_error():
    d = firm(effect="exception", bad=0.35); rng = np.random.default_rng(0); p = rng.random(len(d)) < 0.8
    orc, harm = d.harm_oracle.values, d.harmful_if_approved.values
    total = (p != orc).mean(); parts = (p & harm).mean() + (p & ~orc & ~harm).mean() + (~p & orc).mean()
    assert abs(total - parts) < 1e-12
    c.ROGUE_EFFECT = "segment"


def test_scoped_screen_works_for_tree_rules():
    d = firm(n=40000); c.LAW_REF = "scoped"
    h = dict(id="X", kind="loosen", conds=[("competitor", ">", 0.5), ("disc", "<=", 30.0)])
    out = c.good_law([h], d, c.features(d), now=48)
    c.LAW_REF = "global"
    assert out[0]["outcome"] != "quarantined_no_controls"


def test_outcome_screen_population_excludes_stricter_law_overrides():
    d = firm(n=40000)
    lo = dict(id="L", kind="loosen", lits=["region = 'DE'"], cap=35.0); ti = dict(id="T", kind="tighten", lits=["region = 'DE'", "segment = 'SMB'"], cap=10.0)
    n_alone = c.good_law([lo], d, None, now=48)[0].get("outcome_n"); n_with = c.good_law([lo, ti], d, None, now=48)[0].get("outcome_n")
    assert n_alone is not None and n_with is not None and n_with < n_alone
