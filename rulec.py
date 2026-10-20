"""Trusted rule compiler (rulec-2). A proposed condition (LLM or human) is parsed against an allow-list into an AST; the SAME AST is
emitted as canonical SQL, evaluated in Python, and hashed. Anything outside the grammar raises RuleError.
Grammar:  expr := term (OR term)* ; term := factor (AND factor)* ; factor := NOT factor | ( expr ) | cmp | boolcol
          cmp  := strcol (= | !=) 'literal'  |  numcol (= | != | < | <= | > | >=) number
Bounds: source <= 400 chars, <= 80 tokens, nesting depth <= 6, numbers <= 7 integer digits and <= 4 decimals, per-column value domains.
Caps (the bound on the policy variable) are validated separately by validate_cap()."""
import re
from decimal import Decimal, InvalidOperation
import numpy as np

VERSION = "rulec-3"
STR_COLS = {"segment": {"SMB", "MM", "ENT"}, "region": {"FR", "DE", "UK", "US"}}
NUM_COLS = {"term": (1, 10), "size_k": (0, 1_000_000), "tenure_y": (0, 100), "disc": (0, 100)}
BOOL_COLS = {"renewal", "quarter_end", "competitor", "churn_high"}
MAX_LEN, MAX_TOKENS, MAX_DEPTH = 400, 80, 6
TOKEN = re.compile(r"\s*(?:(?P<num>\d{1,7}(?:\.\d{1,4})?(?![\d.]))|(?P<str>'[A-Za-z]{1,8}')|(?P<op><=|>=|!=|=|<|>)|(?P<par>[()])|(?P<word>[A-Za-z_][A-Za-z_0-9]{0,30}))")
CMP = {"=": np.equal, "!=": np.not_equal, "<": np.less, "<=": np.less_equal, ">": np.greater, ">=": np.greater_equal}


class RuleError(ValueError):
    pass


def _num(text, col):
    try: v = Decimal(text)
    except InvalidOperation: raise RuleError(f"bad number {text!r}")
    lo, hi = NUM_COLS[col]
    if not v.is_finite() or v < lo or v > hi: raise RuleError(f"{col} value {text} outside [{lo}, {hi}]")
    return format(v.normalize(), "f")  # exact canonical decimal text, no rounding


def tokenize(s):
    if not isinstance(s, str) or not s.strip(): raise RuleError("empty rule")
    if len(s) > MAX_LEN: raise RuleError("rule too long")
    s = s.strip(); pos, out = 0, []
    while pos < len(s):
        m = TOKEN.match(s, pos)
        if not m or m.end() == pos: raise RuleError(f"illegal text at {pos}: {s[pos:pos + 20]!r}")
        kind = m.lastgroup; val = m.group(kind); pos = m.end()
        if kind == "word" and val.upper() in ("AND", "OR", "NOT"): kind, val = "kw", val.upper()
        out.append((kind, val))
        if len(out) > MAX_TOKENS: raise RuleError("too many tokens")
    return out


def parse(s):
    """source text -> AST: ('or', [..]) | ('and', [..]) | ('not', x) | ('bool', col) | ('cmp', col, op, value_text)"""
    toks = tokenize(s); i = 0

    def peek(): return toks[i] if i < len(toks) else (None, None)

    def take(kind=None, val=None):
        nonlocal i
        k, v = peek()
        if k is None or (kind and k != kind) or (val and v != val): raise RuleError(f"expected {val or kind}, got {v!r}")
        i += 1; return v

    def factor(depth):
        if depth > MAX_DEPTH: raise RuleError("nesting too deep")
        k, v = peek()
        if k == "kw" and v == "NOT": take(); return ("not", factor(depth + 1))
        if k == "par" and v == "(": take(); e = expr(depth + 1); take("par", ")"); return e
        col = take("word")
        if col in BOOL_COLS:
            if peek()[0] == "op": raise RuleError(f"boolean column {col} cannot be compared")
            return ("bool", col)
        op = take("op")
        if col in STR_COLS:
            if op not in ("=", "!="): raise RuleError(f"{col} only supports = / !=")
            lit = take("str").strip("'")
            if lit not in STR_COLS[col]: raise RuleError(f"{col} has no value {lit!r}")
            return ("cmp", col, op, lit)
        if col in NUM_COLS: return ("cmp", col, op, _num(take("num"), col))
        raise RuleError(f"column {col!r} not allowed")

    def term(depth):
        parts = [factor(depth)]
        while peek() == ("kw", "AND"): take(); parts.append(factor(depth))
        return parts[0] if len(parts) == 1 else ("and", parts)

    def expr(depth):
        parts = [term(depth)]
        while peek() == ("kw", "OR"): take(); parts.append(term(depth))
        return parts[0] if len(parts) == 1 else ("or", parts)

    ast = expr(0)
    if i != len(toks): raise RuleError(f"trailing tokens: {toks[i:]}")
    return ast


