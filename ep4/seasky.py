"""Sea and sky motion, camera moves, 2.5D parallax, gulls and the envelope flights (SPEC §4.1-4.4, §4.10).

Used by ep4.video (scene_dusk, scene_night) and ep4.transitions (the w3 rush). Everything heavy is loaded once at import;
the parallax sky fill is built lazily on the first parallax() call (it is only needed during the s1 tilt).
"""
import math
import os

import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw, ImageFilter

from .common import (A, W, H, F, ease, ease_io, twos, load, comp, rough, bez, blank,
                     ENV_PAPER, ENV_FLAP, ENV_FOLD, ENV_STAMP)
from .timeline import *  # noqa: F401,F403  (T, TILT, LIGHT_ON, PARALLAX, FLY_OUT, FLY_HOME, ...)

# ------------------------------------------------------------------ plates and masks (§4.1, recovered)
DUSK, NIGHT = load("dusk.jpg"), load("night.jpg")
MD = np.load(os.path.join(A, "dusk_masks.npz"))
MN = np.load(os.path.join(A, "night_masks.npz"))


def prep_masks(m):
    land = np.asarray(Image.fromarray(m["land"]).resize((W, H), Image.BILINEAR), np.float32) / 255
    land = ndi.gaussian_filter(land, 2)
    hz = float(m["hz"]); wx, wy = (m["win"] * np.array([W, H])).tolist()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = np.exp(-(((xx - wx) ** 2 + (yy - wy) ** 2) / (2 * 40.0 ** 2))).astype(np.float32)
    return dict(land=land, hz=hz, win=(wx, wy), glow=glow)


KD, KN = prep_masks(MD), prep_masks(MN)
# clouds as their own layer: full render minus the cloudless render, so they can drift over a still sky
KD["nc"], KN["nc"] = load("dusk_nc.jpg"), load("night_nc.jpg")
KD["cloud"], KN["cloud"] = DUSK - KD["nc"], NIGHT - KN["nc"]
LIGHT_D = DUSK - load("dusk_off.jpg")     # the lit window, its glow and reflection, so the light can come on
KD_win, KN_win = KD["win"], KN["win"]

# ------------------------------------------------------------------ row shifters (§4.2.1, recovered)
COLS = np.arange(W)


def shift_rows(img, rows, dx):
    """shift each listed row horizontally by dx (float, px), linear-interpolated, edges clamped"""
    src = COLS[None, :] - dx[:, None]
    i0 = np.floor(src).astype(np.int32); f = (src - i0)[..., None]
    i0c = np.clip(i0, 0, W - 1); i1c = np.clip(i0 + 1, 0, W - 1)
    r = rows[:, None]
    return img[r, i0c] * (1 - f) + img[r, i1c] * f


def shift_rows_zero(img, rows, dx):
    """like shift_rows, but what slides in from outside the frame is empty (for the cloud layer)"""
    src = COLS[None, :] - dx[:, None]
    i0 = np.floor(src).astype(np.int32); f = (src - i0)[..., None]
    v0 = ((i0 >= 0) & (i0 < W))[..., None]; v1 = ((i0 + 1 >= 0) & (i0 + 1 < W))[..., None]
    r = rows[:, None]
    return img[r, np.clip(i0, 0, W - 1)] * (1 - f) * v0 + img[r, np.clip(i0 + 1, 0, W - 1)] * f * v1


# ------------------------------------------------------------------ cloud_layer (§4.2.2, recovered v8)
_CW = {}


