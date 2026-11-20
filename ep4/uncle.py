"""The uncle scenes: s3 "he reads it carefully" and s5 "he forgets everything" (SPEC §3.3, §4.6).

Layers (from ep4.backdrops SCENE=uncle): uncle_bg.jpg -> body -> head (rotated about the neck pivot) -> collar (hides the
neck seam) -> the round window cut through the head, with the envelope icon in it -> a dry glint on the glasses lens ->
overlays (the letter card in s3, the drifting words in s5).

The figure (breathing, the read-nod) runs on the true 24 fps clock; every overlay (icon, hole size, card, words, glint)
samples time through twos() (§1.3).

Interface (§7): scene_reads(lt), scene_forget(lt), uncle_frame(lt, tilt, open_frac, icon, extra_lay=None) -> float32
H x W x 3, and the constants WIN_C, WIN_R. `lt` is seconds into the uncle shot (it drives the breathing loop).
"""
import math
import os

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from ep4.common import (A, F, H, INK, W, CARD_PAPER, ENV_FLAP, ENV_FOLD, ENV_PAPER, ENV_STAMP, blank, ease,
                        ease_io, font, rough, to_f32, twos)
from ep4 import timeline as TL

WIN_C = (0.27975 * W, 0.2924 * H)          # (537.1, 315.8): the hole, in the head's rest pose (recovered)
WIN_R = 62 * F                             # 93 px

READ_DEG = 2.0                             # the read-nod: head forward (nose down) about the neck pivot, degrees
BREATH_T = 4.6                             # breathing period, s
BREATH_HEAD, BREATH_BODY = 2.2, 1.2        # px amplitude (measured: head top 169-175, shoulders 663-666)
ICON_W = 112                               # envelope paper width in the hole when icon = 1 (measured)
SS = 4                                     # hole supersampling

_S = {}


# ------------------------------------------------------------------------------------------------ assets
def _rgba(name):
    im = Image.open(os.path.join(A, name)).convert("RGBA")
    return im if im.size == (W, H) else im.resize((W, H), Image.LANCZOS)


def _crop_layer(im, margin):
    """crop an RGBA full-frame layer to its bbox + margin, premultiplied (RGBa) so resampling has no dark fringe"""
    x0, y0, x1, y1 = im.getbbox()
    box = (max(0, x0 - margin), max(0, y0 - margin), min(W, x1 + margin), min(H, y1 + margin))
    return im.crop(box).convert("RGBa"), box


def _assets():
    if _S: return _S
    bg = Image.open(os.path.join(A, "uncle_bg.jpg")).convert("RGB")
    if bg.size != (W, H): bg = bg.resize((W, H), Image.LANCZOS)
    _S["bg"] = bg.convert("RGBA")
    geo = np.load(os.path.join(A, "uncle_geo.npz"))
    _S["pivot"] = tuple(float(v) for v in geo["pivot"])
    _S["lens"] = tuple(float(v) for v in geo["lens"])
    split = float(geo["split"])
    hp, bp = os.path.join(A, "uncle_head.png"), os.path.join(A, "uncle_body.png")
    if os.path.exists(hp) and os.path.exists(bp):
        head, body = _rgba("uncle_head.png"), _rgba("uncle_body.png")
    else:                                   # split the combined figure at `split` (body keeps the area under the neck)
        fig = _rgba("uncle_fig.png")
        a = np.asarray(fig).copy(); b = a.copy()
        a[int(split):, :, 3] = 0; b[:int(split) - 30, :, 3] = 0
        head, body = Image.fromarray(a, "RGBA"), Image.fromarray(b, "RGBA")
    _S["head"], _S["head_box"] = _crop_layer(head, 40)
    _S["body"], _S["body_box"] = _crop_layer(body, 8)
    _S["collar"], _S["collar_box"] = _crop_layer(_rgba("uncle_collar.png"), 8)
    return _S


def _cards():
    try:
        from ep4 import cards
        return cards
    except Exception:
        return None


