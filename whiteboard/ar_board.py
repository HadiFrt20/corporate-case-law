"""Board 3: the autoresearch project (what changed, and how the improvement was obtained). Writes ar_board.excalidraw.
Confirmatory and detector numbers are parsed from the committed result files; dev-score steps come from autoresearch/ADR.md."""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import exd
exd.ROUGH, exd.FONT = 1, 5
exd._seed = iter(range(900000, 10**7))
from exd import *
RED, GRN, BLU, PUR, AMB = "#C8102E", "#1F7A4D", "#2D5F8B", "#5B3E96", "#B26A00"

def confirm(p):
    t = open(os.path.join(ROOT, "autoresearch", p)).read()
    g, lo, hi = map(float, re.search(r"confirm_world_gap: ([+-][\d.]+)  \[95% CI ([+-][\d.]+), ([+-][\d.]+)\]", t).groups())
    neg = re.search(r"worlds_negative:\s+(\d+) of (\d+)", t).groups()
    return dict(g=g, lo=lo, hi=hi, neg=int(neg[0]), n=int(neg[1]), res=re.search(r"confirm_result:\s+(\w+)", t).group(1), text=t)
C1, C2, C3 = confirm("CONFIRM_1.txt"), confirm("CONFIRM_2.txt"), confirm("CONFIRM_3.txt")
DR = json.load(open(os.path.join(ROOT, "autoresearch", "detector_result.json")))["stats"]
rows3 = [l for l in C3["text"].splitlines() if l.startswith("  gen")]
g3 = lambda l: float(re.search(r"gap\s+([+-][\d.]+)", l).group(1))
EXC3 = sum(g3(l) for l in rows3 if l.split()[1] == "exception") / 24; SEG3 = sum(g3(l) for l in rows3 if l.split()[1] == "segment") / 24
RULES3 = float(re.search(r"rules_mean:\s+([\d.]+)", C3["text"]).group(1))

E = []
ZW, ZH = 1100, 880
def Z(c, r): return 40 + c * 1150, 190 + r * 930
def tilt(els, a):
    for e in els: e["angle"] = a
    return els
def note(i, x, y, w, h, s, a=0.0, fs=17): return tilt(box(i, x, y, w, h, s, "sticky", fs, tcolor="#4A3B00"), a)
def B(i, x, y, w, h, s, kind="neu", fs=17, **k): return box(i, x, y, w, h, s, kind, fs, tcolor=k.pop("tcolor", OAT if kind == "dark" else SL), **k)
def H(els): els[0]["fillStyle"] = "hachure"; return els
def T(i, x, y, s, fs=17, col=SL, **k): return text(i, x, y, s, fs, col, **k)
def num(i, x, y, n, title, sub=None):
    out = B(i, x, y, 54, 54, str(n), "lava", 24, shape="ellipse", tcolor=None)
    out.append(T(i + "_h", x + 70, y + 6, title, 32, RED))
    if sub: out.append(T(i + "_s", x + 72, y + 50, sub, 18, MUTED))
    return out

# ---------------- header ----------------
E.append(T("h_t", 40, 20, "Board 3 · Autoresearch: what changed, and how the improvement was obtained", 46))
E.append(line("h_u", 40, 84, [[0, 0], [900, 6], [1900, 0]], RED, 3))
E.append(T("h_s", 40, 100, "karpathy/autoresearch adapted to Corporate Case Law · an AI agent (Claude Code) ran the loop, a second model (GPT-6 Astra) reviewed it 4 times, I set the goal and the rules · 22 Oct 2026", 20, MUTED))