def cloud_layer(K, rows, t, hzp):
    """the cloud wisps drift left (faster high up) and slowly change shape: two smooth displacement fields swap in
    and out, so the strokes stretch and thin a little as they travel, the way cloud does at dusk"""
    key = (id(K), len(rows))
    if key not in _CW:
        r = np.random.default_rng(77)
        f = [ndi.gaussian_filter(r.standard_normal((len(rows), W)).astype(np.float32), (40, 90)) for _ in range(4)]
        f = [x / (x.std() + 1e-6) for x in f]
        _CW[key] = (f, np.arange(len(rows), dtype=np.float32)[:, None], COLS[None, :].astype(np.float32),
                    K["cloud"][rows])
    f, ys, xs, cl = _CW[key]
    drift = -(t * 12.0) * (1.3 - 0.6 * ys / hzp)                       # px: about 12 px/s, a little faster high up
    a1, a2 = math.sin(t * 0.55), math.cos(t * 0.41 + 0.7)
    wx = 7.0 * (a1 * f[0] + a2 * f[1]); wy = 2.2 * (a1 * f[2] + a2 * f[3])
    sy, sx = ys - wy, xs - drift - wx
    sy = np.broadcast_to(sy, sx.shape)
    return np.stack([ndi.map_coordinates(cl[..., c], [sy, sx], order=1, mode="constant", cval=0.0)
                     for c in range(3)], -1)


# ------------------------------------------------------------------ glints (§4.2.3, recovered v9)
_GL = {}


def glints(K, hzp, y0, t, night):
    key = (id(K), night)
    if key not in _GL:
        r = np.random.default_rng(91 if night else 90); n = 34 if night else 22; G = []
        for _ in range(n):
            d = r.uniform(0, 1) ** 1.6 * 0.5                            # depth: most near the horizon
            y = hzp + 3 + d * (H - hzp); x = K["win"][0] + r.normal(0, 3 + 30 * d)
            G.append((x, y, (3 + 16 * d) * r.uniform(0.6, 1.3), 0.7 + 1.6 * d, r.uniform(0, 6.28), r.uniform(1.2, 2.6),
                      math.exp(-d / 0.45)))
        _GL[key] = G
    acc = np.zeros((H - y0, W), np.float32)
    for x, y, hl, hh, ph, rate, k in _GL[key]:
        b_ = max(0.0, math.sin(ph + t * rate)) ** 3 * k
        if b_ < 0.02: continue
        xa, xb = int(x - hl - 3), int(x + hl + 4); ya, yb = int(y - hh - 3) - y0, int(y + hh + 4) - y0
        if ya < 0 or yb > acc.shape[0] or xa < 0 or xb > W: continue
        gx = np.arange(xa, xb, dtype=np.float32)[None, :]; gy = np.arange(ya + y0, yb + y0, dtype=np.float32)[:, None]
        acc[ya:yb, xa:xb] += b_ * np.exp(-((gx - x) / hl) ** 4) * np.exp(-((gy - y) / hh) ** 2)
    return np.clip(acc, 0, 1.2)[..., None]


# ------------------------------------------------------------------ living_sea (§4.2.4, final v9)
_SEA = {}


def living_sea(img, K, t, night=False, on=1.0):
    """small movements for the painted sea scenes: drifting sky, swaying water, a flickering window.
    t is the SCENE clock (s1/s2: absolute t; s8: t - T['s8'][0])."""
    out = img.copy()
    hzp = int(K["hz"] * H)
    # sky: the cloud layer drifts and reshapes over the still cloudless sky; the land stays put
    rows = np.arange(0, hzp + 2)
    sky = K["nc"][rows] + cloud_layer(K, rows, t, hzp)
    keep = K["land"][rows][..., None]
    out[rows] = sky * (1 - keep) + img[rows] * keep
    # water: rows sway sideways, more strongly toward the viewer, so strokes and reflections ripple
    y0 = hzp + 2
    if hzp not in _SEA:
        _SEA[hzp] = (np.arange(y0, H, dtype=np.float32)[:, None], COLS[None, :].astype(np.float32))
    ys, xs = _SEA[hzp]
    depth = (ys - hzp) / (H - hzp)
    dx = (1.0 + 6.5 * depth) * np.sin(ys * 0.06 + t * 1.5) + (0.6 + 3.0 * depth) * np.sin(ys * 0.019 - t * 0.9 + 1.3)
    dy = (0.3 + 2.6 * depth) * np.sin(xs * 0.011 + ys * 0.045 + t * 1.25)       # a gentle swell, stronger near the viewer
    sy = np.clip(ys + dy, y0, H - 1); sx = np.clip(xs - dx, 0, W - 1)
    for c in range(3): out[y0:, :, c] = ndi.map_coordinates(img[..., c], [sy, sx], order=1)
    # glints in the window's reflection: short horizontal flecks that wink on and off in place (stepped on twos).
    out[y0:] += on * glints(K, hzp, y0, twos(t), night) * np.array([0.30, 0.22, 0.09], np.float32)
    # window: a soft flicker, stepped on twos
    tt = twos(t)
    fl = 0.05 * math.sin(tt * 7.3) + 0.03 * math.sin(tt * 17.1 + 1) + (0.04 if night else 0.0)
    g = K["glow"][..., None]
    out = out * (1 + on * fl * g) + on * g * np.array([0.10, 0.07, 0.02], np.float32) * (0.5 + fl * 5) * (0.6 if not night else 1.0)
    return np.clip(out, 0, 1)


