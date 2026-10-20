"""Render blog figures as crops of the real boards (whiteboard/combined.excalidraw), one zone at a time.

Each zone figure gets a header band with a "you are here" locator: zones already shown in the post are
filled, the current zone is red, the rest are outlines. ORDER is the order the zones appear in BLOG.md.
"""
import json, os, subprocess
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); BOARD = os.path.join(HERE, "..", "whiteboard", "combined.excalidraw")
RENDER = os.path.expanduser("~/.claude/skills/excalidraw-diagram/references")
Image.MAX_IMAGE_PIXELS = None
C1, C2, C3 = (40, 1150), (1160, 2300), (2310, 3460)
R1, R2, R3, R4 = (180, 1080), (1090, 2060), (2070, 3000), (3000, 3900)
D1, D2, D3 = (3700, 4800), (4880, 5960), (6030, 7150)
ZONES = {  # board: {zone: (name, (x0, x1), (y0, y1), title)}
    1: {0: ("b1_z00_oneline", (-50, 3500), (-50, 175), "the whole paper in one line"),
        1: ("b1_z01_problem", C1, R1, "the problem"), 2: ("b1_z02_planes", C2, R1, "the architecture: 5 planes"),
        3: ("b1_z03_mesh", C3, R1, "pillar 1: Neurosymbolic Mesh"), 4: ("b1_z04_skillgraph", C1, R2, "pillar 2: the Skill Graph"),
        5: ("b1_z05_twins", C2, R2, "pillar 3: Living Digital Twins"), 6: ("b1_z06_security", C3, R2, "pillar 4: Deep Security"),
        7: ("b1_z07_spec", C1, R3, "Spec-as-Code"), 8: ("b1_z08_rollout", C2, R3, "rollout: 6 stages"),
        9: ("b1_z09_flywheel", C3, R3, "the Wisdom Listener flywheel"), 10: ("b1_z10_reality", C1, R4, "reality check"),
        11: ("b1_z11_databricks", C2, R4, "on Databricks (my mapping)"), 12: ("b1_z12_selftest", C3, R4, "explain it back")},
    2: {1: ("b2_z01_holes", D1, (190, 1060), "CLM's 3 holes"), 2: ("b2_z02_residual", D2, (190, 1060), "the residual of policy"),
        3: ("b2_z03_replay", D3, (190, 1060), "replay: facts as of the decision"), 4: ("b2_z04_pipeline", (3700, 7150), (1085, 2000), "the pipeline"),
        5: ("b2_z05_code", D1, (2085, 2950), "a holding is code"), 6: ("b2_z06_results", D2, (2085, 2950), "tested: v5"),
        7: ("b2_z07_novelty", D3, (2085, 2950), "novel? the honest answer"), 8: ("b2_z08_kill", (3700, 7150), (3000, 3460), "next experiments + kill rule"),
        9: ("b2_z09_dbx", D1, (3480, 4300), "built on Databricks"), 10: ("b2_z10_hmda", D2, (3480, 4300), "real decisions"),
        11: ("b2_z11_rare_causal", D3, (3480, 4300), "rare rules + causal check")}}
