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
COLS = round(ROWS * (16 / 9) / 0.4996)  # cell aspect so the grid is true 16:9


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
    size = min(W / (cols * 0.6021), H / (rows * 1.1645))
    for _ in range(4):
        font = ImageFont.truetype(FONT_PATH, max(8, int(round(size))))
        cw = font.getlength("M")
        asc, desc = font.getmetrics()
        lh = asc + desc
        scale = min(W / (cols * cw), H / (rows * lh))
        if abs(scale - 1) < 0.0015:
            break
        size *= scale
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
    print(f"wrote {fname}  {cols}x{rows}  size {int(round(size))}  span {int(cols * cw)}x{int(rows * lh)}")


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
    stars(g, 760, ROWS, seed=7)
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
    stars(g, 640, ROWS, seed=11)
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


def rect(g, c1, r1, c2, r2, fill_ch, fill_col, edge_col=None):
    for y in range(r1, r2 + 1):
        for x in range(c1, c2 + 1):
            if edge_col is not None and (y in (r1, r2) or x in (c1, c2)):
                put(g, y, x, "\u2500" if y in (r1, r2) else "\u2502", edge_col)
            else:
                put(g, y, x, fill_ch, fill_col)


def spruce(g, cx, base, height):
    # snow-laden conifer: widest at the base, frost-white branch edges
    for i in range(height + 1):
        y = base - i
        hw = int((height - i) * 0.42)
        for dx in range(-hw, hw + 1):
            put(g, y, cx + dx, "\u2593", (26, 30, 54))
        if hw >= 1:
            put(g, y, cx - hw, "*", (150, 160, 205))
            put(g, y, cx + hw, "*", (150, 160, 205))
    put(g, base - height - 1, cx, "*", (208, 216, 244))
    put(g, base - height - 2, cx, "*", (208, 216, 244))
    put(g, base + 1, cx, "\u2502", (58, 64, 92))
    put(g, base + 2, cx, "\u2502", (58, 64, 92))


def mokki():
    g = blank()
    horizon = 33
    stars(g, 520, horizon + 2, seed=3)

    # smooth snow field, gently drifting
    hz = [horizon + int(0.9 * math.sin(x * 0.02) + 0.4 * math.sin(x * 0.07 + 1.0)) for x in range(COLS)]
    for x in range(COLS):
        for y in range(hz[x], ROWS):
            t = (y - hz[x]) / max(1, ROWS - hz[x])
            ch = RAMP[3] if t < 0.10 else (RAMP[2] if t < 0.5 else RAMP[1])
            put(g, y, x, ch, lerp((92, 100, 142), (9, 11, 24), t))

    spruce(g, 44, 35, 13)
    spruce(g, 122, 35, 10)

    # cabin
    c1, c2, r1, r2 = 72, 96, 23, 34
    rect(g, c1, r1, c2, r2, "\u2588", (17, 20, 40), (98, 108, 160))
    # snow-covered gable roof
    peak_c, peak_r = (c1 + c2) // 2, 15
    for r in range(peak_r, r1):
        hw = int((r - peak_r) * ((c2 - c1 + 8) / 2) / (r1 - peak_r))
        for x in range(peak_c - hw, peak_c + hw + 1):
            edge = abs(x - peak_c) >= hw - 1
            put(g, r, x, "\u2592" if edge else "\u2591", (206, 214, 240) if edge else (118, 126, 174))
    # chimney seated on the roof
    rect(g, 88, 13, 90, 20, "\u2588", (12, 14, 28), (98, 108, 160))

    # lit window + warm halo
    wx1, wy1, wx2, wy2 = 77, 25, 81, 28
    for r in range(wy1, wy2 + 1):
        for x in range(wx1, wx2 + 1):
            g[r][x] = ("\u2588", (255, 198, 112))
    # mullions
    mc, mr = (wx1 + wx2) // 2, (wy1 + wy2) // 2
    for r in range(wy1, wy2 + 1):
        g[r][mc] = ("\u2502", (72, 50, 24))
    for x in range(wx1, wx2 + 1):
        g[mr][x] = ("\u2500", (72, 50, 24))
    for r in range(wy1 - 4, wy2 + 5):
        for x in range(wx1 - 4, wx2 + 5):
            dx = max(wx1 - x, 0, x - wx2)
            dy = max(wy1 - r, 0, r - wy2)
            d = max(dx, dy)
            if d == 0 or d > 4:
                continue
            f = (1 - d / 4.5) * 0.55
            base = g[r][x]
            put(g, r, x, base[0] if base[0] != " " else "\u2591", lerp(base[1], (176, 112, 54), f))

    # door
    rect(g, 86, 30, 89, 34, "\u2588", (10, 11, 22), (92, 100, 150))

    # smoke rising and drifting from the chimney
    random.seed(21)
    for k in range(17):
        y = 11 - k
        if y < 0:
            break
        fade = 1 - k / 17
        cx = 89 + k * 0.55 + 1.5 * math.sin(k * 0.6)
        spread = 0.5 + k * 0.22
        for _ in range(1 + int(k * 0.14)):
            x = int(round(cx + random.uniform(-spread, spread)))
            if random.random() < 0.45 + fade * 0.5:
                ch = random.choice([".", "\u00b7", "o"])
                put(g, y, x, ch, lerp((14, 16, 28), (104, 112, 140), fade * 0.85))

    # snowfall, in front of everything
    random.seed(41)
    for _ in range(620):
        x = random.randrange(COLS)
        y = random.randrange(ROWS)
        if g[y][x][0] != " ":
            continue
        t = random.random()
        ch = "." if t < 0.82 else ("\u00b7" if t < 0.94 else "*")
        g[y][x] = (ch, lerp((70, 78, 112), (228, 234, 252), 0.3 + 0.6 * t))

    draw_grid(g, "4-mokki.png")


def main():
    Image.new("RGB", (W, H), (0, 0, 0)).save(f"{OUT}/1-black.png")
    print("wrote 1-black.png")
    aurora()
    tunturi()
    mokki()


if __name__ == "__main__":
    main()
