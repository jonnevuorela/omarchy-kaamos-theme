#!/usr/bin/env python3
"""Kaamos arctic ASCII-art wallpapers: 3840x2160, grids matched to 16:9."""
import math, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
    # Exact cell step across the full 3840x2160 16:9 canvas so there is zero border margin
    cw = W / cols
    lh = H / rows
    size = max(cw / 0.6021, lh / 1.1645)
    font = ImageFont.truetype(FONT_PATH, max(8, int(math.ceil(size))))
    img = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(img)
    for r, row in enumerate(grid):
        y = round(r * lh)
        for c, (ch, col) in enumerate(row):
            if ch == " ":
                continue
            d.text((round(c * cw), y), ch, font=font, fill=col)
    img.save(f"{OUT}/{fname}")
    print(f"wrote {fname}  {cols}x{rows}  size {int(math.ceil(size))}  span {W}x{H}")


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


def fbm_noise(shape, scales, seed=0):
    """Multi-octave smooth 2D noise using bicubic-upsampled random grids."""
    rng = np.random.default_rng(seed)
    h, w = shape
    out = np.zeros((h, w), dtype=np.float32)
    total_w = 0.0
    for cell_h, cell_w, weight in scales:
        gh = max(2, int(h / cell_h) + 2)
        gw = max(2, int(w / cell_w) + 2)
        grid = rng.random((gh, gw), dtype=np.float32)
        pil_img = Image.fromarray((grid * 255).astype(np.uint8), mode="L")
        pil_up = pil_img.resize((w, h), resample=Image.Resampling.BICUBIC)
        out += (np.asarray(pil_up, dtype=np.float32) / 255.0) * weight
        total_w += weight
    return out / max(1e-6, total_w)


