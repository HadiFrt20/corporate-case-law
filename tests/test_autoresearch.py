"""Adversarial tests for the autoresearch harness v2 trust boundary (AR-009)."""
import math, os, sys, textwrap
import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, "autoresearch"), ROOT]
import harness as H

CFG = H.P(world="easy", effect="segment", seed=7)


def ok(lits, kind="loosen", cap=25.0):
    return {"kind": kind, "lits": lits, "cap": cap}


@pytest.mark.parametrize("lit", ["approved", "renewed", "statute", "outcome_known", "NOT approved", "month > 30",
                                 "disc <= 20", "outcome_known_month > 40", "harm_oracle", "segment = 'ENT' OR 1=1"])
def test_validate_rejects_non_decision_fields(lit):
    law, err = H.validate([ok([lit])])
    assert law is None and "grammar" in err


@pytest.mark.parametrize("bad, why", [
    ([ok(["renewal"])] * 16, "holdings"), ([ok(["renewal"] * 5)], "literals"), ([ok([])], "literals"),
    ([ok(["renewal"], cap=float("nan"))], "cap"), ([ok(["renewal"], cap=math.inf)], "cap"), ([ok(["renewal"], cap=100.0)], "cap"),
    ([ok(["renewal"], kind="tighten", cap=30.0)], "cap"), ([dict(ok(["renewal"]), other_keys=["ast"])], "only lits"),
    ([ok(["renewal"], kind="approve_all")], "kind"), ("not a list", "list")])
def test_validate_rejects_malformed_laws(bad, why):
    law, err = H.validate(bad)
    assert law is None and why in err


def test_validate_accepts_and_normalises_a_good_law():
    law, err = H.validate([ok(["segment = 'ENT'", "competitor"], cap=30), ok(["region = 'DE'", "segment = 'SMB'"], "tighten", 10)])
    assert err is None and [h["cap"] for h in law] == [30.0, 10.0] and set(law[0]) == {"id", "kind", "lits", "cap"}


def test_view_hides_ground_truth_and_future_outcomes():
    import worlds as WD, ccl_sim as C
    df, _ = WD.firm(H.P(world="hard", effect="exception", seed=7))
    v = H.view_of(df, 40)
    assert not set(H.HIDDEN) & set(v.columns) and set(v.columns) <= set(H.VIEW_COLS) | {"outcome_known"}
    assert (v.month < 40).all()
    assert not (v.renewed & ~v.outcome_known).any()                          # no renewal shown where it was not knowable
    known = C.outcome_rows(df, 40).values[(df.month < 40).values]
    assert (v.outcome_known.values == known).all()


def run_method(tmp_path, body):
    p = tmp_path / "evil_method.py"; p.write_text(textwrap.dedent(body))
    return H.eval_config(CFG, False, str(p))


def test_monkeypatching_ccl_sim_in_the_method_cannot_change_scoring(tmp_path):
    benign = run_method(tmp_path, "def build_law(view, X, m):\n    return []\n")
    evil = run_method(tmp_path, """
        import ccl_sim as C, numpy as np
        C.apply = lambda hs, d, Xd: (np.ones(len(d), bool), None)     # 'approve everything' in the method's process
        C.outcome_rows = lambda df, m: df.month >= 0
        def build_law(view, X, m):
            return []
    """)
    assert evil["violation"] is None and np.allclose(evil["agree"], benign["agree"])


def test_method_cannot_find_the_firm_or_oracle_in_memory(tmp_path):
    r = run_method(tmp_path, """
        import gc, inspect
        def build_law(view, X, m):
            for f in inspect.stack():
                if any(k in f.frame.f_locals for k in ("df", "seed", "cfg")): raise RuntimeError("LEAK: caller frame")
            for o in gc.get_objects():
                try:
                    cols = getattr(o, "columns", None)
                    if cols is None: continue
                    names = {str(c) for c in list(cols)}
                except Exception: continue
                if "harm_oracle" in names or "binding" in names: raise RuntimeError("LEAK: oracle in memory")
            if "harm_oracle" in view.columns or "binding" in view.columns: raise RuntimeError("LEAK: view")
            return []
    """)
    assert r["violation"] is None, r["violation"]


