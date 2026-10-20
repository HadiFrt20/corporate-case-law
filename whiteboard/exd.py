# Minimal Excalidraw element helpers: fills boilerplate only; all coordinates are passed by hand.
import json, itertools
_seed = itertools.count(1000)
ROUGH, FONT = 0, 3  # whiteboard mode: set ROUGH=1, FONT=5 (Excalifont)
SL, LAVA, OAT, MUTED = "#1B3139", "#FF3621", "#F9F7F4", "#5A6B72"
C = {"ok": ("#E3F3EA", "#1F7A4D"), "warn": ("#FFF1DB", "#B26A00"), "bad": ("#FBE4E2", "#B3261E"),
     "neu": ("#FFFFFF", SL), "lava": ("#FFE6E2", LAVA), "ai": ("#EEE8F7", "#5B3E96"), "dark": ("#1B3139", "#1B3139"), "sticky": ("#FFF1A8", "#A68A00"), "blue": ("#E3EEF7", "#2D5F8B")}
def _base(t, i, x, y, w, h, stroke=SL, bg="transparent", **k):
    s = next(_seed)
    d = dict(type=t, id=i, x=x, y=y, width=w, height=h, strokeColor=stroke, backgroundColor=bg, fillStyle=k.pop("fillStyle", "solid"),
             strokeWidth=k.pop("sw", 2), strokeStyle=k.pop("style", "solid"), roughness=k.pop("rough", ROUGH), opacity=100, angle=0,
             seed=s, version=1, versionNonce=s + 7, isDeleted=False, groupIds=[], boundElements=None, link=None, locked=False)
    d.update(k); return d
def text(i, x, y, s, fs=16, color=SL, align="left", w=None, container=None):
    lines = s.split("\n")
    w = w or max(len(l) for l in lines) * fs * 0.62
    return _base("text", i, x, y, w, len(lines) * fs * 1.25, stroke=color, sw=1, text=s, originalText=s, fontSize=fs,
                 fontFamily=FONT, textAlign=align, verticalAlign="middle" if container else "top", containerId=container, lineHeight=1.25)
def box(i, x, y, w, h, s, kind="neu", fs=16, shape="rectangle", style="solid", tcolor=None, align="center", fill="solid"):
    bg, st = C[kind]
    r = _base(shape, i, x, y, w, h, stroke=st, bg=bg, style=style, fillStyle=fill, boundElements=[{"id": i + "_t", "type": "text"}],
              **({"roundness": {"type": 3}} if shape == "rectangle" else {}))
    lines = s.split("\n"); th = len(lines) * fs * 1.25
    t = text(i + "_t", x + 8, y + (h - th) / 2, s, fs, tcolor or (OAT if kind == "dark" else st), align, w - 16, container=i)
    return [r, t]
def dot(i, x, y, kind="lava", d=12):
    bg, st = C[kind]; return _base("ellipse", i, x, y, d, d, stroke=st, bg=st, sw=1)
def line(i, x, y, pts, color=MUTED, sw=1, style="solid"):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return _base("line", i, x, y, max(xs) - min(xs), max(ys) - min(ys), stroke=color, sw=sw, style=style, points=pts)
def arrow(i, x, y, pts, color=SL, src=None, dst=None, sw=2, style="solid"):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return _base("arrow", i, x, y, max(xs) - min(xs), max(ys) - min(ys), stroke=color, sw=sw, style=style, points=pts,
                 startBinding={"elementId": src, "focus": 0, "gap": 4} if src else None,
                 endBinding={"elementId": dst, "focus": 0, "gap": 4} if dst else None, startArrowhead=None, endArrowhead="arrow")
def save(path, els):
    ids = {e["id"]: e for e in els}
    for e in els:  # register arrow bindings on their targets
        if e["type"] == "arrow":
            for b in (e["startBinding"], e["endBinding"]):
                if b and b["elementId"] in ids:
                    t = ids[b["elementId"]]; t["boundElements"] = (t["boundElements"] or []) + [{"id": e["id"], "type": "arrow"}]
    json.dump({"type": "excalidraw", "version": 2, "source": "https://excalidraw.com", "elements": els,
               "appState": {"viewBackgroundColor": OAT, "gridSize": 20}, "files": {}}, open(path, "w"), indent=1)
def frame(i, x, y, w, h, name):
    s = next(_seed)
    return dict(type="frame", id=i, x=x, y=y, width=w, height=h, name=name, strokeColor="#bbb", backgroundColor="transparent", fillStyle="solid",
                strokeWidth=1, strokeStyle="solid", roughness=0, opacity=100, angle=0, seed=s, version=1, versionNonce=s + 7, isDeleted=False,
                groupIds=[], boundElements=None, link=None, locked=False, frameId=None)
def in_frame(fid, els):
    for e in els: e["frameId"] = fid
    return els
