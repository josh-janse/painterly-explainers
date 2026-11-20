"""Painted backdrop plates for ep4 (SPEC §3; the lost `ep4_scenes.py`).

Usage, from the repo root (one scene per process; the engine is exec'd into this module's namespace):

    python3 -m ep4.backdrops SCENE [--dpi 144] [--out DIR]
    SCENE in: dusk, night, uncle, paper_yellow, paper_pink, paper_cream
    env NOCLOUDS=1     dusk/night without the cloud wisps   -> dusk_nc.jpg / night_nc.jpg
    env WINDOW_OFF=1   dusk/night with the window dark       -> dusk_off.jpg / night_off.jpg
    env PAPER_FROM_CANVAS=1   paper_*: copy docs/ref/canvas_v6/paper_*.jpg instead of painting

Writes into out/ep4/ (or --out): see SPEC §3.1 for the files and mask keys. `scripts/build_backdrops.sh` builds all.

env EP4_FORMAT=reel   paint the 9:16 plates instead (1080 x 1920, page 190.5 x 338.667 mm at 144 dpi) into out/ep4_reel/:
                      dusk/night repainted on the portrait geometry (horizon y 1150, window (680, 980), docs/REEL_LAYOUT.md
                      §2 s1-s2, §4), the uncle repainted at 1.25x through the figure map U(x, y), paper_* rotated 90 deg
                      from the approved landscape plates (env PAPER_PAINT=1 paints them at the portrait page instead).
                      Same seeds, file names and mask keys as landscape. The landscape recipe is untouched.
The dusk/night code is the recovered v9 recipe (SPEC §3.2) with the v8 patches. The uncle and the paper plates were
rebuilt from the spec's measurements and the canvas plates (their code was lost).
"""
if __name__ != "__main__":
    raise ImportError("ep4.backdrops is a script: run  python3 -m ep4.backdrops SCENE")

import os, sys, shutil
import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENG = os.path.join(_ROOT, "engine")
from ep4.common import FORMAT as _FORMAT, A as _A, A_LANDSCAPE as _A_LAND
REEL = _FORMAT == "reel"
_args = sys.argv[1:]
if not _args or _args[0] in ("-h", "--help"):
    print(__doc__); sys.exit(0)
SCENE = _args[0]
_dpi, _outdir = 144, _A
if "--dpi" in _args: _dpi = int(_args[_args.index("--dpi") + 1])
if "--out" in _args: _outdir = os.path.abspath(_args[_args.index("--out") + 1])
os.makedirs(_outdir, exist_ok=True)
NIGHT = SCENE == "night"
WOFF = bool(os.environ.get("WINDOW_OFF"))
NOCL = bool(os.environ.get("NOCLOUDS"))
_suffix = "_nc" if (NOCL and SCENE in ("dusk", "night")) else ("_off" if (WOFF and SCENE in ("dusk", "night")) else "")
OUT = os.path.join(_outdir, f"{SCENE}{_suffix}.jpg")
VARIANT = bool(_suffix)
f32 = np.float32

if SCENE.startswith("paper_") and os.environ.get("PAPER_FROM_CANVAS"):
    shutil.copy(os.path.join(_ROOT, "docs", "ref", "canvas_v6", f"{SCENE}.jpg"), OUT)
    print("copied", OUT); sys.exit()
if SCENE.startswith("paper_") and REEL and not os.environ.get("PAPER_PAINT"):
    # the approved landscape sheet turned a quarter: the same paper at exactly 1080 x 1920. paper_ground has no marks
    # with a direction (isotropic mottle, stains and light; the vignette is normalised per axis), so it reads the same.
    _src = os.path.join(_A_LAND, f"{SCENE}.jpg")
    _im = Image.open(_src).convert("RGB")
    assert _im.size == (1920, 1080), (_src, _im.size)
    _im.transpose(Image.ROTATE_90).save(OUT, quality=95)
    print("rotated", _src, "->", OUT); sys.exit()

# ---------------- engine config (must come before the engine exec) ----------------
SEED = {"dusk": 4, "night": 4, "uncle": 12, "paper_yellow": 23, "paper_pink": 23, "paper_cream": 23}[SCENE]
EDGE_TOOTH = 0.6
PAGE_MM = (1080 / 144 * 25.4, 1920 / 144 * 25.4) if REEL else (1920 / 144 * 25.4, 1080 / 144 * 25.4)   # 1080 x 1920 / 1920 x 1080 at 144 dpi
os.chdir(_ENG)                                         # texture paths are tex/... relative to engine/
sys.argv = ["ep4_scenes", str(_dpi), OUT]
exec(open(os.path.join(_ENG, "engine.py")).read())
exec(open(os.path.join(_ENG, "marks.py")).read())
exec(open(os.path.join(_ENG, "figures.py")).read())

PX = lambda pts: [(X(x), Y(y)) for x, y in pts]
S144 = W / 1920.0                                      # px coordinates below are written for the 1920 x 1080 frame
PXA = lambda pts: [(x * S144, y * S144) for x, y in pts]

def to_u8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)

def save(img=None, path=None):
    path = path or OUT
    Image.fromarray(to_u8(canvas if img is None else img)).save(path, quality=92)
    print("saved", path)

def save_rgba(rgb_, a_, path):
    Image.fromarray(np.dstack([to_u8(rgb_), to_u8(a_)]), "RGBA").save(path, optimize=True)
    print("saved", path)

def paper_ground(base, vignette=0.032, seed=7):
    """the plain coloured paper plate: soft plaster mottle, light tooth, a few large faint stains, a gentle vignette"""
    global canvas
    canvas = np.ones((H, W, 3), f32) * rgb(*base)
    canvas *= (1 - 0.016 * mottle)[..., None]                              # the plaster blotches of the scan
    canvas *= (1 - 0.012 * smooth(0.3, 2.0, -tooth))[..., None]            # light granulation in the tooth
    n = lowfreq(520 * K, seed, 3)                                          # big faint stains with a slightly darker tide line
    st = smooth(0.7, 1.3, n); edge = st * (1 - st) * 4
    canvas *= (1 - 0.008 * st - 0.008 * edge)[..., None]
    canvas *= (1 + 0.012 * lowfreq(1400 * K, seed + 1, 2))[..., None]      # broad uneven light
    r2 = ((xx - 0.5) / 0.5) ** 2 + ((yy - 0.5) / 0.5) ** 2
    canvas *= (1 - vignette * r2)[..., None]


# =====================================================================================================================
# paper plates (SPEC §3.4)
# =====================================================================================================================
if SCENE.startswith("paper_"):
    # base colours set so the finished plate means land on the canvas plates / video means (§3.4)
    base = {"paper_yellow": (253, 227, 154), "paper_pink": (250, 176, 191), "paper_cream": (230, 225, 213)}[SCENE]
    paper_ground(base)
    save(); sys.exit()


