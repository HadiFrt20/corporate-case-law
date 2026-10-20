"""CLM paper (arXiv 2609.04377) as ONE continuous hand-drawn whiteboard: 12 numbered zones, read left->right, row by row."""
import sys, math, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exd
exd.ROUGH, exd.FONT = 1, 5
from exd import *
RED, GRN, BLU, PUR, AMB = "#C8102E", "#1F7A4D", "#2D5F8B", "#5B3E96", "#B26A00"
E = []
def tilt(els, a):
    for e in els: e["angle"] = a
    return els
def note(i, x, y, w, h, s, a=0.0, fs=18): return tilt(box(i, x, y, w, h, s, "sticky", fs, tcolor="#4A3B00"), a)
def num(i, x, y, n, title, sub=None):
    out = box(i, x, y, 54, 54, str(n), "lava", 24, shape="ellipse")
    out.append(text(i + "_h", x + 70, y + 6, title, 32, RED))
    if sub: out.append(text(i + "_s", x + 72, y + 50, sub, 18, MUTED))
    return out
def code(i, x, y, w, h, s, fs=15):
    r = box(i, x, y, w, h, "", "neu", fs)
    t = text(i + "_c", x + 16, y + 14, s, fs, BLU)
    t["fontFamily"] = 3
    return r + [t]
def hach(els):
    els[0]["fillStyle"] = "hachure"; return els

# ================= title + summary flow (zoom level 1) =================
E.append(text("t", 60, 20, "Corporate Language Model (CLM): the paper on one whiteboard", 46, SL))
E.append(line("t_ul", 60, 84, [[0, 0], [700, 7], [1500, 0]], RED, 3))
E.append(text("t_s", 60, 98, "arXiv 2609.04377 · Avini & Trez (Unisinos / Care Intelligence) · position paper · read zones 1 -> 12", 20, MUTED))
flow = ["org noise", "typed memory", "composed skills", "governed action", "audit + learn"]
for k, f in enumerate(flow):
    E += box(f"sf{k}", 1880 + k * 300, 30, 220, 60, f, ["warn", "ok", "lava", "blue", "ai"][k], 19, fill="hachure", tcolor=SL)
    if k: E.append(arrow(f"sfa{k}", 1880 + k * 300 - 78, 60, [[0, 0], [74, 0]], SL, f"sf{k-1}", f"sf{k}"))
E.append(arrow("sf_loop", 3180, 94, [[0, 0], [-60, 40], [-1100, 40], [-1190, 0]], MUTED, "sf4", "sf0", sw=1, style="dashed"))
E.append(text("sf_l", 2380, 140, "the whole paper in one line (it compounds: the loop)", 17, MUTED))

# ================= 1. the problem =================
E += num("n1", 60, 200, 1, "the problem", "why does AI keep failing on OUR business?")
E.append(text("p_claim", 80, 290, "the failure is EPISTEMIC, not linguistic:\nthe model writes fine, it just doesn't know how this firm decides", 21, RED))
E += note("P1", 70, 380, 300, 130, "P1  tacit knowledge\nis never written down\n(WhatsApp, calls, PDF margins)", -0.03, 17)
E += note("P2", 400, 370, 300, 130, "P2  LLMs know nothing\nabout YOUR ontology\n('qualified opp' here ≠ generic)", 0.02, 17)
E += note("P3", 730, 385, 300, 130, "P3  no audit path\n= legal rejects it, or\nsomeone signs blind", -0.02, 17)
E += note("P4", 180, 545, 300, 120, "P4  sovereignty is law\nLGPD / GDPR / HIPAA", 0.03, 17)
E += note("P5", 560, 545, 330, 120, "P5  playbooks can't adapt,\nagents can't be audited", -0.025, 17)
E += hach(box("p_box", 230, 730, 600, 90, "treat all 5 as DESIGN CONSTRAINTS from day 1\n(not a feature backlog)  <- the core move", "lava", 20, tcolor=SL))
routes = [(220, 512, [[0, 0], [-70, 150], [40, 214]]), (550, 502, [[0, 0], [0, 224]]), (880, 517, [[0, 0], [50, 100], [-60, 209]]),
          (330, 667, [[0, 0], [20, 59]]), (725, 667, [[0, 0], [-25, 59]])]