# ---------------- 1. the loop we copied ----------------
x, y = Z(0, 0)
E += num("z1", x, y, 1, "the loop we copied", "karpathy/autoresearch: one file to edit, one metric, keep or discard")
E += B("z1_p", x + 30, y + 120, 300, 110, "program.md\nthe research rules\n(written by the human)", "sticky", 18)
E += H(B("z1_m", x + 400, y + 120, 300, 110, "method.py\nthe ONLY file\nthe agent edits", "lava", 18))
E += B("z1_h", x + 770, y + 120, 300, 110, "harness.py\nFROZEN: builds firms,\nscores the law", "dark", 18)
E.append(arrow("z1_a1", x + 332, y + 175, [[0, 0], [64, 0]], SL, "z1_p", "z1_m"))
E.append(arrow("z1_a2", x + 702, y + 175, [[0, 0], [64, 0]], SL, "z1_m", "z1_h"))
E += B("z1_s", x + 770, y + 330, 300, 90, "one number:\nCCL minus the best black box", "blue", 18)
E.append(arrow("z1_a3", x + 920, y + 232, [[0, 0], [0, 94]], SL, "z1_h", "z1_s"))
E += B("z1_k", x + 400, y + 330, 300, 90, "better? keep the commit\nworse? git reset", "ok", 18, shape="diamond")
E.append(arrow("z1_a4", x + 768, y + 375, [[0, 0], [-64, 0]], SL, "z1_s", "z1_k"))
E.append(arrow("z1_a5", x + 550, y + 326, [[0, 0], [0, -92]], GRN, "z1_k", "z1_m"))
E.append(T("z1_l", x + 30, y + 470, "what I changed in the recipe:", 20, RED))
for k, s in enumerate(["a FROZEN harness the agent cannot touch (method runs in its own process)",
                       "a dev panel to decide on, other panels it may NOT look at to decide",
                       "pre-registered confirmatory tests: manifest committed BEFORE the run",
                       "every failure kept in the log (WORKLOG + 24 ADRs)",
                       "a stopping rule (the original never stops on its own)"]):
    E.append(dot(f"z1_d{k}", x + 40, y + 523 + k * 44, "lava"))
    E.append(T(f"z1_t{k}", x + 64, y + 513 + k * 44, s, 18))
E += note("z1_n", x + 30, y + 760, 1040, 80, "transparency: the agent wrote the code and ran ~40 experiments.\nAstra graded C+ -> B- -> B+ -> B+. I wrote none of the method by hand.", -0.01, 17)

# ---------------- 2. the trust boundary ----------------
x, y = Z(1, 0)
E += num("z2", x, y, 2, "the trust boundary", "after review 1 (C+): the method could see too much")
E += B("z2_h", x + 30, y + 120, 470, 330, "HARNESS process\n\nthe whole firm, the seed\nthe hidden rules, the oracle\nthe 5 baselines\n\ndecides with ITS OWN rule engine", "dark", 19)
E += H(B("z2_r", x + 600, y + 120, 470, 330, "METHOD process (python -I)\n\nsees: the past only\nno ground-truth columns\nrenewals only where knowable\n\nreturns: plain JSON rules", "lava", 19))
E.append(arrow("z2_a1", x + 502, y + 230, [[0, 0], [94, 0]], SL, "z2_h", "z2_r"))
E.append(T("z2_a1l", x + 505, y + 190, "view of\nthe past", 16, MUTED))
E.append(arrow("z2_a2", x + 598, y + 360, [[0, 0], [-94, 0]], RED, "z2_r", "z2_h"))
E.append(T("z2_a2l", x + 515, y + 372, "<= 15 rules", 16, RED))
E += B("z2_g", x + 30, y + 490, 1040, 130, "gates: at most 15 rules · at most 4 conditions each\nliterals only over deal fields (never approved, renewed or outcomes)\nno ASTs, no trees, no code: a model cannot hide inside the law", "warn", 18)
E.append(T("z2_t", x + 30, y + 650, "35 adversarial tests, each trying to break it:", 20, RED))
for k, s in enumerate(["a method that monkeypatches the rule engine -> no effect on the score",
                       "a method that searches memory for the firm -> finds nothing (positive control finds it)",
                       "a rule that reads outcomes -> invalid · a hanging method -> timeout"]):
    E.append(T(f"z2_tl{k}", x + 40, y + 695 + k * 40, "· " + s, 18))

