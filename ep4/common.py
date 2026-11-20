"""Shared picture helpers for the ep4 rebuild (SPEC §1.2, §1.5, §4.1, §4.4.4, §4.8).

Everything here is in output pixels (1920 x 1080). Layout numbers in the spec written `NN*F` are in 1280-space.
"""
import math
import os

import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "out", "ep4")                # backdrop outputs (ep4.backdrops writes here)
FONTS = os.path.join(ROOT, "assets", "fonts")

W, H = 1920, 1080
FPS = 24
F = 1.5                                    # layout scale from the 1280 x 720 canvas frames

# ---- palette (§1.5) ----
INK = (46, 44, 45)                         # text, prompt-box outline, arrow, dark tag bg
TAG_LIGHT = (238, 238, 236)                # title tag background
HL = (245, 212, 74)                        # the one accent: Vox-ish marker yellow
CARD_PAPER = (242, 233, 217)
CARD_PAPER_REPLY = (248, 244, 236)
CARD_LABEL = (109, 106, 111)
TAPE = (224, 206, 160, int(0.70 * 255))       # masking tape: warmer and a touch darker than CARD_PAPER so it reads on the card (v10: 236,224,196 @ 0.78 vanished on it)
ENV_PAPER = (239, 230, 214)
ENV_FLAP = (168, 151, 127)
ENV_FOLD = (205, 191, 168)
ENV_STAMP = (188, 97, 94, int(0.85 * 255))
TRAIL_OUT = (243, 235, 224, 170)
TRAIL_HOME = (246, 207, 134, 150)


# ---- easing and the "on twos" clock (§1.2, §1.3) ----
def ease(p): p = min(max(p, 0.0), 1.0); return 1 - (1 - p) ** 3
def ease_io(p): p = min(max(p, 0.0), 1.0); return p * p * (3 - 2 * p)
def ease_in(p): p = min(max(p, 0.0), 1.0); return p * p
def twos(t): return math.floor(t * 12) / 12          # overlays step at 12 fps (the house "on twos" stutter)
def clamp01(p): return min(max(p, 0.0), 1.0)


# ---- images ----
_LOADED = {}
def load(name):
    """float32 RGB 0-1 array (H x W x 3) of out/ep4/<name>, resized to W x H if needed. Cached; treat as read-only."""
    if name not in _LOADED:
        im = Image.open(os.path.join(A, name)).convert("RGB")
        if im.size != (W, H): im = im.resize((W, H), Image.LANCZOS)
        _LOADED[name] = np.asarray(im, np.float32) / 255
    return _LOADED[name]

def load_rgba(name):
    """PIL RGBA image of out/ep4/<name> at W x H (e.g. uncle_fig.png, uncle_collar.png)"""
    im = Image.open(os.path.join(A, name)).convert("RGBA")
    return im if im.size == (W, H) else im.resize((W, H), Image.LANCZOS)

def to_pil(arr):
    """float32 RGB 0-1 -> PIL RGBA"""
    return Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)).convert("RGBA")

def to_f32(im):
    """PIL image -> float32 RGB 0-1"""
    return np.asarray(im.convert("RGB"), np.float32) / 255

def comp(base, lay):
    """float32 RGB base with an RGBA overlay (W x H) on top -> PIL RGBA"""
    im = to_pil(base)
    if lay is not None: im.alpha_composite(lay)
    return im

def blank():
    """an empty full-frame RGBA overlay"""
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


# ---- fonts ----
_FONTS = {}
def font(key, px):
    """cached FreeTypeFont: key in mono, mono5, sans, serif, serif_i, serif_b"""
    k = (key, int(px))
    if k not in _FONTS:
        _FONTS[k] = ImageFont.truetype(os.path.join(FONTS, f"{key}.ttf"), int(px))
    return _FONTS[k]

def tracked(dr, xy, text, fnt, fill, track):
    """draw text one character at a time with extra tracking (px); returns the x after the last character"""
    x, y = xy
    for ch in text:
        dr.text((x, y), ch, font=fnt, fill=fill)
        x += dr.textlength(ch, font=fnt) + track
    return x


# ---- static edge roughness (§4.8.1, recovered) ----
def rough(im, amp=1.5, size=12, seed=0, fine=0.3):
    """static turbulent displacement on an RGBA image, so flat shapes read as cut or printed rather than vector-perfect"""
    a = np.asarray(im, np.float32); h, w = a.shape[:2]
    r = np.random.default_rng(seed)
    def field():
        f = ndi.gaussian_filter(r.standard_normal((h, w)).astype(np.float32), size / 3)
        g = ndi.gaussian_filter(r.standard_normal((h, w)).astype(np.float32), 1.0)
        return f / (f.std() + 1e-6) * amp + g / (g.std() + 1e-6) * amp * fine
    dx, dy = field(), field()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.stack([ndi.map_coordinates(a[..., c], [yy + dy, xx + dx], order=1, mode="nearest") for c in range(4)], -1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


# ---- curves ----
def bez(p0, p1, p2, p3, u):          # cubic Bezier point (ep4_video's own helper; NOT the engine's quadratic bez)
    a = 1 - u
    return (a**3 * p0[0] + 3*a*a*u * p1[0] + 3*a*u*u * p2[0] + u**3 * p3[0],
            a**3 * p0[1] + 3*a*a*u * p1[1] + 3*a*u*u * p2[1] + u**3 * p3[1])