for k, (sx, sy, pts) in enumerate(routes):
    E.append(arrow(f"pa{k}", sx, sy, pts, MUTED, f"P{k+1}", "p_box", sw=1))
E.append(text("p_bad", 80, 850, "3 answers that don't cut it:", 21, SL))
E.append(text("p_b1", 100, 890, "x  RAG: depends on corpus quality, loosely tied to the ontology, can't act", 18, RED))
E.append(text("p_b2", 100, 925, "x  prompt eng / fine-tune: helps at the margins; fine-tune = frozen statistics", 18, RED))
E.append(text("p_b3", 100, 960, "x  static playbooks: faithful but rigid, out of date the day the business changes", 18, RED))

# ================= 2. the stack =================
E += num("n2", 1180, 200, 2, "the architecture: 5 planes", "4 stacked + 1 that wraps everything")
E += box("ds", 1200, 290, 1000, 660, "", "neu", 16, style="dashed")
E[-2]["backgroundColor"] = "transparent"; E[-2]["strokeColor"] = RED
E.append(text("ds_l", 1230, 304, "DEEP SECURITY LAYER (plane 5, transversal): wraps every plane, see zone 6", 18, RED))
planes = [("gov", "Governance: audit trail · ROI · rollback\nevery output = Skill->Objection->Persona->Goal path", "ai", "why we trust it"),
          ("wo", "Wisdom-Out: persona voice · route to stage\ncall legacy systems via MCP", "blue", "how to deliver"),
          ("tac", "Tactical: Skill Graph + Living Twins\nNO free-form prompts, ever", "lava", "how to act"),
          ("fnd", "Foundation: ingest -> extract -> bind to ontology\nmemory w/ provenance + ACL + types (not a vector store)", "ok", "what is known")]
for k, (pid, lab, kind, why) in enumerate(planes):
    y = 360 + k * 135
    E += hach(box(pid, 1290, y, 640, 105, lab, kind, 18, tcolor=SL))
    E.append(text(pid + "_w", 1950, y + 38, why, 20, C[kind][1]))
E.append(arrow("up", 1250, 880, [[0, 0], [0, -500]], SL, None, None, sw=3))
E.append(text("up_l", 1215, 900, "each plane needs the one below -> stages can't be skipped (zone 8)", 17, SL))
E.append(text("ds_n", 1990, 300 + 640, "", 1, MUTED))
E.append(text("typo", 1630, 960, "(paper's Fig.1 labels Tactical 'why we trust it' too: a typo)", 14, MUTED))
E.append(arrow("a12", 832, 775, [[0, 0], [452, -90]], RED, "p_box", "fnd"))
E.append(text("a12_l", 900, 690, "so build a foundation", 18, RED))