# ---------------- 3. the metric and the panels ----------------
x, y = Z(2, 0)
E += num("z3", x, y, 3, "one number, five panels", "the score: CCL agreement minus the BEST of 5 fixed baselines, in points")
E += B("z3_c", x + 30, y + 120, 1040, 110, "gap = CCL  minus  max(GBM, GBM + veto, GBM + T-learner, 15-leaf tree, tree + veto)\n0 = ties the best black box · +0.10 = one fewer error per 1,000 decisions", "blue", 19)
pan = [("dev", "decides keep / discard", "ok"), ("monitor", "seen at checkpoints only", "warn"), ("stress", "harm-detector torture tests", "warn"),
       ("fresh", "worlds drawn at run time", "bad"), ("confirm", "pre-registered, ONE run", "lava")]
for k, (n, d, kd) in enumerate(pan):
    E += B(f"z3_p{k}", x + 30 + k * 212, y + 290, 196, 150, f"{n}\n\n" + d.replace(" ", "\n", 1), kd, 15)
E.append(arrow("z3_ar", x + 40, y + 470, [[0, 0], [1020, 0]], MUTED, None, None, sw=2))
E.append(T("z3_arl", x + 280, y + 480, "less you are allowed to look  ->  more it counts", 18, MUTED))
E += note("z3_n", x + 60, y + 560, 980, 130, "the rule that mattered most: the agent may only decide on DEV.\nLooking at the other panels to choose a change would turn them into dev.", 0.01, 19)
E.append(T("z3_f", x + 30, y + 740, "caveat: the comparator picks the best baseline AFTER the fact, per world; the baselines are not tuned", 17, MUTED))

# ---------------- 4. line 1: what changed (dev staircase) ----------------
x, y = Z(0, 1)
E += num("z4", x, y, 4, "line 1: what changed, step by step", "dev score after each KEPT change (v1 dev panel, 12 configs)")
steps = [("start (v5.1)", -1.141, "neu"), ("overrules +\nrefinement", -0.655, "ok"), ("integer\nthresholds", -0.411, "ok"), ("admission\n4 months", -0.182, "ok"),
         ("support 40,\nbeam 60", -0.092, "ok"), ("drop the\noutcome screen", -0.024, "ok"), ("support 30", +0.110, "ok"), ("drop the\nmoot court", +0.181, "ok")]
bx0, by0, sc = x + 60, y + 400, 200   # zero line y, px per point
E.append(line("z4_0", bx0 - 20, by0, [[0, 0], [1000, 0]], SL, 2))
E.append(T("z4_0l", bx0 - 55, by0 - 12, "0", 18))
for k, (lab, v, kd) in enumerate(steps):
    h = abs(v) * sc; top = by0 - h if v > 0 else by0
    E += H(B(f"z4_b{k}", bx0 + k * 122, top, 92, max(h, 6), "", "ok" if v > 0 else ("bad" if k == 0 else "warn"), 14))
    E.append(T(f"z4_v{k}", bx0 + k * 122, (top - 28) if v > 0 else (by0 + h + 6), f"{v:+.2f}", 17, GRN if v > 0 else RED))
    E.append(T(f"z4_l{k}", bx0 + k * 122 - 6, by0 - 120 if v < 0 else by0 + 14, lab, 14, MUTED))
E += note("z4_n", x + 640, y + 560, 430, 150, "discarded on the way: power-aware miner,\n4 conditions per rule, 6-month admission,\n18-month window, the NAIVE overrule (-4.4)", 0.02, 16)
E.append(T("z4_f", x + 30, y + 760, "the moot court (replay before admitting a mined rule) cost accuracy: it starved rare rules of data", 18, RED))