# ------------------------------------------------------------------ camera helpers (§4.2.5)
def push_box(t, dur, focus, amount=0.045):
    s = 1 + amount * ease_io(t / dur)
    fx, fy = focus
    w, h = W / s, H / s
    x0 = min(max(fx - w * fx / W, 0), W - w); y0 = min(max(fy - h * fy / H, 0), H - h)
    return (x0, y0, s)


def cam_box(s, cx, cy):
    """a W/s x H/s view centred on source point (cx, cy), clamped inside the frame"""
    w, h = W / s, H / s
    x0 = min(max(cx - w / 2, 0), W - w); y0 = min(max(cy - h / 2, 0), H - h)
    return (x0, y0, s)


def apply_box(im, box):
    x0, y0, s = box
    if abs(s - 1) < 1e-6 and abs(x0) < 1e-6 and abs(y0) < 1e-6: return im
    return im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + W / s, y0 + H / s))


def cam(im, s, cx, cy): return apply_box(im, cam_box(s, cx, cy))


def push(img_pil, t, dur, focus, amount=0.045):
    """slow push-in toward a focus point (2.5D camera move on a still)"""
    return apply_box(img_pil, push_box(t, dur, focus, amount))


def to_screen_fn(box):
    x0, y0, s = box
    return lambda x, y: ((x - x0) * s, (y - y0) * s)


# ------------------------------------------------------------------ 2.5D parallax (§4.3)
_PX = {}


def _blur_ds(a, sg, k=4):
    """gaussian blur of an (H, W[, C]) array at 1/k resolution (for the big sigmas of the sky fill), back to full size"""
    h, w = a.shape[:2]
    hs, ws = h // k, w // k
    sm = a[:hs * k, :ws * k].reshape(hs, k, ws, k, *a.shape[2:]).mean((1, 3))
    sig = (sg / k, sg / k) + ((0,) if a.ndim == 3 else ())
    sm = ndi.gaussian_filter(sm, sig, mode="nearest")
    zf = (h / hs, w / ws) + ((1,) if a.ndim == 3 else ())
    out = ndi.zoom(sm, zf, order=1, mode="nearest", grid_mode=True)
    return out[:h, :w]


