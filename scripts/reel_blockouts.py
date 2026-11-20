"""Composition blockouts for the 9:16 reel of ep4 (1080 x 1920). Layout design only: flat shapes, real text at real
size in the project fonts, with the Reels/Shorts safe box and the 3:4 grid crop drawn over each frame.

    python3 scripts/reel_blockouts.py            -> out/ep4_reel/blockouts/NN_*.png, out/ep4_reel/blockouts_{1,2,3}.jpg,
                                                    out/ep4_reel/layout.json (every computed box, for docs/REEL_LAYOUT.md)

Nothing here is imported by the renderer; the numbers it prints are the proposal in docs/REEL_LAYOUT.md.
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out", "ep4_reel")
FR = os.path.join(OUT, "blockouts")
os.makedirs(FR, exist_ok=True)

W, H = 1080, 1920
SAFE = (60, 250, 960, 1470)            # x0, y0, x1, y1: clear of the top bar, caption/audio, buttons, left edge
GRID = (0, 240, 1080, 1680)            # the centre 3:4 crop the profile grid shows
INK = (46, 44, 45)
HLC = (245, 212, 74)
TAG_LIGHT = (238, 238, 236)
CARD = (242, 233, 217)
LABEL = (109, 106, 111)
GUIDE = (255, 128, 0)                  # blockout-only annotation (paths, motion): never content

_F = {}
def font(key, px):
    k = (key, int(px))
    if k not in _F: _F[k] = ImageFont.truetype(os.path.join(ROOT, "assets", "fonts", f"{key}.ttf"), int(px))
    return _F[k]

LAYOUT = {}        # beat -> {element: box/values}
CHECKS = []        # (beat, element, box) of text and key action, tested against SAFE

def rec(beat, name, val, key=True):
    LAYOUT.setdefault(beat, {})[name] = val
    if key and isinstance(val, (list, tuple)) and len(val) == 4 and all(isinstance(v, (int, float)) for v in val):
        CHECKS.append((beat, name, tuple(val)))

def ibox(b): return [int(round(v)) for v in b]

def wrap(dr, text, fnt, width):
    words, lines, cur = text.split(" "), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if dr.textlength(trial, font=fnt) <= width: cur = trial
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

def tracked(dr, xy, text, fnt, fill, tr):
    x, y = xy
    for ch in text:
        dr.text((x, y), ch, font=fnt, fill=fill); x += dr.textlength(ch, font=fnt) + tr
    return x

def tracked_len(dr, text, fnt, tr):
    return sum(dr.textlength(c, font=fnt) + tr for c in text) - tr

def lerp(a, b, t): return a + (b - a) * t
def mix(c1, c2, t): return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))

def cubic(P, u):
    a = 1 - u
    return (a**3 * P[0][0] + 3*a*a*u * P[1][0] + 3*a*u*u * P[2][0] + u**3 * P[3][0],
            a**3 * P[0][1] + 3*a*a*u * P[1][1] + 3*a*u*u * P[2][1] + u**3 * P[3][1])

def dashed(dr, pts, fill, width=4, dash=18, gap=12):
    acc, on = 0.0, True
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0); s = 0.0
        while s < L:
            step = min((dash if on else gap) - acc, L - s)
            if on:
                a, b = s / L, (s + step) / L
                dr.line([(lerp(x0, x1, a), lerp(y0, y1, a)), (lerp(x0, x1, b), lerp(y0, y1, b))], fill=fill, width=width)
            s += step; acc += step
            if acc >= (dash if on else gap): acc = 0.0; on = not on

def arrowhead(dr, tip, frm, fill, size=26, width=5):
    vx, vy = tip[0] - frm[0], tip[1] - frm[1]; L = math.hypot(vx, vy) or 1; vx, vy = vx / L, vy / L
    for ang in (0.5, -0.5):
        c, s = math.cos(ang), math.sin(ang)
        wx, wy = vx * c - vy * s, vx * s + vy * c
        dr.line([tip, (tip[0] - wx * size, tip[1] - wy * size)], fill=fill, width=width)

def guide_arrow(dr, pts, fill=GUIDE, width=5):
    dashed(dr, pts, fill, width)
    arrowhead(dr, pts[-1], pts[-2], fill)

def guide_label(dr, xy, text, fill=GUIDE, px=28, anchor="la"):
    dr.text(xy, text, font=font("mono5", px), fill=fill, anchor=anchor)


# =====================================================================================================================
# the sea plate (dusk / night) at 1080 x 1920 -- the proposal for the repainted portrait plate
# =====================================================================================================================
HZ_Y = 1150                              # horizon (HZ = 0.599); landscape 0.58 of 1080 = 626
HILL_X, HILL_H = 680, 168                # hill crest x, height above the horizon (landscape 1500, 135)
HILL_L, HILL_R = 330, 215                # left concave tail / right fall scale, px (landscape 0.20 W = 384, 0.13 W = 250)
COT_W, COT_H, ROOF_H = 44, 40, 44        # cottage body / roof, px (landscape 36 x 19 + 21: scaled up as the hero)
WIN = (HILL_X, HZ_Y - HILL_H - 2)        # the lit window = the push/rush focus, (680, 980)
PARALLAX_R = 90                          # near-plane lead during the tilt, source px (landscape 70)

def hill_top(x):
    dx = x - HILL_X
    if dx < 0:
        a = abs(dx) / HILL_L; b = math.exp(-a * a / (1 + 0.6 * a))
    else:
        b = math.exp(-abs(dx / HILL_R) ** 1.9)
    return HZ_Y - HILL_H * b

def sea_plate(night=False, lit=True):
    """returns (far RGBA sky plane, near RGBA plane) so the tilt can shift the near plane (parallax)"""
    far = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(far)
    top, mid, low = ((40, 44, 82), (62, 64, 104), (98, 86, 118)) if night else ((132, 136, 184), (170, 156, 192), (238, 186, 168))
    for y in range(H):
        t = min(1, y / HZ_Y)
        c = mix(top, mid, t / 0.6) if t < 0.6 else mix(mid, low, (t - 0.6) / 0.4)
        d.line([(0, y), (W, y)], fill=c + (255,))
    # sunset glow from off-frame left, low
    glow = Image.new("RGBA", (W, H)); gd = ImageDraw.Draw(glow)
    for r in range(900, 0, -30):
        a = int(70 * (1 - r / 900)) if not night else int(30 * (1 - r / 900))
        gd.ellipse([-260 - r, HZ_Y - 80 - r * 0.8, -260 + r, HZ_Y - 80 + r * 0.8], fill=(250, 214, 168, a))
    far.alpha_composite(glow)
    # cloud wisps: more of them than landscape, spread down the tall sky (we start zoomed in on it)
    for cy, cx0, ln in [(300, 120, 380), (360, 260, 300), (520, 40, 320), (640, 420, 360), (820, 120, 300), (900, 560, 280)]:
        d.rounded_rectangle([cx0, cy, cx0 + ln, cy + 16], 8, fill=((226, 170, 172, 120) if not night else (120, 96, 110, 90)))
    if night:
        for i in range(70):
            x = (i * 397) % W; y = (i * 211) % 700
            d.ellipse([x, y, x + 3, y + 3], fill=(240, 232, 214, 200))
    near = Image.new("RGBA", (W, H)); n = ImageDraw.Draw(near)
    seac = ((40, 44, 78), (20, 25, 51)) if night else ((119, 120, 149), (89, 94, 131))
    for y in range(HZ_Y, H):
        n.line([(0, y), (W, y)], fill=mix(*seac, (y - HZ_Y) / (H - HZ_Y)) + (255,))
    # far land on the right, then the hill with its long concave left tail
    n.polygon([(760, HZ_Y)] + [(x, HZ_Y - 30 * math.exp(-((x - 1010) / 110) ** 2) - 3) for x in range(760, 1100, 10)] + [(1100, HZ_Y)],
              fill=((170, 146, 170) if not night else (70, 64, 92)))
    hillc = (121, 100, 119) if not night else (54, 48, 63)
    n.polygon([(-20, HZ_Y + 2)] + [(x, hill_top(x)) for x in range(-20, 1100, 6)] + [(1100, HZ_Y + 2)], fill=hillc)
    # cottage on the crest
    cx, base = HILL_X, hill_top(HILL_X) + 6
    wall = (206, 186, 176) if not night else (78, 72, 92); roof = (96, 70, 80) if not night else (34, 30, 44)
    n.rectangle([cx + 6, base - COT_H - 30, cx + 14, base - COT_H - 6], fill=roof)
    n.rectangle([cx - COT_W / 2, base - COT_H, cx + COT_W / 2, base], fill=wall)
    n.polygon([(cx - COT_W / 2 - 6, base - COT_H + 1), (cx - 2, base - COT_H - ROOF_H), (cx + COT_W / 2 + 6, base - COT_H + 1)], fill=roof)
    if lit:
        g = Image.new("RGBA", (W, H)); gg = ImageDraw.Draw(g)
        for r in range(90, 0, -6):
            gg.ellipse([WIN[0] - r, WIN[1] - r, WIN[0] + r, WIN[1] + r], fill=(255, 214, 140, int(60 * (1 - r / 90))))
        near.alpha_composite(g)
        n.rectangle([WIN[0] - 7, WIN[1] - 9, WIN[0] + 7, WIN[1] + 7], fill=(255, 220, 150))
        for k in range(22):                                    # the reflection column under the window
            y = HZ_Y + 12 + k * 26; w_ = 26 - k * 0.6
            n.line([(WIN[0] - w_, y), (WIN[0] + w_, y)], fill=(255, 214, 140, 210 - k * 7), width=4)
    return far, near

def cam_box(s, cx, cy):
    w, h = W / s, H / s
    return (min(max(cx - w / 2, 0), W - w), min(max(cy - h / 2, 0), H - h), s)

def push_box(p, focus, amount):
    s = 1 + amount * p; w, h = W / s, H / s; fx, fy = focus
    return (min(max(fx - w * fx / W, 0), W - w), min(max(fy - h * fy / H, 0), H - h), s)

def ease_io(p): p = min(max(p, 0.0), 1.0); return p * p * (3 - 2 * p)

def sea_frame(box, dy=0.0, night=False, lit=True):
    far, near = sea_plate(night, lit)
    im = far.copy(); sh = Image.new("RGBA", (W, H)); sh.alpha_composite(near, (0, int(round(dy))))
    im.alpha_composite(sh)
    x0, y0, s = box
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + W / s, y0 + H / s)), (lambda x, y: ((x - x0) * s, (y - y0) * s))

BIRDS_R = [(330, 0.12), (470, 0.15), (400, 0.10)]          # (x0 source px, y fraction) -- landscape 0.17/0.21/0.13
def gulls(dr, to_screen, s, t):
    for (x0, yf), sp, hs in zip(BIRDS_R, (40, 34, 46), (17, 14, 19)):
        x, y = to_screen(x0 + sp * t, yf * H); r = hs * s
        dr.line([(x - r, y - r * 0.3), (x - r * 0.4, y - r * 0.5), (x, y)], fill=(70, 62, 80), width=max(3, int(r / 6)))
        dr.line([(x, y), (x + r * 0.4, y - r * 0.5), (x + r, y - r * 0.3)], fill=(70, 62, 80), width=max(3, int(r / 6)))

def envelope(im, c, w, rot=0, alpha=255):
    h = w / 1.55
    e = Image.new("RGBA", (int(w) + 8, int(h) + 8)); d = ImageDraw.Draw(e)
    d.rectangle([4, 4, 4 + w, 4 + h], fill=(239, 230, 214, alpha), outline=(205, 191, 168, alpha), width=max(1, int(w / 90)))
    d.line([(4, 4), (4 + w / 2, 4 + 0.6 * h), (4 + w, 4)], fill=(168, 151, 127, alpha), width=max(1, int(w / 100)))
    d.rectangle([4 + w * 0.80, 4 + h * 0.08, 4 + w * 0.93, 4 + h * 0.33], fill=(188, 97, 94, int(alpha * 0.85)))
    e = e.rotate(rot, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(e, (int(c[0] - e.width / 2), int(c[1] - e.height / 2)))
    return (c[0] - w / 2, c[1] - h / 2, c[0] + w / 2, c[1] + h / 2)

def trail(dr, P, u1, col, r0=3.5, r1=1.6):
    n = 60
    for i in range(n + 1):
        u = i / n * u1
        if i % 2: continue
        x, y = cubic(P, u); r = lerp(r0, r1, u)
        dr.ellipse([x - r, y - r, x + r, y + r], fill=col)


# =====================================================================================================================
# the uncle at portrait size: the landscape polygons (ep4/backdrops.py, 1920 x 1080 px) mapped by one similarity
# =====================================================================================================================
U_S = 1.25                                 # figure scale vs landscape
U_X0, U_Y0 = 60, 600                       # where the landscape point (393, 172) (back of skull, head top) lands
def U(x, y): return (U_X0 + (x - 393) * U_S, U_Y0 + (y - 172) * U_S)
HEAD = [(581, 172), (490, 199), (412, 277), (393, 361), (405, 441), (477, 574), (594, 597), (608, 600), (630, 606),
        (647, 607), (649, 595), (670, 574), (705, 563), (735, 540), (746, 511), (743, 489), (754, 475), (751, 463),
        (757, 457), (770, 455), (784, 441), (751, 406), (737, 383), (726, 378), (737, 360), (731, 347), (736, 342),
        (731, 299), (708, 246), (662, 196)]
BODY = [(470, 568), (540, 572), (605, 585), (650, 600), (694, 636), (720, 674), (700, 694), (710, 719), (713, 734),
        (721, 771), (728, 866), (731, 907), (733, 1003), (736, 1640), (84, 1640), (95, 1010), (109, 907), (178, 754),
        (285, 672), (394, 624), (458, 603)]          # bottom extended from y 1090 to 1640 (portrait frame runs to 1920)
COLLAR = [(461, 600), (460, 612), (534, 622), (597, 632), (631, 641), (638, 648), (641, 663), (687, 699), (721, 677),
          (690, 642), (650, 609), (605, 597), (533, 586), (475, 573)]
WIN_C = U(537.1, 315.8); WIN_R = 93 * U_S
LENS = U(721, 366.5)
EMERGE = U(790, 440)                        # where the words leave the face (in front of the mouth/nose)

def uncle(im, hole=1.0, icon=0.0, tilt=0.0, bg=True):
    d = ImageDraw.Draw(im)
    if bg:
        for y in range(H):
            d.line([(0, y), (W, y)], fill=mix((226, 212, 185), (232, 226, 214), min(1, y / 900)))
        d.ellipse([700, -500, 1500, 400], fill=(228, 214, 188))      # lamp glow, upper right
    th = math.radians(2.0 * tilt); px, py = U(604, 584)
    def R(p):
        x, y = p[0] - px, p[1] - py
        return (px + math.cos(th) * x - math.sin(th) * y, py + math.sin(th) * x + math.cos(th) * y)
    d.polygon([U(*p) for p in BODY], fill=(90, 79, 61))
    d.polygon([R(U(*p)) for p in HEAD], fill=(66, 56, 54))
    d.polygon([U(*p) for p in COLLAR], fill=(213, 202, 184))
    lx, ly = R(LENS); d.ellipse([lx - 32, ly - 28, lx + 32, ly + 28], outline=(196, 169, 134), width=4)
    if hole > 0:
        cx, cy = R(WIN_C); r = WIN_R * hole
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(228, 217, 201))
        if icon > 0: envelope(im, (cx, cy), 112 * U_S * icon)
    return R

def uncle_head_box():
    xs = [U(*p)[0] for p in HEAD]; ys = [U(*p)[1] for p in HEAD]
    return (min(xs), min(ys), max(xs), max(ys))


# =====================================================================================================================
# cards, prompt box, tag
# =====================================================================================================================
def card_img(lines, w, rot, label=None, bold=False, size=40, marks=None, pad=50, lab_px=28):
    """returns (rotated RGBA, map(px,py)->rotated coords, {word: (x0, x1, top)} in unrotated coords, paper (w, h))"""
    meas = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    lh, pgap = 1.42 * size, 0.55 * size
    lab_f = font("mono", lab_px); lab_tr = lab_px * 0.12; lab_h = lab_px * 1.25 + 12
    M = 30; y = M + pad + (lab_h if label else 0); items = []
    for k, tl in enumerate(lines):
        st, tx = ("r", tl) if isinstance(tl, str) else tl
        f_ = font("serif_i" if st == "i" else ("serif_b" if bold else "serif"), size)
        if k: y += pgap
        for ln in wrap(meas, tx, f_, w - 2 * pad):
            items.append((f_, ln, M + pad, y)); y += lh
    h = int(y - M + pad - 0.3 * size)
    im = Image.new("RGBA", (int(w) + 2 * M, h + 2 * M)); d = ImageDraw.Draw(im)
    d.rectangle([M + 6, M + 12, M + w + 6, M + h + 12], fill=(46, 44, 45, 40))
    d.rectangle([M, M, M + w, M + h], fill=CARD + (255,))
    words = {}
    for f_, ln, x, yy in items:
        for tok in ln.replace(".", " ").replace("?", " ").replace(",", " ").split():
            i = (" " + ln + " ").find(" " + tok)
            if tok not in words and i >= 0:
                x0 = x + meas.textlength(ln[:i], font=f_); words[tok] = (x0, x0 + meas.textlength(tok, font=f_), yy)
    for ph in (marks or []):
        first, last = ph.split()[0], ph.split()[-1]
        if first in words:
            x0 = words[first][0]; x1 = words[last][1] if last in words else words[first][1]; yy = words[first][2]
            d.rectangle([x0 - 5, yy + 0.08 * size, x1 + 7, yy + 1.25 * size], fill=HLC + (255,))
    if label: tracked(d, (M + pad, M + pad), label, lab_f, LABEL, lab_tr)
    for f_, ln, x, yy in items: d.text((x, yy), ln, font=f_, fill=INK)
    W0, H0 = im.size
    out = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    W1, H1 = out.size; ar = math.radians(rot)
    def rp(px, py):
        dx, dy = px - W0 / 2, py - H0 / 2
        return (W1 / 2 + dx * math.cos(ar) + dy * math.sin(ar), H1 / 2 - dx * math.sin(ar) + dy * math.cos(ar))
    return out, rp, words, (w, h), M, size

def tape(im, c, rot):
    t = Image.new("RGBA", (156, 46), (236, 224, 196, 200)).rotate(rot, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(t, (int(c[0] - t.width / 2), int(c[1] - t.height / 2)))

def prompt_box(im, x, y, w, text, px, hl=None, nchars=None):
    d = ImageDraw.Draw(im); f_ = font("sans", px)
    padx, pady = 48, 40
    lines = wrap(d, text, f_, w - 2 * padx); lh = px * 1.4
    hgt = len(lines) * lh + 2 * pady - 0.3 * px
    d.rounded_rectangle([x, y, x + w, y + hgt], radius=27, outline=INK, width=3)
    tx, ty = x + padx, y + pady
    shown = len(text) if nchars is None else nchars; used = 0
    for i, ln in enumerate(lines):
        if hl:
            j = (" " + ln + " ").find(" " + hl + " ")
            if j >= 0:
                l0 = tx + d.textlength(ln[:j], font=f_) - 7
                d.rounded_rectangle([l0, ty + i * lh + 0.02 * px, l0 + d.textlength(hl, font=f_) + 15, ty + i * lh + 1.28 * px], 4, fill=HLC)
        take = max(0, min(len(ln), shown - used)); d.text((tx, ty + i * lh), ln[:take], font=f_, fill=INK); used += len(ln) + 1
    return (x, y, x + w, y + hgt), lines, lh

def text_block(im, x, y, text, f_, width, lh, cursor=False):
    d = ImageDraw.Draw(im); lines = wrap(d, text, f_, width)
    for i, ln in enumerate(lines): d.text((x, y + i * lh), ln, font=f_, fill=INK)
    wmax = max(d.textlength(ln, font=f_) for ln in lines)
    if cursor:
        cx = x + d.textlength(lines[-1], font=f_) + 9; cy = y + (len(lines) - 1) * lh
        d.rectangle([cx, cy + 0.12 * lh, cx + 5, cy + 0.88 * lh], fill=INK)
    return (x, y, x + wmax, y + (len(lines) - 1) * lh + f_.size * 1.2), lines

TITLE_LINES = ["THE UNCLE WHO", "ONLY READS LETTERS"]
TITLE_PX = 46
TITLE_TL = (96, 400)             # top-left anchor of the tag: the empty upper sky, clear of the window reflection
def title_tag(im):
    d = ImageDraw.Draw(im); f_ = font("mono", TITLE_PX); tr = TITLE_PX * 0.10
    padx, pady, gap = 22, 16, 10
    lh = TITLE_PX * 1.25
    tw = max(tracked_len(d, s, f_, tr) for s in TITLE_LINES)
    bw, bh = tw + 2 * padx, len(TITLE_LINES) * lh + (len(TITLE_LINES) - 1) * gap + 2 * pady
    x0, y0 = TITLE_TL
    d.rectangle([x0, y0, x0 + bw, y0 + bh], fill=TAG_LIGHT)
    for i, s in enumerate(TITLE_LINES):
        tracked(d, (x0 + padx, y0 + pady + i * (lh + gap) + 1), s, f_, INK, tr)
    return (x0, y0, x0 + bw, y0 + bh)


# =====================================================================================================================
# overlays: UI zones, safe box, 3:4 crop, header and caption
# =====================================================================================================================
def overlays(im, num, when, caption, show_caption=True):
    ov = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(ov)
    sx0, sy0, sx1, sy1 = SAFE
    red = (200, 40, 40, 62)
    d.rectangle([0, 0, W, sy0], fill=red); d.rectangle([0, sy1, W, H], fill=red)
    d.rectangle([0, sy0, sx0, sy1], fill=red); d.rectangle([sx1, sy0, W, sy1], fill=red)
    for x in range(sx1 + 30, W, 60):                     # the button column
        pass
    im.alpha_composite(ov)
    d = ImageDraw.Draw(im)
    d.rectangle([sx0, sy0, sx1, sy1], outline=(0, 200, 230), width=5)
    for y in (GRID[1], GRID[3]):
        dashed(d, [(0, y), (W, y)], (230, 0, 200), width=5, dash=30, gap=16)
    d.text((W - 14, GRID[1] + 8), "3:4 grid", font=font("mono5", 26), fill=(230, 0, 200), anchor="ra")
    d.text((W - 14, GRID[3] - 8), "3:4 grid", font=font("mono5", 26), fill=(230, 0, 200), anchor="rd")
    # header in the top bar zone
    d.rectangle([0, 0, W, 96], fill=(20, 20, 22))
    d.text((40, 48), f"{num:02d}", font=font("mono5", 52), fill=(255, 255, 255), anchor="lm")
    d.text((140, 48), when, font=font("mono", 36), fill=(220, 220, 220), anchor="lm")
    if not show_caption: return im
    # caption in the caption zone
    d.rectangle([0, 1720, W, H], fill=(20, 20, 22))
    f_ = font("sans", 38); lines = wrap(d, caption, f_, W - 80)
    for i, ln in enumerate(lines[:4]): d.text((40, 1742 + i * 44), ln, font=f_, fill=(255, 255, 255))
    return im


FRAMES = []
def frame(num, slug, when, caption):
    def deco(fn):
        FRAMES.append((num, slug, when, caption, fn)); return fn
    return deco

def sheet_bg(color):
    return Image.new("RGBA", (W, H), color + (255,))


# =====================================================================================================================
# the beats
# =====================================================================================================================
TILT = (0.6, 5.0); S0 = 2.0
def dusk_box(t):
    if t < TILT[1]:
        p = ease_io((t - TILT[0]) / (TILT[1] - TILT[0]))
        return cam_box(S0 - (S0 - 1) * p, (0.45 + 0.05 * p) * W, (0.25 + 0.25 * p) * H), PARALLAX_R * (1 - p) ** 1.5
    return push_box(ease_io((t - 5.0) / 12.5), WIN, 0.06), 0.0

@frame(1, "s1_open_sky", "s1  0.0 s", "Open on the sky only (zoom 2.0, near plane 90 px low). Gulls sit mid-box; no horizon or house yet.")
def f01():
    box, dy = dusk_box(0.0); im, ts = sea_frame(box, dy, lit=False); d = ImageDraw.Draw(im)
    gulls(d, ts, box[2], 0.0)
    rec("01", "camera_box_t0", [round(v, 1) for v in box])
    rec("01", "gulls_screen", [[round(c) for c in ts(x0, yf * H)] for x0, yf in BIRDS_R], key=False)
    return im

@frame(2, "s1_tilt", "s1  3.0 s", "Tilt down with parallax: the hill and sea rise faster than the sky. Same move as landscape, vertical travel only.")
def f02():
    box, dy = dusk_box(3.0); im, ts = sea_frame(box, dy, lit=False); d = ImageDraw.Draw(im)
    gulls(d, ts, box[2], 3.0)
    guide_arrow(d, [(950, 760), (950, 1000)]); guide_arrow(d, [(1010, 1180), (1010, 900)])
    guide_label(d, (940, 740), "sky", anchor="rd"); guide_label(d, (1000, 1200), "near plane", anchor="ra")
    rec("02", "camera_box_t3", [round(v, 1) for v in box]); rec("02", "parallax_dy", round(dy, 1), key=False)
    return im

@frame(3, "s1_title", "s1  6.5 s", "Full frame: horizon at 1150, cottage window at (680, 980) in the middle third. Title: one two-line tag, 46 px mono, in the empty upper sky.")
def f03():
    box, _ = dusk_box(6.5); im, ts = sea_frame(box); d = ImageDraw.Draw(im)
    gulls(d, ts, box[2], 6.5)
    tb = title_tag(im)
    rec("03", "title_tag", ibox(tb)); rec("03", "window", list(WIN), key=False); rec("03", "horizon_y", HZ_Y, key=False)
    rec("03", "cottage", ibox((WIN[0] - 30, WIN[1] - 75, WIN[0] + 30, WIN[1] + 30)))
    return im

PATH_OUT_R = [(-150, 1330), (330, 1280), (540, 1100), WIN]
@frame(4, "s2_letter_out", "s2  14.5-16.9 s", "The letter flies in from the lower left, above the caption zone, and shrinks into the window (280 px to 16 px).")
def f04():
    box, _ = dusk_box(15.6); im, ts = sea_frame(box); d = ImageDraw.Draw(im)
    gulls(d, ts, box[2], 15.6)
    P = [ts(*p) for p in PATH_OUT_R]
    trail(d, P, 0.55, (243, 235, 224, 200))
    dashed(d, [cubic(P, u / 40) for u in range(41)], GUIDE, 3)
    for u, a in ((0.10, 90), (0.30, 255)):
        c = cubic(P, u); wv = lerp(280, 16, ease_io(u)); eb = envelope(im, c, wv, lerp(-14, -2, u), a)
        if a == 255: rec("04", "envelope_at_u0.30", ibox(eb))
    rec("04", "PATH_OUT", [list(p) for p in PATH_OUT_R], key=False)
    return im

@frame(5, "w3_window_to_window", "w3  17.5-18.6 s", "Rush into the cottage window at (680, 980), resolve out of the head hole at (240, 780). Both focus points sit in the box.")
def f05():
    im = Image.new("RGBA", (W, H)); uncle(im, hole=1.0)
    blur = Image.new("RGBA", (W, H), (250, 226, 171, 120)); im.alpha_composite(blur)
    d = ImageDraw.Draw(im); cx, cy = WIN_C
    for r in (150, 240, 340):
        dashed(d, [(cx + r * math.cos(a / 30 * 2 * math.pi), cy + r * math.sin(a / 30 * 2 * math.pi)) for a in range(31)], GUIDE, 3)
    guide_label(d, (cx + 160, cy - 300), "resolve: zoom 2.2 to 1.0 about the hole")
    d.rectangle([600, 1180, 760, 1340], outline=GUIDE, width=4)
    guide_label(d, (600, 1350), "rush focus = window (680, 980)", px=24)
    rec("05", "rush_focus", list(WIN), key=False); rec("05", "resolve_focus", [round(v) for v in WIN_C], key=False)
    return im

LETTER = [("i", "Dear Uncle,"), ("r", "What can I cook tonight with eggs and spinach?"), ("i", "Love, Sam")]
LETTER_W, LETTER_ROT, LETTER_POS = 430, -2, (515, 1000)     # paper top-left at rest (before rotation)
@frame(6, "s3_envelope_lands", "s3  19.2 s", "Uncle at 1.25x, facing right, head inside the box. The hole (r 116) holds the envelope icon (140 px).")
def f06():
    im = Image.new("RGBA", (W, H)); uncle(im, hole=1.0, icon=1.0)
    rec("06", "head", ibox(uncle_head_box())); rec("06", "hole", ibox((WIN_C[0] - WIN_R, WIN_C[1] - WIN_R, WIN_C[0] + WIN_R, WIN_C[1] + WIN_R)))
    rec("06", "lens_centre", [round(v) for v in LENS], key=False)
    return im

def letter_card(im, x_off=0):
    out, rp, words, (w, h), M, fs = card_img(LETTER, LETTER_W, LETTER_ROT, size=40, pad=44)
    x, y = LETTER_POS[0] - M + x_off, LETTER_POS[1] - M
    im.alpha_composite(out, (int(x), int(y)))
    corners = [rp(M, M), rp(M + w, M), rp(M + w, M + h), rp(M, M + h)]
    xs = [x + c[0] for c in corners]; ys = [y + c[1] for c in corners]
    return (min(xs), min(ys), max(xs), max(ys)), (w, h)

@frame(7, "s3_reads", "s3  23.0 s", "The letter slides in from the right to rest below-right of his face (430 px card, 40 px serif). The read-nod now looks down at it.")
def f07():
    im = Image.new("RGBA", (W, H)); uncle(im, hole=1.0, icon=1.0, tilt=1.0)
    cb, (w, h) = letter_card(im)
    d = ImageDraw.Draw(im); guide_arrow(d, [(1060, 1200), (975, 1200)]); guide_label(d, (1060, 1150), "in", anchor="ra")
    rec("07", "letter_card", ibox(cb)); rec("07", "letter_paper_wh", [w, h], key=False)
    return im

def yellow_scene(im, typed=True):
    rb = {}
    x, w = 84, 852
    bb, lines, lh = prompt_box(im, x, 0, w, "Dear Uncle, what can I cook tonight with eggs and spinach? Love, Sam", 44)
    f_ = font("serif_b", 56); rlh = 56 * 1.36
    tmp = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    rl = wrap(tmp, "A spinach omelette. Wilt the spinach in butter, pour in three beaten eggs, fold it over and serve.", f_, w - 6)
    grp = (bb[3] - bb[1]) + 64 + (len(rl) - 1) * rlh + 56 * 1.2
    y0 = int(840 - grp / 2)                                   # group centred a little above the safe-box centre (860)
    return x, w, y0, f_, rlh

def draw_yellow(im, typed=True):
    x, w, y0, f_, rlh = yellow_scene(im)
    bb, lines, lh = prompt_box(im, x, y0, w, "Dear Uncle, what can I cook tonight with eggs and spinach? Love, Sam", 44)
    tb, rl = text_block(im, x + 6, bb[3] + 64, "A spinach omelette. Wilt the spinach in butter, pour in three beaten eggs, fold it over and serve.", f_, w - 6, rlh, cursor=True)
    return bb, tb, lines, rl

def torn_v(d, x, color, h0=0, h1=H):
    pts = [(x + 6 * math.sin(y * 0.11) + 3 * math.sin(y * 0.53), y) for y in range(h0, h1 + 12, 12)]
    d.line(pts, fill=color, width=6)

def torn_h(d, y, color):
    pts = [(x, y + 6 * math.sin(x * 0.11) + 3 * math.sin(x * 0.53)) for x in range(0, W + 12, 12)]
    d.line(pts, fill=color, width=6)

@frame(8, "w4_yellow_from_right", "w4  24.3 s", "Yellow sheet revealed from the right (edge x = W to 0, 0.6 s). Horizontal travel is only 1080 px here, so it reads calmer than landscape.")
def f08():
    im = Image.new("RGBA", (W, H)); uncle(im, hole=1.0, icon=1.0, tilt=1.0); letter_card(im)
    y = sheet_bg((236, 212, 144)); draw_yellow(y)
    ex = 470
    im.alpha_composite(y.crop((ex, 0, W, H)), (ex, 0))
    d = ImageDraw.Draw(im); torn_v(d, ex, (250, 240, 214))
    guide_arrow(d, [(ex + 160, 1560), (ex + 30, 1560)])
    return im

@frame(9, "s4_reply", "s4  29.0 s", "Prompt box 852 wide, 44 px Manrope (2 lines); reply 56 px bold serif, 4 lines, types under it. Group centred in the box.")
def f09():
    im = sheet_bg((236, 212, 144)); bb, tb, lines, rl = draw_yellow(im)
    rec("09", "prompt_box", ibox(bb)); rec("09", "reply_text", ibox(tb))
    rec("09", "prompt_lines", lines, key=False); rec("09", "reply_lines", rl, key=False)
    return im

@frame(10, "w5_yellow_slides_down", "w5  29.6 s", "The yellow sheet slides down with its content, off through the caption zone, uncovering the uncle (envelope still in the hole).")
def f10():
    im = Image.new("RGBA", (W, H)); uncle(im, hole=1.0, icon=1.0, tilt=1.0)
    y = sheet_bg((236, 212, 144)); draw_yellow(y)
    off = 1060
    sh = Image.new("RGBA", (W, H)); sh.alpha_composite(y.crop((0, 0, W, H - off)), (0, off))
    d = ImageDraw.Draw(im); d.rectangle([0, off - 26, W, off], fill=(40, 30, 20, 60))
    im.alpha_composite(sh); d = ImageDraw.Draw(im); torn_h(d, off, (250, 240, 214))
    guide_arrow(d, [(990, off - 260), (990, off - 60)])
    return im

# the word cloud: (text, px, alpha, rest x, rest y [text top-left at 36.0 s], drift px/s (vx, vy))
WORDS_R = [("spinach", 50, .85, 590, 820, (6, -12)), ("eggs", 46, .75, 640, 905, (8, -8)), ("tonight", 42, .60, 650, 640, (10, -18)),
           ("omelette", 42, .55, 520, 520, (8, -22)), ("Dear Uncle", 38, .45, 650, 455, (8, -20)), ("butter", 34, .35, 760, 740, (14, -16)),
           ("Sam", 30, .25, 330, 420, (4, -26)), ("fold", 28, .20, 840, 590, (14, -22)), ("cook", 28, .12, 480, 330, (6, -18)),
           ("love", 28, .08, 800, 330, (12, -14))]

@frame(11, "s5_words_drift", "s5  36.0 s", "He forgets: the words leave his face and rise up and right into the empty top of the frame. 28-50 px mono, all inside the box.")
def f11():
    im = Image.new("RGBA", (W, H)); uncle(im, hole=1.0, icon=0.0)
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    words = {}
    for text, px, a, x, y, (vx, vy) in WORDS_R:
        f_ = font("mono", px); d.text((x, y), text, font=f_, fill=INK + (int(255 * max(a, 0.25)),))
        bb = d.textbbox((x, y), text, font=f_)
        end = (bb[2] + vx * 3.7, bb[1] + vy * 3.7)
        words[text] = ibox(bb)
        rec("11", "word_" + text.replace(" ", "_"), ibox(bb))
        rec("11", "word_" + text.replace(" ", "_") + "_at_fade_end", ibox((bb[0] + vx * 3.7, bb[1] + vy * 3.7, end[0], bb[3] + vy * 3.7)))
    im.alpha_composite(lay); d = ImageDraw.Draw(im)
    ex, ey = EMERGE
    for text, px, a, x, y, v in WORDS_R[:4]:
        guide_arrow(d, [(ex, ey), (lerp(ex, x, 0.5), lerp(ey, y, 0.5) + 20), (x - 8, y + px * 0.6)], width=3)
    rec("11", "emerge_point", [round(ex), round(ey)], key=False)
    guide_label(d, (100, 1500), "alpha shown >= 0.25 for legibility here; real alphas .85 to .08", px=24)
    return im

@frame(12, "s5_gone", "s5  39.6 s", "\"Gone.\" Words faded out, the hole closing (r 116 to 0 over 0.45 s). The last second is the solid head.")
def f12():
    im = Image.new("RGBA", (W, H)); uncle(im, hole=0.45, icon=0.0)
    lay = Image.new("RGBA", (W, H)); d = ImageDraw.Draw(lay)
    for text, px, a, x, y, (vx, vy) in WORDS_R:
        d.text((x + vx * 3.6, y + vy * 3.6), text, font=font("mono", px), fill=INK + (int(255 * a * 0.06),))
    im.alpha_composite(lay)
    return im

@frame(13, "w6_pink_from_left", "w6  41.0 s", "CHANGED: pink from the left, not from the bottom. An upward wipe mimics the feed's swipe-to-next and starts behind the caption.")
def f13():
    im = Image.new("RGBA", (W, H)); uncle(im, hole=0.0)
    p = sheet_bg((233, 163, 178)); draw_pink(p, empty=True)
    ex = 610
    im.alpha_composite(p.crop((0, 0, ex, H)), (0, 0))
    d = ImageDraw.Draw(im); torn_v(d, ex, (250, 225, 230))
    guide_arrow(d, [(ex - 160, 1560), (ex - 30, 1560)])
    return im

def draw_pink(im, empty=False):
    x, w = 84, 852
    q = "Thanks! Can you make it without eggs?"
    tmp = Image.new("RGBA", (W, H)); bb0, _, _ = prompt_box(tmp, x, 0, w, q, 52)
    f_ = font("serif_b", 76)
    grp = (bb0[3] - bb0[1]) + 70 + 76 * 1.2
    y0 = int(840 - grp / 2)
    bb, lines, lh = prompt_box(im, x, y0, w, q, 52, hl=None if empty else "it", nchars=0 if empty else None)
    tb = None
    if not empty: tb, _ = text_block(im, x + 6, bb[3] + 70, "Make what, dear?", f_, w, 76 * 1.35)
    return bb, tb, lines

@frame(14, "s6_make_what", "s6  48.5 s", "Prompt box 52 px Manrope (2 lines, \"it\" highlighted); \"Make what, dear?\" 76 px bold serif, one line.")
def f14():
    im = sheet_bg((233, 163, 178)); bb, tb, lines = draw_pink(im)
    rec("14", "prompt_box", ibox(bb)); rec("14", "answer_text", ibox(tb)); rec("14", "prompt_lines", lines, key=False)
    return im

@frame(15, "w7_cream_from_right", "w7  49.5 s", "Cream sheet revealed from the right, as in landscape (empty cream: the cards drop in after).")
def f15():
    im = sheet_bg((233, 163, 178)); draw_pink(im)
    c = sheet_bg((218, 211, 199)); ex = 560
    im.alpha_composite(c.crop((ex, 0, W, H)), (ex, 0))
    d = ImageDraw.Draw(im); torn_v(d, ex, (240, 236, 228)); guide_arrow(d, [(ex + 160, 1560), (ex + 30, 1560)])
    return im

C_ARGS = [([("r", "What can I cook tonight with eggs and spinach?")], 3, "YOUR FIRST LETTER", False, None),
          (["A spinach omelette.", "Wilt the spinach in butter, pour in three beaten eggs…"], -1.5, "HIS REPLY", True, "spinach omelette"),
          ([("r", "Thanks! Can you make it without eggs?")], 1, "YOUR NEW LETTER", False, "it")]
CARD_W = 720
CARD_X = [100, 140, 114]           # paper left edges (before rotation)
CARD_OVERLAP = [0, 14, 16]         # how far each card tucks under the one above (px)
ANS2 = "Without eggs? Try spinach and cheese on toast."

def history(im, marks=True, arrow=True, reply=True, y_top=None):
    if y_top is None:
        tmp = Image.new("RGBA", (W, H)); pl, _, rb_ = history(tmp, False, False, True, y_top=0)
        y_top = int(860 - (rb_[3] - pl[0]["box"][1]) / 2)        # centre cards + reply on the safe-box centre
        LAYOUT.setdefault("_s7", {})["y_top"] = y_top
    d = ImageDraw.Draw(im)
    y = y_top; placed = []
    for i, (lines, rot, label, bold, mk) in enumerate(C_ARGS):
        out, rp, words, (w, h), M, fs = card_img(lines, CARD_W, rot, label, bold, 40, [mk] if (marks and mk) else None, pad=50)
        y -= CARD_OVERLAP[i]
        ox = CARD_X[i] - M - (out.width - (CARD_W + 2 * M)) / 2; oy = y - M - (out.height - (h + 2 * M)) / 2
        im.alpha_composite(out, (int(ox), int(oy)))
        corners = [rp(M, M), rp(M + w, M), rp(M + w, M + h), rp(M, M + h)]
        xs = [ox + c[0] for c in corners]; ys = [oy + c[1] for c in corners]
        placed.append(dict(box=(min(xs), min(ys), max(xs), max(ys)), rp=rp, words=words, M=M, fs=fs, ox=ox, oy=oy, h=h))
        tape(im, (CARD_X[i] + CARD_W * (0.50 + 0.07 * (i - 1)), y - 4), (6, -8, 4)[i])
        y += h
    d = ImageDraw.Draw(im)
    ap = None
    if arrow:
        c2, c3 = placed[1], placed[2]
        x0, x1, ty = c3["words"]["it"]; a0 = c3["rp"]((x0 + x1) / 2, ty + 0.02 * c3["fs"]); a0 = (c3["ox"] + a0[0], c3["oy"] + a0[1] - 10)
        x0, x1, ty = c2["words"]["omelette"]; a3 = c2["rp"](x1 + 18, ty + 0.62 * c2["fs"]); a3 = (c2["ox"] + a3[0] + 4, c2["oy"] + a3[1])
        R = c2["box"][2]
        band_y = c3["box"][1] - 4                              # the clear strip just above card 3 (under his reply's text)
        pts = [a0, (a0[0] + 8, a0[1] - 34), (a0[0] + 70, band_y - 10), (R - 40, band_y - 12), (R + 30, band_y - 34),
               (R + 62, (band_y + a3[1]) / 2), (R + 44, a3[1] + 20), (R + 6, a3[1] + 6), (a3[0] + 70, a3[1] + 2), a3]
        # Catmull-Rom through the waypoints
        Q = [pts[0]] + pts + [pts[-1]]; P = []
        for i in range(1, len(Q) - 2):
            p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
            for k in range(16):
                u = k / 16
                P.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u * u + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u ** 3) for j in range(2)))
        P.append(pts[-1])
        d.line(P, fill=INK, width=5, joint="curve"); arrowhead(d, P[-1], P[-4], INK, size=26, width=5)
        ap = dict(waypoints=[[round(v) for v in p] for p in pts], outermost_x=round(max(p[0] for p in P)))
    rb = None
    if reply:
        f_ = font("serif_b", 60)
        rb, rl = text_block(im, 104, placed[2]["box"][3] + 70, ANS2, f_, 840, 60 * 1.35)
    return placed, ap, rb

@frame(16, "s7_cards_drop", "s7  56.0 s", "Three letters drop in and tape down in a vertical stack, 720 px cards, 40 px serif, 28 px mono labels, 120 px gutter kept free on the right for the arrow.")
def f16():
    im = sheet_bg((218, 211, 199)); placed, _, _ = history(im, marks=False, arrow=False, reply=False)
    for i, p in enumerate(placed): rec("16", f"card{i + 1}", ibox(p["box"]))
    d = ImageDraw.Draw(im); guide_arrow(d, [(990, 400), (990, 520)]); guide_label(d, (980, 380), "drop 60 px", anchor="rd", px=24)
    return im

@frame(17, "s7_annotate_reply", "s7  61.0 s", "\"it\" swept yellow, ink arrow loops up round the reply card's right edge (x <= 940) to \"spinach omelette\"; the new reply types below the stack.")
def f17():
    im = sheet_bg((218, 211, 199)); placed, ap, rb = history(im)
    for i, p in enumerate(placed): rec("17", f"card{i + 1}", ibox(p["box"]))
    rec("17", "arrow", ap, key=False); rec("17", "arrow_outermost", [ap["outermost_x"] - 1, 900, ap["outermost_x"], 901])
    rec("17", "reply_text", ibox(rb))
    return im

PATH_HOME_R = [WIN, (480, 900), (300, 1140), (430, 1290)]
@frame(18, "s8_reply_home", "f8-s8  61.2-72.0 s", "Dip to black, night. The reply swoops from the window toward us, 16 to 340 px, ending low-centre inside the box; slow 4% push; fade out.")
def f18():
    im, ts = sea_frame(push_box(0.7, WIN, 0.04), night=True); d = ImageDraw.Draw(im)
    P = [ts(*p) for p in PATH_HOME_R]
    trail(d, P, 1.0, (246, 207, 134, 200), 1.6, 3.6)
    dashed(d, [cubic(P, u / 40) for u in range(41)], GUIDE, 3)
    envelope(im, cubic(P, 0.55), lerp(16, 340, 0.55), 4, 110)
    eb = envelope(im, P[3], 340, 8)
    rec("18", "envelope_end", ibox(eb)); rec("18", "PATH_HOME", [list(p) for p in PATH_HOME_R], key=False)
    return im


# =====================================================================================================================
def contact(frames, idx, total):
    cw, ch, gap, cap = 600, 1067, 30, 150
    head = 150
    sw = 3 * cw + 4 * gap; sh = head + 2 * (ch + cap) + gap
    S = Image.new("RGB", (sw, sh), (28, 28, 30)); d = ImageDraw.Draw(S)
    d.text((gap, 40), f"EP4 REEL  BLOCKOUTS  {idx}/{total}", font=font("mono5", 46), fill=(255, 255, 255))
    d.text((sw - gap, 24), "cyan: safe box 60-960 x 250-1470", font=font("mono", 26), fill=(0, 200, 230), anchor="ra")
    d.text((sw - gap, 58), "magenta: 3:4 grid crop y 240-1680", font=font("mono", 26), fill=(230, 0, 200), anchor="ra")
    d.text((sw - gap, 92), "red: platform UI   orange: motion guides", font=font("mono", 26), fill=(255, 140, 60), anchor="ra")
    for k, (num, slug, when, caption, im) in enumerate(frames):
        r, c = divmod(k, 3)
        x = gap + c * (cw + gap); y = head + r * (ch + cap)
        S.paste(im.convert("RGB").resize((cw, ch), Image.LANCZOS), (x, y))
        f_ = font("sans", 27); lines = wrap(d, f"{num:02d}  {caption}", f_, cw)
        for i, ln in enumerate(lines[:4]): d.text((x, y + ch + 10 + i * 33), ln, font=f_, fill=(235, 235, 235))
    S.save(os.path.join(OUT, f"blockouts_{idx}.jpg"), quality=88)


def main():
    done = []
    for num, slug, when, caption, fn in FRAMES:
        base = fn().convert("RGBA")
        im = overlays(base.copy(), num, when, caption)
        im.convert("RGB").save(os.path.join(FR, f"{num:02d}_{slug}.png"), optimize=True)
        done.append((num, slug, when, caption, overlays(base, num, when, caption, show_caption=False)))
    for i in range(0, len(done), 6):
        contact(done[i:i + 6], i // 6 + 1, (len(done) + 5) // 6)
    bad = []
    for beat, name, (x0, y0, x1, y1) in CHECKS:
        if x0 < SAFE[0] - 0.5 or y0 < SAFE[1] - 0.5 or x1 > SAFE[2] + 0.5 or y1 > SAFE[3] + 0.5:
            bad.append((beat, name, (round(x0), round(y0), round(x1), round(y1))))
    LAYOUT["_meta"] = dict(W=W, H=H, SAFE=SAFE, GRID=GRID, HZ_Y=HZ_Y, WIN=WIN, U_S=U_S, U_X0=U_X0, U_Y0=U_Y0,
                           WIN_C=[round(v, 1) for v in WIN_C], WIN_R=WIN_R, outside_safe=bad)
    with open(os.path.join(OUT, "layout.json"), "w") as fh: json.dump(LAYOUT, fh, indent=1, default=str)
    print("frames:", len(done)); print("outside safe box:", bad or "none")


if __name__ == "__main__":
    main()