# ---------------- 5. overruling precedents ----------------
x, y = Z(1, 1)
E += num("z5", x, y, 5, "the new idea: overruling precedents", "a stricter-law rule mined from OUTCOMES")
E += B("z5_q", x + 30, y + 120, 1040, 90, "inside ONE population, do above-policy approvals renew worse than that SAME population's in-policy deals?", "blue", 19)
E += H(B("z5_a", x + 60, y + 250, 300, 140, "US mid-market\nabove policy\nrenews 35%", "bad", 20))
E += H(B("z5_b", x + 420, y + 250, 300, 140, "US mid-market\nin policy\nrenews 85%", "ok", 20))
E += B("z5_r", x + 770, y + 250, 300, 140, "region = 'US' AND\nsegment = 'MM' AND\ndisc > 15  => REJECT", "dark", 18)
E.append(arrow("z5_ar", x + 722, y + 320, [[0, 0], [44, 0]], RED, "z5_b", "z5_r"))
E.append(T("z5_d", x + 300, y + 400, "drop of 0.50 >= 0.20 threshold", 18, RED))
E.append(T("z5_t", x + 30, y + 470, "the trap (experiment 1, dev -4.4): Simpson's paradox", 21, RED))
E += note("z5_n", x + 30, y + 520, 500, 150, "'region = US' looks harmful only because\nit mixes the rogue mid-market book with\nhealthy segments", -0.02, 17)
E += H(B("z5_f", x + 570, y + 520, 500, 150, "fix: the drop must survive every refinement\n(US & MM: yes · US & not MM: no -> reject 'US')\nthen: a statistical test, then Bonferroni", "ok", 17))
E.append(T("z5_c", x + 30, y + 720, "the honest label: an observational association screen, not causal identification", 18, MUTED))

# ---------------- 6. the Goodhart ----------------
x, y = Z(2, 1)
E += num("z6", x, y, 6, "the Goodhart we caught", "experiment 16: looked better, was worse")
E += B("z6_a", x + 30, y + 120, 500, 160, "'refinements must show the FULL 0.20 drop'\n\ndev: +0.181 -> +0.184  (kept)", "ok", 19)
E += H(B("z6_b", x + 570, y + 120, 500, 160, "stress panel, true drop 0.25:\n\nharm caught 96% -> 38%", "bad", 21))
E.append(arrow("z6_ab", x + 532, y + 200, [[0, 0], [34, 0]], RED, "z6_a", "z6_b"))
E += note("z6_why", x + 30, y + 330, 1040, 120, "why: every harmful world in dev had a 0.50 drop. Demanding 0.20 in every noisy sub-cell cost nothing there,\nand vetoed real harm near the threshold. The metric rewarded a check that destroyed sensitivity.", 0.01, 17)
E += B("z6_f1", x + 30, y + 500, 500, 130, "fix 1: a statistical refinement test\n(reject only on significant evidence)", "ok", 18)
E += B("z6_f2", x + 570, y + 500, 500, 130, "fix 2: the DEV PANEL was wrong:\nadd near-threshold harm to dev", "lava", 18)
E.append(T("z6_l", x + 30, y + 690, "lesson: when a change looks free on dev, ask what dev cannot see", 20, RED))

# ---------------- 7. the clean tests failed ----------------
x, y = Z(0, 2)
E += num("z7", x, y, 7, "then the clean tests failed: four times", "worlds nobody (including the agent) had seen")
xs = lambda v: x + 640 + v * 470     # -1.0 .. +0.8 points
for v, lab, col, sty in [(0.0, "0", SL, "solid"), (-0.25, "margin -0.25", RED, "dashed")]:
    E.append(line(f"z7_v{lab}", xs(v), y + 130, [[0, 0], [0, 540]], col, 2, sty)); E.append(T(f"z7_vl{lab}", xs(v) - 40, y + 680, lab, 16, col))
tests = [("fresh run 1", -0.419, -0.901, 0.063), ("fresh run 2", -0.042, -0.676, 0.591), ("confirm 1", C1["g"], C1["lo"], C1["hi"]), ("confirm 2", C2["g"], C2["lo"], C2["hi"])]
for k, (lab, g, lo, hi) in enumerate(tests):
    yy = y + 180 + k * 120
    E.append(T(f"z7_t{k}", x + 30, yy - 12, lab, 19))
    E.append(line(f"z7_ci{k}", xs(lo), yy, [[0, 0], [xs(hi) - xs(lo), 0]], RED, 4))
    E.append(dot(f"z7_d{k}", xs(g) - 9, yy - 9, "bad", 18))
    E.append(T(f"z7_g{k}", xs(hi) + 14, yy - 12, f"{g:+.3f}  FAIL", 17, RED))
E.append(T("z7_f", x + 30, y + 730, f"confirm 1 and 2: {C1['neg']} and {C2['neg']} of 24 worlds negative, intervals entirely below zero", 18, RED))
E.append(T("z7_f2", x + 30, y + 770, "each test: manifest (method + harness hashes) committed BEFORE the single run", 17, MUTED))