# =====================================================================================================================
# dusk and night, 9:16 (docs/REEL_LAYOUT.md §2 s1-s2, §4): the landscape recipe below, repainted on the portrait page.
# Geometry is written in output px. Sizes that were px in landscape stay px (kh / kw turn a landscape H- / W-unit
# size into the same px size here); the hill is 1.24x taller with a 0.86x tail, the cottage 1.2x, the sea column
# longer. Same seed, same draw order, same mask keys, so the _nc / _off variants still match pixel for pixel.
# =====================================================================================================================
if SCENE in ("dusk", "night") and REEL:
    kh, kw = 1080.0 / H, 1920.0 / W                       # landscape H-units -> portrait H-units (W-units likewise)
    HZ_PX = 1150.0; HZ = HZ_PX / H                         # 0.599
    CREST_X, HILL_H, TAIL, FALL = 680.0, 166.0, 330.0, 215.0
    WINP = (680.0, 980.0)                                  # the lit window = push / rush / flight focus
    COT = 1.2                                              # cottage size vs its landscape px size
    XPX = xx * W                                           # (1, W) px
    # ---------------- SKY: one graded wash, the sun just set off-frame left (distance in px from the glow) ----------------
    # (the glow sits further off-frame than landscape's -288 px so the hill and the cottage stand against the same
    #  lilac-blue they do in landscape; the left horizon keeps the peach)
    gxp, gyp, D0 = -380.0, HZ_PX + 43.0, 1500.0
    d = np.sqrt((XPX - gxp) ** 2 + (yy * H - gyp) ** 2) / D0 + 0.03 * lowfreq(900 * K, 11, 2)
    if NIGHT:
        stops_d = [0.0, 0.35, 0.60, 0.95, 1.5]
        stops_c = [(150, 112, 120), (98, 86, 118), (62, 64, 104), (40, 44, 82), (30, 33, 66)]
    else:
        stops_d = [0.0, 0.22, 0.48, 0.85, 1.5]
        stops_c = [(250, 214, 168), (238, 186, 168), (196, 168, 190), (150, 150, 192), (118, 126, 178)]
    canvas = np.stack([np.interp(d, stops_d, [c[i] for c in stops_c]) for i in range(3)], -1).astype(f32) / 255
    canvas *= (1 - 0.012 * mottle)[..., None]
    canvas *= (1 - 0.03 * smooth(0.3, 2.0, -tooth))[..., None]
    del d
    # cloud wisps, spread down the tall sky (we open zoomed in on it): (y, x0, length) px, cooler high, warmer low
    _rng_state = rng.bit_generator.state
    WISPS = [(300, 120, 400, (186, 160, 196), 0.35), (365, 280, 320, (226, 170, 172), 0.45),
             (440, 640, 360, (200, 164, 192), 0.3),
             (520, 30, 360, (244, 196, 176), 0.4), (650, 430, 380, (214, 160, 176), 0.35),
             (800, 90, 330, (246, 206, 178), 0.3), (880, 380, 240, (212, 172, 186), 0.25)]
    for i, (cy, cx0, ln, col, a) in ([] if os.environ.get("NOCLOUDS") else enumerate(WISPS)):
        if NIGHT: col = tuple(int(c * 0.55) for c in col); a *= 0.8
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        for j in range(5):
            y = cy + rng.normal(0, 13.0); x0 = cx0 + rng.uniform(-58, 96); l = ln * rng.uniform(0.5, 1.0)
            draw_stroke(dr, bez((x0, y), (x0 + l / 2, y - 8.6), (x0 + l, y + 3.2), 30),
                        rng.uniform(10, 22) * DPI / 100, 2 * DPI / 100, 0.9, 0.3)
        soft_strokes(lay, rgb(*col), a, 7)
    rng.bit_generator.state = _rng_state
    if NIGHT:   # stars: sparse, uneven, in the top ~700 px
        riso(np.ones((H, W), f32) * smooth(0.36, 0.03, yy), rgb(240, 232, 214), 0.0012 * smooth(0.40, 0.0, yy), 501, size=0.6)
    haze = np.exp(-((yy - HZ + 0.006 * kh) / (0.02 * kh)) ** 2) * (0.5 if not NIGHT else 0.25)
    canvas += (rgb(250, 222, 196) * (0.5 if NIGHT else 1) - canvas) * haze[..., None] * 0.5

    # ---------------- DISTANT LAND: the chalky far band on the right, fading into haze ----------------
    far = lambda xp: (HZ_PX - 38.0 * np.exp(-((np.asarray(xp, f32) - 1010.0) / 110.0) ** 2) - 4.3) / H
    xs = np.linspace(760, 1140, 160)
    FAR = poly_mask([(760, HZ_PX + 2.2)] + [(x, far(x) * H) for x in xs] + [(1140, HZ_PX + 2.2)])
    paint(FAR, rgb(170, 146, 170) if not NIGHT else rgb(70, 64, 92), rgb(178, 156, 176) if not NIGHT else rgb(76, 70, 96),
          soft=2, wob=1, wob_scale=80, width=0.06, dry=0.05, dry_edge=0.3, mot=0.4, rim=0.0, seed=21, alpha=0.75)
    # main headland: rounded top at the crest, a long concave tail running out left along the horizon, a shorter fall right
    def top(xp):
        xp = np.asarray(xp, f32); dx = xp - CREST_X
        aL = np.abs(dx) / TAIL
        bump = np.where(dx < 0, np.exp(-aL ** 2 / (1 + 0.6 * aL)), np.exp(-np.abs(dx / FALL) ** 1.9))
        xl = xp / 1920.0                                   # the landscape ripple, same px wavelength, 1.2x amplitude
        return (HZ_PX - HILL_H * bump - (3.2 * np.sin(xl * 41) + 1.9 * np.sin(xl * 97)) * smooth(0.02, 0.2, bump)) / H
    xs = np.linspace(-60, 1140, 440)
    HL = poly_mask([(-60, HZ_PX + 3.2)] + [(x, top(x) * H) for x in xs] + [(1140, HZ_PX + 3.2)])
    HFADE = smooth(0.0, 0.04 * kh, (HZ - top(XPX))) ** 0.8                 # the thin toe thins out into the horizon haze
    HFADE = HFADE * (0.12 + 0.88 * smooth(-60 / W, 400 / W, xx))           # and its far-left run dissolves into the sky
    Shl = brushwork(SRC_BROAD, su=1.0, sv=1.0, wob=8, seed=31, spread=0.6, patch=120, n=6, cover=0.5, base=-0.3)[0] * 0.6
    c1, c2 = (rgb(112, 96, 118), rgb(128, 106, 120)) if not NIGHT else (rgb(44, 42, 62), rgb(52, 48, 66))
    paint(HL, c1, c2, S=Shl, soft=1.5, wob=1.5, wob_scale=60, width=0.06, dry=0.04, dry_edge=0.5, mot=0.7, rim=0.03, seed=32, valvar=0.03, alpha=HFADE)
    HL_SHAPE = HL.copy()
    HL = HL * HFADE
    # translucent glazes on the lit (left, sunset) flank
    for i in range(3):
        y0 = HZ_PX - 134 + i * 37
        band = [(x, y0 + 5.0 * np.sin(x / 1920.0 * 19 + i)) for x in np.linspace(300, 745, 30)]
        pts = band + [(x, y + 16) for x, y in band[::-1]]
        col = [rgb(196, 146, 150), rgb(170, 128, 146), rgb(214, 168, 160)][i % 3]
        if NIGHT: col = col * 0.45
        paint(poly_mask(pts) * HL, col, col * 0.95, S=streaks(SRC_BROAD, angle=0.08, su=1.4, sv=0.5, seed=40 + i), soft=1.0, wob=1, wob_scale=40,
              width=0.1, dry=0.4, dry_edge=0.6, mot=0.4, rim=0.0, seed=40 + i, alpha=0.16)
    hz2 = np.exp(-((yy - HZ + 0.004 * kh) / (0.022 * kh)) ** 2) * HL * (0.55 if not NIGHT else 0.35)
    canvas += (rgb(236, 210, 196) * (0.45 if NIGHT else 1) - canvas) * hz2[..., None]
    # cottage: the landscape cottage at 1.2x its px size, placed so the window centre is exactly WINP
    bw, bh = 0.019 * 1920 * COT, 0.018 * 1080 * COT                 # 43.8 x 23.3
    wx, wy = WINP
    cx = wx - 0.002 * 1920 * COT                                     # landscape: window 0.002 W right of the centre
    base_y = wy + bh * 0.52                                          # and 0.52 of the body above its base
    U_ = lambda pts: [(cx + ax * COT, base_y + ay * COT) for ax, ay in pts]     # landscape cottage px offsets
    bwl, bhl = 0.019 * 1920, 0.018 * 1080
    body = U_([(-bwl / 2, 0), (-bwl / 2, -bhl), (bwl / 2, -bhl), (bwl / 2, 0)])
    roof = U_([(-bwl / 2 - 7.68, -bhl + 1.08), (-3.84, -bhl - 20.52), (bwl / 2 + 7.68, -bhl + 1.08)])
    chim = U_([(7.68, -bhl - 10.8), (7.68, -bhl - 21.6), (15.36, -bhl - 21.6), (15.36, -bhl - 6.48)])
    wall = (rgb(206, 186, 176), rgb(196, 176, 170)) if not NIGHT else (rgb(78, 72, 92), rgb(72, 66, 86))
    roofc = (rgb(96, 70, 80), rgb(90, 66, 76)) if not NIGHT else (rgb(34, 30, 44), rgb(30, 28, 40))
    EDGE_TOOTH = 0.3
    paint(poly_mask(chim), *roofc, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.0, seed=51)
    paint(poly_mask(body), *wall, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.02, seed=52)
    paint(poly_mask(roof), *roofc, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.0, seed=53)
    lit = U_([(-bwl / 2, 0), (-bwl / 2, -bhl), (-bwl / 2 + 5.76, -bhl), (-bwl / 2 + 5.76, 0)])
    paint(poly_mask(lit), rgb(246, 210, 180) * (0.5 if NIGHT else 1), rgb(240, 200, 176) * (0.5 if NIGHT else 1), soft=0.5, wob=0.1, width=0.05, dry=0.0,
          dry_edge=0.1, rim=0.0, seed=54, alpha=0.8)
    EDGE_TOOTH = 0.6
    # the lit window and its glow (radius in px: landscape 23.8 / 43.2, x 1.2)
    gd = np.sqrt((XPX - wx) ** 2 + (yy * H - wy) ** 2)
    glow = np.exp(-(gd / ((23.76 if not NIGHT else 43.2) * COT)) ** 2) * (0.3 if not NIGHT else 0.55)
    if not WOFF: canvas += (rgb(255, 214, 140) - canvas) * glow[..., None]
    hw, hh = 6.144 * COT, 5.184 * COT
    win = [(wx - hw, wy - hh), (wx + hw, wy - hh), (wx + hw, wy + hh), (wx - hw, wy + hh)]
    EDGE_TOOTH = 0.2
    paint(poly_mask(win), *((rgb(92, 78, 86), rgb(86, 72, 80)) if WOFF else (rgb(255, 222, 150), rgb(250, 204, 120))), soft=0.4, wob=0.1, width=0.05, dry=0.0, dry_edge=0.0, rim=0.0, seed=55)
    EDGE_TOOTH = 0.6
    if not NIGHT:   # a thin wisp from the chimney
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        (sx, sy), = U_([(11.52, -bhl - 22.68)])
        draw_stroke(dr, bez((sx, sy), (sx - 23.04 * COT, sy - 32.4 * COT), (sx - 86.4 * COT, sy - 48.6 * COT), 40), 4 * DPI / 100, 9 * DPI / 100, 0.7, 0.1)
        soft_strokes(lay, rgb(236, 220, 214), 0.35, 4)

    # ---------------- SEA: horizontal brushwork in two close hues, sunset glow reflected on the left ----------------
    SEA = poly_mask([(-54, HZ_PX), (1134, HZ_PX), (1134, 2016), (-54, 2016)])
    Ssea, Csea = brushwork(SRC_BROAD, su=2.6, sv=1.6, wob=6, seed=61, spread=0.02, patch=300, n=6, cover=0.6)
    s1, s2 = (rgb(120, 128, 160), rgb(136, 136, 166)) if not NIGHT else (rgb(36, 42, 74), rgb(42, 46, 78))
    paint(SEA, s1, s2, S=Ssea, C=Csea, soft=1.0, wob=0.3, wob_scale=200, width=0.03, dry=0.05, dry_edge=0.1,
          mot=0.5, rim=0.0, seed=62, valvar=0.06, cvar=0.4, edge_tex=0.2)
    deep = (rgb(84, 92, 134), rgb(92, 96, 136)) if not NIGHT else (rgb(22, 26, 52), rgb(26, 30, 56))
    paint(SEA * smooth(HZ + (0.12 / 0.42) * (1 - HZ), 1.0, yy), *deep, S=Ssea, C=Csea, soft=8, wob=1, wob_scale=150, width=0.3, dry=0.15, dry_edge=0.4, mot=0.5, rim=0.0,
          seed=63, alpha=0.7)
    glowc = (rgb(240, 196, 176), rgb(232, 182, 180)) if not NIGHT else (rgb(110, 90, 112), rgb(100, 84, 108))
    paint(SEA * smooth(0.75, 0.0, xx) * smooth(HZ + 0.11, HZ, yy), *glowc, S=Ssea, C=Csea, soft=8, wob=1, wob_scale=150,
          width=0.2, dry=0.25, dry_edge=0.6, mot=0.5, rim=0.0, seed=64, valvar=0.08, alpha=0.4)
    del Ssea, Csea
    Sw = streaks(SRC_FINE, su=1.4, sv=1.0, seed=65)
    # crests: short tapered horizontal strokes, longer and wider toward the viewer (lengths in landscape px)
    lay = stroke_layer(); dr = ImageDraw.Draw(lay)
    for _ in range(34 if not NIGHT else 22):
        y = HZ + 0.02 * kh + (1 - HZ) * rng.uniform(0.08, 1) ** 1.1; depth = (y - HZ) / (1 - HZ)
        x = rng.uniform(-0.05, 1.0); ln = (0.015 + 0.10 * depth) * kw * 0.85 * rng.uniform(0.5, 1.3)
        draw_stroke(dr, bez((X(x), Y(y)), (X(x + ln / 2), Y(y - 0.002 * kh)), (X(x + ln), Y(y)), 16),
                    (0.6 + 4.5 * depth) * DPI / 100, 0.6 * DPI / 100, 0.8, 0.3)
    cr = (rgb(232, 214, 210), rgb(240, 222, 206)) if not NIGHT else (rgb(120, 122, 156), rgb(130, 128, 160))
    apply_strokes(lay, *cr, Sw, dry=0.6, seed=66, rim=0)
    lay = stroke_layer(); dr = ImageDraw.Draw(lay)
    for _ in range(14):
        y = HZ + 0.01 * kh + (1 - HZ) * rng.uniform(0.05, 1) ** 1.3; depth = (y - HZ) / (1 - HZ)
        x = rng.uniform(-0.05, 1.0); ln = (0.03 + 0.14 * depth) * kw * 0.85 * rng.uniform(0.6, 1.2)
        draw_stroke(dr, bez((X(x), Y(y)), (X(x + ln / 2), Y(y + 0.002 * kh)), (X(x + ln), Y(y)), 16), (1 + 5 * depth) * DPI / 100, 0.8 * DPI / 100, 0.8, 0.3)
    tr = (rgb(92, 98, 140), rgb(100, 104, 146)) if not NIGHT else (rgb(18, 22, 46), rgb(22, 26, 50))
    apply_strokes(lay, *tr, Sw, dry=0.55, seed=67, rim=0)
    if not WOFF:
        # window reflection: broken gold dashes straight down from the cottage, a longer column in the tall sea
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        for _ in range(34 if NIGHT else 16):
            y = HZ + 0.006 * kh + rng.uniform(0, 0.30) ** 1.2 * (1 - HZ) / 0.42; depth = (y - HZ) / (1 - HZ)
            w = (0.004 + 0.02 * depth) * kw * rng.uniform(0.6, 1.4); x = wx / W + rng.normal(0, 0.002 + 0.01 * depth) * kw
            draw_stroke(dr, [(X(x - w), Y(y)), (X(x), Y(y)), (X(x + w), Y(y))], (1 + 2.5 * depth) * DPI / 100, 0.8 * DPI / 100, 0.9, 0.5)
        apply_strokes(lay, rgb(250, 214, 150), rgb(244, 196, 130), Sw, dry=0.3, seed=68, rim=0)
    LAND = np.clip(HL + FAR, 0, 1)
    if not VARIANT:
        np.savez_compressed(OUT.rsplit(".", 1)[0] + "_masks.npz", land=(LAND * 255).astype(np.uint8),
                            land_shape=(np.clip(HL_SHAPE + FAR, 0, 1) * 255).astype(np.uint8),
                            hz=np.float32(HZ), win=np.array([wx / W, wy / H], f32))
        print("saved", OUT.rsplit(".", 1)[0] + "_masks.npz")
    save(); sys.exit()