ORDER = {1: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 2: [1, 2, 7, 5, 3, 4, 6, 11, 10, 9, 8]}  # appearance order in BLOG.md
WIDE = {"b1_z00_oneline", "b2_z04_pipeline", "b2_z08_kill"}
# locator layout: (col, row, colspan) on a 3-wide grid; board 1 row 0 = the one-line strip
GRID = {1: {0: (0, 0, 3), **{z: ((z - 1) % 3, (z - 1) // 3 + 1, 1) for z in range(1, 13)}},
        2: {1: (0, 0, 1), 2: (1, 0, 1), 3: (2, 0, 1), 4: (0, 1, 3), 5: (0, 2, 1), 6: (1, 2, 1), 7: (2, 2, 1),
            8: (0, 3, 3), 9: (0, 4, 1), 10: (1, 4, 1), 11: (2, 4, 1)}}
LAVA, SLATE, OAT, SEEN = (255, 54, 33), (27, 49, 57), (249, 247, 244), (203, 213, 216)
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"; FONT_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


def crop_board(d, name, x0, x1, y0, y1, anchors=False):
    """Write the elements fully inside the window to an .excalidraw file and render it."""
    def bbox(e):
        if e.get("points"):
            xs = [p[0] for p in e["points"]]; ys = [p[1] for p in e["points"]]
            return e["x"] + min(xs), e["x"] + max(xs), e["y"] + min(ys), e["y"] + max(ys)
        return e["x"], e["x"] + e.get("width", 0), e["y"], e["y"] + e.get("height", 0)
    def inside(e):
        a, b_, c, d_ = bbox(e)
        return a >= x0 - 20 and c >= y0 - 15 and b_ <= x1 + 60 and d_ <= y1 + 20  # tight: neighbouring zones must not leak in
    els = [json.loads(json.dumps(e)) for e in d["elements"] if inside(e)]
    ids = {e["id"] for e in els}
    els = [e for e in els if not (e.get("containerId") and e["containerId"] not in ids)]
    for e in els:
        for k in ("startBinding", "endBinding"):
            if e.get(k) and e[k]["elementId"] not in ids: e[k] = None
        if e.get("boundElements"): e["boundElements"] = [b for b in e["boundElements"] if b["id"] in ids] or None
    if anchors:  # invisible corner dots so every recap row renders with the same canvas width
        base = next(e for e in els if e["type"] == "rectangle")
        els += [dict(base, id=f"anchor_{name}_{i}", x=x, y=y0, width=1, height=1, strokeColor="transparent", backgroundColor="transparent",
                     boundElements=None, groupIds=[], frameId=None) for i, x in enumerate((x0, x1))]
    f = os.path.join(HERE, "_crops", name + ".excalidraw"); json.dump(dict(d, elements=els), open(f, "w"))
    subprocess.run(["uv", "run", "python", "render_excalidraw.py", f, "--width", str(int(x1 - x0) + 200)], cwd=RENDER, capture_output=True, check=True)
    return Image.open(f.replace(".excalidraw", ".png")).convert("RGB")


def locator(board, current, cell=34, gap=5):
    """Mini map of the board: seen zones filled, current zone red, unseen zones outlined."""
    g = GRID[board]; rows = max(r for _, r, _ in g.values()) + 1
    h_row = lambda r: cell // 2 if board == 1 and r == 0 else cell
    W = 3 * cell + 2 * gap; H = sum(h_row(r) for r in range(rows)) + gap * (rows - 1)
    im = Image.new("RGB", (W + 2, H + 2), OAT); dr = ImageDraw.Draw(im); f = ImageFont.truetype(FONT_B, 13)
    seen = set(ORDER[board][:ORDER[board].index(current)])
    for z, (c, r, span) in g.items():
        x = c * (cell + gap); y = sum(h_row(k) for k in range(r)) + gap * r; w = span * cell + (span - 1) * gap
        fill = LAVA if z == current else SEEN if z in seen else OAT
        dr.rounded_rectangle([x, y, x + w, y + h_row(r)], radius=5, fill=fill, outline=SLATE, width=2)
        if z:
            dr.text((x + w / 2, y + h_row(r) / 2), str(z), font=f, anchor="mm", fill=(255, 255, 255) if z == current else SLATE)
    return im


def with_header(img, board, zone, title, width):
    """Resize the zone render and add a header band: label on the left, locator on the right."""
    img = img.resize((width, int(width * img.size[1] / img.size[0])), Image.LANCZOS)
    loc = locator(board, zone); band = loc.size[1] + 30
    out = Image.new("RGB", (width, img.size[1] + band), OAT); dr = ImageDraw.Draw(out)
    n = len(ORDER[board]); step = ORDER[board].index(zone) + 1
    where = f"zone {zone}" if zone else "header"
    dr.text((40, band / 2), f"Board {board} · {where} · step {step} of {n}", font=ImageFont.truetype(FONT_B, 30), fill=SLATE, anchor="lm")
    out.paste(loc, (width - loc.size[0] - 40, (band - loc.size[1]) // 2))
    dr.line([(0, band - 1), (width, band - 1)], fill=SEEN, width=3)
    out.paste(img, (0, band))
    return out


def main():
    d = json.load(open(BOARD)); os.makedirs(os.path.join(HERE, "_crops"), exist_ok=True)
    for f in os.listdir(os.path.join(HERE, "img")):
        if f.endswith(".png"): os.remove(os.path.join(HERE, "img", f))  # stale figures from the old layout
    for board, zones in ZONES.items():
        for zone, (name, (x0, x1), (y0, y1), title) in zones.items():
            w = 2000 if name in WIDE else 1500
            with_header(crop_board(d, name, x0, x1, y0, y1), board, zone, title, w).save(os.path.join(HERE, "img", name + ".png"), optimize=True)
            print(name, flush=True)
    # recap overviews, rendered one row at a time so the browser never clips a tall canvas, then stacked
    for board, (x0, x1), rows in [(1, (-50, 3500), [(-50, 175), R1, R2, R3, R4]),
                                  (2, (3540, 7200), [(-50, 1060), (1085, 2000), (2085, 2950), (3000, 3460), (3480, 4400)])]:
        parts = [crop_board(d, f"b{board}_recap_r{i}", x0, x1, a, b, anchors=True) for i, (a, b) in enumerate(rows)]
        parts = [p.resize((2000, int(2000 * p.size[1] / p.size[0])), Image.LANCZOS) for p in parts]
        out = Image.new("RGB", (2000, sum(p.size[1] for p in parts)), OAT); y = 0
        for p in parts: out.paste(p, (0, y)); y += p.size[1]
        out.save(os.path.join(HERE, "img", f"b{board}_recap.png"), optimize=True); print(f"b{board}_recap", flush=True)


if __name__ == "__main__":
    main()
