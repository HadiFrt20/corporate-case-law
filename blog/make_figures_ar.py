"""Figures for the autoresearch post: board 3 (whiteboard/ar_board.excalidraw), one zone at a time, with the same
'you are here' locator as the first post, plus a full-board recap stacked from row renders."""
import json, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import make_figures as MF

BOARD3 = os.path.join(HERE, "..", "whiteboard", "ar_board.excalidraw")
Z = lambda c, r: (30 + c * 1150, 30 + c * 1150 + 1120, 180 + r * 930, 180 + r * 930 + 900)
TITLES = ["the loop we copied", "the trust boundary", "one number, five panels", "line 1: what changed", "overruling precedents",
          "the Goodhart we caught", "the clean tests failed", "a pre-registered diagnosis", "line 2: fix the miner", "confirm 3",
          "when does it stop?", "what it does not show"]
ZONES3 = {0: ("b3_z00_header", (20, 3440), (0, 150), "the board in one line")}
for k in range(12):
    x0, x1, y0, y1 = Z(k % 3, k // 3)
    ZONES3[k + 1] = (f"b3_z{k + 1:02d}", (x0, x1), (y0, y1), TITLES[k])
MF.ZONES[3] = ZONES3
MF.ORDER[3] = list(range(0, 13))
MF.GRID[3] = {0: (0, 0, 3), **{z: ((z - 1) % 3, (z - 1) // 3 + 1, 1) for z in range(1, 13)}}


def main():
    d = json.load(open(BOARD3)); os.makedirs(os.path.join(HERE, "_crops"), exist_ok=True)
    for zone, (name, (x0, x1), (y0, y1), title) in ZONES3.items():
        w = 2000 if zone == 0 else 1500
        MF.plain(MF.crop_board(d, name, x0, x1, y0, y1), w).save(os.path.join(HERE, "img", name + ".png"), optimize=True)
        print(name, flush=True)
    rows = [(0, 1080)] + [(180 + r * 930, 180 + r * 930 + 900) for r in range(1, 4)]
    parts = [MF.crop_board(d, f"b3_recap_r{i}", 20, 3440, a, b, anchors=True) for i, (a, b) in enumerate(rows)]
    parts = [p.resize((2000, int(2000 * p.size[1] / p.size[0])), Image.LANCZOS) for p in parts]
    out = Image.new("RGB", (2000, sum(p.size[1] for p in parts)), MF.OAT); y = 0
    for p in parts: out.paste(p, (0, y)); y += p.size[1]
    out.save(os.path.join(HERE, "img", "b3_recap.png"), optimize=True); print("b3_recap")


if __name__ == "__main__":
    main()