def _env_sprite():
    """the envelope sprite (cards.ENV when cards.py is there, else our own) and its paper box in sprite px"""
    if "env" not in _S:
        sp = None
        c = _cards()
        if c is not None:
            try:
                sp = c.ENV if hasattr(c, "ENV") else rough(c.envelope(320), 0.6, 10, seed=7, fine=0.15)
                sp = sp.convert("RGBA")
            except Exception:
                sp = None
        if sp is None: sp = _envelope_fallback(320)
        a = np.asarray(sp)[..., 3]
        ys, xs = np.where(a > 200)
        _S["env"] = (sp, (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
    return _S["env"]


def _envelope_fallback(w=320):
    """SPEC §4.8.3 envelope: paper, thin border, flap V, lower folds, red stamp, soft shadow"""
    h = int(round(w / 1.55)); m = 24; s = 2
    im = Image.new("RGBA", ((w + 2 * m) * s, (h + 2 * m) * s), (0, 0, 0, 0))
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).rectangle([(m + 3) * s, (m + 6) * s, (m + w + 3) * s, (m + h + 6) * s], fill=60)
    sh = sh.filter(ImageFilter.GaussianBlur(9 * s))
    im.paste((60, 48, 40, 255), (0, 0), sh)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = m * s, m * s, (m + w) * s, (m + h) * s
    d.rectangle([x0, y0, x1, y1], fill=ENV_PAPER + (255,), outline=ENV_FOLD + (255,), width=2 * s)
    cx, cy = (x0 + x1) / 2, y0 + 0.6 * (y1 - y0)
    d.line([(x0, y1), (cx, y0 + 0.5 * (y1 - y0)), (x1, y1)], fill=ENV_FOLD + (255,), width=2 * s)
    d.line([(x0, y0), (cx, cy), (x1, y0)], fill=ENV_FLAP + (255,), width=int(2.5 * s))
    sw, shh = 0.13 * w * s, 0.25 * h * s; ix, iy = 0.07 * w * s, 0.08 * h * s
    st = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(st).rectangle([x1 - ix - sw, y0 + iy, x1 - ix, y0 + iy + shh], fill=ENV_STAMP)
    im.alpha_composite(st)
    im = im.resize((w + 2 * m, h + 2 * m), Image.LANCZOS)
    return rough(im, 0.6, 10, seed=7, fine=0.15)


LETTER_LINES = [("i", "Dear Uncle,"), ("r", "What can I cook tonight with eggs and spinach?"), ("i", "Love, Sam")]
CARD_CENTRE = (1460.0, 541.0)              # paper centre at rest (measured, frame 552)


def _letter():
    """the letter card (cards.card when available) and the offset of its paper centre from the sprite's top-left"""
    if "letter" not in _S:
        im = None
        c = _cards()
        if c is not None:
            try:
                im = c.LETTER if hasattr(c, "LETTER") else c.card(LETTER_LINES, 420 * F, -2)
                if isinstance(im, tuple): im = im[0]
                im = im.convert("RGBA")
            except Exception:
                im = None
        if im is None: im = _letter_fallback()
        a = np.asarray(im)[..., 3]
        ys, xs = np.where(a > 230)
        _S["letter"] = (im, ((xs.min() + xs.max() + 1) / 2, (ys.min() + ys.max() + 1) / 2))
    return _S["letter"]


def _wrap(dr, text, fnt, width):
    out, line = [], ""
    for w_ in text.split():
        t = (line + " " + w_).strip()
        if dr.textlength(t, font=fnt) <= width or not line: line = t
        else: out.append(line); line = w_
    if line: out.append(line)
    return out


def _letter_fallback(w=420 * F, rot=-2, size=30):
    """a stand-in for cards.card(): paper (242,233,217), roughened edge, soft shadow, Source Serif text"""
    fs = int(size * F); m = 40; padx, pady = 66, 62
    lh, gap = 1.42 * fs, 0.62 * fs
    tmp = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    paras = []
    for st, txt in LETTER_LINES:
        fnt = font("serif_i" if st == "i" else "serif", fs)
        paras.append((fnt, _wrap(tmp, txt, fnt, w - 2 * padx)))
    hh = 2 * pady + sum(len(l) for _, l in paras) * lh + gap * (len(paras) - 1) - (lh - fs * 1.2)
    w, hh = int(w), int(hh)
    paper = Image.new("RGBA", (w + 2 * m, hh + 2 * m), (0, 0, 0, 0))
    ImageDraw.Draw(paper).rectangle([m, m, m + w, m + hh], fill=CARD_PAPER + (255,))
    paper = rough(paper, 0.8, 12, seed=101, fine=0.15)
    sh = Image.new("L", paper.size, 0)
    ImageDraw.Draw(sh).rectangle([m, m + 10, m + w, m + hh + 10], fill=int(0.16 * 255))
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    im = Image.new("RGBA", paper.size, INK + (0,))
    im.putalpha(sh)
    im.alpha_composite(paper)
    d = ImageDraw.Draw(im)
    y = m + pady
    for fnt, lines in paras:
        for ln in lines:
            d.text((m + padx, y), ln, font=fnt, fill=INK + (255,))
            y += lh
        y += gap
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)