def _build_parallax():
    """Far plane: sky (hill painted out, extended below the horizon). Near plane: hill, house and sea."""
    hzp = int(KD["hz"] * H)
    nc = KD["nc"]
    src = MD["land_shape"] if "land_shape" in MD.files else MD["land"]
    land = ndi.gaussian_filter(np.asarray(Image.fromarray(src).resize((W, H), Image.BILINEAR), np.float32) / 255, 2)
    wx, wy = KD["win"]; yy0, xx0 = np.mgrid[0:H, 0:W].astype(np.float32)
    land = np.maximum(land, ndi.gaussian_filter(((np.abs(xx0 - wx) < 30) & (yy0 > wy - 38) & (yy0 < wy + 14)).astype(np.float32), 1.2))
    del yy0, xx0
    landD = ndi.gaussian_filter(ndi.grey_dilation((land > 0.02).astype(np.float32), size=(11, 11)), 1.5)
    # sky behind the hill: a smooth fill grown in from the surrounding sky (normalised convolution at a few scales),
    # plus paper/wash texture borrowed from clear sky higher up (a column-copy fill leaves vertical streaks)
    hole = (landD > 0.05).astype(np.float32); hole[hzp:] = 1.0
    known = 1 - hole
    fill = nc * known[..., None]; filled = known.copy()
    for sg in (6, 16, 40, 100):
        if sg <= 6:
            num = ndi.gaussian_filter(nc * known[..., None], (sg, sg, 0)); den = ndi.gaussian_filter(known, sg)[..., None]
        else:
            num = _blur_ds(nc * known[..., None], sg); den = _blur_ds(known, sg)[..., None]
        est = num / np.maximum(den, 1e-4); w_ = np.clip(den * 6, 0, 1) * (1 - filled)[..., None]
        fill = fill + est * w_; filled = np.clip(filled + w_[..., 0], 0, 1)
    lf = fill.copy()                                                     # the smooth fill, no texture yet
    # texture: the high-pass of the clear sky (land excluded so no house/hill detail is borrowed)
    detail = (nc - ndi.gaussian_filter(nc, (5, 5, 0))) * known[..., None]
    above = (np.arange(H)[:, None] < hzp)
    fill = fill + np.roll(detail, 150, axis=0) * (hole * above)[..., None]
    # below the horizon (revealed only while the near plane is pushed down): the smooth horizon row continued, plus
    # sky texture tiled (mirrored) from a clear band high in the sky, so there is no column-copy streaking
    band = detail[120:420]
    nb = H - hzp
    reps = np.concatenate([band, band[::-1]] * (nb // (2 * len(band)) + 1), 0)[:nb]
    row = ndi.gaussian_filter1d(lf[hzp - 3], 25, axis=0)
    fill[hzp:] = row[None] + reps
    fill = fill * (1 - known[..., None]) + nc * known[..., None]
    rowsf = np.arange(H, dtype=np.float32)[:, None]
    near_a = np.maximum(land, np.clip(rowsf - hzp + 1, 0, 1))[..., None].astype(np.float32)   # hill + house + sea
    sky_keep = ((1 - landD) * (rowsf < hzp))[..., None].astype(np.float32)                    # live sky where it is really sky
    _PX.update(SKYFILL=fill.astype(np.float32), NEAR_A=near_a, SKY_KEEP=sky_keep)


def shift_down(a, dy):
    """shift an image down by a fractional number of pixels (top filled with zeros)"""
    i = int(math.floor(dy)); f = dy - i
    def sh(n):
        if n <= 0: return a
        o = np.zeros_like(a); o[n:] = a[:-n]; return o
    return sh(i) * (1 - f) + sh(i + 1) * f if f > 1e-3 else sh(i)


def parallax(base, dy):
    if dy < 0.05: return base
    if not _PX: _build_parallax()
    SK, SF = _PX["SKY_KEEP"], _PX["SKYFILL"]
    sky = base * SK + SF * (1 - SK)
    na = shift_down(_PX["NEAR_A"], dy); nb = shift_down(base, dy)
    return sky * (1 - na) + nb * na


# ------------------------------------------------------------------ painted gulls (§4.4.2)
BIRDS = [(380, 0.17, 40, 0.0, 17), (560, 0.21, 34, 1.3, 14), (470, 0.13, 46, 2.1, 19)]
BIRD_RGBA = (70, 62, 80, 218)
_BS = {}


def bird_sprite(span, wy):
    """a gull as two tapered, curved brush-stroke wings and a small body; span = half wingspan px, wy = wing-tip
    offset px (+ down). Drawn at 4x and reduced, cached on a quarter-pixel grid."""
    key = (round(span * 4), round(wy * 4))
    if key in _BS: return _BS[key]
    s, k = key[0] / 4, 4
    wy = key[1] / 4
    pad = 6
    w_ = int(2 * (s + pad)); h_ = int(1.3 * s + 2 * pad + 2 * abs(wy))
    cx, cy = w_ / 2, pad + 0.55 * s + abs(wy)
    im = Image.new("RGBA", (w_ * k, h_ * k), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    for sg in (-1, 1):
        p0 = (0.0, 0.0)
        p1 = (sg * 0.28 * s, -0.42 * s - 0.25 * wy)
        p2 = (sg * 0.62 * s, -0.36 * s - 0.1 * wy)
        p3 = (sg * 1.0 * s, 0.10 * s + wy)
        n = 28
        for j in range(n + 1):
            u = j / n
            x, y = bez(p0, p1, p2, p3, u)
            # thick at the shoulder, a slim arm, tapering to a point at the tip
            th = s * (0.13 * (1 - u) ** 0.7 + 0.025) * (1 + 0.5 * math.exp(-((u - 0.3) / 0.18) ** 2))
            r_ = th / 2 * k
            X_, Y_ = (cx + x) * k, (cy + y) * k
            dr.ellipse([X_ - r_, Y_ - r_, X_ + r_, Y_ + r_], fill=BIRD_RGBA)
    bw, bh = 0.13 * s * k, 0.09 * s * k
    dr.ellipse([cx * k - bw, cy * k - bh * 0.6, cx * k + bw, cy * k + bh * 1.4], fill=BIRD_RGBA)
    im = im.resize((w_, h_), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.45))
    _BS[key] = (im, cx, cy)
    if len(_BS) > 4000: _BS.clear()
    return _BS[key]


def birds(im, t, to_screen, scale):
    """draw the gulls on the camera-applied PIL image (screen space). Positions on the true clock; flaps on twos."""
    tt = twos(t)
    for x0, yf, speed, ph, hs in BIRDS:
        x = x0 + speed * t
        y = yf * H + 3.0 * math.sin(t * 1.1 + ph * 2.0)
        sx, sy = to_screen(x, y)
        span = hs * scale
        if sx < -3 * span or sx > W + 3 * span or sy < -3 * span or sy > H + 3 * span: continue
        sm = (math.sin(t * 0.7 + ph) + 1) / 2
        g = 0.35 + 0.65 * sm * sm * (3 - 2 * sm)                         # alternate flapping and gliding
        wy = 0.35 * span * math.sin(tt * 5.2 + ph) * g
        spr, cx, cy = bird_sprite(span, wy)
        im.alpha_composite(spr, (int(round(sx - cx)), int(round(sy - cy))))


# ------------------------------------------------------------------ envelope flights (§4.4.3, §4.10)
class Path:
    """a cubic Bezier flight path in source px, with its dotted-trail style (spacing and dot radius at the start
    and the end of the path, px)"""
    def __init__(self, pts, spacing, radius):
        self.pts = [tuple(map(float, p)) for p in pts]
        self.spacing, self.radius = spacing, radius
        us = np.linspace(0, 1, 801)
        P = np.array([bez(*self.pts, u) for u in us])
        self._u = us
        self._L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])

    def __call__(self, u): return bez(*self.pts, u)

    def dots(self, u_end):
        """(x, y, r) of the trail dots from the start of the path to u_end"""
        L = self._L[-1]; s_end = np.interp(u_end, self._u, self._L)
        out, s = [], 0.0
        while s <= s_end:
            f = s / L
            u = float(np.interp(s, self._L, self._u))
            x, y = self(u)
            out.append((x, y, self.radius[0] + (self.radius[1] - self.radius[0]) * f))
            s += self.spacing[0] + (self.spacing[1] - self.spacing[0]) * f
        return out