def to_sql(ast):
    t = ast[0]
    if t == "or": return " OR ".join(f"({to_sql(a)})" for a in ast[1])
    if t == "and": return " AND ".join(f"({to_sql(a)})" for a in ast[1])
    if t == "not": return f"NOT ({to_sql(ast[1])})"
    if t == "bool": return ast[1]
    _, col, op, v = ast
    return f"{col} {op} '{v}'" if col in STR_COLS else f"{col} {op} {v}"


def columns(ast):
    t = ast[0]
    if t in ("or", "and"): return set().union(*(columns(a) for a in ast[1]))
    if t == "not": return columns(ast[1])
    return {ast[1]}


def evaluate(ast, d, _top=True):
    """the SAME AST evaluated on a pandas DataFrame. Null contract: any null/non-finite fact in a referenced column is an error
    (SQL three-valued logic and Python two-valued logic would otherwise disagree)."""
    if _top:
        for col in columns(ast):
            x = d[col]
            if x.isna().any() or (col in NUM_COLS and not np.isfinite(x.astype(float)).all()): raise RuleError(f"null or non-finite facts in {col}")
    t = ast[0]
    if t == "or":
        m = np.zeros(len(d), bool)
        for a in ast[1]: m |= evaluate(a, d, False)
        return m
    if t == "and":
        m = np.ones(len(d), bool)
        for a in ast[1]: m &= evaluate(a, d, False)
        return m
    if t == "not": return ~evaluate(ast[1], d, False)
    if t == "bool": return d[ast[1]].values.astype(bool)
    _, col, op, v = ast
    x = d[col].values
    return CMP[op](x, v) if col in STR_COLS else CMP[op](x.astype(float), float(v))


def compile_rule(s):
    return to_sql(parse(s))


def scope_without(ast, col):
    """population scope = the AST minus TOP-LEVEL conjuncts on `col`; None if `col` also appears anywhere else (ambiguous scope)"""
    parts = ast[1] if ast[0] == "and" else [ast]
    keep = [p for p in parts if not (p[0] == "cmp" and p[1] == col)]
    if any(col in columns(p) for p in keep): return None
    if not keep: return ("or", [("cmp", col, ">=", "0"), ("cmp", col, "<", "0")])  # only bounds on col: the scope is everyone (always true)
    return keep[0] if len(keep) == 1 else ("and", keep)


def union(asts):
    """exact OR of existing ASTs: a merge built this way is semantics-preserving by construction"""
    flat = []
    for a in asts: flat += a[1] if a[0] == "or" else [a]
    return flat[0] if len(flat) == 1 else ("or", flat)


def validate_cap(kind, cap):
    """the bound on the policy variable (disc): finite, inside the variable's domain, on the correct side of the 15% policy"""
    txt = str(cap).strip()
    if len(txt) > 8 or not re.fullmatch(r"\d{1,3}(\.\d{1,2})?", txt): raise RuleError(f"cap {cap!r} must be a plain decimal with at most 2 decimals")
    v = Decimal(txt)
    if kind == "loosen" and not (Decimal(15) < v <= Decimal(100)): raise RuleError(f"loosening cap {cap} must be in (15, 100]")
    if kind == "tighten" and not (Decimal(0) <= v < Decimal(15)): raise RuleError(f"tightening cap {cap} must be in [0, 15)")
    if kind not in ("loosen", "tighten"): raise RuleError(f"unknown action {kind!r}")
    out = float(v)
    if Decimal(repr(out)) != v: raise RuleError(f"cap {cap!r} is not exactly representable")
    return out


def sql_string(v):
    """escape a string value for a SQL literal (checker inputs come from data, still never trusted)"""
    return "'" + str(v).replace("'", "''") + "'"