# ------------------------------------------------------------------------------------------------ geometry
def _head_xf(tilt, dy):
    """the head transform: rotate by tilt*READ_DEG (clockwise on screen = nose down) about the pivot, then shift dy"""
    S = _assets()
    th = math.radians(READ_DEG * tilt)
    c, s = math.cos(th), math.sin(th)
    px, py = S["pivot"]
    def fwd(x, y):
        X, Y = x - px, y - py
        return (px + c * X - s * Y, py + s * X + c * Y + dy)
    return th, c, s, fwd


def _circle_mask(cx, cy, r, ox, oy, w, h):
    """crisp supersampled disc, as an L image (w x h) whose top-left is at (ox, oy)"""
    big = Image.new("L", (w * SS, h * SS), 0)
    ImageDraw.Draw(big).ellipse([(cx - ox - r) * SS, (cy - oy - r) * SS, (cx - ox + r) * SS, (cy - oy + r) * SS],
                                fill=255)
    return big.resize((w, h), Image.LANCZOS)


def breath(lt):
    return math.sin(2 * math.pi * lt / BREATH_T)


# ------------------------------------------------------------------------------------------------ the frame
def uncle_frame(lt, tilt, open_frac, icon, extra_lay=None, glint=0.0):
    """one uncle frame: lt = seconds into the shot (breathing), tilt 0..1 (read-nod), open_frac 0..1 (hole radius),
    icon 0..1 (envelope size in the hole), extra_lay = full-frame RGBA overlay drawn last, glint 0..1 (lens glint)"""
    S = _assets()
    b = breath(lt)
    bdy, hdy = BREATH_BODY * b, BREATH_HEAD * b
    im = S["bg"].copy()

    # body and collar: a sub-pixel breathing shift
    def shifted(lay, box, dy):
        w, h = lay.size
        out = lay.transform((w, h), Image.AFFINE, (1, 0, 0, 0, 1, -dy), resample=Image.BICUBIC)
        return out.convert("RGBA"), box
    body, bbox = shifted(S["body"], S["body_box"], bdy)
    im.alpha_composite(body, (bbox[0], bbox[1]))

    # head: rotate about the pivot and ride the breath, in its crop box
    th, c, s, fwd = _head_xf(tilt, hdy)
    hb = S["head_box"]; ox, oy = hb[0], hb[1]
    px, py = S["pivot"]
    lpx, lpy = px - ox, py - oy
    # inverse map (output -> input) in crop coordinates: p_in = R^-1 (p_out - pv - d) + pv
    a_, b_, d_, e_ = c, s, -s, c
    cx0 = -a_ * lpx - b_ * (lpy + hdy) + lpx
    cy0 = -d_ * lpx - e_ * (lpy + hdy) + lpy
    hw, hh = S["head"].size
    head = S["head"].transform((hw, hh), Image.AFFINE, (a_, b_, cx0, d_, e_, cy0), resample=Image.BICUBIC)
    head = head.convert("RGBA")

    # the window: a crisp disc cut through the head, so the paper behind shows through it
    wx, wy = fwd(*WIN_C)
    r = WIN_R * open_frac
    m = None
    if r > 0.4:
        R = int(math.ceil(WIN_R)) + 4
        mx, my = int(math.floor(wx)) - R, int(math.floor(wy)) - R
        mw = mh = 2 * R + 2
        m = _circle_mask(wx, wy, r, mx, my, mw, mh)
        box = (mx - ox, my - oy, mx - ox + mw, my - oy + mh)
        al = head.getchannel("A")
        al.paste(ImageChops.multiply(al.crop(box), Image.eval(m, lambda v: 255 - v)), box[:2])
        head.putalpha(al)
    im.alpha_composite(head, (ox, oy))

    collar, cb = shifted(S["collar"], S["collar_box"], bdy)
    im.alpha_composite(collar, (cb[0], cb[1]))

    # the envelope icon in the hole (rotates with the head; clipped to the hole)
    if m is not None and icon > 0.02:
        sp, (x0, y0, x1, y1) = _env_sprite()
        k = ICON_W * icon / (x1 - x0)
        sw, sh_ = max(1, int(round(sp.width * k))), max(1, int(round(sp.height * k)))
        ic = sp.resize((sw, sh_), Image.LANCZOS)
        pcx, pcy = (x0 + x1) / 2 * k, (y0 + y1) / 2 * k            # paper centre in the scaled sprite
        if abs(th) > 1e-4:
            w0, h0 = ic.size
            ic = ic.rotate(-math.degrees(th), expand=True, resample=Image.BICUBIC)
            dx, dy = pcx - w0 / 2, pcy - h0 / 2
            pcx = ic.width / 2 + c * dx - s * dy
            pcy = ic.height / 2 + s * dx + c * dy
        lay = Image.new("RGBA", m.size, (0, 0, 0, 0))
        lay.alpha_composite(ic, (int(round(wx - mx - pcx)), int(round(wy - my - pcy))))
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), m))
        im.alpha_composite(lay, (mx, my))

    # a thin dry glint across the glasses lens
    if glint > 0.01:
        lx, ly = fwd(*S["lens"])
        P = 40
        g = Image.new("L", (2 * P * SS, 2 * P * SS), 0)
        ca, sa = math.cos(math.radians(-50) + th), math.sin(math.radians(-50) + th)
        gx, gy = P - 5, P - 3
        L = 11
        ImageDraw.Draw(g).line([((gx - ca * L) * SS, (gy - sa * L) * SS), ((gx + ca * L) * SS, (gy + sa * L) * SS)],
                               fill=255, width=int(1.6 * SS))
        g = g.resize((2 * P, 2 * P), Image.LANCZOS).filter(ImageFilter.GaussianBlur(0.8))
        g = g.point(lambda v: int(v * min(1.0, glint) * 150 / 255))
        gl = Image.new("RGBA", g.size, (255, 248, 232, 0)); gl.putalpha(g)
        im.alpha_composite(gl, (int(round(lx)) - P, int(round(ly)) - P))

    if extra_lay is not None:
        im.alpha_composite(extra_lay)
    return to_f32(im)