# ================= 3. neurosymbolic mesh =================
E += num("n3", 2330, 200, 3, "pillar 1: Neurosymbolic Mesh", "the only part with real mechanics: guarded generation")
E.append(text("m_eq", 2350, 290, "LLM (fluent)  +  knowledge graph (typed rules)  =  fluid outside, governed inside", 20, PUR))
E += hach(box("m_llm", 2350, 390, 180, 90, "LLM / SLM\ndrafts", "ai", 19, tcolor=SL))
E += code("m_ir", 2590, 370, 260, 130, '{ "entity": ...,\n  "relation": ...,\n  "policy": ...,\n  "provenance": ... }', 15)
E.append(text("m_ir_l", 2600, 508, "schema-bounded draft\n(JSON-LD from the ontology)", 15, MUTED))
E += hach(box("m_val", 2910, 355, 230, 160, "symbolic\nvalidator", "warn", 20, shape="diamond", tcolor=SL))
E += hach(box("m_out", 3200, 390, 180, 90, "render prose\nor spec", "ok", 19, tcolor=SL))
E.append(arrow("ma1", 2532, 435, [[0, 0], [56, 0]], PUR, "m_llm", "m_ir"))
E.append(arrow("ma2", 2852, 435, [[0, 0], [56, 0]], BLU, "m_ir", "m_val"))
E.append(arrow("ma3", 3142, 435, [[0, 0], [56, 0]], GRN, "m_val", "m_out"))
E.append(text("ma3_l", 3150, 400, "pass", 16, GRN))
E.append(arrow("ma_fail", 3025, 518, [[0, 0], [0, 90], [-585, 90], [-585, -36]], RED, "m_val", "m_llm"))
E.append(text("mf_l", 2560, 618, "FAIL -> rejected, not down-ranked -> repair or regenerate with the violation", 17, RED))
E.append(text("m_chk", 2350, 670, "validator asks: entity exists in ontology?  relation legal?  policy ok for this tenant?  provenance attached?", 17, SL))
E += box("m_rag", 2350, 730, 480, 120, "classic RAG:\nretrieved text goes IN, then\nthe model writes freely", "bad", 18)
E += box("m_mesh", 2880, 730, 500, 120, "the Mesh:\nthe graph CONSTRAINS what comes OUT\n(off-ontology output = inadmissible)", "ok", 18)
E.append(text("m_vs", 2838, 775, "vs", 22, SL))
E.append(text("m_hon", 2350, 870, "honest: they say it's NOT constrained decoding everywhere, just high-stakes paths", 17, MUTED))
E.append(text("m_why", 2350, 905, "-> this is their answer to 'isn't it just GraphRAG + agents + compliance?'", 18, RED))
E.append(arrow("a23", 2202, 300, [[0, 0], [126, -40]], MUTED, "ds", None, sw=1, style="dashed"))
E.append(text("a23_l", 2120, 230, "4 pillars give\nplanes their form", 15, MUTED))

# ================= 4. skill graph (hero) =================
E += num("n4", 60, 1110, 4, "pillar 2: the Skill Graph", "the paper's signature idea. worked example from the paper")
ctx = [("c_obj", "objection:\nprice_surface"), ("c_per", "persona:\nCFO"), ("c_stg", "stage:\nlate_negotiation"), ("c_goal", "goal:\nmargin_preservation")]
for k, (cid, lab) in enumerate(ctx):
    E += hach(box(cid, 80, 1240 + k * 135, 250, 95, lab, "warn", 17, shape="ellipse", tcolor=SL))
E.append(text("c_l", 85, 1205, "context vector c (detected)", 17, AMB))
E += hach(box("f_dia", 420, 1390, 200, 170, "filter\nS(c)", "blue", 21, shape="diamond", tcolor=SL))
for k in range(4):
    yy = 1287 + k * 135
    E.append(arrow(f"ca{k}", 332, yy, [[0, 0], [86, 1475 - yy]], AMB, ctx[k][0], "f_dia", sw=1))
skills = [("s1", "value-reframing", "ok"), ("s2", "concession-boundary", "ok"), ("s3", "social-proof", "ok")]
for k, (sid, lab, kind) in enumerate(skills):
    E += hach(box(sid, 730, 1250 + k * 115, 260, 75, lab, kind, 19, tcolor=SL))
    E.append(arrow(f"fa{k}", 622, 1475, [[0, 0], [106, 1287 + k * 115 - 1475]], GRN, "f_dia", sid, sw=2))