# ---------------- 8. the diagnosis ----------------
x, y = Z(1, 2)
E += num("z8", x, y, 8, "a pre-registered diagnosis", "detector experiment: 3 frozen methods, same 33 worlds")
d = [("H1 overrules cause the false rejections", f"supported: {DR['twolit']['nh_ovr_share']:.0%}", "ok"),
     ("H2 two-literal refinements fix it", f"FALSIFIED: -{DR['onelit']['nh_ovr_false_rej'] - DR['twolit']['nh_ovr_false_rej']} of {DR['onelit']['nh_ovr_false_rej']}", "bad"),
     ("H3 overrules are worth having", f"supported: {DR['twolit']['caught_strong']:.0f}% vs {DR['noovr']['caught_strong']:.0f}% harm caught", "ok")]
for k, (h, r, kd) in enumerate(d):
    E += B(f"z8_h{k}", x + 30, y + 120 + k * 110, 600, 90, h, "neu", 18)
    E += H(B(f"z8_r{k}", x + 660, y + 120 + k * 110, 410, 90, r, kd, 18))
E += note("z8_n1", x + 30, y + 480, 500, 150, "false overrules sat on thin numeric tails:\nterm > 2 AND tenure <= 0\nsize <= 28 AND tenure <= 1\n= multiple testing", -0.02, 16)
E += note("z8_n2", x + 570, y + 480, 500, 150, "and worlds with NO overrule still lost 0.3 pts:\nthe MINER missed generated rules\n(650k mined as '> 1000')", 0.02, 16)
E += B("z8_k", x + 30, y + 680, 1040, 110, "the real lesson: the dev panel contained NO generated worlds.\nLine 1 was tuned on a distribution unlike the test.", "lava", 20)

# ---------------- 9. line 2: what changed ----------------
x, y = Z(2, 2)
E += num("z9", x, y, 9, "line 2: fix the miner, on the right dev panel", "dev v4: 32 configs, half of them generated worlds")
steps2 = [("start\n(line 1 final)", 0.144), ("fine size\ngrid (2.5%)", 0.234), ("errors cost 2x\nin the miner", 0.305), ("overrule must beat\nthe THRESHOLD", 0.326)]
bx0, by0, sc = x + 90, y + 470, 800
E.append(line("z9_0", bx0 - 20, by0, [[0, 0], [700, 0]], SL, 2))
for k, (lab, v) in enumerate(steps2):
    h = v * sc
    E += H(B(f"z9_b{k}", bx0 + k * 170, by0 - h, 120, h, "", "ok", 14))
    E.append(T(f"z9_v{k}", bx0 + k * 170 + 10, by0 - h - 30, f"{v:+.3f}", 18, GRN))
    E.append(T(f"z9_l{k}", bx0 + k * 170 - 10, by0 + 14, lab, 14, MUTED))
E += note("z9_n", x + 800, y + 160, 280, 230, "discarded:\nCART threshold tuning\nprecision 0.95\nbeam 100\nerror weight 3 (flat)", 0.02, 16)
E += B("z9_e1", x + 30, y + 600, 500, 90, "before:  size_k > 1000 AND disc <= 28", "bad", 17)
E += B("z9_e2", x + 570, y + 600, 500, 90, "after:  size_k > 706 AND disc <= 28\n(hidden rule: size > 650)", "ok", 17)
E.append(arrow("z9_ea", x + 532, y + 645, [[0, 0], [34, 0]], GRN, "z9_e1", "z9_e2"))
E.append(T("z9_f", x + 30, y + 740, "generated worlds without overrules: -0.365 -> -0.033", 20, GRN))

# ---------------- 10. confirm 3 ----------------
x, y = Z(0, 3)
E += num("z10", x, y, 10, f"confirm 3: {C3['res']}", "one pre-registered run, 24 new worlds, simulator and compiler pinned")
for v, lab, col, sty in [(0.0, "0", SL, "solid"), (-0.25, "margin -0.25", RED, "dashed")]:
    E.append(line(f"z10_v{lab}", x + 640 + v * 600, y + 130, [[0, 0], [0, 380]], col, 2, sty))
    E.append(T(f"z10_vl{lab}", x + 640 + v * 600 - 40, y + 520, lab, 16, col))