# ------------------------------------------------------------------------------------------------ overlays
def _pulse(t, c, w=0.33):
    """a brief 0 -> 1 -> 0 bump centred at c"""
    p = (t - c) / w
    return 0.0 if abs(p) >= 1 else 0.5 + 0.5 * math.cos(math.pi * p)


def _back(p, c1=0.6):
    """ease-out with a small overshoot"""
    p = min(max(p, 0.0), 1.0); c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


CARD_IN, CARD_DUR, CARD_OFF = 1.2, 0.7, 912      # s3: the letter slides in from the right (start, s, px travel)


def letter_layer(lt):
    """s3 overlay: the letter card sliding in from the right at s3 + 1.2, resting at CARD_CENTRE"""
    tt = twos(lt)
    if tt < CARD_IN: return None
    im, (pcx, pcy) = _letter()
    x = CARD_CENTRE[0] + CARD_OFF * (1 - _back((tt - CARD_IN) / CARD_DUR))
    lay = blank()
    lay.alpha_composite(im, (int(round(x - pcx)), int(round(CARD_CENTRE[1] - pcy))))
    return lay


# (text, size_1280, x_1280, y_1280, alpha) -- the storyboard word cloud (recovered first four + canvas list)
WORDS = [("spinach", 26, 0, 90, .85), ("eggs", 24, 60, 160, .75), ("tonight", 22, 150, 40, .6),
         ("omelette", 22, 200, 220, .55), ("Dear Uncle", 20, 290, 120, .45), ("butter", 18, 380, 290, .35),
         ("Sam", 16, 470, 60, .25), ("fold", 15, 520, 190, .2), ("cook", 13, 610, 260, .12), ("love", 12, 660, 140, .08)]
WORD_ORIGIN = (790, 145)        # where the cloud's (0, 0) lands (fit to the reference; storyboard origin was (660, 165))
WORD_EMERGE = (812, 360)        # words leave the face here (text left edge, mid-height)
WORD_GAP, WORD_TRAVEL, WORD_FADEIN = 0.30, 3.0, 0.4
WORD_DELAY = 0.05               # words and the icon's exit start together, on the first twos step after FORGET
_WORD_IMG = {}


