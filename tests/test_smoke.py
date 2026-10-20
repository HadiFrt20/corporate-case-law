"""Fixed-seed smoke tests: catch the regressions that bit v2 (miner order, metric semantics, outcome leakage)."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ccl_sim as c


def firm(world="easy", n=30000, seed=1):
    c.set_world(world)
    return c.make_firm(np.random.default_rng(seed), n, 0.35)


def test_outcomes_never_known_before_term_ends():
    d = firm()
    assert (d.outcome_known_month >= d.month + 12).all()


def test_good_decision_ignores_rogue_rule():
    d = firm()
    # 30% < disc <= 35% is allowed only by the rogue rule (every other cap is <= 30)
    rogue_only = (d.region == "US") & (d.segment == "MM") & (d.disc > 30) & (d.disc <= 35)
    assert rogue_only.sum() > 0 and not d.good_decision[rogue_only].any()


def test_schema_miner_finds_stricter_germany_rule_first():
    d = firm()
    hs = c.mine_schema(d)
    assert hs and hs[0]["kind"] == "tighten" and "region = 'DE'" in hs[0]["lits"]


def test_recovery_scores_exact_planted_rule_as_recovered():
    d = firm(n=60000)
    h = dict(id="H0", kind="loosen", lits=["segment = 'ENT'", "competitor"], cap=30.0, support=1, replay_prec=1.0)
    rec = c.recovery([h], d, c.features(d))
    assert rec["R2 enterprise vs competitor <=30%"]["exact"]


def test_hard_world_literals_cover_unused_field_and_negation():
    d = firm("hard", n=5000)
    lits = c.generic_literals(d)
    assert any(l.startswith("tenure_y") for l in lits) and "region != 'FR'" in lits
    assert c.literal("region != 'FR'", d).mean() < 1.0


def test_stricter_law_overrides_a_loosening_approval():
    d = firm("hard", n=20000)
    loosen = dict(id="L", kind="loosen", lits=["competitor", "region != 'FR'"], cap=26.0)
    tighten = dict(id="T", kind="tighten", lits=["region = 'DE'", "segment = 'SMB'"], cap=10.0)
    pred, cite = c.apply([loosen, tighten], d, None)
    de_smb = (d.region == "DE").values & (d.segment == "SMB").values & (d.disc.values > 10)
    assert de_smb.sum() > 0 and not pred[de_smb].any() and (cite[de_smb] == "T").all()
