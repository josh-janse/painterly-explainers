"""Paper-sheet wipes w4-w7 (SPEC §4.9): a sheet with a torn edge sweeps across the frame.

    sheet(a, b, p, direction, seed) -> f32

a = outgoing frame, b = incoming frame (float32 RGB 0-1, H x W x 3), p = 0..1 through the wipe (eased inside).
    "left": b is revealed from the right, its torn left edge moving x = W -> 0 (w4, w7); both images static
    "right": the mirror of "left": b is revealed from the left, its torn right edge moving x = 0 -> W (reel w6)
    "up":   b is revealed from the bottom, its torn top edge rising y = H -> 0 (landscape w6); both images static
    "down": a is the top sheet and slides down off the frame with its content, revealing b (static) (w5)
The top sheet has a thin bright fibrous lip on its torn edge and casts a soft shadow on the sheet beneath.
Which direction each wipe uses is per format: ep4/layout.py WIPES.
"""
import numpy as np
import scipy.ndimage as ndi

from ep4.common import W, H, ease

_EDGES = {}
def torn_profile(n, seed):
    """offsets (px) along an edge n px long: a slow wobble, a mid ripple and short fibrous jags"""
    k = (n, seed)
    if k not in _EDGES:
        r = np.random.default_rng(seed)
        def band(sigma, amp):
            f = ndi.gaussian_filter1d(r.standard_normal(n + 64), sigma, mode="wrap")[32:-32]
            return f / (f.std() + 1e-6) * amp
        teeth = band(2.6, 2.4)                                                    # rounded teeth ~8-14 px apart (measured w7)
        jag = teeth + np.maximum(teeth, 0) * 0.5 + band(0.7, 0.6)                 # tips a little sharper, a fine fibre fuzz
        prof = band(60, 2.6) + band(16, 1.4) + jag
        lip = np.clip(0.55 + band(4, 0.35), 0.1, 1.0)                           # the lip comes and goes
        _EDGES[k] = (prof.astype(np.float32), ndi.gaussian_filter1d(prof, 6).astype(np.float32), lip.astype(np.float32))
    return _EDGES[k]

def _layers(d, ds, lip, shadow_a, shadow_s, shadow_off, lip_w=2.6, lip_a=0.45):
    """from the signed distance d (px, > 0 inside the top sheet) -> top-sheet alpha, lip strength, shadow on the sheet below"""
    top = np.clip(d + 0.5, 0, 1)
    lp = np.clip(1 - np.abs(d - lip_w / 2) / (lip_w / 2 + 0.5), 0, 1) * lip * lip_a
    out = np.clip(-(ds + shadow_off), 0, None)                                      # distance outside the (smoothed) edge
    sh = shadow_a * np.exp(-out / shadow_s) * (1 - top)
    return top, lp, sh

def sheet(a, b, p, direction, seed):
    pe = ease(p)
    prof, sprof, lip = torn_profile(H if direction in ("left", "right") else W, seed)
    lipc = np.array([1.0, 0.985, 0.955], np.float32)
    if direction == "left":
        ex = W * (1 - pe)
        d = np.arange(W, dtype=np.float32)[None, :] - (ex + prof[:, None])
        ds = np.arange(W, dtype=np.float32)[None, :] - (ex + sprof[:, None])
        top, lp, sh = _layers(d, ds, lip[:, None], 0.24, 10.0, 2.0)
        under, over = a, b
    elif direction == "right":
        ex = W * pe
        d = (ex - prof[:, None]) - np.arange(W, dtype=np.float32)[None, :]
        ds = (ex - sprof[:, None]) - np.arange(W, dtype=np.float32)[None, :]
        top, lp, sh = _layers(d, ds, lip[:, None], 0.24, 10.0, 2.0)
        under, over = a, b
    elif direction == "up":
        ey = H * (1 - pe)
        d = np.arange(H, dtype=np.float32)[:, None] - (ey + prof[None, :])
        ds = np.arange(H, dtype=np.float32)[:, None] - (ey + sprof[None, :])
        top, lp, sh = _layers(d, ds, lip[None, :], 0.20, 12.0, 1.0)
        under, over = a, b
    elif direction == "down":
        ey = H * pe; sy = int(round(ey))
        over = np.empty_like(a); over[sy:] = a[:H - sy]; over[:sy] = a[:1]           # the yellow sheet's content moves with it
        d = np.arange(H, dtype=np.float32)[:, None] - (ey + prof[None, :])
        ds = np.arange(H, dtype=np.float32)[:, None] - (ey + prof[None, :] * 0.6 + sprof[None, :] * 0.4)
        top, lp, sh = _layers(d, ds, lip[None, :], 0.42, 5.0, 0.5)                   # a darker, tighter ragged shadow upward
        under = b
    else:
        raise ValueError(direction)
    base = under * (1 - sh[..., None])
    sheet_ = over * (1 - lp[..., None]) + lipc * lp[..., None]
    return (base * (1 - top[..., None]) + sheet_ * top[..., None]).astype(np.float32)