E += box("s_x", 730, 1600, 260, 70, "discount-now\n(illustrative reject)", "bad", 16, style="dashed")
E.append(arrow("fax", 600, 1520, [[0, 0], [128, 115]], RED, "f_dia", "s_x", sw=1, style="dashed"))
E.append(text("f_steps", 420, 1580, "edges walked:\ntreats_objection\nbest_for_persona\nworks_in_stage\nthen rank", 15, BLU))
E.append(text("s_out", 1000, 1275, "output = a\nCOMPOSITION\nof 3 skills,\nkept consistent\nby edge types", 18, GRN))
E.append(text("s_expl", 1000, 1440, "the path\nIS the\nexplanation", 24, RED))
E.append(line("s_expl_u", 1000, 1535, [[0, 0], [70, 3], [140, 0]], RED, 2))
E += code("score", 80, 1790, 620, 150, "Score(s|c) = 0.4·A + 0.4·E − 0.2·R\n  A = fit to context      R = risk 0.1 / 0.3 / 0.6\n  E = EMA (α=0.3) of outcomes, last 500 events\n      success +.15  partial +.05\n      fail −.10   abandoned −.05", 16)
E.append(text("score_l", 80, 1950, "hand-set weights (declared in code, not learned) -> auditable, but arbitrary", 16, MUTED))
E += note("gap", 740, 1720, 330, 120, "bonus: empty graph region\n= a persona/stage/objection\nwith NO playbook (gap finder)", 0.03, 16)
E.append(text("g_real", 740, 1870, "real graph today: 41 nodes,\n100 edges, 2 objections (!)\nmatcher = keyword substring", 17, RED))
E.append(text("g_typ", 80, 1990, "graph G=(V,E,τV,τE): 5 node types (skill, persona, objection, goal, stage) · 9 edge types", 16, SL))
E.append(arrow("a34", 2700, 960, [[0, 0], [-1500, 140], [-1720, 240]], MUTED, None, "f_dia", sw=1, style="dashed"))
E.append(text("a34_l", 1700, 1040, "pillar 2 = where the 'reasoning' lives", 16, MUTED))

# ================= 5. living twins =================
E += num("n5", 1180, 1110, 5, "pillar 3: Living Digital Twins", "a surrogate for how a FUNCTION decides, not a machine")
tw = [("tw1", 1210, 1240, 250, 120, "commercial"), ("tw2", 1400, 1210, 250, 120, "finance"), ("tw3", 1590, 1250, 230, 115, "operations"),
      ("tw4", 1260, 1350, 270, 115, "customer success"), ("tw5", 1500, 1345, 270, 120, "owner / founder")]
for tid, x, y, w, h, lab in tw:
    E += box(tid, x, y, w, h, lab, "blue", 19, shape="ellipse")
    E[-2]["backgroundColor"] = "transparent"
E.append(text("tw_l", 1210, 1490, "each twin = typed params (incentives, evidence thresholds,\nstyle) updated as evidence accumulates", 17, BLU))
steps = ["hydrate: fetch only relevant, PERMITTED, current context (ACL at retrieval)", "simulate: walk the Skill Graph for 2nd-order effects",
         "re-weight: reconcile finance vs sales vs ops views", "adjust: same logic, CFO register vs field-rep register"]
E.append(line("tl", 1230, 1590, [[0, 0], [0, 270]], SL, 2))
for k, s in enumerate(steps):
    E.append(dot(f"td{k}", 1224, 1600 + k * 85, "lava", 14))
    E.append(text(f"tt{k}", 1255, 1594 + k * 85, f"{k+1}. {s}", 17, SL))
E.append(text("tl_h", 1255, 1560, "runtime sequence, every request:", 17, MUTED))
E += note("tw_q", 1860, 1220, 320, 130, "\"a manufacturing twin: how a\nmachine behaves under load.\na CLM twin: how a CFO\nreasons under margin pressure\"", 0.03, 15)
E.append(text("tw_c", 1880, 1380, "\"not chatbots in costume\"", 19, PUR))
E.append(text("tw_r", 1230, 1920, "reality: twin session state lives in process memory -> lost on restart\n(a Lakebase-shaped hole, see zone 11)", 17, RED))

