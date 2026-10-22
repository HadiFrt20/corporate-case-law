"""Trusted world definitions for the CCL autoresearch harness (human-owned, frozen with the harness).

A configuration is a dict: world, effect ("exception" | "segment"), seed, bad_renew, stress (optional).
  world: "easy" | "hard"            planted rules from ccl_sim
         "alt"                      a fixed alternative world (monitoring panel)
         "gen:<n>"                  a world generated from rule templates with generator seed n (fresh test)
  stress: None
          "confounded"              a non-causal drop: in one population, above-policy deals renew badly
                                    WHETHER OR NOT they are approved (weak customers get bigger discounts);
                                    approving them causes nothing, so the harm oracle says not harmful
"""
import numpy as np
import ccl_sim as C

ALT_LOOSEN = [
    ("A1 mid-market vs competitor <=27", lambda d: (d.segment == "MM") & d.competitor, 27),
    ("A2 long-tenure renewal <=24", lambda d: d.renewal & (d.tenure_y >= 8), 24),
    ("A3 deal > 750k <=22", lambda d: d.size_k > 750, 22),
    ("A4 UK quarter-end <=21", lambda d: (d.region == "UK") & d.quarter_end, 21),
    ("A5 France enterprise rogue approver <=34 (bad outcomes)", lambda d: (d.region == "FR") & (d.segment == "ENT"), 34),
]
ALT_TIGHT = ("A0 US SMB stricter >9 rejected", lambda d: (d.region == "US") & (d.segment == "SMB"), 9)
SEGS, REGS, BOOLS = ["SMB", "MM", "ENT"], ["FR", "DE", "UK", "US"], ["renewal", "quarter_end", "competitor", "churn_high"]


def generated(n):
    """a fresh planted-rule world from templates: 4 legitimate exceptions of mixed shapes, 1 rogue approver, 1 stricter rule"""
    r = np.random.default_rng(10_000 + n)
    seg, reg, b = (lambda: str(r.choice(SEGS))), (lambda: str(r.choice(REGS))), (lambda: str(r.choice(BOOLS)))
    shapes = []
    s1, s2 = seg(), b(); shapes.append((f"G conj {s1} & {s2}", lambda d, s1=s1, s2=s2: (d.segment == s1) & d[s2]))
    t = int(r.integers(4, 13)); s3 = b(); shapes.append((f"G tenure >= {t} & {s3}", lambda d, t=t, s3=s3: (d.tenure_y >= t) & d[s3]))
    k = int(r.choice([300, 420, 650, 900])); shapes.append((f"G size > {k}", lambda d, k=k: d.size_k > k))
    g1, g2 = reg(), b(); shapes.append((f"G {g2} outside {g1}", lambda d, g1=g1, g2=g2: d[g2] & (d.region != g1)))
    loosen = [(name, fn, int(r.integers(18, 31))) for name, fn in shapes]
    rs, rr = seg(), reg()
    loosen.append((f"G rogue {rr} {rs} (bad outcomes)", lambda d, rs=rs, rr=rr: (d.segment == rs) & (d.region == rr), int(r.integers(30, 36))))
    ts, tr = seg(), reg()
    while (ts, tr) == (rs, rr): ts, tr = seg(), reg()
    tight = (f"G stricter {tr} {ts}", lambda d, ts=ts, tr=tr: (d.segment == ts) & (d.region == tr), int(r.integers(8, 12)))
    return loosen, tight


def setup(cfg):
    C.ROGUE_EFFECT, C.LAW_REF = cfg["effect"], "global"
    w = cfg["world"]
    if w in ("easy", "hard"): C.set_world(w); return
    C.set_world("hard")                                   # tenure_y exists in every non-easy world
    C.LOOSEN, C.TIGHT = (ALT_LOOSEN, ALT_TIGHT) if w == "alt" else generated(int(w.split(":")[1]))
    C.ROGUE = C.LOOSEN[-1][0]


def firm(cfg):
    setup(cfg)
    rng = np.random.default_rng(cfg["seed"])
    df = C.make_firm(rng, int(cfg.get("n", 120000)), cfg.get("bad_renew", 0.35))   # n: smaller firms = small cells (detector panel)
    if cfg.get("stress") == "confounded":
        # one population (not the rogue one) whose above-policy deals renew at 0.50 regardless of approval
        q = np.random.default_rng(cfg["seed"] + 7)
        pop = (df.segment == str(q.choice(SEGS))) & (df.region == str(q.choice(REGS))) & (df.binding.values != C.ROGUE)
        weak = pop.values & (df.disc.values > C.STATUTE_CAP)
        df.loc[weak, "renewed"] = q.random(int(weak.sum())) < 0.50   # not caused by approval: harm_oracle unchanged
    return df, C.features(df)
