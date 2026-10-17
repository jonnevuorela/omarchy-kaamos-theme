#!/usr/bin/env python3
"""Kaamos arctic ASCII-art wallpapers: 3840x2160, grids matched to 16:9."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont

W, H = 3840, 2160
FONT_PATH = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backgrounds")

RAMP = [" ", "\u2591", "\u2592", "\u2593", "\u2588"]
FROST = (236, 240, 255)
DEEP = (26, 30, 56)
MID = (94, 102, 216)
DIM = (34, 38, 70)

ROWS = 46
COLS = round(ROWS * 3.438)  # -> 16:9 once cell metrics are applied

BOX = {(1, 0): "\u2500", (-1, 0): "\u2500", (0, 1): "\u2502", (0, -1): "\u2502",
       (1, 1): "\u2572", (-1, -1): "\u2572", (1, -1): "\u2571", (-1, 1): "\u2571"}


def lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def tri(t):
    return lerp(DEEP, MID, t / 0.5) if t < 0.5 else lerp(MID, FROST, (t - 0.5) / 0.5)


def blank(rows=ROWS, cols=COLS):
    return [[(" ", (0, 0, 0)) for _ in range(cols)] for _ in range(rows)]


def put(g, r, c, ch, col):
    if 0 <= r < len(g) and 0 <= c < len(g[r]):
        g[r][c] = (ch, col)


def draw_grid(grid, fname):
    cols = max(len(r) for r in grid)
    rows = len(grid)
    size = min((W * 0.995) / (cols * 0.6021), (H * 0.995) / (rows * 1.1645))
    font = ImageFont.truetype(FONT_PATH, max(8, int(round(size))))
    cw = font.getlength("M") * 0.955
    asc, desc = font.getmetrics()
    lh = (asc + desc) * 0.97
    left = (W - cols * cw) / 2
    top = (H - rows * lh) / 2
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for r, row in enumerate(grid):
        y = round(top + r * lh)
        for c, (ch, col) in enumerate(row):
            if ch == " ":
                continue
            d.text((round(left + c * cw), y), ch, font=font, fill=col)
    img.save(f"{OUT}/{fname}")
    print(f"wrote {fname}  {cols}x{rows}  size {int(round(size))}")


def stars(g, n, ymax, band=None, seed=0):
    random.seed(seed)
    for _ in range(n):
        x = random.randrange(len(g[0]))
        y = random.randrange(ymax)
        if band:
            b = band[0] + (x / len(g[0])) * (band[1] - band[0])
            y = int(max(0, min(ymax - 1, random.gauss(b, band[2]))))
        t = random.random()
        ch = "." if t < 0.72 else ("+" if t < 0.94 else "*")
        col = lerp(DIM, FROST, 0.2 + 0.62 * t)
        cur = g[y][x]
        if cur[0] == " " or (ch in "+*" and cur[0] == "."):
            g[y][x] = (ch, col)


def aurora():
    g = blank()
    stars(g, 620, int(ROWS * 0.85), seed=7)
    for x in range(COLS):
        lobe = 0.5 + 0.5 * math.sin(x * 0.026 + 0.4)
        presence = lobe ** 1.15 * (0.55 + 0.45 * abs(math.sin(x * 0.10 + 0.8)))
        if presence < 0.05:
            continue
        te = 3 + 2.6 * math.sin(x * 0.05 + 1.0) + 1.6 * math.sin(x * 0.17)
        be = te + 9 + 11 * presence + 3.0 * math.sin(x * 0.07 + 2.0) + 2.0 * math.sin(x * 0.21)
        lo = 0.5 + 0.5 * math.sin(x * 0.055 + 0.2)
        for y in range(max(0, int(te)), min(ROWS, int(be))):
            u = max(0.0, y - te) / max(1.0, be - te)
            striation = 0.45 + 0.55 * abs(math.sin(x * 0.8 + y * 0.02))
            i = (u ** 1.6) * striation * (0.35 + 0.65 * lo) * (0.5 + 0.5 * presence)
            if i < 0.09:
                continue
            ch = RAMP[min(4, 1 + int(i * 4.3))]
            g[y][x] = (ch, tri(i))
    draw_grid(g, "2-kaamos-aurora.png")


def tunturi():
    g = blank()
    stars(g, 640, 22, seed=11)
    for base, amp, freq, phase, top, bot, rim in [
        (24, 9.0, 0.020, 0.0, (46, 54, 120), (10, 12, 28), (140, 150, 225)),
        (30, 7.5, 0.028, 1.6, (34, 40, 94), (8, 10, 22), (185, 195, 245)),
        (37, 6.5, 0.037, 3.1, (26, 30, 66), (0, 0, 0), (238, 242, 255)),
    ]:
        prof = []
        for x in range(COLS):
            h = amp * abs(math.sin(x * freq + phase)) + 0.55 * amp * abs(math.sin(x * freq * 2.3 + phase + 1.1))
            prof.append(int(base - h))
        for x in range(COLS):
            a = prof[x]
            b = prof[x + 1] if x + 1 < COLS else a
            apex = prof[x - 1] if x > 0 else a
            if b < a and a <= apex:
                ch = "^"
            elif b < a:
                ch = "/"
            elif b > a:
                ch = "\\"
            else:
                ch = "^"
            g[a][x] = (ch, rim)
            for y in range(a + 1, ROWS):
                t = min(1.0, (y - a) / max(1, ROWS - a) * 1.7)
                g[y][x] = (RAMP[3] if t < 0.2 else (RAMP[2] if t < 0.5 else RAMP[1]), lerp(top, bot, t))
    draw_grid(g, "3-tunturi.png")


def seg(g, c1, r1, c2, r2, guide=False, color=None):
    n = max(abs(c2 - c1), abs(r2 - r1))
    if n == 0:
        return
    for i in range(1, n):
        c = round(c1 + (c2 - c1) * i / n)
        r = round(r1 + (r2 - r1) * i / n)
        if g[r][c][0] not in (" ", ".", "+", "*"):
            continue
        if guide and i % 3:
            continue
        pc = round(c1 + (c2 - c1) * (i - 1) / n)
        pr = round(r1 + (r2 - r1) * (i - 1) / n)
        dc = 0 if c == pc else (1 if c2 > c1 else -1)
        dr = 0 if r == pr else (1 if r2 > r1 else -1)
        ch = BOX.get((dc, dr), "\u00b7")
        g[r][c] = (ch, color or lerp(DIM, FROST, 0.35 if guide else 0.62))


def hero(g, c, r, color=FROST):
    for dc, dr in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
        put(g, r + dr, c + dc, "*", color)
    for dc, dr in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        if g[r + dr][c + dc][0] in (" ", ".", "+"):
            g[r + dr][c + dc] = ("\u00b7", lerp(DIM, MID, 0.55))


def hero_big(g, c, r):
    for k in range(1, 4):
        for dc, dr in [(-k, 0), (k, 0), (0, -k), (0, k)]:
            put(g, r + dr, c + dc, "*" if k < 3 else "+", lerp(FROST, MID, 0.25 if k < 3 else 0.6))
    for dc, dr in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
        put(g, r + dr, c + dc, "+", lerp(FROST, MID, 0.5))
    for k in range(4, 7):
        for dc, dr in [(-k, 0), (k, 0), (0, -k), (0, k)]:
            if g[r + dr][c + dc][0] in (" ", ".", "+"):
                g[r + dr][c + dc] = ("\u00b7", lerp(DIM, FROST, 0.35))


def text(g, s, c, r, col):
    for i, ch in enumerate(s):
        put(g, r, c + i, ch, (0, 0, 0) if ch == " " else col)


def otava():
    g = blank()
    stars(g, 720, ROWS, band=(5, 27, 2.4), seed=3)
    stars(g, 280, ROWS, seed=5)
    pts = {"A": (34, 31), "B": (48, 32), "C": (52, 23), "D": (38, 22),
           "E": (64, 29), "F": (78, 27), "G": (92, 24)}
    pohjan = (122, 9)
    # barely-there dotted ties so the seven stars read as one figure
    for a, b in [("A", "B"), ("B", "C"), ("C", "D"), ("D", "A"),
                 ("B", "E"), ("E", "F"), ("F", "G")]:
        seg(g, pts[a][0], pts[a][1], pts[b][0], pts[b][1], color=lerp(DIM, MID, 0.7))
    seg(g, pts["D"][0], pts["D"][1], pohjan[0], pohjan[1], guide=True, color=lerp(DIM, MID, 0.6))
    for (c, r) in pts.values():
        hero(g, c, r)
    hero_big(g, pohjan[0], pohjan[1])
    text(g, "P O H J A N T \u00c4 H T I", pohjan[0] - 15, pohjan[1] + 4, lerp(FROST, MID, 0.35))
    text(g, "O T A V A", 40, 36, lerp(FROST, MID, 0.45))
    draw_grid(g, "4-otava.png")


def main():
    Image.new("RGB", (W, H), (0, 0, 0)).save(f"{OUT}/1-black.png")
    print("wrote 1-black.png")
    aurora()
    tunturi()
    otava()


if __name__ == "__main__":
    main()