def _word_img(text, px, alpha):
    k = (text, px, alpha)
    if k not in _WORD_IMG:
        fnt = font("mono", px)
        l, t, r, b = fnt.getbbox(text)
        im = Image.new("RGBA", (r + 4, b + 4), INK + (0,))
        ImageDraw.Draw(im).text((0, 0), text, font=fnt, fill=INK + (255,))
        _WORD_IMG[k] = im
    return _WORD_IMG[k]


def words_layer(lt):
    """s5 overlay: the words of the letter drift out of his face from FORGET and fade by "Gone" (on twos)"""
    tt = twos(lt)
    t0 = TL.FORGET + WORD_DELAY
    if tt < t0: return None
    fa, fb = TL.FADE_WORDS
    fade = 1 - min(max((tt - fa) / (fb - fa), 0.0), 1.0)
    if fade <= 0: return None
    lay = blank()
    for i, (text, size, x, y, alpha) in enumerate(WORDS):
        ti = t0 + i * WORD_GAP
        dt = tt - ti
        if dt <= 0: continue
        a = alpha * min(1.0, dt / WORD_FADEIN) * fade
        if a < 0.004: continue
        px = int(round(size * F))
        ex, ey = WORD_EMERGE[0], WORD_EMERGE[1] - 0.62 * px
        tx, ty = WORD_ORIGIN[0] + x * F, WORD_ORIGIN[1] + y * F
        e = ease(dt / WORD_TRAVEL)
        sd = dt - 1.2                                       # slow spread once the word is out: C1 ramp into a drift
        dd = 0.0 if sd <= 0 else (sd * sd / 2 if sd < 1 else sd - 0.5)
        vx, vy = 14 + 0.012 * x * F, -3 - 0.004 * x * F
        X = ex + (tx - ex) * e + vx * dd
        Y = ey + (ty - ey) * e + vy * dd
        img = _word_img(text, px, alpha)
        if a < 0.999:
            img = img.copy(); img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        lay.alpha_composite(img, (int(round(X)), int(round(Y))))
    return lay


# ------------------------------------------------------------------------------------------------ scenes
def s3_state(lt):
    """(tilt, open_frac, icon, glint) for s3 at local time lt"""
    tilt = ease_io((lt - TL.READ_TILT) / 0.7)
    tt = twos(lt)
    icon = 0.0 if tt < 0.70 else ease((tt - 0.70) / 0.30)
    glint = _pulse(tt, 0.95) + 0.7 * _pulse(tt, 4.3)
    return tilt, 1.0, icon, glint


def s5_state(lt):
    """(tilt, open_frac, icon, glint) for s5 at local time lt"""
    tilt = 1.0 - ease_io((lt - TL.FORGET) / 1.0)
    tt = twos(lt)
    q = min(max((tt - (TL.FORGET + WORD_DELAY)) / 0.5, 0.0), 1.0)
    icon = 1.0 - q ** 1.5                                    # shrinks away, accelerating (measured 32.89 -> 33.25)
    open_frac = 1.0 - ease_io((tt - TL.HOLE_CLOSE) / 0.7)
    glint = 0.7 * _pulse(tt, 1.3)
    return tilt, open_frac, icon, glint


def scene_reads(lt):
    """s3 (18.20 -> 24.10): window open from the first frame, envelope arrives at 0.70 s, the letter slides in at 1.2 s,
    he tips his head down to read at READ_TILT"""
    lt = max(0.0, lt)
    tilt, op, icon, gl = s3_state(lt)
    return uncle_frame(lt, tilt, op, icon, letter_layer(lt), glint=gl)


def scene_forget(lt):
    """s5 (30.19 -> 40.90): starts nodded with the envelope in his head; at FORGET the envelope leaves and the words
    drift out and fade (FADE_WORDS); the hole shuts from HOLE_CLOSE, closed by "Gone"; the head lifts upright"""
    lt = max(0.0, lt)
    tilt, op, icon, gl = s5_state(lt)
    return uncle_frame(lt, tilt, op, icon, words_layer(lt), glint=gl)


if __name__ == "__main__":                 # python3 -m ep4.uncle OUT.png T  (absolute time)
    import sys
    from ep4.common import to_pil
    out, t = sys.argv[1], float(sys.argv[2])
    f = scene_reads(t - TL.T["s3"][0]) if t < TL.T["w4"][0] else scene_forget(t - TL.T["s5"][0])
    to_pil(f).convert("RGB").save(out)
