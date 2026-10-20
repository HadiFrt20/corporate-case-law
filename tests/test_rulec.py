"""Adversarial tests for the trusted rule compiler (LLM proposals never reach SQL unparsed)."""
import os, sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from rulec import compile_rule, RuleError, sql_string, parse, evaluate, validate_cap


@pytest.mark.parametrize("ok,expected", [
    ("segment = 'ENT' AND competitor", "(segment = 'ENT') AND (competitor)"),
    ("size_k > 1000 OR (segment='ENT' AND NOT churn_high)", "(size_k > 1000) OR ((segment = 'ENT') AND (NOT (churn_high)))"),
    ("region != 'FR' and competitor", "(region != 'FR') AND (competitor)"),
    ("disc <= 30.5", "disc <= 30.5"),
    ("disc <= 30.0001", "disc <= 30.0001"),
])
def test_valid_rules_compile_to_canonical_sql(ok, expected):
    assert compile_rule(ok) == expected


@pytest.mark.parametrize("bad", [
    "segment = 'ENT'; DROP TABLE decisions",
    "segment = 'ENT' OR 1 = 1",
    "current_user() = 'x'",
    "segment = 'ENT' --",
    "approved",
    "deal_id > 0",
    "segment = 'XYZ'",
    "segment > 'ENT'",
    "competitor = 1",
    "size_k > '1000'",
    "(SELECT 1)",
    "region = 'US' AND region = 'U''S'",
    "segment = 'ENT' AND",
    "",
    " AND ".join(["competitor"] * 50),
    "disc <= 99999999",
    "disc <= 1e9",
    "size_k > 12345678",
    "disc <= 30.00001",
    "disc <= 101",
    "term > 0",
    "(" * 8 + "competitor" + ")" * 8,
    "competitor" + " " * 500,
])
def test_hostile_or_invalid_rules_are_rejected(bad):
    with pytest.raises(RuleError):
        compile_rule(bad)


def test_sql_string_escapes_quotes():
    assert sql_string("O'Brien") == "'O''Brien'"


@pytest.mark.parametrize("kind,cap", [("loosen", float("inf")), ("loosen", 1e9), ("loosen", 15), ("loosen", 101), ("tighten", 15), ("tighten", -1), ("loosen", "nan"), ("x", 20)])
def test_caps_are_validated(kind, cap):
    with pytest.raises(RuleError):
        validate_cap(kind, cap)


def test_valid_caps_pass():
    assert validate_cap("loosen", 30) == 30.0 and validate_cap("tighten", 10) == 10.0


def test_python_and_sql_evaluate_the_same_ast():
    d = pd.DataFrame(dict(segment=["ENT", "SMB", "ENT", "MM"], region=["FR", "US", "DE", "UK"], competitor=[True, False, False, True],
                          churn_high=[False, True, False, False], size_k=[50.0, 2000.0, 999.0, 1001.0], disc=[20.0, 30.0, 30.0001, 10.0], term=[1, 2, 3, 1]))
    ast = parse("size_k > 1000 OR (segment = 'ENT' AND NOT churn_high AND disc <= 30.0001)")
    assert evaluate(ast, d).tolist() == [True, True, True, True]
    assert evaluate(parse("disc <= 30"), d).tolist() == [True, True, False, True]  # exact boundary, no rounding


@pytest.mark.parametrize("cap", ["15.0000000000000001", "14.999999", "30.123", "1e2", "30.5.1"])
def test_caps_cannot_cross_a_boundary_through_float_rounding(cap):
    with pytest.raises(RuleError):
        validate_cap("loosen", cap) if not cap.startswith("14") else validate_cap("tighten", cap)


def test_null_facts_are_rejected_not_silently_evaluated():
    d = pd.DataFrame(dict(disc=[20.0, np.nan], segment=["ENT", "ENT"]))
    with pytest.raises(RuleError):
        evaluate(parse("disc != 30"), d)


def test_scope_strips_only_top_level_policy_bounds():
    from rulec import scope_without, to_sql
    assert to_sql(scope_without(parse("competitor AND region != 'FR' AND disc <= 26"), "disc")) == "(competitor) AND (region != 'FR')"
    assert scope_without(parse("competitor AND (disc <= 26 OR churn_high)"), "disc") is None  # ambiguous -> no scope


def test_union_is_exact_by_construction():
    from rulec import union
    a, b = parse("segment = 'ENT' AND disc <= 30"), parse("size_k > 1000 AND disc <= 30")
    d = pd.DataFrame(dict(segment=["ENT", "SMB", "SMB"], size_k=[10.0, 2000.0, 10.0], disc=[25.0, 25.0, 25.0]))
    assert (evaluate(union([a, b]), d) == (evaluate(a, d) | evaluate(b, d))).all()
