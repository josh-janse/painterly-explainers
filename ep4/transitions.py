"""Transitions owned by the picture pipeline (SPEC §4.5, §4.10): the w3 window-to-window rush/resolve, the f8 dip to
night and the end fade. Also the lazy hooks the dispatcher uses to reach modules built separately (uncle, cards,
sheets) and the labelled placeholder frames drawn while one of them is missing.

(sheet() for the paper wipes w4-w7 lives in ep4.sheets.)
"""
import importlib
import math

import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw

from .common import W, H, ease, ease_io, ease_in, load, load_rgba, to_pil, to_f32, font
from .timeline import T, END, TILT, local
from . import layout as L

# ------------------------------------------------------------------ lazy hooks + placeholders
_OPT = {}
_WARNED = set()


def optional(mod, attr):
    """ep4.<mod>.<attr> if that module imports and defines it, else None (cached per process)"""
    key = (mod, attr)
    if key not in _OPT:
        try:
            m = importlib.import_module(f"ep4.{mod}")
            _OPT[key] = getattr(m, attr, None)
        except Exception as ex:                      # missing file, or a module that is mid-edit
            if mod not in _WARNED:
                _WARNED.add(mod); print(f"[ep4] ep4.{mod} not available ({type(ex).__name__}: {ex}); using placeholders")
            _OPT[key] = None
        if _OPT[key] is None and key not in _WARNED:
            _WARNED.add(key); print(f"[ep4] ep4.{mod}.{attr} missing; using a placeholder")
    return _OPT[key]


def call(mod, attr, *args, **kw):
    """call ep4.<mod>.<attr>(*args); returns None if it is missing or raises (warned once per function)"""
    fn = optional(mod, attr)
    if fn is None: return None
    try:
        return fn(*args, **kw)
    except Exception as ex:
        k = ("err", mod, attr)
        if k not in _WARNED:
            _WARNED.add(k); print(f"[ep4] ep4.{mod}.{attr} raised {type(ex).__name__}: {ex}; using a placeholder")
        return None


