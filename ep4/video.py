"""The ep4 picture: scene_dusk (s1+s2), scene_night (s8), the frame(t) dispatcher and the render loop (SPEC §4).

    python3 -m ep4.video OUT.mp4 [t0 t1]     render a time range (default the whole 0 -> END) to H.264
    python3 -m ep4.video OUT.png t           render one frame
    EP4_FORMAT=reel python3 -m ep4.video ...  the 9:16 reel (1080 x 1920, plates from out/ep4_reel/, docs/REEL_LAYOUT.md)

Modules built separately (uncle, cards, sheets) are imported lazily; any function that is missing (or raises) is
replaced by a labelled placeholder frame so the whole timeline always renders end to end.
Env: PRESET (x264 preset, default slow), CRF (default 21).
"""
import math
import os
import subprocess
import sys
import time

import numpy as np
from PIL import Image

from .common import W, H, FPS, ease_io, twos, comp, blank, to_f32, TRAIL_OUT, TRAIL_HOME
from .timeline import T, END, TILT, LIGHT_ON, TITLE, FLY_OUT, FLY_HOME, in_, frac, local
from . import layout as L
from . import seasky as S
from .seasky import DUSK, NIGHT, KD, KN, KD_win, KN_win, LIGHT_D, PATH_OUT, PATH_HOME
from .transitions import optional, call, placeholder, rush_resolve, in_rush, dip, end_fade


# ------------------------------------------------------------------ scenes 1-2: one continuous shot (§4.4)
def dusk_box(t):
    """the camera for the dusk shot at time t: (x0, y0, s) in source px"""
    if t < TILT[1]:
        p = ease_io((t - TILT[0]) / (TILT[1] - TILT[0]))
        z0, (ax, bx), (ay, by) = L.DUSK_ZOOM0, L.DUSK_CX, L.DUSK_CY
        return S.cam_box(z0 - (z0 - 1.0) * p, (ax + bx * p) * W, (ay + by * p) * H)   # starts on sky only
    return S.push_box(t - TILT[1], T["s2"][1] - TILT[1], KD_win, L.PUSH_S2)


def scene_dusk(t, t_scene0=0):
    """scenes 1 and 2 are one shot: high on the sky with gulls, tilt down to the sea and the house (the near plane rising
    faster than the sky), the window lights, then a slow push in; the letter flies out to the window"""
    on = ease_io((t - LIGHT_ON) / 0.5)
    base = S.living_sea(DUSK - (1 - on) * LIGHT_D, KD, t, on=on)
    if t < TILT[1]:
        p = ease_io((t - TILT[0]) / (TILT[1] - TILT[0]))
        base = S.parallax(base, L.PARALLAX * (1 - p) ** 1.5)
    box = dusk_box(t)
    lay = None
    if t >= T["s2"][0] + FLY_OUT[0]:
        lay = blank()
        u = ease_io(min(1, (twos(t) - T["s2"][0] - FLY_OUT[0]) / FLY_OUT[1]))
        S.fly(lay, PATH_OUT, u, *L.FLY_OUT_SIZE, *L.FLY_OUT_ROT, t, TRAIL_OUT)
    im = S.apply_box(comp(base, lay), box)
    x0, y0, sc = box
    S.birds(im, t, lambda x, y: ((x - x0) * sc, (y - y0) * sc), sc)
    if TITLE[0] <= t < TITLE[1]:
        tl = call("cards", "title_reveal", t - TITLE[0], TITLE[1] - TITLE[0])     # skipped until cards.py has it
        if tl is not None: im.alpha_composite(tl)
    return to_f32(im)


# ------------------------------------------------------------------ scene 8: night, the reply flies home (§4.10)
def scene_night(t):
    lt = t - T["s8"][0]
    base = S.living_sea(NIGHT, KN, lt, night=True)
    lay = None
    u = ease_io(min(1, max(0, (twos(lt) - FLY_HOME[0]) / FLY_HOME[1])))
    if u > 0:
        lay = blank()
        S.fly(lay, PATH_HOME, u, *L.FLY_HOME_SIZE, *L.FLY_HOME_ROT, t, TRAIL_HOME)
    im = S.push(comp(base, lay), lt, END - T["s8"][0], KN_win, L.PUSH_S8)
    return to_f32(im)


# ------------------------------------------------------------------ the dispatcher (§4.10)
def _scene(mod, fn, label_t, *args, **kw):
    img = call(mod, fn, *args, **kw)
    if img is not None: return img
    sig = ", ".join(f"{x:.2f}" if isinstance(x, float) else repr(x) for x in args)
    sig += "".join(f", {k}={v!r}" for k, v in kw.items())
    return placeholder(f"{mod}.{fn}({sig})", label_t)