X2 = lambda v: x + 640 + v * 600
for k, (lab, c) in enumerate([("confirm 1", C1), ("confirm 2", C2), ("confirm 3", C3)]):
    yy = y + 180 + k * 110; col = GRN if c["res"] == "PASS" else RED
    E.append(T(f"z10_t{k}", x + 30, yy - 12, lab, 19, col))
    E.append(line(f"z10_ci{k}", X2(c["lo"]), yy, [[0, 0], [X2(c["hi"]) - X2(c["lo"]), 0]], col, 4))
    E.append(dot(f"z10_d{k}", X2(c["g"]) - 9, yy - 9, "ok" if c["res"] == "PASS" else "bad", 18))
    E.append(T(f"z10_g{k}", X2(c["hi"]) + 14, yy - 12, f"{c['g']:+.3f} [{c['lo']:+.3f}, {c['hi']:+.3f}]  {c['res']}", 16, col))
E += H(B("z10_s1", x + 30, y + 590, 330, 110, f"exception worlds\n{EXC3:+.2f} pts", "ok", 19))
E += H(B("z10_s2", x + 385, y + 590, 330, 110, f"segment worlds\n{SEG3:+.2f} pts", "warn", 19))
E += B("z10_s3", x + 740, y + 590, 330, 110, f"{RULES3:.1f} rules on average\nharm caught 94% (lows 44%, 56%)", "blue", 17)
E.append(T("z10_f", x + 30, y + 750, "non-inferior, NOT superior: the interval contains zero · Bonferroni over all 3 tests still passes", 18, GRN))

# ---------------- 11. when it stops ----------------
x, y = Z(1, 3)
E += num("z11", x, y, 11, "when does autoresearch stop?", "the original: never, until a human interrupts it")
lv = [("inner loop", "at most 12 experiments, or 4 discards in a row\n(a plateau), then lock the method", "ok"),
      ("line", "exactly ONE confirmatory test, reported\nwhatever it shows", "warn"),
      ("question", "closed after 3 tests (2 FAIL, 1 PASS):\nmore lines are diagnostic only", "lava")]
for k, (n, d_, kd) in enumerate(lv):
    E += B(f"z11_n{k}", x + 30, y + 130 + k * 170, 230, 130, n, "dark", 22)
    E += H(B(f"z11_d{k}", x + 290, y + 130 + k * 170, 780, 130, d_, kd, 19))
E += note("z11_x", x + 60, y + 660, 980, 120, "why: 'keep tweaking and re-testing until something passes' is how a loop manufactures a result.\nLine 2 was allowed only because line 1's records diagnosed a NEW cause, and it is the last one.", -0.01, 17)

# ---------------- 12. what it does not show ----------------
x, y = Z(2, 3)
E += num("z12", x, y, 12, "what it does NOT show", "Astra round 4: record B+, narrow claim B, broad claim C-")
for k, s in enumerate(["that it works on a real firm (no real data with outcomes yet)",
                       "superiority (the interval contains zero)",
                       "parity with TUNED black boxes (the five are fixed, untuned)",
                       "which of the three line-2 changes did the work",
                       "harm detection under unobserved confounding (fooled, like every outcome method)",
                       "power for harm exactly at the 0.20 threshold (about 16% by construction)",
                       "that 6 readable rules are easier to govern (CCL's original claim: untested)"]):
    E.append(T(f"z12_x{k}", x + 40, y + 130 + k * 62, "✗  " + s, 19, RED if k < 1 else SL))
E += B("z12_n", x + 30, y + 600, 1040, 140, "next: one real dataset with decisions, the written policy, and what happened afterwards\n(renewal, default, churn). Without real outcomes, more simulation will not change the conclusion.", "lava", 19)
E.append(T("z12_src", x + 30, y + 790, "github.com/HadiFrt20/corporate-case-law · autoresearch/ (ADR.md, WORKLOG.md, CONFIRM_1-3.txt)", 16, MUTED))

save(os.path.join(HERE, "ar_board.excalidraw"), E)
print("elements", len(E))