def placeholder(label, t, under=None):
    """a clearly labelled stand-in frame: `under` (an f32 frame) dimmed, or a neutral grey, with the label"""
    base = (under * 0.45 + 0.25) if under is not None else np.full((H, W, 3), 0.42, np.float32)
    im = to_pil(base); dr = ImageDraw.Draw(im)
    f1, f2 = font("mono", 54), font("mono", 32)
    dr.rectangle([90, H // 2 - 110, W - 90, H // 2 + 90], fill=(30, 30, 32, 255))
    dr.text((130, H // 2 - 85), "PLACEHOLDER", font=f1, fill=(245, 212, 74))
    dr.text((130, H // 2 - 5), label, font=f2, fill=(238, 238, 236))
    dr.text((130, H // 2 + 40), f"t = {t:.3f} s", font=f2, fill=(180, 180, 180))
    return to_f32(im)


# ------------------------------------------------------------------ uncle frame for the resolve
WIN_C = L.WIN_C                 # the hole in the uncle's head (same values as ep4.uncle)
WIN_R = L.WIN_R
_UF = {}


def _uncle_fallback():
    """uncle_bg + uncle_fig + uncle_collar with the head window cut as a plain circle at WIN_C (until uncle.py exists)"""
    if "img" not in _UF:
        bg = load("uncle_bg.jpg")
        im = to_pil(bg)
        im.alpha_composite(load_rgba("uncle_fig.png")); im.alpha_composite(load_rgba("uncle_collar.png"))
        a = to_f32(im)
        k = 4; r = WIN_R
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d = np.sqrt((xx - WIN_C[0]) ** 2 + (yy - WIN_C[1]) ** 2)
        m = np.clip(r + 0.5 - d, 0, 1)[..., None]
        a = a * (1 - m) + bg * m
        _UF["img"] = a.astype(np.float32)
    return _UF["img"]


def uncle_at(lt):
    """the s3 picture at local time lt: scene_reads(lt), else uncle_frame(lt, 0, 1, 0), else the plate fallback"""
    img = call("uncle", "scene_reads", max(0.0, lt))
    if img is None: img = call("uncle", "uncle_frame", max(0.0, lt), 0.0, 1.0, 0.0)
    return img if img is not None else _uncle_fallback()


# ------------------------------------------------------------------ w3: window-to-window rush (§4.5)
RUSH = (T["w3"][0], T["w3"][0] + 0.55 * (T["w3"][1] - T["w3"][0]))     # 17.50 -> 17.885
RESOLVE = (RUSH[1], RUSH[1] + 0.715)                                    # 17.885 -> 18.60 (_RD, runs into s3)
RUSH_COL = np.array([250, 226, 171], np.float32) / 255                  # warm window light (fitted to v9, 17.71-17.88)
CREAM_COL = np.array([247, 233, 203], np.float32) / 255                 # the white-out / uncle's paper, lit (v9, 17.92-18.20)
_GRID = {}


def _grid():
    if "g" not in _GRID: _GRID["g"] = np.mgrid[0:H, 0:W].astype(np.float32)
    return _GRID["g"]


def zoom_at(img, s, focus):
    """scale an f32 image by s about the fixed point focus (focus stays put on screen; bicubic)"""
    if s <= 1.0005: return img
    fx, fy = focus
    w, h = W / s, H / s
    x0, y0 = fx - fx / s, fy - fy / s
    im = to_pil(img).resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
    return to_f32(im)


def _blur(img, sigma):
    if sigma < 0.3: return img
    # blur at half resolution for the big sigmas (it is a soft-focus wash, the detail is gone anyway)
    if sigma > 4:
        small = np.asarray(to_pil(img).convert("RGB").resize((W // 2, H // 2), Image.BILINEAR), np.float32) / 255
        small = ndi.gaussian_filter(small, (sigma / 2, sigma / 2, 0), mode="nearest")
        return np.asarray(Image.fromarray((np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
    return ndi.gaussian_filter(img, (sigma, sigma, 0), mode="nearest")


def light_rush(img, s, focus, blur, glow, radius, col):
    """zoom into focus, soften, and flood with light from it"""
    out = _blur(zoom_at(img, s, focus), blur)
    if glow > 0:
        yy, xx = _grid()
        g = np.minimum(np.exp(-(((xx - focus[0]) ** 2 + (yy - focus[1]) ** 2) / (2 * radius ** 2))) * glow, 1.0)[..., None]
        out = out + (col - out) * g
    return np.clip(out, 0, 1)


def rush_resolve(t):
    """17.50 -> 18.60: rush into the lit cottage window, white out, then resolve out of the uncle's head window.

    Curves fitted frame by frame to v9 (zoom / blur / glow amount + radius per frame, least squares on the reference):
    the zoom is a plain q^2 push; the blur stays light until mid-rush; the glow only starts at q ~ 0.33, grows from a
    tight hot spot on the window and floods the frame by 17.875; the cut to the uncle lands inside the full white-out
    (17.917 is a near-uniform cream) and the uncle comes out washed and soft, sharp by ~18.33."""
    if t < RUSH[1]:
        from .video import scene_dusk           # lazy: video imports this module
        q = (t - RUSH[0]) / (RUSH[1] - RUSH[0])
        img = scene_dusk(t)
        from .seasky import KD_win, push_box
        x0, y0, s = push_box(t - TILT[1], T["s2"][1] - TILT[1], KD_win, L.PUSH_S2)
        focus = ((KD_win[0] - x0) * s, (KD_win[1] - y0) * s)       # the window on screen
        glow = min(1.0, 1.75 * max(0.0, q - 0.33))
        return light_rush(img, 1 + 2.6 * q * q, focus, 16 * q ** 2.4, glow, 150 * 2 ** ((q - 0.56) / 0.11), RUSH_COL)
    dt = t - RESOLVE[0]
    img = uncle_at(local("s3", t))
    def fall(L, p): return max(0.0, 1 - dt / L) ** p
    flash = math.exp(-dt / 0.02)               # first resolve frame: a flat-topped, very soft white-out (no ghost of the head)
    glow = min(1.0, 1.105 * fall(0.423, 1.2)) + 0.5 * flash      # > 1 = the glow clips flat over the middle of the frame
    radius = max(150.0, 900 * math.exp(-(dt - 0.073) * 8.6))
    blur = 18.4 * fall(0.615, 2.25) + 30 * flash
    return light_rush(img, 1 + 0.825 * fall(0.57, 2.0), WIN_C, blur, glow, radius, CREAM_COL)


def in_rush(t): return RUSH[0] <= t < RESOLVE[1]


# ------------------------------------------------------------------ f8: dip to black and up into night (§4.10)
def dip(t):
    from .video import scene_night
    p = (t - T["f8"][0]) / (T["f8"][1] - T["f8"][0])
    if p < 0.45:
        a = call("cards", "scene_history", 0, static=True)
        if a is None: a = placeholder("cards.scene_history (static, f8 dip)", t)
        return (a * (1 - ease_io(p / 0.45))).astype(np.float32)
    if p > 0.55:
        return (scene_night(T["s8"][0]) * ease_io((p - 0.55) / 0.45)).astype(np.float32)
    return np.zeros((H, W, 3), np.float32)


# ------------------------------------------------------------------ end fade (measured 70.90 -> 71.95)
def end_fade(img, t):
    k = min(1.0, max(0.0, (END - 0.10 - t) / 1.05))
    return img if k >= 1 else (img * k).astype(np.float32)