# ================= 6. deep security rings =================
E += num("n6", 2330, 1110, 6, "pillar 4: Deep Security = 3 rings", "the generator only reaches the world through every ring")
cx, cy = 2860, 1600
rings = [("r_sov", 900, 620, "lava"), ("r_hitl", 660, 450, "warn"), ("r_gov", 420, 280, "ai"), ("r_core", 200, 100, "dark")]
for rid, w, h, kind in rings:
    lab = "generative\nengine" if rid == "r_core" else ""
    E += box(rid, cx - w / 2, cy - h / 2, w, h, lab, kind, 17, shape="ellipse")
    if rid != "r_core": E[-2]["backgroundColor"] = "transparent"; E[-2]["strokeWidth"] = 3
for rid, lab, col, y, w in [("rl_sov", "SOVEREIGNTY ring", RED, 1300, 190), ("rl_hitl", "HUMAN-IN-THE-LOOP ring", AMB, 1402, 250), ("rl_gov", "GOVERNANCE ring", PUR, 1492, 180)]:
    E.append(text(rid, cx - w / 2, y, lab, 18, col, "center", w))
E.append(text("rd_sov", 2420, 1920, "sovereignty: data (+ models where feasible) stay inside · tenant isolation · rollback declared up front", 15, RED))
E.append(text("rd_hitl", 2420, 1945, "human-in-loop: approval before legacy write-back, money, contract change (approvals logged + learned)", 15, AMB))
E.append(text("rd_gov", 2420, 1970, "governance: provenance on every artifact · secret scanning · prompt-injection firewall vs ontology", 15, PUR))
E.append(arrow("r_out", 2962, 1600, [[0, 0], [430, 0]], SL, "r_core", None, sw=3))
E.append(text("r_out_l", 3290, 1540, "real world", 18, SL))
E.append(text("r_flo", 2420, 2002, "4 floors: sovereign by default · legacy kept (not ripped out) · ground truth before generation · human oversight mandatory", 16, SL))
E.append(text("r_hos", 2420, 2030, "hospital proof: local-only de-identification upstream, nothing leaves the perimeter -> LGPD approval", 16, GRN))

# ================= 7. spec-as-code =================
E += num("n7", 60, 2090, 7, "Spec-as-Code: intent -> 4 artifacts", "fixes the 'semantic fall off the cliff' (good advice, no path to action)")
E += code("si", 80, 2210, 500, 330, '{ "@type": "SemanticIntent",\n  "goal": "generate-jci-aligned-\n           discharge-summary",\n  "constraints": {\n    "regulatoryFramework": ["LGPD","JCI"],\n    "deploymentMode": "on-premise",\n    "requiresHumanApproval": true },\n  "acceptanceCriteria": [\n    "Include mandatory JCI sections",\n    "Preserve provenance",\n    "Reject if ontology check fails" ] }', 15)
E.append(text("si_l", 80, 2550, "real example from the hospital deployment", 15, MUTED))
chain = [("bs", "Business Spec", "lava"), ("bdd", "BDD: Given / When / Then", "warn"), ("tst", "tests", "neu"), ("ic", "Interface Contracts", "blue"), ("ts", "Technical Spec", "ai")]
for k, (cid, lab, kind) in enumerate(chain):
    E += hach(box(cid, 680, 2210 + k * 80, 330, 56, lab, kind, 18, tcolor=SL))
    if k: E.append(arrow(f"ch{k}", 845, 2210 + k * 80 - 22, [[0, 0], [0, 20]], SL, chain[k-1][0], cid, sw=2))
E.append(arrow("si_a", 582, 2300, [[0, 0], [96, -60]], BLU, "si", "bs"))
E.append(text("ch_l", 680, 2610, "ONE derivation chain -> 'consistent by construction'\n-> change impact + rollback become tractable", 17, SL))
E += note("who", 80, 2620, 360, 110, "who writes it: the hospital's\nQUALITY COMMITTEE, not engineers", -0.02, 17)
E.append(text("si_r", 470, 2700, "compiler heuristics = proprietary, not shown", 17, RED))