def mokki():
    """High-density 3/4 perspective desolate cabin in heavy night snowfall, filling 16:9."""
    m_rows = 84
    m_cols = round(m_rows * (16 / 9) / 0.4996)  # ~299 cols
    sh, sw = m_rows * 6, m_cols * 6
    yy, xx = np.mgrid[0:sh, 0:sw].astype(np.float32)
    yn = yy / sh
    xn = xx / sw

    rgb = np.zeros((sh, sw, 3), dtype=np.float32)
    noise_fine = fbm_noise((sh, sw), [(4, 4, 1.0), (10, 10, 0.6)], seed=12)
    drift_noise = fbm_noise((sh, sw), [(32, 90, 1.0), (14, 40, 0.5), (6, 16, 0.25)], seed=7)
    gust_noise = fbm_noise((sh, sw), [(16, 85, 1.0), (7, 40, 0.6)], seed=99)

    # 1. Overcast snowy night sky clouds spanning the upper 16:9 frame (so the top of the screen isn't empty)
    cloud_band = (
        np.exp(-((yn - 0.14) / 0.15) ** 2) * (0.35 + 0.65 * drift_noise)
        + np.exp(-((yn - 0.30) / 0.16) ** 2) * (0.25 + 0.55 * gust_noise) * 0.6
    )
    rgb[..., 0] += cloud_band * 34
    rgb[..., 1] += cloud_band * 39
    rgb[..., 2] += cloud_band * 64

    # 2. High distant fell range spanning across the upper-middle frame (y ~ 0.24..0.46)
    ridge_distant = (
        0.34
        - 0.11 * np.exp(-((xn - 0.18) / 0.25) ** 2)
        - 0.08 * np.exp(-((xn - 0.78) / 0.28) ** 2)
        - 0.035 * np.sin(xn * 5.5 + 0.3)
    )
    mask_dist = yn >= ridge_distant
    d_dist = np.clip((yn - ridge_distant) / 0.26, 0.0, 1.0)
    dist_lum = np.exp(-d_dist * 2.5) * 0.38 * (0.78 + 0.38 * drift_noise)
    for c, val in enumerate([64, 72, 118]):
        rgb[..., c] = np.where(mask_dist, np.maximum(rgb[..., c], val * dist_lum), rgb[..., c])

    # 3. Second closer fell slope descending from left to right (y ~ 0.42..0.56)
    ridge_far = (
        0.47
        - 0.13 * np.exp(-((xn - 0.14) / 0.28) ** 2)
        - 0.04 * np.sin(xn * 4.8 + 0.6)
        + 0.07 * xn
    )
    mask_far = yn >= ridge_far
    dist_far = np.clip((yn - ridge_far) / 0.24, 0.0, 1.0)
    far_lum = np.exp(-dist_far * 2.4) * 0.48 * (0.8 + 0.35 * drift_noise)
    for c, val in enumerate([74, 84, 134]):
        rgb[..., c] = np.where(mask_far, val * far_lum, rgb[..., c])

    # 4. Midground hillside contour (higher up so foreground snowdrifts fill the lower frame)
    hill_mid = (
        0.59
        - 0.055 * np.sin(xn * 4.4 - 0.7)
        - 0.025 * np.cos(xn * 10.5)
    )

    # 5. Asymmetric Nordic spruces (taller, spanning across the 16:9 width)
    tree_specs = [
        (0.04, 0.02, 0.26, 0.030, 0.48),
        (0.09, 0.01, 0.34, 0.038, 0.62),
        (0.14, 0.00, 0.40, 0.044, 0.74),
        (0.20, 0.02, 0.31, 0.036, 0.60),
        (0.26, 0.01, 0.22, 0.028, 0.46),
        (0.45, -0.01, 0.20, 0.024, 0.38),
        (0.49, 0.00, 0.26, 0.030, 0.48),
        (0.76, 0.01, 0.35, 0.042, 0.68),
        (0.82, 0.02, 0.27, 0.034, 0.54),
        (0.89, 0.01, 0.21, 0.027, 0.44),
        (0.95, 0.02, 0.28, 0.033, 0.50),
    ]
    for tx, ty_off, th, tw, tb in tree_specs:
        col_idx = min(sw - 1, max(0, int(tx * sw)))
        base_y = float(hill_mid[0, col_idx]) + ty_off
        top_y = base_y - th
        in_v = (yn >= top_y) & (yn <= base_y)
        u = np.clip((yn - top_y) / max(1e-4, th), 0.0, 1.0)
        n_tiers = 8.0
        tier_phase = (u * n_tiers) % 1.0
        bough_flare = 0.42 + 0.58 * (tier_phase ** 0.65)
        half_w = tw * (u ** 0.82) * bough_flare * (0.85 + 0.3 * noise_fine)
        dx = xn - tx
        in_tree = in_v & (np.abs(dx) <= half_w)

        rel_x = np.abs(dx) / np.maximum(1e-4, half_w)
        snow_cushion = np.exp(-((tier_phase - 0.28) / 0.32) ** 2) * (0.35 + 0.65 * (rel_x ** 0.6))
        windward = np.where(dx <= 0.0, 1.2, 0.72)
        tree_lum = tb * (0.16 + 0.72 * snow_cushion * windward * (0.7 + 0.5 * noise_fine))
        for c, val in enumerate([116, 126, 172]):
            rgb[..., c] = np.where(in_tree, val * tree_lum, rgb[..., c])

    # 6. Sweeping foreground snowdrifts filling the entire bottom down to y=1.0
    mask_ground = yn >= hill_mid
    gd = np.clip((yn - hill_mid) / (1.0 - hill_mid + 1e-4), 0.0, 1.0)
    drift_contours = np.sin(gd * 10.0 + xn * 6.5 + drift_noise * 3.4)
    drift_crest = np.clip(drift_contours, 0.0, 1.0) ** 2.4 * (1.0 - gd * 0.45)
    ground_lum = (0.18 + 0.34 * np.exp(-gd * 2.1) + 0.26 * drift_crest) * (0.80 + 0.35 * drift_noise)
    for c, val in enumerate([112, 122, 168]):
        rgb[..., c] = np.where(mask_ground, val * ground_lum, rgb[..., c])

    # 7. Draw the 3/4 perspective Mökki (slightly larger & nestled at x=0.63, y=0.55)
    pil_scene = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), mode="RGB")
    draw = ImageDraw.Draw(pil_scene, "RGBA")

    def pt(nx, ny):
        return (int(round(nx * sw)), int(round(ny * sh)))

    ridge_top_y = 0.468
    eave_y = 0.548
    base_y = 0.616

    chimney = [
        pt(0.666, ridge_top_y - 0.002),
        pt(0.678, ridge_top_y - 0.004),
        pt(0.678, ridge_top_y - 0.032),
        pt(0.666, ridge_top_y - 0.030),
    ]
    draw.polygon(chimney, fill=(22, 25, 44, 240))
    draw.line([pt(0.666, ridge_top_y - 0.030), pt(0.678, ridge_top_y - 0.032)], fill=(130, 140, 184, 220), width=2)

    front_wall = [
        pt(0.576, eave_y),
        pt(0.611, ridge_top_y + 0.007),
        pt(0.646, eave_y + 0.007),
        pt(0.646, base_y + 0.006),
        pt(0.576, base_y),
    ]
    side_wall = [
        pt(0.646, eave_y + 0.007),
        pt(0.720, eave_y - 0.005),
        pt(0.720, base_y - 0.005),
        pt(0.646, base_y + 0.006),
    ]
    draw.polygon(front_wall, fill=(10, 12, 22, 255))
    draw.polygon(side_wall, fill=(7, 8, 16, 255))

    n_strips = 26
    for i in range(n_strips):
        t0 = i / n_strips
        t1 = (i + 1) / n_strips
        x_tl = 0.611 + (0.644 - 0.611) * t0
        y_tl = (ridge_top_y - 0.003) + (eave_y + 0.010 - (ridge_top_y - 0.003)) * t0
        x_tr = 0.692 + (0.728 - 0.692) * t0
        y_tr = (ridge_top_y - 0.013) + (eave_y - 0.003 - (ridge_top_y - 0.013)) * t0

        x_bl = 0.611 + (0.644 - 0.611) * t1
        y_bl = (ridge_top_y - 0.003) + (eave_y + 0.010 - (ridge_top_y - 0.003)) * t1
        x_br = 0.692 + (0.728 - 0.692) * t1
        y_br = (ridge_top_y - 0.013) + (eave_y - 0.003 - (ridge_top_y - 0.013)) * t1

        shade = 0.80 - 0.36 * (t0 ** 0.85)
        col = (int(116 * shade), int(126 * shade), int(174 * shade), 245)
        draw.polygon([pt(x_tl, y_tl), pt(x_tr, y_tr), pt(x_br, y_br), pt(x_bl, y_bl)], fill=col)

    left_gable_eave = [
        pt(0.568, eave_y + 0.004),
        pt(0.611, ridge_top_y - 0.003),
        pt(0.611, ridge_top_y + 0.007),
        pt(0.572, eave_y + 0.012),
    ]
    right_gable_eave = [
        pt(0.611, ridge_top_y - 0.003),
        pt(0.644, eave_y + 0.010),
        pt(0.640, eave_y + 0.017),
        pt(0.611, ridge_top_y + 0.007),
    ]
    draw.polygon(left_gable_eave, fill=(142, 152, 198, 240))
    draw.polygon(right_gable_eave, fill=(114, 124, 170, 235))

    wx1, wy1, wx2, wy2 = 0.595, 0.562, 0.624, 0.597
    draw.polygon([pt(wx1, wy1), pt(wx2, wy1 + 0.002), pt(wx2, wy2 + 0.002), pt(wx1, wy2)], fill=(245, 188, 102, 255))
    draw.polygon([pt(wx1 + 0.004, wy1 + 0.005), pt(wx2 - 0.004, wy1 + 0.006), pt(wx2 - 0.004, wy2 - 0.004), pt(wx1 + 0.004, wy2 - 0.005)], fill=(255, 224, 152, 255))
    wmx, wmy = (wx1 + wx2) * 0.5, (wy1 + wy2) * 0.5
    draw.line([pt(wmx, wy1), pt(wmx, wy2 + 0.002)], fill=(28, 20, 16, 240), width=2)
    draw.line([pt(wx1, wmy), pt(wx2, wmy + 0.002)], fill=(28, 20, 16, 240), width=2)

    sx1, sy1, sx2, sy2 = 0.670, 0.566, 0.690, 0.590
    draw.polygon([pt(sx1, sy1), pt(sx2, sy1 - 0.002), pt(sx2, sy2 - 0.002), pt(sx1, sy2)], fill=(215, 152, 74, 245))
    smx = (sx1 + sx2) * 0.5
    draw.line([pt(smx, sy1 - 0.001), pt(smx, sy2 - 0.001)], fill=(28, 20, 16, 230), width=2)

    rgb = np.asarray(pil_scene, dtype=np.float32)

    # 8. Wind-bent turbulent chimney smoke plume rising high toward the top edge
    ch_x, ch_y = 0.672, ridge_top_y - 0.031
    smoke_h = ch_y - yn
    in_smoke = smoke_h > 0.0
    h_norm = np.clip(smoke_h / 0.42, 0.0, 1.0)
    smoke_curve_x = (
        ch_x
        - 0.17 * (h_norm ** 1.18)
        + 0.018 * np.sin(h_norm * 13.0)
        + (drift_noise - 0.5) * 0.06 * (h_norm ** 0.75)
    )
    smoke_width = 0.007 + 0.052 * (h_norm ** 0.92)
    smoke_dist = np.abs(xn - smoke_curve_x) / smoke_width
    smoke_density = (
        in_smoke
        * np.exp(-(smoke_dist ** 2) * 1.5)
        * (1.0 - h_norm ** 0.85)
        * np.clip(smoke_h / 0.008, 0.0, 1.0)
        * (0.55 + 0.75 * drift_noise)
    )
    for c, val in enumerate([138, 148, 192]):
        rgb[..., c] += smoke_density * val * 0.82

    # 9. Warm light spill across the snowbank + soft misty window bloom
    wx, wy = 0.610, 0.580
    d_win = np.sqrt(((xn - wx) * 1.6) ** 2 + ((yn - wy) * 1.0) ** 2)
    bloom = np.exp(-(d_win / 0.036) ** 1.5) * 0.48 + np.exp(-(d_win / 0.095) ** 1.3) * 0.18

    dx_cone = xn - wx
    dy_cone = yn - 0.610
    in_cone = dy_cone > 0.0
    cone_angle = (dx_cone + dy_cone * 0.72) / (dy_cone + 0.022)
    cone_mask = (
        in_cone
        * np.exp(-(cone_angle ** 2) / 0.50)
        * np.exp(-dy_cone / 0.18)
        * np.clip(dy_cone / 0.016, 0.0, 1.0)
    )
    warm_spill = cone_mask * 0.80 * (0.78 + 0.35 * drift_noise)

    wx2_c, wy2_c = 0.680, 0.578
    d_win2 = np.sqrt(((xn - wx2_c) * 1.6) ** 2 + ((yn - wy2_c) * 1.0) ** 2)
    bloom2 = np.exp(-(d_win2 / 0.028) ** 1.5) * 0.30

    total_warm = bloom + bloom2 + warm_spill
    rgb[..., 0] += total_warm * 238
    rgb[..., 1] += total_warm * 150
    rgb[..., 2] += total_warm * 58

    # 10. Swirling blizzard snow-fog bands drifting across the cabin & trees
    horizon_band = np.exp(-((yn - 0.56) / 0.16) ** 2)
    blizzard_veil = horizon_band * (0.25 + 0.65 * gust_noise) * 0.40
    haze_rgb = np.array([68.0, 76.0, 118.0], dtype=np.float32)
    rgb = rgb * (1.0 - blizzard_veil[..., None] * 0.42) + haze_rgb * (blizzard_veil[..., None] * 0.45)

    pil_final = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), mode="RGB")
    pil_final = pil_final.filter(ImageFilter.GaussianBlur(radius=1.55))

    pil_small = pil_final.resize((m_cols, m_rows), resample=Image.Resampling.BICUBIC)
    small_rgb = np.asarray(pil_small, dtype=np.float32)

    g = blank(m_rows, m_cols)
    rng = random.Random(42)

    # Pre-generate slanted wind-driven snow streaks (no '+' or '*' star characters!)
    # Each flake is a soft frosty silver-grey wisp (`░` or `·`/`'`) rather than a royal-blue star cross
    snow_map = {}
    for _ in range(420):
        sr = rng.randrange(m_rows)
        sc = rng.randrange(m_cols)
        strength = rng.uniform(0.35, 0.95)
        snow_map[(sr, sc)] = strength
        # Occasional 2-cell diagonal wind streak (drifting down-left with the wind)
        if strength > 0.68 and sr + 1 < m_rows and sc - 1 >= 0:
            snow_map[(sr + 1, sc - 1)] = strength * 0.55

    for r in range(m_rows):
        for c in range(m_cols):
            cr, cg, cb = small_rgb[r, c]
            lum = (0.299 * cr + 0.587 * cg + 0.114 * cb) / 255.0
            flake_str = snow_map.get((r, c), 0.0)

            # Soft frosty grey-white snowflakes in the dark sky (NEVER '+' or '*' or royal blue!)
            if flake_str > 0.0 and lum < 0.045:
                ch = "\u2591" if flake_str > 0.62 else "\u00b7"
                # Neutral frosty silver-grey (almost desaturated cool white/grey)
                base_v = int(68 + 88 * flake_str)
                col = (base_v, base_v + 4, min(255, base_v + 16))
                g[r][c] = (ch, col)
                continue

            if lum < 0.018:
                continue

            # Soft snow flurries passing in front of solid forms (gentle frost-grey lift)
            if flake_str > 0.0 and lum < 0.48:
                mix = flake_str * 0.34
                cr = cr * (1.0 - mix) + 172.0 * mix
                cg = cg * (1.0 - mix) + 178.0 * mix
                cb = cb * (1.0 - mix) + 198.0 * mix
                lum = (0.299 * cr + 0.587 * cg + 0.114 * cb) / 255.0

            lum_d = min(1.0, max(0.0, lum + rng.uniform(-0.015, 0.015)))
            if lum_d < 0.46:
                ch = "\u2591"
                gain = 1.65
            elif lum_d < 0.66:
                ch = "\u2592"
                gain = 0.98 + (lum_d - 0.46) * 1.4
            elif lum_d < 0.82:
                ch = "\u2593"
                gain = 1.05 + (lum_d - 0.66) * 1.2
            else:
                ch = "\u2588"
                gain = 1.05

            col = (
                min(255, int(cr * gain)),
                min(255, int(cg * gain)),
                min(255, int(cb * gain)),
            )
            g[r][c] = (ch, col)

    draw_grid(g, "4-mokki.png")


def main():
    Image.new("RGB", (W, H), (0, 0, 0)).save(f"{OUT}/1-black.png")
    print("wrote 1-black.png")
    aurora()
    tunturi()
    mokki()


if __name__ == "__main__":
    main()