# =====================================================================================================================
# dusk and night (SPEC §3.2, recovered v9 code with the v8 hill patches)
# =====================================================================================================================
if SCENE in ("dusk", "night"):
    HZ = 0.58
    # ---------------- SKY: one graded wash, the sun just set off-frame left ----------------
    gx, gy = -0.15, HZ + 0.04
    d = np.sqrt((xx - gx) ** 2 + ((yy - gy) * H / W) ** 2) + 0.03 * lowfreq(900 * K, 11, 2)
    if NIGHT:
        stops_d = [0.0, 0.35, 0.60, 0.95, 1.5]
        stops_c = [(150, 112, 120), (98, 86, 118), (62, 64, 104), (40, 44, 82), (30, 33, 66)]
    else:
        stops_d = [0.0, 0.22, 0.48, 0.85, 1.5]
        stops_c = [(250, 214, 168), (238, 186, 168), (196, 168, 190), (150, 150, 192), (118, 126, 178)]
    canvas = np.stack([np.interp(d, stops_d, [c[i] for c in stops_c]) for i in range(3)], -1).astype(f32) / 255
    canvas *= (1 - 0.012 * mottle)[..., None]
    canvas *= (1 - 0.03 * smooth(0.3, 2.0, -tooth))[..., None]           # granulation, kept light
    del d
    # cloud wisps: long soft horizontal strokes, lit underneath. The random state is restored afterwards so a
    # NOCLOUDS=1 render matches the full render everywhere except the clouds (the video drifts them as a layer).
    _rng_state = rng.bit_generator.state
    for i, (cy, cx0, ln, col, a) in ([] if os.environ.get("NOCLOUDS") else enumerate([
            (0.20, 0.08, 0.34, (226, 170, 172), 0.45), (0.24, 0.18, 0.26, (244, 196, 176), 0.4),
            (0.31, 0.02, 0.22, (214, 160, 176), 0.35), (0.14, 0.52, 0.30, (186, 160, 196), 0.35),
            (0.36, 0.30, 0.18, (246, 206, 178), 0.3), (0.40, 0.60, 0.20, (212, 172, 186), 0.25)])):
        if NIGHT: col = tuple(int(c * 0.55) for c in col); a *= 0.8
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        for j in range(5):
            y = cy + rng.normal(0, 0.012); x0 = cx0 + rng.uniform(-0.03, 0.05); l = ln * rng.uniform(0.5, 1.0)
            draw_stroke(dr, bez((X(x0), Y(y)), (X(x0 + l / 2), Y(y - 0.008)), (X(x0 + l), Y(y + 0.003)), 30),
                        rng.uniform(10, 22) * DPI / 100, 2 * DPI / 100, 0.9, 0.3)
        soft_strokes(lay, rgb(*col), a, 7)
    rng.bit_generator.state = _rng_state
    if NIGHT:   # stars: sparse, uneven, mostly high
        riso(np.ones((H, W), f32) * smooth(0.45, 0.05, yy), rgb(240, 232, 214), 0.0012 * smooth(0.5, 0.0, yy), 501, size=0.6)
    haze = np.exp(-((yy - HZ + 0.006) / 0.02) ** 2) * (0.5 if not NIGHT else 0.25)
    canvas += (rgb(250, 222, 196) * (0.5 if NIGHT else 1) - canvas) * haze[..., None] * 0.5

    # ---------------- DISTANT LAND: two flat chalky bands on the right, the far one fading into haze ----------------
    far = lambda x: HZ - 0.035 * np.exp(-((np.asarray(x, f32) - 0.93) / 0.12) ** 2) - 0.004
    xs = np.linspace(0.6, 1.05, 160)
    FAR = poly_mask(PX([(0.6, HZ + 0.002)]) + [(X(x), Y(far(x))) for x in xs] + PX([(1.05, HZ + 0.002)]))
    paint(FAR, rgb(170, 146, 170) if not NIGHT else rgb(70, 64, 92), rgb(178, 156, 176) if not NIGHT else rgb(76, 70, 96),
          soft=2, wob=1, wob_scale=80, width=0.06, dry=0.05, dry_edge=0.3, mot=0.4, rim=0.0, seed=21, alpha=0.75)
    # main headland with the cottage on top
    def top(x):
        x = np.asarray(x, f32); dx = x - 0.78
        # a broad, low hill: rounded at the top, and on the left a long concave tail that runs out along the horizon
        # (exp(-a^2 / (1 + 0.6a)) is Gaussian near the top and exponential far out, so the slope keeps easing off
        # instead of steepening into a drop); the right side keeps its shorter fall
        aL = np.abs(dx) / 0.20
        bump = np.where(dx < 0, np.exp(-aL ** 2 / (1 + 0.6 * aL)), np.exp(-np.abs(dx / 0.13) ** 1.9))
        return HZ - 0.125 * bump - (0.0025 * np.sin(x * 41) + 0.0015 * np.sin(x * 97)) * smooth(0.02, 0.2, bump)
    xs = np.linspace(-0.05, 1.05, 440)
    HL = poly_mask(PX([(-0.05, HZ + 0.003)]) + [(X(x), Y(top(x))) for x in xs] + PX([(1.05, HZ + 0.003)]))
    # The fades go in as paint's alpha, not into the mask: paint() thresholds its mask at 0.5, so a faded mask gets
    # cut off with a hard edge wherever the fade crosses one half (that was the blunt end on the left toe).
    HFADE = smooth(0.0, 0.04, (HZ - top(xx))) ** 0.8              # the long thin toe thins out into the horizon haze
    HFADE = HFADE * (0.12 + 0.88 * smooth(0.24, 0.58, xx))       # and its far-left run dissolves into the sky rather than stopping
    Shl = brushwork(SRC_BROAD, su=1.0, sv=1.0, wob=8, seed=31, spread=0.6, patch=120, n=6, cover=0.5, base=-0.3)[0] * 0.6
    c1, c2 = (rgb(112, 96, 118), rgb(128, 106, 120)) if not NIGHT else (rgb(44, 42, 62), rgb(52, 48, 66))
    paint(HL, c1, c2, S=Shl, soft=1.5, wob=1.5, wob_scale=60, width=0.06, dry=0.04, dry_edge=0.5, mot=0.7, rim=0.03, seed=32, valvar=0.03, alpha=HFADE)
    HL_SHAPE = HL.copy()                                          # the unfaded outline, for the video's parallax planes
    HL = HL * HFADE                                               # (the glazes, haze and saved mask use the faded hill)
    # translucent glazes on the lit (left, sunset) flank
    for i in range(3):
        y0 = HZ - 0.10 + i * 0.03
        band = [(x, y0 + 0.35 * (0.8 - x) * 0 + 0.004 * np.sin(x * 19 + i)) for x in np.linspace(0.55, 0.82, 30)]
        pts = PX(band) + [(X(x), Y(y + 0.012)) for x, y in band[::-1]]
        col = [rgb(196, 146, 150), rgb(170, 128, 146), rgb(214, 168, 160)][i % 3]
        if NIGHT: col = col * 0.45
        paint(poly_mask(pts) * HL, col, col * 0.95, S=streaks(SRC_BROAD, angle=0.08, su=1.4, sv=0.5, seed=40 + i), soft=1.0, wob=1, wob_scale=40,
              width=0.1, dry=0.4, dry_edge=0.6, mot=0.4, rim=0.0, seed=40 + i, alpha=0.16)
    # horizon haze laid back over the foot of the hill so it sinks into the distance
    hz2 = np.exp(-((yy - HZ + 0.004) / 0.022) ** 2) * HL * (0.55 if not NIGHT else 0.35)
    canvas += (rgb(236, 210, 196) * (0.45 if NIGHT else 1) - canvas) * hz2[..., None]
    # cottage: clean built shapes, a lit sliver on the sunset side
    cx = 0.78; base_y = float(top(cx)) + 0.006; bw, bh = 0.019, 0.018
    body = [(cx - bw / 2, base_y), (cx - bw / 2, base_y - bh), (cx + bw / 2, base_y - bh), (cx + bw / 2, base_y)]
    roof = [(cx - bw / 2 - 0.004, base_y - bh + 0.001), (cx - 0.002, base_y - bh - 0.019), (cx + bw / 2 + 0.004, base_y - bh + 0.001)]
    chim = [(cx + 0.004, base_y - bh - 0.010), (cx + 0.004, base_y - bh - 0.020), (cx + 0.008, base_y - bh - 0.020), (cx + 0.008, base_y - bh - 0.006)]
    wall = (rgb(206, 186, 176), rgb(196, 176, 170)) if not NIGHT else (rgb(78, 72, 92), rgb(72, 66, 86))
    roofc = (rgb(96, 70, 80), rgb(90, 66, 76)) if not NIGHT else (rgb(34, 30, 44), rgb(30, 28, 40))
    EDGE_TOOTH = 0.3
    paint(poly_mask(PX(chim)), *roofc, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.0, seed=51)
    paint(poly_mask(PX(body)), *wall, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.02, seed=52)
    paint(poly_mask(PX(roof)), *roofc, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.0, seed=53)
    lit = [(cx - bw / 2, base_y), (cx - bw / 2, base_y - bh), (cx - bw / 2 + 0.003, base_y - bh), (cx - bw / 2 + 0.003, base_y)]
    paint(poly_mask(PX(lit)), rgb(246, 210, 180) * (0.5 if NIGHT else 1), rgb(240, 200, 176) * (0.5 if NIGHT else 1), soft=0.5, wob=0.1, width=0.05, dry=0.0,
          dry_edge=0.1, rim=0.0, seed=54, alpha=0.8)
    EDGE_TOOTH = 0.6
    # the lit window and its glow
    wx, wy = cx + 0.002, base_y - bh * 0.52
    gd = np.sqrt(((xx - wx) * W / H) ** 2 + (yy - wy) ** 2)
    glow = np.exp(-(gd / (0.022 if not NIGHT else 0.04)) ** 2) * (0.3 if not NIGHT else 0.55)
    if not WOFF: canvas += (rgb(255, 214, 140) - canvas) * glow[..., None]
    win = [(wx - 0.0032, wy - 0.0048), (wx + 0.0032, wy - 0.0048), (wx + 0.0032, wy + 0.0048), (wx - 0.0032, wy + 0.0048)]
    EDGE_TOOTH = 0.2
    paint(poly_mask(PX(win)), *((rgb(92, 78, 86), rgb(86, 72, 80)) if WOFF else (rgb(255, 222, 150), rgb(250, 204, 120))), soft=0.4, wob=0.1, width=0.05, dry=0.0, dry_edge=0.0, rim=0.0, seed=55)
    EDGE_TOOTH = 0.6
    if not NIGHT:   # a thin wisp from the chimney
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        sx, sy = X(cx + 0.006), Y(base_y - bh - 0.021)
        draw_stroke(dr, bez((sx, sy), (sx - X(0.012), sy - Y(0.03)), (sx - X(0.045), sy - Y(0.045)), 40), 4 * DPI / 100, 9 * DPI / 100, 0.7, 0.1)
        soft_strokes(lay, rgb(236, 220, 214), 0.35, 4)

    # ---------------- SEA: horizontal brushwork in two close hues, sunset glow reflected on the left ----------------
    SEA = poly_mask(PX([(-0.05, HZ), (1.05, HZ), (1.05, 1.05), (-0.05, 1.05)]))
    Ssea, Csea = brushwork(SRC_BROAD, su=2.6, sv=1.6, wob=6, seed=61, spread=0.02, patch=300, n=6, cover=0.6)
    s1, s2 = (rgb(120, 128, 160), rgb(136, 136, 166)) if not NIGHT else (rgb(36, 42, 74), rgb(42, 46, 78))
    paint(SEA, s1, s2, S=Ssea, C=Csea, soft=1.0, wob=0.3, wob_scale=200, width=0.03, dry=0.05, dry_edge=0.1,
          mot=0.5, rim=0.0, seed=62, valvar=0.06, cvar=0.4, edge_tex=0.2)
    deep = (rgb(84, 92, 134), rgb(92, 96, 136)) if not NIGHT else (rgb(22, 26, 52), rgb(26, 30, 56))
    paint(SEA * smooth(0.70, 1.0, yy), *deep, S=Ssea, C=Csea, soft=8, wob=1, wob_scale=150, width=0.3, dry=0.15, dry_edge=0.4, mot=0.5, rim=0.0,
          seed=63, alpha=0.7)
    glowc = (rgb(240, 196, 176), rgb(232, 182, 180)) if not NIGHT else (rgb(110, 90, 112), rgb(100, 84, 108))
    paint(SEA * smooth(0.50, 0.0, xx) * smooth(HZ + 0.16, HZ, yy), *glowc, S=Ssea, C=Csea, soft=8, wob=1, wob_scale=150,
          width=0.2, dry=0.25, dry_edge=0.6, mot=0.5, rim=0.0, seed=64, valvar=0.08, alpha=0.4)
    del Ssea, Csea
    Sw = streaks(SRC_FINE, su=1.4, sv=1.0, seed=65)
    # crests: short tapered horizontal strokes, longer and wider toward the viewer
    lay = stroke_layer(); dr = ImageDraw.Draw(lay)
    for _ in range(34 if not NIGHT else 22):
        y = HZ + 0.02 + (1 - HZ) * rng.uniform(0.08, 1) ** 1.1; depth = (y - HZ) / (1 - HZ)
        x = rng.uniform(-0.05, 1.0); ln = (0.015 + 0.10 * depth) * rng.uniform(0.5, 1.3)
        draw_stroke(dr, bez((X(x), Y(y)), (X(x + ln / 2), Y(y - 0.002)), (X(x + ln), Y(y)), 16),
                    (0.6 + 4.5 * depth) * DPI / 100, 0.6 * DPI / 100, 0.8, 0.3)
    cr = (rgb(232, 214, 210), rgb(240, 222, 206)) if not NIGHT else (rgb(120, 122, 156), rgb(130, 128, 160))
    apply_strokes(lay, *cr, Sw, dry=0.6, seed=66, rim=0)
    lay = stroke_layer(); dr = ImageDraw.Draw(lay)
    for _ in range(14):
        y = HZ + 0.01 + (1 - HZ) * rng.uniform(0.05, 1) ** 1.3; depth = (y - HZ) / (1 - HZ)
        x = rng.uniform(-0.05, 1.0); ln = (0.03 + 0.14 * depth) * rng.uniform(0.6, 1.2)
        draw_stroke(dr, bez((X(x), Y(y)), (X(x + ln / 2), Y(y + 0.002)), (X(x + ln), Y(y)), 16), (1 + 5 * depth) * DPI / 100, 0.8 * DPI / 100, 0.8, 0.3)
    tr = (rgb(92, 98, 140), rgb(100, 104, 146)) if not NIGHT else (rgb(18, 22, 46), rgb(22, 26, 50))
    apply_strokes(lay, *tr, Sw, dry=0.55, seed=67, rim=0)
    if not WOFF:
        # window reflection: broken gold dashes straight down from the cottage
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        for _ in range(26 if NIGHT else 12):
            y = HZ + 0.006 + rng.uniform(0, 0.30) ** 1.2; depth = (y - HZ) / (1 - HZ)
            w = (0.004 + 0.02 * depth) * rng.uniform(0.6, 1.4); x = wx + rng.normal(0, 0.002 + 0.01 * depth)
            draw_stroke(dr, [(X(x - w), Y(y)), (X(x), Y(y)), (X(x + w), Y(y))], (1 + 2.5 * depth) * DPI / 100, 0.8 * DPI / 100, 0.9, 0.5)
        apply_strokes(lay, rgb(250, 214, 150), rgb(244, 196, 130), Sw, dry=0.3, seed=68, rim=0)
    LAND = np.clip(HL + FAR, 0, 1)
    if not VARIANT:     # the _nc / _off renders share the full render's masks
        np.savez_compressed(OUT.rsplit(".", 1)[0] + "_masks.npz", land=(LAND * 255).astype(np.uint8),
                            land_shape=(np.clip(HL_SHAPE + FAR, 0, 1) * 255).astype(np.uint8),
                            hz=np.float32(HZ), win=np.array([wx, wy], f32))
        print("saved", OUT.rsplit(".", 1)[0] + "_masks.npz")
    save(); sys.exit()


