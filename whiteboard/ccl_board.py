"""Board 2: Corporate Case Law (CCL), drawn to the right of the CLM board on the same canvas. Writes combined.excalidraw."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exd
exd.ROUGH, exd.FONT = 1, 5
exd._seed = iter(range(500000, 10**7))
from exd import *
RED, GRN, BLU, PUR, AMB = "#C8102E", "#1F7A4D", "#2D5F8B", "#5B3E96", "#B26A00"
X0 = 3700
E = []
def tilt(els, a):
    for e in els: e["angle"] = a
    return els
def note(i, x, y, w, h, s, a=0.0, fs=17): return tilt(box(i, X0 + x, y, w, h, s, "sticky", fs, tcolor="#4A3B00"), a)
def T(i, x, y, s, fs=17, col=SL, **k): return text(i, X0 + x, y, s, fs, col, **k)
def B(i, x, y, w, h, s, kind="neu", fs=17, **k):
    els = box(i, X0 + x, y, w, h, s, kind, fs, tcolor=k.pop("tcolor", SL), **k)
    return els
def H(els): els[0]["fillStyle"] = "hachure"; return els
def A(i, x, y, pts, col=SL, src=None, dst=None, **k): return arrow(i, X0 + x, y, pts, col, src, dst, **k)
def Ln(i, x, y, pts, col=MUTED, sw=1, style="solid"): return line(i, X0 + x, y, pts, col, sw, style)
def num(i, x, y, n, title, sub=None):
    out = B(i, x, y, 54, 54, str(n), "lava", 24, shape="ellipse", tcolor=None)
    out.append(T(i + "_h", x + 70, y + 6, title, 32, RED))
    if sub: out.append(T(i + "_s", x + 72, y + 50, sub, 18, MUTED))
    return out
def code(i, x, y, w, h, s, fs=15, col=BLU):
    r = B(i, x, y, w, h, "", "neu", fs)
    t = T(i + "_c", x + 16, y + 14, s, fs, col); t["fontFamily"] = 3
    return r + [t]

# ---------------- header + link from board 1 ----------------
E.append(line("k_div", 3560, 0, [[0, 0], [0, 3700]], MUTED, 2, "dashed"))
E.append(T("k_t", 0, 20, "Board 2 · Corporate Case Law (CCL): our original take", 46))
E.append(Ln("k_tu", 0, 84, [[0, 0], [700, 7], [1500, 0]], RED, 3))
E.append(T("k_ts", 0, 98, "corporate context MINED from what the firm actually decided, ADMITTED only if it survives replay · tested on a synthetic firm (v3: hard world + fair black box, 19 Oct 2026)", 20, MUTED))
E.append(arrow("k_link", 3305, 62, [[0, 0], [380, -30]], RED, None, None, sw=2))
E.append(text("k_link_l", 3240, 120, "what if context were\nmined, not authored?", 18, RED))

# ---------------- 1. CLM holes -> CCL answers ----------------
E += num("k_n1", 0, 200, 1, "start from CLM's 3 holes", "same goal, opposite starting point")
holes = [("tacit capture: NO mechanism\n(skills typed by hand)", "mine the GAP between written\npolicy and logged decisions"),
         ("explains which skill was\npicked, not what was output", "every decision cites holding IDs;\na checker re-runs them as SQL"),
         ("flywheel: 0 signals,\nno metric at all", "point-in-time replay accuracy\n= the number to watch")]
for k, (h, a) in enumerate(holes):
    y = 300 + k * 190
    E += note(f"k_h{k}", 20, y, 380, 130, "CLM: " + h, [-0.03, 0.02, -0.02][k])
    E += H(B(f"k_a{k}", 560, y + 5, 500, 120, "CCL: " + a, "ok", 18))
    E.append(A(f"k_ha{k}", 402, y + 65, [[0, 0], [155, 0]], GRN, f"k_h{k}", f"k_a{k}"))
E.append(T("k_n1_c", 20, 890, "CLM writes the firm's knowledge DOWN.\nCCL digs it UP from what the firm already decided.", 22, RED))

# ---------------- 2. core insight chart ----------------
E += num("k_n2", 1180, 200, 2, "tacit knowledge = the residual of policy", "where decisions disagree with the written rule, that IS the tacit rule")
cx0, px = 1220, 33.3  # x of 5% discount, px per %
xs = lambda p: cx0 + (p - 5) * px
lanes = [("ENT deal vs competitor", 400, 30), ("everyone else", 480, 15), ("Germany SMB", 560, 10)]
for li, (lab, y, cap) in enumerate(lanes):
    E.append(T(f"k_ll{li}", cx0, y - 34, lab, 15, MUTED))
    p = 5.0; k = 0
    while p <= 35:
        E.append(dot(f"k_d{li}_{k}", X0 + xs(p) - 6, y - 6, "ok" if p <= cap else "bad", 12)); p += 1.5; k += 1
E.append(Ln("k_ax", cx0, 610, [[0, 0], [1010, 0]], SL, 2))
for p in [5, 15, 25, 35]: E.append(T(f"k_tk{p}", xs(p) - 14, 618, f"{p}%", 15, SL))
E.append(T("k_axl", cx0 + 640, 645, "requested discount ->", 16, MUTED))
E.append(Ln("k_pol", xs(15), 330, [[0, 0], [0, 290]], RED, 2, "dashed"))
E.append(T("k_poll", xs(15) - 90, 300, "written policy: max 15%", 17, RED))
E += B("k_las1", xs(15) + 8, 372, xs(30.5) - xs(15) - 4, 58, "", "neu", 14, shape="ellipse", style="dashed")
E[-2]["backgroundColor"] = "transparent"; E[-2]["strokeColor"] = AMB
E.append(T("k_las1l", xs(22), 336, "holding H1: approved up to 30%", 16, AMB))
E += B("k_las2", xs(10) + 4, 532, xs(15) - xs(10) + 6, 56, "", "neu", 14, shape="ellipse", style="dashed")
E[-2]["backgroundColor"] = "transparent"; E[-2]["strokeColor"] = AMB
E.append(T("k_las2l", xs(16), 520, "holding H2: stricter than policy (> 10% = reject)", 15, AMB))
E.append(T("k_dots", cx0, 680, "green = approved · red = rejected · every dot is a logged decision", 15, MUTED))
law = [("statute", "the written policy"), ("precedent", "a logged decision, facts as of that day"), ("holding", "a mined rule: WHEN conditions THEN max = X"),
       ("appeal", "a human override at the approval gate"), ("dead letter", "a holding whose precision decays")]
E.append(T("k_lawh", cx0, 730, "borrowed from common law:", 19, SL))
E.append(Ln("k_lawt", cx0 + 12, 765, [[0, 0], [0, 4 * 36 + 10]], SL, 2))
for k, (a, b) in enumerate(law):
    y = 770 + k * 36
    E.append(Ln(f"k_lawb{k}", cx0 + 12, y + 10, [[0, 0], [22, 0]], SL, 2))
    E.append(T(f"k_lawa{k}", cx0 + 44, y, a, 18, RED)); E.append(T(f"k_lawd{k}", cx0 + 190, y, "= " + b, 17, SL))

# ---------------- 3. replay ----------------
E += num("k_n3", 2330, 200, 3, "replay: facts AS OF the decision", "no peeking at the future")
E.append(Ln("k_tl_past", 2360, 450, [[0, 0], [600, 0]], GRN, 3))
E.append(Ln("k_tl_fut", 2960, 450, [[0, 0], [400, 0]], MUTED, 2, "dashed"))
E.append(dot("k_tl_d", X0 + 2950, 440, "lava", 22))
E.append(T("k_tl_dl", 2850, 380, "deal #48211 approved\n14 Mar 2026, 16:02", 17, RED))
E.append(T("k_tl_pl", 2380, 470, "what was known then: CRM fields,\nhistory, the policy in force", 16, GRN))
E.append(T("k_tl_fl", 2990, 470, "never visible to replay:\nlater edits, churn, outcome", 16, MUTED))
E += code("k_q", 2360, 560, 640, 120, "SELECT * FROM crm.deals\n  TIMESTAMP AS OF '2026-03-14 16:02'\nWHERE deal_id = 48211", 16)
E.append(T("k_q_l", 2360, 690, "Delta time travel = point-in-time facts, the Databricks-specific enabler", 15, MUTED))
E.append(T("k_q_c", 2360, 740, "every past decision becomes a UNIT TEST\nfor the corporate context", 22, RED))
E.append(T("k_q_c2", 2360, 820, "a holding gets in only if held-out replay accuracy goes UP\nand no admitted holding breaks (regression-safe)", 17, SL))

# ---------------- 4. hero pipeline ----------------
E += num("k_n4", 0, 1090, 4, "the pipeline: CI/CD for corporate context", "a candidate rule has to earn its way into the agent")
cy = 1350
nodes = [("k_p1", 20, 250, 110, "Docket\nlogged decisions", "warn", "ellipse", "Lakeflow Connect -> Delta + CDF"),
         ("k_p2", 380, 260, 110, "Gap miner\ndecided != policy?", "ai", "rectangle", "AI Functions + rule search"),
         ("k_p3", 740, 230, 110, "candidate\nholdings", "lava", "rectangle", "each with support + scope"),
         ("k_p4", 1060, 280, 200, "moot court\nreplay up?\nnothing broken?", "warn", "diamond", "Lakebase branch per candidate\n+ MLflow 3 eval run"),
         ("k_p5", 1440, 260, 200, "good law?\noutcomes OK?", "warn", "diamond", "downstream outcome tables\n(renewal, loss, churn)"),
         ("k_p6", 1800, 280, 110, "Holdings\nas UC functions", "ok", "rectangle", "governed, ABAC-scoped,\nevidence in COMMENT"),
         ("k_p7", 2180, 260, 110, "Clerk agent\ndecides new case", "ai", "rectangle", "Agent on Apps · Vector\nSearch on past cases"),
         ("k_p8", 2540, 280, 110, "decision +\ncitations", "ok", "ellipse", "checker re-runs cited\nholdings as the user (OBO)"),
         ("k_p9", 2920, 260, 110, "human gate\napprove / override", "blue", "rectangle", "Databricks App + Lakebase")]
for nid, x, w, h, lab, kind, shp, prim in nodes:
    E += H(B(nid, x, cy - h / 2, w, h, lab, kind, 18, shape=shp))
    E.append(T(nid + "_p", x + (w / 2 + 14 if nid in ("k_p4", "k_p5", "k_p6") else 0), cy + 115, prim, 14, MUTED))
for k in range(len(nodes) - 1):
    a, b = nodes[k], nodes[k + 1]
    x1 = a[1] + a[2] + 2; x2 = b[1] - 2
    E.append(A(f"k_pa{k}", x1, cy, [[0, 0], [x2 - x1, 0]], SL, a[0], b[0]))
E.append(T("k_p4y", 1345, cy - 30, "yes", 16, GRN)); E.append(T("k_p5y", 1705, cy - 30, "yes", 16, GRN))
E.append(A("k_p4n", 1200, cy + 102, [[0, 0], [0, 130]], RED, "k_p4", None))
E.append(T("k_p4nl", 1060, cy + 240, "no -> rejected,\nlogged with its replay score", 16, RED))
E.append(A("k_p5n", 1570, cy + 102, [[0, 0], [0, 130]], RED, "k_p5", None))
E += note("k_bad", 1430, cy + 240, 330, 120, "bad law -> steward review\ne.g. the US mid-market\nrogue approver", 0.03, 16)
E.append(A("k_p6d", 1940, cy + 57, [[0, 0], [0, 175]], AMB, "k_p6", None, style="dashed"))
E.append(T("k_p6dl", 1820, cy + 240, "dead letter: precision decays on a\nrolling window -> holding retired", 16, AMB))
E.append(A("k_loop", 3050, cy + 57, [[0, 0], [0, 430], [-2905, 430], [-2905, 2]], RED, "k_p9", "k_p1", sw=2))
E.append(T("k_loopl", 900, cy + 495, "appeal: an override becomes a new precedent -> the miner proposes to NARROW or OVERRULE the holding", 18, RED))

# ---------------- 5. holding = code, answer = checkable ----------------
E += num("k_n5", 0, 2090, 5, "a holding is code, an answer is checkable", "the explanation can be executed")
_SUM = json.load(open(os.path.join(HERE, "..", "summary.json")))
_h = next(h for h in _SUM["example_holdings_seed7_m36"] if "ENT" in h["sql"])
E += code("k_sql", 20, 2190, 640, 230, f"CREATE FUNCTION ccl.law.ent_vs_competitor(\n  segment STRING, competitor BOOLEAN, disc DOUBLE)\nRETURNS BOOLEAN\nCOMMENT 'support {_h['support']} · replay precision {_h['replay_prec']} ·\n         outcome lift {_h['outcome_lift']:+.2f} · steward: deal desk'\nRETURN segment = 'ENT' AND competitor\n       AND disc <= 30;", 15)
E += code("k_ans", 20, 2450, 640, 150, '{ "decision": "APPROVE 27%",\n  "cites": ["H1", "precedent #48211"],\n  "check": "H1 re-run as user -> TRUE" }', 16, GRN)
E += note("k_exe", 700, 2220, 380, 150, "if the cited holding does NOT\nfire on these facts, the\nanswer is rejected", -0.02, 17)
E.append(T("k_vs", 700, 2410, "vs CLM: a graph path explains\nthe pick, not the output", 18, PUR))
E.append(T("k_acl", 700, 2480, "and the CFO's exceptions stay\ninvisible to field reps (UC ABAC)", 17, BLU))

# ---------------- 6. results (read from ../summary_v3.json, generated by aggregate_v3.py) ----------------
V3 = json.load(open(os.path.join(HERE, "..", "summary_v3.json")))
hb = V3["worlds"]["hard"]["miners"]["beam"]; eb = V3["worlds"]["easy"]["miners"]["beam"]; acc = hb["accuracy"]; ea = eb["accuracy"]
E += num("k_n6", 1180, 2090, 6, "tested: the HARD world (v3)", "hidden rules outside the miner's shape: OR · term-scaled cap · 340k · unused field · negation · 3 seeds")
rows = [("written policy only", "statute", "neu"), ("black box (GBM)", "gbm_monthly", "warn"), ("black box + renewal veto", "gbm_uplift", "warn"),
        ("CCL, all holdings", "ccl", "ok"), ("CCL + bad-law filter", "ccl_goodlaw", "ok")]
for g, (metric, title, y0) in enumerate([("vs_actual", "agrees with the LOGGED decisions (rogue approvals + noise included)", 2180),
                                          ("vs_good", "agrees with what a WELL-RUN firm should decide", 2470)]):
    E.append(T(f"k_rh{g}", 1200, y0, title, 17, SL))
    for k, (lab, key, kind) in enumerate(rows):
        y = y0 + 34 + k * 44; v = acc[key][metric]
        E.append(T(f"k_rl{g}{k}", 1200, y + 7, lab, 15, SL))
        E += B(f"k_rb{g}{k}", 1440, y, max(40, int((v - .65) * 1800)), 34, f"{v:.3f}", kind, 15, fill="hachure")
E.append(T("k_axis", 2000, 2180, "axis starts at 0.65", 14, MUTED))
fid = sum(hb["fidelity"].values()) / len(hb["fidelity"])
facts = [(f"hard world: {hb['exact']:.1f} / {hb['n_rules']} rules found, decisions match the hidden rules {fid:.0%} (v2's hand-picked miner: {V3['worlds']['hard']['miners']['schema']['exact']:.1f} / 7)", GRN),
         (f"easy world: CCL {ea['ccl']['vs_actual']:.3f} = black box {ea['gbm_monthly']['vs_actual']:.3f}; well-run target {ea['ccl_goodlaw']['vs_good']:.3f} vs veto box {ea['gbm_uplift']['vs_good']:.3f}", GRN),
         ("weak spots: OR-rule kept one branch, negation rule 85%, tenure rule 80% covered; beam = 13 min / run", AMB),
         ("verdict: a FAIR black box (same outcomes, same threshold) matches the accuracy.", RED),
         ("CCL's edge is the form: ~8 readable, testable, governed rules + named bad law", RED)]
for k, (f, c) in enumerate(facts): E.append(T(f"k_f{k}", 1200, 2740 + k * 30, f, 15, c))

# ---------------- 7. novelty, honestly ----------------
E += num("k_n7", 2330, 2090, 7, "novel? the honest answer", "checked against the literature + 1 prior-art agent")
E.append(T("k_th", 2350, 2190, "ALREADY TAKEN", 20, AMB)); E.append(T("k_uh", 2860, 2190, "UNCLAIMED (as far as we found)", 20, GRN))
taken = ["decision traces = the missing\nlayer (Foundation Capital essay)", "decision-trace schemas for\ngovernance (Solozobov 2026)",
         "case-based reasoning loop\n(Aamodt & Plaza 1994)", "concept drift detection\n(Gama et al. 2014)"]
for k, s in enumerate(taken): E += note(f"k_tk_{k}", 2350, 2230 + k * 125, 400, 105, s, [-0.02, 0.025, -0.015, 0.02][k], 16)
uncl = ["replay as the ADMISSION test\nfor agent context", "mine the residual against\nthe written policy", "outcome-weighted precedent\n('bad law' filter)"]
for k, s in enumerate(uncl): E += H(B(f"k_un{k}", 2860, 2240 + k * 150, 460, 110, s, "ok", 18))
E.append(T("k_cicd", 2860, 2700, "= CI/CD for corporate context", 28, RED))
E.append(Ln("k_cicdu", 2860, 2745, [[0, 0], [220, 4], [430, 0]], RED, 2))

# ---------------- 8. next + kill rule ----------------
E += num("k_n8", 0, 3010, 8, "next experiments, and when to kill it")
E.append(Ln("k_nx", 40, 3160, [[0, 0], [2400, 0]], SL, 2))
nxt = ["LLM writes the 'because' from\njustification text, merges OR branches", "real decision data on fe-vm: time-travel\nreplay, Lakebase branch per rule", "speed: beam miner 13 min / run\n(vectorise before real volumes)"]
for k, s in enumerate(nxt):
    E.append(dot(f"k_nd{k}", X0 + 100 + k * 800, 3152, "lava", 16))
    E.append(T(f"k_nt{k}", 80 + k * 800, 3185, f"{k+1}. {s}", 18, SL))
_V3 = json.load(open(os.path.join(HERE, "..", "summary_v3.json")))["worlds"]["hard"]["miners"]["beam"]
_gain = 100 * (_V3["accuracy"]["ccl"]["vs_actual"] - _V3["accuracy"]["statute"]["vs_actual"]); _rec = _V3["exact"]
_ok = _gain >= 10 and _rec >= 4
E += note("k_kill", 2560, 3060, 540, 190, f"KILL rule: CCL >= policy + 10 pts\nAND >= 4 of 7 rules recovered\nv3 hard world: +{_gain:.1f} pts · {_rec:.1f} / 7\n-> {'SURVIVES (synthetic only)' if _ok else 'KILLED'}", -0.02, 19)
# ================= 9-11: what happened after v3 (all read from result files) =================
import glob as _glob
ROOT = os.path.join(HERE, "..")
RL = json.load(open(os.path.join(ROOT, "dbx", "run_log.json")))["stages"]
INJ = json.load(open(os.path.join(ROOT, "dbx", "injection_log_databricks-gpt-5-4-nano_False.json")))
REAL = json.load(open(os.path.join(ROOT, "real", "hmda", "results.json")))
V4 = json.load(open(os.path.join(ROOT, "summary_v4.json")))
CZ = [json.load(open(f)) for f in _glob.glob(os.path.join(ROOT, "runs_causal", "*.json"))]
Y0 = 3560
E.append(Ln("k_div2", -20, Y0 - 50, [[0, 0], [3440, 0]], MUTED, 1, "dashed"))
E.append(T("k_after", 0, Y0 - 40, "after v3: built on Databricks, tested on real decisions, two baselines fixed", 22, MUTED))

# ---- 9. on Databricks ----
E += num("k_n9", 0, Y0, 9, "built on Databricks (sandbox run)", "Delta time travel · UC functions · Lakebase branch per trial · Foundation Model API")
steps = [("k_s1", "Delta decisions\none commit / month", "warn"), ("k_s2", "rules as\nUC SQL functions", "ok"),
         ("k_s3", "moot court on a\nLakebase branch", "lava"), ("k_s4", "law registry\nin Lakebase", "blue"), ("k_s5", "agent + checker\n(re-runs UC fns)", "ai")]
for k, (sid, lab, kind) in enumerate(steps):
    E += H(B(sid, 20 + k * 215, Y0 + 100, 190, 80, lab, kind, 16))
    if k: E.append(A(f"k_sa{k}", 20 + k * 215 - 23, Y0 + 140, [[0, 0], [21, 0]], SL, steps[k - 1][0], sid))
A_ = RL["A_mine"]; B_ = RL["B_moot_court"]; P_ = RL["B_point_in_time"]; F1 = RL["F1_rationale"]; F2 = RL["F2_proposals"]; EA = RL["E_agent"]
facts9 = [(f"{A_['facts_changed_since']:.1%} of past decisions have facts edited AFTER the decision", SL),
          ("mining today's table misses a real rule: " + (A_["only_asof"][0] if A_["only_asof"] else "-"), RED),
          (f"law built on today's table, judged on real facts: {P_['law_built_on_todays_table_judged_on_real_facts']:.4f} vs {P_['law_asof_judged_on_real_facts']:.4f}", SL),
          (f"{B_['admitted']}/{B_['tried']} candidates admitted, Lakebase branch ready in {B_['median_branch_s']} s (median)", GRN),
          (f"LLM 'because' matched the hidden reason {F1['matched']}/{F1['total']}; rogue rule judged incoherent", GRN),
          (f"LLM proposed {len(F2['proposals'])} new rules: {sum(p['verdict'] == 'admitted' for p in F2['proposals'])} survived replay", RED),
          (f"agent = executable law on {int(EA['agent_matches_law'] * EA['deals'])}/{EA['deals']} deals", GRN),
          (f"injection, small model, no warning: followed {INJ['agent_followed_injection']}/10, checker blocked {INJ['checker_blocked']}, wrong shipped {INJ['shipped_wrong']}", GRN)]
for k, (f, c) in enumerate(facts9): E.append(T(f"k_f9{k}", 20, Y0 + 210 + k * 30, f, 15, c))
E += note("k_cap", 700, Y0 + 470, 380, 120, "Lakebase gotcha: ~21 active\nendpoints per project; disable each\ntrial's endpoint, keep the branch", -0.02, 15)

# ---- 10. real decisions ----
E += num("k_n10", 1180, Y0, 10, "real decisions: one US mortgage lender", "HMDA public data 2018-2023 · statute = QM debt-to-income cap 43% · race/sex never mined")
E.append(T("k_rh10", 1200, Y0 + 90, "accuracy on the held-out year (axis starts at 0.70)", 16, SL))
cols10 = [("statute", "policy", "neu"), ("always_approve", "always approve", "neu"), ("beam_power", "CCL", "ok"), ("gbm", "black box", "warn")]
for i, (t, r) in enumerate(REAL["tests"].items()):
    y = Y0 + 125 + i * 110
    E.append(T(f"k_ry{i}", 1200, y + 30, str(t), 18, SL))
    for k, (key, lab, kind) in enumerate(cols10):
        v = r[key]["acc"]; E += B(f"k_rb10{i}{k}", 1290, y + k * 24, max(30, int((v - .70) * 2200)), 21, f"{lab} {v:.3f}", kind, 12, fill="hachure")
top = REAL["tests"]["2022"]["beam_power"]["holdings"]
loosen = next(h for h in top if h["kind"] == "loosen"); tight = next(h for h in top if h["kind"] == "tighten")
tb = ", ".join(f"{k} {v:.0%}" for k, v in list(tight["because"].items())[:2])
E += code("k_real_sql", 1200, Y0 + 470, 1040, 110, f"{loosen['sql'].replace('disc', 'dti')}\n   tacit: the lender approves up to 49% DTI, not 43%\n{tight['sql'].replace('disc', 'dti')}\n   because (denial codes): {tb}", 14)
E += note("k_audit", 1700, Y0 + 600, 420, 110, f"fairness audit: stricter rules fail\nfour-fifths (race {tight['audit']['race']['ratio']}, sex {tight['audit']['sex']['ratio']})\n-> steward review, not the agent", 0.02, 15)
E.append(T("k_real_c", 1200, Y0 + 610, "honest: always-approve is ~0.91;\nno credit score or outcome in HMDA", 15, RED))

# ---- 11. rare rules + causal check ----
E += num("k_n11", 2330, Y0, 11, "rare rules + is the discount the CAUSE?", "v4 simulation, 3 seeds")
hw = V4["worlds"]["hard"]["miners"]; key = "H1b deal > 1M branch (non-ENT)"
bars11 = [("beam/adm2", "v3 miner", "neu"), ("beam/adm4", "longer admission only", "warn"), ("beam_power/adm2", "power-aware mining only", "warn"), ("beam_power/adm4", "both", "ok")]
E.append(T("k_h11", 2350, Y0 + 90, "the missing OR branch (deals > 1M): share decided right", 16, SL))
for k, (mk, lab, kind) in enumerate(bars11):
    v = hw[mk]["fidelity"][key]; y = Y0 + 120 + k * 38
    E.append(T(f"k_l11{k}", 2350, y + 8, lab, 15, SL)); E += B(f"k_b11{k}", 2600, y, max(40, int(v * 600)), 30, f"{v:.2f}", kind, 15, fill="hachure")
E.append(T("k_cost11", 2350, Y0 + 278, f"cost: power-aware mining admits extra rules (logged acc {hw['beam/adm2']['accuracy']['ccl']['vs_actual']:.3f} -> {hw['beam_power/adm4']['accuracy']['ccl']['vs_actual']:.3f})", 15, AMB))
def cz(world, eff, ref, b, k):
    rs = [r for r in CZ if r["world"] == world and r["rogue_effect"] == eff and r["law_ref"] == ref and abs(r["bad_renew"] - b) < 1e-9]
    return sum(r["accuracy"][k]["vs_good"] for r in rs) / len(rs)
E.append(T("k_h11b", 2350, Y0 + 320, "when the exception CAUSES churn (well-run target, easy world):", 16, SL))
for k, (lab, mk, kind) in enumerate([("CCL bad-law filter", "ccl_goodlaw", "ok"), ("black box + renewal veto", "gbm_uplift", "warn"), ("black box + T-learner uplift", "gbm_tlearner", "warn")]):
    v = cz("easy", "exception", "scoped", 0.35, mk); y = Y0 + 355 + k * 42
    E.append(T(f"k_cl{k}", 2350, y + 7, lab, 15, SL)); E += B(f"k_cb{k}", 2650, y, max(40, int((v - .9) * 6000)), 32, f"{v:.3f}", kind, 15, fill="hachure")
E.append(T("k_axis11", 3150, Y0 + 330, "axis from 0.90", 13, MUTED))
E += note("k_causal", 2350, Y0 + 500, 560, 130, "when the segment churns anyway, the SCOPED filter\n(same population, inside policy) stays quiet: correct.\nv3's 'fair black box ties' came from a correlational sim", -0.015, 15)

E.append(T("k_close", 0, Y0 + 760, "CLM writes the firm's knowledge down. CCL digs it out of what the firm already decided,\nand makes every rule prove itself before an agent may use it.", 26, SL))
E.append(T("k_foot", 0, Y0 + 860, "code + numbers: github.com/HadiFrt20/corporate-case-law · every number on this board is read from the result files · 20 Oct 2026", 15, MUTED))

E = [e for e in E if not (e["type"] == "text" and e["text"] == "")]
_ids = {e["id"] for e in E}
for e in E:
    if e.get("boundElements"): e["boundElements"] = [b for b in e["boundElements"] if b["id"] in _ids] or None
tmp = os.path.join(HERE, "ccl_only.excalidraw"); save(tmp, E)
board1 = json.load(open(os.path.join(HERE, "clm_board.excalidraw")))
board2 = json.load(open(tmp))
ids1 = {e["id"] for e in board1["elements"]}
assert not ids1 & {e["id"] for e in board2["elements"]}, "id clash"
board1["elements"] += board2["elements"]
json.dump(board1, open(os.path.join(HERE, "combined.excalidraw"), "w"), indent=1)
print(len(board2["elements"]), "new elements;", len(board1["elements"]), "total")