# reconstructed from the reference envelope positions (least-squares fit through the measured centres, with
# u = the recovered easing; residuals < 4 px). The end that touches the window is the plate's window centre.
PATH_OUT = Path([(-182, 1154), (502, 728), (1097, 408), KD_win], spacing=(40, 24), radius=(1.7, 3.6))
PATH_HOME = Path([KN_win, (1198, 508), (700, 765), (559, 859)], spacing=(20, 17), radius=(1.5, 3.4))

_ENV = {}


def _fallback_envelope(w=320):
    """a plain envelope sprite (used only until cards.py provides ENV / envelope())"""
    h = int(w / 1.55); m = 12; k = 3
    im = Image.new("RGBA", ((w + 2 * m) * k, (h + 2 * m) * k), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    X0, Y0, X1, Y1 = m * k, m * k, (m + w) * k, (m + h) * k
    dr.rectangle([X0, Y0, X1, Y1], fill=ENV_PAPER + (255,), outline=ENV_FOLD + (255,), width=2 * k)
    lw = max(1, int(1.6 * k))
    dr.line([(X0, Y0), ((X0 + X1) / 2, Y0 + 0.6 * (Y1 - Y0)), (X1, Y0)], fill=ENV_FLAP + (255,), width=lw)
    dr.line([(X0, Y1), ((X0 + X1) / 2, Y0 + 0.5 * (Y1 - Y0))], fill=ENV_FOLD + (255,), width=lw)
    dr.line([(X1, Y1), ((X0 + X1) / 2, Y0 + 0.5 * (Y1 - Y0))], fill=ENV_FOLD + (255,), width=lw)
    sw, sh = 0.13 * w * k, 0.25 * h * k; ix, iy = 0.07 * w * k, 0.07 * w * k
    st = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(st).rectangle([X1 - ix - sw, Y0 + iy, X1 - ix, Y0 + iy + sh], fill=ENV_STAMP)
    im.alpha_composite(st)
    im = im.resize((w + 2 * m, h + 2 * m), Image.LANCZOS)
    sh_ = Image.new("RGBA", im.size, (0, 0, 0, 0)); a = im.getchannel("A").filter(ImageFilter.GaussianBlur(4))
    sh_.putalpha(a.point(lambda v: int(v * 0.18)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0)); out.alpha_composite(sh_, (0, 3)); out.alpha_composite(im)
    return rough(out, 0.6, 10, seed=7, fine=0.15)


def env_sprite():
    """the envelope art: cards.ENV (or cards.envelope(320)) when cards.py exists, else a simple fallback"""
    if "env" not in _ENV:
        from .transitions import optional
        e = optional("cards", "ENV")
        if e is None:
            fn = optional("cards", "envelope")
            if fn is not None:
                try: e = rough(fn(320), 0.6, 10, seed=7, fine=0.15)
                except Exception as ex: print("[seasky] cards.envelope failed:", ex); e = None
        _ENV["env"] = (e if e is not None else _fallback_envelope(320)).convert("RGBA")
    return _ENV["env"]


_DOT = {}


def _dot(r, rgba):
    key = (round(r * 4), rgba)
    if key not in _DOT:
        rr = key[0] / 4; k = 4; n = int(2 * rr + 4)
        im = Image.new("RGBA", (n * k, n * k), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse([(n / 2 - rr) * k, (n / 2 - rr) * k, (n / 2 + rr) * k, (n / 2 + rr) * k], fill=rgba)
        _DOT[key] = im.resize((n, n), Image.LANCZOS)
    return _DOT[key]


def fly(lay, path, u, size0, size1, rot0, rot1, t, dot_col):
    """the envelope along `path` at progress u (0..1): a dotted trail from the start up to u, then the envelope sprite
    scaled to width size0 -> size1 and rotated rot0 -> rot1 degrees (PIL: + = counter-clockwise), centred on path(u)"""
    if u <= 0: return
    u = min(u, 1.0)
    dot_col = tuple(int(c) for c in dot_col)
    for x, y, r in path.dots(u)[:-1]:
        d = _dot(r, dot_col)
        lay.alpha_composite(d, (int(round(x - d.width / 2)), int(round(y - d.height / 2))))
    env = env_sprite()
    w = size0 + (size1 - size0) * u
    h = max(2, int(round(w * env.height / env.width)))
    spr = env.resize((max(2, int(round(w))), h), Image.LANCZOS)
    spr = spr.rotate(rot0 + (rot1 - rot0) * u, expand=True, resample=Image.BICUBIC)
    cx, cy = path(u)
    x, y = int(round(cx - spr.width / 2)), int(round(cy - spr.height / 2))
    # alpha_composite needs the sprite inside the canvas: crop what falls outside
    xa, ya = max(0, -x), max(0, -y)
    xb, yb = min(spr.width, W - x), min(spr.height, H - y)
    if xb > xa and yb > ya:
        lay.alpha_composite(spr.crop((xa, ya, xb, yb)), (x + xa, y + ya))