# =====================================================================================================================
# the uncle (SPEC §3.3) -- rebuilt: a sharp-cornered cut-paper silhouette, head and shoulders in right profile
# =====================================================================================================================
if SCENE == "uncle":
    # Polygons in 1920 x 1080 px, straight segments only (no spline smoothing: "sharp corners"). Traced against the
    # measured silhouette (§3.3) and docs/ref/canvas_v6/uncle.jpg, then cleaned by hand.
    HEAD = [(581, 172), (490, 199), (412, 277), (393, 361), (405, 441), (477, 574), (594, 597), (608, 600), (630, 606),
            (647, 607), (649, 595), (670, 574), (705, 563), (735, 540), (746, 511), (743, 489), (754, 475), (751, 463),
            (757, 457), (770, 455), (784, 441), (751, 406), (737, 383), (726, 378), (737, 360), (731, 347), (736, 342),
            (731, 299), (708, 246), (662, 196)]
    # the body runs up behind the neck and the collar, so the head can rock over it without opening a gap
    BODY = [(470, 568), (540, 572), (605, 585), (650, 600), (694, 636), (720, 674), (700, 694), (710, 719), (713, 734),
            (721, 771), (728, 866), (731, 907), (733, 1003), (736, 1090), (84, 1090), (95, 1010), (109, 907), (178, 754),
            (285, 672), (394, 624), (458, 603)]
    COLLAR = [(461, 600), (460, 612), (534, 622), (597, 632), (631, 641), (638, 648), (641, 663), (687, 699), (721, 677),
              (690, 642), (650, 609), (605, 597), (533, 586), (475, 573)]
    COLLAR_FOLD = [(632, 643), (668, 650), (690, 652), (692, 657), (668, 656), (640, 652)]     # shadowed turn of the band
    SKULL_HI = [(446, 265), (422, 290), (405, 326), (397, 366), (400, 406), (414, 446), (440, 470), (452, 460),
                (433, 424), (429, 384), (431, 342), (439, 302), (452, 274)]                    # pale band on the back of the skull
    EAR = [(593, 366), (580, 371), (583, 388), (596, 400), (581, 440), (599, 446), (618, 416), (619, 386), (605, 366)]
    MOUTH = [(732, 461), (750, 457), (761, 462), (758, 474), (744, 477), (733, 474)]          # the grey lip notch
    LENS_C, LENS_R, LENS_ROT = (721.0, 366.5), (26.0, 22.5), -0.12
    ARM = [(695, 360), (676, 359.5), (655, 360), (633, 362), (618, 367), (608, 377)]
    PIVOT, SPLIT = (604.0, 584.0), 590.0
    BSC = 1.0                                   # brush/texture scale of the figure's marks (px sizes x BSC)
    RS = lambda s_: s_ * BSC + (BSC - 1) * 0.35 / K          # riso size whose speck blur (size K + 0.35) scales by BSC
    if REEL:
        # REEL_LAYOUT §2 s3: the same polygons through one similarity, x' = 60 + (x - 393) 1.25, y' = 600 + (y - 172) 1.25
        # (back of the skull at x 60, head top at y 600); the body runs off the bottom (its foot 1090 -> 1640 landscape
        # units); every brush, blur, noise and speckle size scales by 1.25 so the marks keep their size on the figure.
        S144 = BSC = 1.25
        UX0, UY0, URX, URY = 60.0, 600.0, 393.0, 172.0
        PXA = lambda pts: [(UX0 + (x - URX) * S144, UY0 + (y - URY) * S144) for x, y in pts]
        BODY = BODY[:13] + [(760, 1640), (84, 1640)] + BODY[15:]       # (the chest keeps its slight outward lean)

    # ---------------- background: pale warm paper, a lamp glow from the upper right ----------------
    canvas = np.ones((H, W, 3), f32) * rgb(241, 236, 225)
    canvas += (rgb(236, 231, 220) - canvas) * smooth(0.2, 1.0, xx)[..., None] * 0.6
    if REEL:    # the lamp re-centred upper right of the tall frame, same falloff in px (landscape: (1536, -108), r 594)
        gd = np.sqrt(((xx * W - 1000) / 1080) ** 2 + ((yy * H + 140) / 1080 * 1.2) ** 2) + 0.05 * lowfreq(700 * K, 3, 2)
        lamp = np.exp(-(gd / 0.62) ** 2)
    else:
        gd = np.sqrt(((xx - 0.80) * W / H) ** 2 + ((yy + 0.10) * 1.2) ** 2) + 0.05 * lowfreq(700 * K, 3, 2)
        lamp = np.exp(-(gd / 0.55) ** 2)
    canvas += (rgb(224, 208, 180) - canvas) * (0.85 * lamp)[..., None]
    canvas *= (1 - 0.008 * mottle)[..., None]
    canvas *= (1 - 0.008 * smooth(0.3, 2.0, -tooth))[..., None]
    n = lowfreq(520 * K, 5, 3); st = smooth(0.7, 1.3, n); edge = st * (1 - st) * 4
    canvas *= (1 - 0.004 * st - 0.005 * edge)[..., None]
    BG = canvas.copy()

    def matte(ops):
        """run paint ops over black and over white: canvas ops are linear (canvas*(1-A) + col*A), so the two results
        give the layer's exact alpha and premultiplied colour, painted edge and all"""
        global canvas
        st_ = rng.bit_generator.state
        canvas = np.zeros((H, W, 3), f32); ops(); c0 = canvas
        rng.bit_generator.state = st_
        canvas = np.ones((H, W, 3), f32); ops(); c1 = canvas
        a_ = np.clip(1 - (c1 - c0).mean(2), 0, 1)
        return c0, a_                                   # premultiplied rgb, alpha

    def head_ops():
        global EDGE_TOOTH
        EDGE_TOOTH = 0.22
        M = poly_mask(PXA(HEAD))
        Sh = streaks(SRC_BROAD, angle=0.02, su=1.6 * BSC, sv=0.8 * BSC, wob=4 * BSC, seed=81)
        paint(M, rgb(62, 52, 51), rgb(70, 58, 57), S=Sh * 0.4, soft=0.4 * BSC, wob=0.15, wob_scale=80 * BSC, width=0.04, dry=0.0,
              dry_edge=0.0, mot=0.4, rim=0.0, seed=82, valvar=0.028, cvar=0.2)
        paint(poly_mask(PXA(SKULL_HI)) * M, rgb(112, 105, 103), rgb(104, 98, 97),
              S=streaks(SRC_FINE, angle=1.35, su=1.2 * BSC, sv=0.8 * BSC, seed=83), soft=0.4 * BSC, wob=0.2, wob_scale=40 * BSC, width=0.05,
              dry=0.12, dry_edge=0.4, mot=0.4, rim=0.0, seed=84, valvar=0.10, alpha=0.95)
        paint(poly_mask(PXA(EAR)) * M, rgb(93, 73, 67), rgb(98, 78, 70), S=Sh, soft=0.4 * BSC, wob=0.2, width=0.05, dry=0.05,
              dry_edge=0.3, mot=0.4, rim=0.0, seed=85, valvar=0.06)
        # warm rim light along the face edge, lamp on the right: the band of head within ~5 px of its right-facing edge
        sh = lambda m, dx, dy: ndi.shift(m, (dy * S144, -dx * S144), order=1, mode="constant", cval=0)
        rim = M * np.clip(1 - np.minimum(np.minimum(sh(M, 5, 0), sh(M, 4, 3)), sh(M, 4, -3)), 0, 1)
        if REEL: X0 = (np.arange(W)[None, :] - UX0) / S144 + URX; Y0 = (np.arange(H)[:, None] - UY0) / S144 + URY
        else: X0 = np.arange(W)[None, :] / S144; Y0 = np.arange(H)[:, None] / S144
        rim = rim * smooth(626, 660, X0) * smooth(286, 300, Y0) * (1 - smooth(600, 612, Y0))
        rim = rim * (1 - poly_mask(PXA(MOUTH)))
        EDGE_TOOTH = 0.35
        paint(np.clip(rim * 1.6, 0, 1), rgb(186, 152, 116), rgb(176, 142, 108), soft=0.2 * BSC, wob=0.3, wob_scale=20 * BSC,
              width=0.08, dry=0.18, dry_edge=0.3, mot=0.4, rim=0.0, seed=86, valvar=0.05)
        EDGE_TOOTH = 0.3
        paint(poly_mask(PXA(MOUTH)), rgb(150, 142, 140), rgb(126, 120, 118),
              S=streaks(SRC_FINE, angle=1.5, su=0.8 * BSC, sv=0.6 * BSC, seed=87), soft=0.3 * BSC, wob=0.2, width=0.05, dry=0.1,
              dry_edge=0.4, mot=0.5, rim=0.0, seed=88, valvar=0.12, cvar=0.5)
        # light speckle, sparse and uneven
        riso(M, rgb(237, 231, 222), 0.0018 + 0.0035 * smooth(0.0, 1.5, lowfreq(160 * K * BSC, 89, 2)), 90, size=RS(0.45))
        # gold wire glasses: an oval lens over the eye, the arm back to the ear
        t = np.linspace(0, 2 * np.pi, 49)
        ca, sa = np.cos(LENS_ROT), np.sin(LENS_ROT)
        ex, ey = LENS_R[0] * np.cos(t), LENS_R[1] * np.sin(t)
        lens = [(LENS_C[0] + ex[i] * ca - ey[i] * sa, LENS_C[1] + ex[i] * sa + ey[i] * ca) for i in range(len(t))]
        ink_line(PXA(lens), 3.2 * S144, rgb(198, 171, 134))
        ink_line(PXA(ARM), 3.0 * S144, rgb(196, 169, 134))
        EDGE_TOOTH = 0.6

    def body_ops():
        global EDGE_TOOTH
        EDGE_TOOTH = 0.22
        M = poly_mask(PXA(BODY))
        # long diagonal strokes running down to the right (the canvas plate's brushwork)
        Sb, Cb = brushwork(SRC_FINE, su=1.6 * BSC, sv=1.0 * BSC, wob=4 * BSC, seed=91, spread=0.08, patch=260 * BSC, n=5, cover=0.55,
                           base=np.radians(58))
        paint(M, rgb(84, 74, 57), rgb(96, 85, 64), S=Sb, C=Cb, soft=0.4 * BSC, wob=0.15, wob_scale=80 * BSC,
              width=0.04, dry=0.0, dry_edge=0.08, mot=0.5, rim=0.0, seed=93, valvar=0.07, cvar=0.3)
        # a few dry-brush drags, a shade darker, on the same diagonal
        Sf = streaks(SRC_BROAD, angle=np.radians(60), su=1.4 * BSC, sv=0.8 * BSC, seed=92)
        paint(M * smooth(0.2, 1.4, lowfreq(300 * K * BSC, 94, 2)), rgb(74, 65, 50), rgb(80, 70, 52), S=Sf, soft=1.0 * BSC, wob=0.5,
              width=0.1, dry=0.6, dry_edge=0.6, mot=0.5, rim=0.0, seed=95, valvar=0.05, alpha=0.3)
        # the collar's shadow falling on the cardigan
        shc = [(x + 3, y + 9) for x, y in COLLAR]
        paint(poly_mask(PXA(shc)) * M, rgb(58, 50, 38), rgb(62, 54, 40), soft=3 * BSC, wob=0.3, width=0.12, dry=0.0,
              dry_edge=0.1, mot=0.3, rim=0.0, seed=96, alpha=0.45)
        riso(M, rgb(232, 224, 205), 0.0008 + 0.0035 * smooth(0.4, 1.8, lowfreq(200 * K * BSC, 97, 2)), 98, size=RS(0.5))
        EDGE_TOOTH = 0.6

    def collar_ops():
        global EDGE_TOOTH
        EDGE_TOOTH = 0.2
        paint(poly_mask(PXA(COLLAR)), rgb(213, 202, 184), rgb(220, 210, 192),
              S=streaks(SRC_FINE, angle=0.2, su=1.0 * BSC, sv=1.0 * BSC, seed=101), soft=0.4 * BSC, wob=0.15, wob_scale=60 * BSC, width=0.04,
              dry=0.0, dry_edge=0.05, mot=0.3, rim=0.0, seed=102, valvar=0.015)
        paint(poly_mask(PXA(COLLAR_FOLD)), rgb(150, 140, 124), rgb(170, 160, 142), soft=1.2 * BSC, wob=0.3, width=0.1, dry=0.1,
              dry_edge=0.4, mot=0.3, rim=0.0, seed=103, alpha=0.75)
        EDGE_TOOTH = 0.6

    body_pm, body_a = matte(body_ops)
    head_pm, head_a = matte(head_ops)
    col_pm, col_a = matte(collar_ops)
    fig_pm = head_pm + body_pm * (1 - head_a)[..., None]
    fig_a = head_a + body_a * (1 - head_a)
    whole = BG * (1 - fig_a)[..., None] + fig_pm
    whole = whole * (1 - col_a)[..., None] + col_pm
    unpm = lambda pm, a_: np.where(a_[..., None] > 1e-4, pm / np.maximum(a_, 1e-4)[..., None], 0)
    base = OUT.rsplit(".", 1)[0]
    save(BG, base + "_bg.jpg")
    save_rgba(unpm(fig_pm, fig_a), fig_a, base + "_fig.png")
    save_rgba(unpm(col_pm, col_a), col_a, base + "_collar.png")
    save_rgba(unpm(head_pm, head_a), head_a, base + "_head.png")        # extras: head and body apart, for convenience
    save_rgba(unpm(body_pm, body_a), body_a, base + "_body.png")
    if REEL:
        np.savez(base + "_geo.npz", pivot=np.array(PXA([PIVOT])[0], f32), split=np.float32(UY0 + (SPLIT - URY) * S144),
                 lens=np.array(PXA([LENS_C])[0], f32))
    else:
        np.savez(base + "_geo.npz", pivot=np.array(PIVOT, f32) * S144, split=np.float32(SPLIT * S144),
                 lens=np.array(LENS_C, f32) * S144)
    print("saved", base + "_geo.npz")
    save(whole); sys.exit()

raise SystemExit(f"unknown SCENE {SCENE!r}")