# ================= 8. maturity staircase =================
E += num("n8", 1180, 2090, 8, "rollout: 6 stages, no skipping", "each stage useful alone, each needs the one before")
st = [("1 capture +\ngrounding", "ok", "solid"), ("2 reliable\nretrieval", "ok", "solid"), ("3 twins", "ok", "solid"),
      ("4 domain\nSLMs", "warn", "solid"), ("5 spec-as-\ncode", "neu", "dashed"), ("6 governed\nactuation", "neu", "dashed")]
for k, (lab, kind, style) in enumerate(st):
    x, y = 1210 + k * 165, 2640 - k * 80
    E += hach(box(f"st{k}", x, y, 155, 80 + k * 80, lab, kind, 17, style=style, tcolor=SL))
    E[-1]["y"] = y + 10; E[-1]["verticalAlign"] = "top"
E.append(text("st_lg", 1210, 2810, "green = in production · amber = in test · dashed = still a design (snapshot 26 Apr 2026)", 16, SL))
E.append(text("st_cl", 1210, 2200, "claim: trying stage 6 without 2-3 =\n'root cause of most failed enterprise\nAI projects'  <- asserted, no data", 17, RED))
E.append(text("st_hos", 1210, 2860, "hospital: Clinical Aggregator container INSIDE the EHR env;\ngo-live 'scheduled' 29 Apr 2026 = 3 days AFTER the evidence snapshot", 16, AMB))

# ================= 9. wisdom listener flywheel =================
E += num("n9", 2330, 2090, 9, "the 'Wisdom Listener' effect", "new term: value compounds with use")
fc, fr = (2860, 2560), 270
fw = ["more tacit\ncaptured", "sharper skill\nselection", "twins more\naccurate", "better\noutputs", "humans delegate\nmore work"]
pos = []
for k, lab in enumerate(fw):
    a = math.radians(-90 + k * 72); x = fc[0] + fr * math.cos(a) - 105; y = fc[1] + fr * 0.8 * math.sin(a) - 38
    pos.append((x, y)); E += hach(box(f"fw{k}", x, y, 210, 76, lab, "ok", 17, tcolor=SL))
for k in range(5):
    (x1, y1), (x2, y2) = pos[k], pos[(k + 1) % 5]
    sx, sy, ex, ey = x1 + 105, y1 + 38, x2 + 105, y2 + 38
    dx, dy = ex - sx, ey - sy; d = math.hypot(dx, dy); ux, uy = dx / d, dy / d
    sx, sy, ex, ey = sx + ux * 110, sy + uy * 50, ex - ux * 110, ey - uy * 50
    E.append(arrow(f"fwa{k}", sx, sy, [[0, 0], [ex - sx, ey - sy]], GRN, f"fw{k}", f"fw{(k+1)%5}"))
E.append(text("fw_c", 2770, 2540, "flywheel", 26, GRN))
E += note("fw_r", 3170, 2250, 230, 150, "0 production\nsignals stored.\n= a hypothesis\nwith a name", 0.05, 18)
E.append(text("fw_t", 2420, 2900, "theory hooks: Teece dynamic capabilities · Argote learning curves · Nonaka SECI", 16, MUTED))

# ================= 10. reality check =================
E += num("n10", 60, 3020, 10, "reality check: claimed vs shown", "a position paper by the vendor. no baseline, no ablation, no metrics")
rc = [("tacit knowledge captured continuously", "mechanism never described; skills hand-coded"),
      ("explainable by construction", "explains which skill was picked, not the LLM's final text"),
      ("value compounds (Wisdom Listener)", "0 outcome signals; single April snapshot"),
      ("4 artifacts consistent by construction", "compiler is proprietary"),
      ("beats RAG/GraphRAG/platforms (Table 1)", "self-graded: CLM 'Yes' on all 6 rows"),
      ("deployed in a JCI hospital", "only plane 1 + de-ID + one spec; Skill Graph demo is SALES")]
E.append(text("rc_h1", 80, 3130, "CLAIMED", 22, AMB)); E.append(text("rc_h2", 600, 3130, "ACTUALLY SHOWN", 22, RED))
for k, (a, b) in enumerate(rc):
    y = 3175 + k * 60
    E.append(text(f"rca{k}", 80, y, a, 17, SL))
    E.append(arrow(f"rcx{k}", 520, y + 11, [[0, 0], [66, 0]], RED, None, None, sw=1))
    E.append(text(f"rcb{k}", 600, y, b, 17, RED))
