"""AR-014 analysis: computes H1, H2, H3 and the pre-registered selection rule from the detector dumps. No tuning here."""
import json, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
M = {k: json.load(open(os.path.join(HERE, f"detector_{k}.json"))) for k in ("twolit", "onelit", "noovr")}


def no_harm(c): return c["effect"] == "segment" or c.get("stress") == "confounded" or (c["effect"] == "exception" and c["bad_renew"] >= 0.70)
def strong_harm(c): return c["effect"] == "exception" and c["bad_renew"] in (0.60, 0.55) and not c.get("n")


def score(rs):
    g = []
    for r in rs:
        ccl = np.average(r["agree"], weights=r["n"]); g.append((ccl - max(r["base_cached"].values())) * 100)
    return float(np.mean(g))


def caught(rs):
    hc = sum(sum(r["harm_cases"]) for r in rs); return 100 * sum(sum(r["blocked_harm"]) for r in rs) / hc if hc else float("nan")


out = {}
for k, rs in M.items():
    nh = [r for r in rs if no_harm(r["cfg"])]
    fr = sum(sum(r["all_false_rej_n"]) for r in nh); ofr = sum(sum(r["ovr_false_rej"]) for r in nh)
    out[k] = dict(score=score(rs), rules=float(np.mean([np.mean(r["rules"]) for r in rs])),
                  nh_false_rej=fr, nh_ovr_false_rej=ofr, nh_ovr_share=(ofr / fr if fr else float("nan")),
                  caught_strong=caught([r for r in rs if strong_harm(r["cfg"])]),
                  ovr_months_noharm=float(np.mean([np.mean([len(p) > 0 for p in r["ovr_pops"]]) for r in nh])))
for k, v in out.items(): print(k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})

t, o, n = out["twolit"], out["onelit"], out["noovr"]
h1 = t["nh_ovr_share"] >= 0.5
red = 1 - t["nh_ovr_false_rej"] / o["nh_ovr_false_rej"] if o["nh_ovr_false_rej"] else float("nan")
h2 = red >= 0.30 and (o["caught_strong"] - t["caught_strong"]) <= 5
h3 = t["score"] > n["score"]
print(f"H1 overrules cause >=50% of no-harm false rejections (twolit): share {t['nh_ovr_share']:.1%} -> {'SUPPORTED' if h1 else 'NOT supported'}")
print(f"H2 two-literal cuts overrule false rejections >=30% without losing >5 pts of strong-harm catch: reduction {red:.1%}, "
      f"catch {o['caught_strong']:.1f} -> {t['caught_strong']:.1f} -> {'SUPPORTED' if h2 else 'NOT supported'}")
print(f"H3 twolit beats no-overrules on the detector panel: {t['score']:+.3f} vs {n['score']:+.3f} -> {'SUPPORTED' if h3 else 'NOT supported'}")
best = max(out, key=lambda k: out[k]["score"])
close = [k for k in out if out[best]["score"] - out[k]["score"] <= 0.02]
sel = min(close, key=lambda k: out[k]["rules"])
print(f"SELECTION (pre-registered): highest score {best}; within 0.02: {close}; selected {sel}")
json.dump(dict(stats=out, H1=h1, H2=h2, H3=h3, reduction=red, selected=sel), open(os.path.join(HERE, "detector_result.json"), "w"), indent=1)