def _sheet(a, b, p, direction, seed, key, t):
    img = call("sheets", "sheet", a, b, p, direction, seed)
    if img is not None: return img
    # stand-in: a hard wipe in the right direction, dimmed and labelled
    e = 1 - (1 - min(max(p, 0), 1)) ** 3
    out = a.copy()
    if direction == "left": x = int(W * (1 - e)); out[:, x:] = b[:, x:]
    elif direction == "right": x = int(W * e); out[:, :x] = b[:, :x]
    elif direction == "up": y = int(H * (1 - e)); out[y:] = b[y:]
    else:
        y = int(H * e); out[:y] = b[:y]; out[y:] = a[:H - y]
    return placeholder(f"sheets.sheet ({key} '{direction}')", t, under=out)


def frame(t):
    """the picture at time t (seconds) as float32 RGB 0-1"""
    if t < T["w3"][0]:
        img = scene_dusk(t)
    elif in_rush(t):                                    # 17.50 -> 18.60 (the resolve runs into s3)
        img = rush_resolve(t)
    elif in_("s3", t):
        img = _scene("uncle", "scene_reads", t, local("s3", t))
    elif in_("w4", t):
        img = _sheet(_scene("uncle", "scene_reads", t, local("s3", t)), _scene("cards", "scene_reply", t, 0),
                     frac("w4", t), L.WIPES["w4"], 12, "w4", t)
    elif in_("s4", t):
        img = _scene("cards", "scene_reply", t, local("s4", t))
    elif in_("w5", t):
        img = _sheet(_scene("cards", "scene_reply", t, T["s4"][1] - T["s4"][0]), _scene("uncle", "scene_forget", t, 0),
                     frac("w5", t), L.WIPES["w5"], 13, "w5", t)
    elif in_("s5", t):
        img = _scene("uncle", "scene_forget", t, local("s5", t))
    elif in_("w6", t):
        img = _sheet(_scene("uncle", "scene_forget", t, T["s5"][1] - T["s5"][0]), _scene("cards", "scene_second", t, 0),
                     frac("w6", t), L.WIPES["w6"], 14, "w6", t)
    elif in_("s6", t):
        img = _scene("cards", "scene_second", t, local("s6", t))
    elif in_("w7", t):
        img = _sheet(_scene("cards", "scene_second", t, 0, static=True), _scene("cards", "scene_history", t, 0),
                     frac("w7", t), L.WIPES["w7"], 15, "w7", t)
    elif in_("s7", t):
        img = _scene("cards", "scene_history", t, local("s7", t))
    elif in_("f8", t):
        img = dip(t)
    else:
        img = scene_night(t)
    return end_fade(np.asarray(img, np.float32), t)


def to_u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


# ------------------------------------------------------------------ render loop
def render(out, t0=0.0, t1=END):
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    n1 = min(n1, int(round(END * FPS)))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", os.environ.get("CRF", "21"),
           "-preset", os.environ.get("PRESET", "slow"), "-pix_fmt", "yuv420p", out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    st = time.time(); last = st
    print(f"rendering frames {n0}..{n1 - 1} ({(n1 - n0) / FPS:.2f} s) -> {out}", flush=True)
    for n in range(n0, n1):
        t = n / FPS
        ff.stdin.write(to_u8(frame(t)).tobytes())
        if (n - n0) % int(5 * FPS) == int(5 * FPS) - 1 or n == n1 - 1:
            el = time.time() - st
            print(f"  t={t:6.2f}  {n - n0 + 1}/{n1 - n0} frames  {el:6.1f} s  ({el / (n - n0 + 1):.2f} s/frame)", flush=True)
    ff.stdin.close(); ff.wait()
    print(f"done in {time.time() - st:.1f} s", flush=True)
    return ff.returncode


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__); return 0
    out = argv[0]
    if out.lower().endswith((".png", ".jpg", ".jpeg")):
        t = float(argv[1]) if len(argv) > 1 else 0.0
        st = time.time()
        Image.fromarray(to_u8(frame(t))).save(out)
        print(f"saved {out} (t={t}) in {time.time() - st:.2f} s")
        return 0
    t0 = float(argv[1]) if len(argv) > 1 else 0.0
    t1 = float(argv[2]) if len(argv) > 2 else END
    return render(out, t0, t1)


if __name__ == "__main__":
    import ep4.video as _v          # run through the package module so lazy imports share one copy
    sys.exit(_v.main(sys.argv[1:]))
