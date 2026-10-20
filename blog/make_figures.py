"""Render blog figures as crops of the real boards (whiteboard/combined.excalidraw)."""
import json, os, subprocess, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); BOARD = os.path.join(HERE, "..", "whiteboard", "combined.excalidraw")
RENDER = os.path.expanduser("~/.claude/skills/excalidraw-diagram/references")
CROPS = {  # name: (x0, x1, y0, y1) in canvas coordinates
    "b1_overview": (-50, 3500, -50, 3950), "b1_planes": (1160, 2300, 180, 1080), "b1_mesh": (2310, 3460, 180, 1080),
    "b1_skillgraph": (40, 1150, 1090, 2060), "b1_reality": (40, 1150, 3000, 3900),
    "b2_overview": (3540, 7200, -50, 4500), "b2_holes": (3700, 4800, 190, 1060), "b2_residual": (4880, 5960, 190, 1060),
    "b2_replay": (6030, 7150, 190, 1060), "b2_pipeline": (3700, 7150, 1085, 2000), "b2_code": (3700, 4800, 2085, 2950),
    "b2_results": (4880, 5960, 2085, 2950), "b2_novelty": (6030, 7150, 2085, 2950), "b2_kill": (3700, 7150, 3000, 3460),
    "b2_dbx": (3700, 4800, 3480, 4300), "b2_hmda": (4880, 5960, 3480, 4300), "b2_rare_causal": (6030, 7150, 3480, 4300)}
d = json.load(open(BOARD))
for name, (x0, x1, y0, y1) in CROPS.items():
    def bbox(e):
        if e.get("points"):
            xs = [p[0] for p in e["points"]]; ys = [p[1] for p in e["points"]]
            return e["x"] + min(xs), e["x"] + max(xs), e["y"] + min(ys), e["y"] + max(ys)
        return e["x"], e["x"] + e.get("width", 0), e["y"], e["y"] + e.get("height", 0)
    def inside(e):
        a, b_, c, d_ = bbox(e)
        return a >= x0 - 20 and c >= y0 - 15 and b_ <= x1 + 60 and d_ <= y1 + 20  # tight: neighbouring zones must not leak in
    els = [e for e in d["elements"] if inside(e)]
    ids = {e["id"] for e in els}
    els = [e for e in els if not (e.get("containerId") and e["containerId"] not in ids)]
    for e in els:
        for k in ("startBinding", "endBinding"):
            if e.get(k) and e[k]["elementId"] not in ids: e[k] = None
        if e.get("boundElements"): e["boundElements"] = [b for b in e["boundElements"] if b["id"] in ids] or None
    f = os.path.join(HERE, "_crops", name + ".excalidraw"); json.dump(dict(d, elements=els), open(f, "w"))
    subprocess.run(["uv", "run", "python", "render_excalidraw.py", f], cwd=RENDER, capture_output=True)
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(f.replace(".excalidraw", ".png")); w = 2000 if "overview" in name or name in ("b2_pipeline", "b2_kill") else 1500
    im.convert("RGB").resize((w, int(w * im.size[1] / im.size[0])), Image.LANCZOS).save(os.path.join(HERE, "img", name + ".png"), optimize=True)
    print(name, len(els), "elements", flush=True)