def test_a_law_that_reads_outcomes_is_invalid(tmp_path):
    r = run_method(tmp_path, "def build_law(view, X, m):\n    return [{'kind': 'loosen', 'lits': ['renewed'], 'cap': 35.0}]\n")
    assert r["violation"] and "grammar" in r["violation"]


def test_method_crash_is_reported_not_hidden(tmp_path):
    r = run_method(tmp_path, "def build_law(view, X, m):\n    raise ValueError('boom')\n")
    assert r["violation"] and "boom" in r["violation"]


def test_leak_probe_positive_control(tmp_path):
    """the same probe, run IN-PROCESS next to a frame holding the firm, must detect it (so the test above means something)"""
    import importlib.util, pandas as pd
    p = tmp_path / "probe.py"
    p.write_text(textwrap.dedent('''
        import gc, inspect
        def build_law(view, X, m, frames=True):
            if frames:
                for f in inspect.stack():
                    if any(k in f.frame.f_locals for k in ("df", "seed", "cfg")): raise RuntimeError("LEAK: caller frame")
            for o in gc.get_objects():
                try:
                    cols = getattr(o, "columns", None)
                    if cols is None: continue
                    names = {str(c) for c in list(cols)}
                except Exception: continue
                if "harm_oracle" in names or "binding" in names: raise RuntimeError("LEAK: oracle in memory")
            return []
    '''))
    spec = importlib.util.spec_from_file_location("probe", p); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    df = pd.DataFrame({"harm_oracle": [True]})   # noqa: F841  (what the v1 harness had in the caller frame)
    with pytest.raises(RuntimeError, match="caller frame"):
        mod.build_law(df, None, 40)
    with pytest.raises(RuntimeError, match="oracle in memory"):      # the GC route on its own (round 2: never validated before)
        mod.build_law(df, None, 40, frames=False)



def test_outcome_timing_handcrafted():
    """independent of ccl_sim.outcome_rows: approved deals only, decided before m, term ended STRICTLY before m"""
    import pandas as pd
    df = pd.DataFrame(dict(month=[20, 20, 20, 33, 21], term=[1] * 5, approved=[True, False, True, True, True],
                           renewed=[True, True, False, True, True], disc=[10.0] * 5, statute=[True] * 5,
                           segment=["SMB"] * 5, region=["FR"] * 5, renewal=[False] * 5, quarter_end=[False] * 5,
                           competitor=[False] * 5, churn_high=[False] * 5, size_k=[100.0] * 5))
    df["outcome_known_month"] = df.month + 12 * df.term          # 32, 32, 32, 45, 33
    v = H.view_of(df, 33)
    assert list(v.outcome_known) == [True, False, True, False]   # rejected deal never known; the month-21 deal ends at 33, not < 33
    assert list(v.renewed) == [True, False, False, False]        # the rejected deal's renewal is hidden even though it is True
    assert 33 not in set(v.month)                                # the month-33 deal is not in the past
    assert not H.view_of(df, 32).outcome_known.any()             # maturity exactly at m is not yet known


def test_total_literal_budget_boundary():
    assert H.validate([ok(["renewal", "competitor", "churn_high"])] * 15)[1] is None           # 45 literals: allowed
    law, err = H.validate([ok(["renewal", "competitor", "churn_high", "quarter_end"])] * 12)    # 48 literals
    assert law is None and "45" in err


def test_ast_and_conds_rejected_end_to_end(tmp_path):
    r = run_method(tmp_path, "def build_law(view, X, m):\n    return [{'kind': 'loosen', 'ast': ['or'], 'cap': 30.0}]\n")
    assert r["violation"] and "only lits/cap" in r["violation"]


def test_hanging_method_times_out(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "MONTH_TIMEOUT_S", 3)
    r = run_method(tmp_path, "import time\ndef build_law(view, X, m):\n    time.sleep(60)\n    return []\n")
    assert r["violation"] and "timeout" in r["violation"]


def test_law_on_a_missing_field_is_invalid_not_a_crash(tmp_path):
    r = run_method(tmp_path, "def build_law(view, X, m):\n    return [{'kind': 'loosen', 'lits': ['tenure_y > 8'], 'cap': 25.0}]\n")
    assert r["violation"] and "not available" in r["violation"]          # the easy world has no tenure field