E += note("prior", 80, 3560, 480, 150, "not cited, but obviously related:\n1980s expert systems (the knowledge\nacquisition bottleneck!) · Palantir\nOntology/AIP · constrained decoding · SHACL", -0.02, 16)
E += note("coi", 620, 3570, 420, 120, "authors = Care Intelligence founders;\n'authorship' registered w/ book chamber;\nwritten with Claude (disclosed)", 0.03, 16)
E.append(text("verdict", 80, 3740, "verdict: good vocabulary + one buildable pattern (guarded generation). NOT evidence.", 21, SL))
E.append(line("verdict_u", 80, 3772, [[0, 0], [500, 4], [960, 0]], RED, 2))

# ================= 11. databricks translation =================
E += num("n11", 1180, 3020, 11, "on Databricks (my mapping)", "every layer has a governed primitive. verify statuses before using")
mp = [("Foundation plane", "Unity Catalog + lineage + metric views", GRN),
      ("Skill Graph", "UC Skills securables · UC functions as Genie trusted assets", GRN),
      ("twin session state", "Lakebase (fixes their 'lost on restart')", GRN),
      ("guarded generation", "structured outputs + UC functions + MLflow 3 judges", GRN),
      ("governed legacy tools", "UC HTTP connections / managed MCP", GRN),
      ("security rings", "Unity AI Gateway policies + budgets + audit · Apps OBO", GRN),
      ("sovereignty floor", "GAP: in-region + customer governance, not air-gapped", RED)]
E.append(text("mp_root", 1210, 3120, "CLM", 24, SL))
E.append(line("mp_trunk", 1235, 3155, [[0, 0], [0, 6 * 70 + 18]], SL, 2))
for k, (a, b, col) in enumerate(mp):
    y = 3170 + k * 70
    E.append(line(f"mpb{k}", 1235, y + 12, [[0, 0], [30, 0]], SL, 2))
    E.append(text(f"mpa{k}", 1275, y, a, 18, SL))
    E.append(text(f"mpd{k}", 1500, y, "-> " + b, 17, col))
E.append(text("mp_use", 1210, 3680, "use it: in the GEO article (ontology idea) + agent-governance PoV\n(their 3 rings vs 'IdP = identity, UC + UAIG = system of record')", 17, BLU))

# ================= 12. explain it back =================
E += num("n12", 2330, 3020, 12, "explain it back (self-test)", "answer out loud before reading the chat answers")
qs = ["Q1  why is CLM NOT just\nGraphRAG + agents +\na compliance wrapper?", "Q2  walk the CFO price-\nobjection traversal:\nwhich edges, which score?",
      "Q3  what does 'explainable\nby construction' NOT\nexplain?", "Q4  why can't you jump\nstraight to stage 6?",
      "Q5  which experiment would\nconvince you the flywheel\nis real?", "Q6  a French hospital asks for\nthis on Databricks. what's\nyour honest gap?"]
for k, q in enumerate(qs):
    x, y = 2360 + (k % 2) * 520, 3120 + (k // 2) * 200
    E += note(f"q{k}", x, y, 460, 160, q, [-0.03, 0.025, 0.02, -0.03, -0.02, 0.03][k], 19)
E.append(text("foot", 60, 3830, "source: arXiv 2609.04377 v1 (posted 2026-09-03), 22 pp · board by Claude for Hadi · 15 Oct 2026", 15, MUTED))

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clm_board.excalidraw")
E = [e for e in E if not (e["type"] == "text" and e["text"] == "")]
_ids = {e["id"] for e in E}
for e in E:
    if e.get("boundElements"): e["boundElements"] = [b for b in e["boundElements"] if b["id"] in _ids] or None
save(out, E)
print(len(E), out)
