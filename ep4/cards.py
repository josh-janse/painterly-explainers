"""Cards, tags and the paper scenes of ep4 (SPEC §4.4.4-4.4.5, §4.7, §4.8).

    title_reveal(lt, dur) -> RGBA layer        the single title tag folding in / wiping out (s1)
    scene_reply(lt, static=False) -> f32       s4, yellow: Sam's letter in a prompt box, the reply types
    scene_second(lt, static=False) -> f32      s6, pink: the second letter types, "...", "Make what, dear?", "it" swept
    scene_history(t, static=False) -> f32      s7, cream: three taped letters, it -> omelette annotation, the new reply
    envelope(w), ENV, tape(w, h, rot, seed)    art other modules use

All layouts are in 1280-space numbers times F (= output px). Overlays step on twos (§1.3): every scene samples its
local clock through twos(). Edge roughness uses the softened v9 amounts (§4.8.1).
"""
import math
import re

import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw

from ep4.common import (W, H, F, INK, HL, TAG_LIGHT, CARD_PAPER, CARD_LABEL, TAPE, ENV_PAPER, ENV_FLAP, ENV_FOLD,
                        ENV_STAMP, ease, ease_io, twos, load, font, comp, blank, rough, tracked, bez)
from ep4.timeline import (REPLY_TYPE, Q2_TYPE, ANS_DOTS, ANS_TYPE, IT_SWEEP, CARD0, CARD_GAP, ANS2_DOTS, ANS2_TYPE,
                          ANNOT)

def _f32(im): return np.asarray(im.convert("RGB"), np.float32) / 255


# ------------------------------------------------------------------ tags and the title (§4.4.4, §4.4.5)
TAGC = {}
def tag(lines, pos, anchor="tl"):
    """mono boxed tags; lines = [(text, size, fg, bg)]"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    x, y = pos; boxes = []
    for text, size, fg, bg in lines:
        fnt = font("mono", size * F); tr = size * F * (0.14 if size < 20 else 0.10)
        tw = sum(dr.textlength(c, font=fnt) + tr for c in text) - tr
        padx, pady = (12 * F, 7 * F) if size < 20 else (14 * F, 9 * F)
        bw, bh = tw + 2 * padx, size * F * 1.25 + 2 * pady
        boxes.append((text, fnt, tr, fg, bg, bw, bh, padx, pady))
    if anchor == "bl":
        y = y - sum(b[6] for b in boxes) - 10 * F * (len(boxes) - 1)
    for text, fnt, tr, fg, bg, bw, bh, padx, pady in boxes:
        bx = x if anchor in ("tl", "bl") else x - bw
        key = (int(bw), int(bh), tuple(bg))
        if key not in TAGC:
            m = 8; bi = Image.new("RGBA", (int(bw) + 2 * m, int(bh) + 2 * m), (0, 0, 0, 0))
            ImageDraw.Draw(bi).rectangle([m, m, m + bw, m + bh], fill=tuple(bg))
            TAGC[key] = rough(bi, 0.6, 10, seed=31 + len(TAGC), fine=0.1)        # v8 softened (v7: 1.1, fine 0.22)
        lay.alpha_composite(TAGC[key], (int(bx) - 8, int(y) - 8))
        tracked(dr, (bx + padx, y + pady + 1), text, fnt, fg, tr)
        y += bh + 10 * F
    return lay

TITLE_TEXT = "THE UNCLE WHO ONLY READS LETTERS"
TITLE_LAY = None
_TITLE_BOX = None
def title_reveal(lt, dur):
    """the title folds in: the tag grows from its left edge in stepped, ragged jumps (on twos); on the way out it is
    wiped away left to right the same way. One tag only (owner change 2: no "EPISODE 4")."""
    global TITLE_LAY, _TITLE_BOX
    if TITLE_LAY is None:
        TITLE_LAY = tag([(TITLE_TEXT, 22, INK, TAG_LIGHT)], (64 * F, H - 64 * F), "bl")
        a = np.asarray(TITLE_LAY.getchannel("A"))
        ys, xs = np.nonzero(a > 0); _TITLE_BOX = (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1)
    x0, x1, y0, y1 = _TITLE_BOX
    lt = twos(lt); span = x1 - x0 + 24
    if lt <= 0 or lt >= dur: return blank()
    r = np.random.default_rng(int(lt * 12) + 3)
    band = np.repeat(r.uniform(-1, 1, (y1 - y0) // 5 + 2), 5)[: y1 - y0] * 5 * F   # ragged leading edge, re-cut every frame
    p_in = ease(lt / 0.42); p_out = ease((lt - (dur - 0.42)) / 0.36)
    edge_in = x0 - 12 + p_in * (span + 12) + band * (p_in < 1)
    edge_out = x0 - 12 + p_out * (span + 12) + band * (0 < p_out < 1)
    cols = np.arange(x0, x1)[None, :]
    m = ((cols < edge_in[:, None]) & (cols >= edge_out[:, None])).astype(np.float32)
    out = np.array(TITLE_LAY); out[y0:y1, x0:x1, 3] = (out[y0:y1, x0:x1, 3] * m).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


# ------------------------------------------------------------------ text helpers and the prompt box (§4.7.1)
def wrap(dr, text, fnt, width):
    words, lines, cur = text.split(" "), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if dr.textlength(trial, font=fnt) <= width: cur = trial
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

def text_block(lay, xy, text, fnt, width, lh, fill=INK, nchars=None, cursor=False):
    dr = ImageDraw.Draw(lay)
    lines = wrap(dr, text, fnt, width)
    shown = len(text) if nchars is None else nchars
    x, y = xy; used = 0
    last = (x, y)
    for ln in lines:
        take = max(0, min(len(ln), shown - used))
        dr.text((x, y), ln[:take], font=fnt, fill=fill)
        last = (x + dr.textlength(ln[:take], font=fnt), y)
        used += len(ln) + 1
        if take < len(ln): break
        y += lh
    if cursor:
        cx, cy = last
        dr.rectangle([cx + 6 * F, cy + 0.12 * lh, cx + 9 * F, cy + 0.88 * lh], fill=fill)
    return lines

PBC = {}
def prompt_box(lay, xy, w, text, size, highlight=None, nchars=None):
    """the chat prompt box: a hand-wavy rounded outline (cached, roughened) with text typed into it. Its height comes
    from the full text so it doesn't grow while typing. highlight = (word, p): a marker sweep behind the word."""
    dr = ImageDraw.Draw(lay); fnt = font("sans", size * F)
    lines = wrap(dr, text, fnt, w - 64 * F)
    lh = size * F * 1.4
    hgt = len(lines) * lh + 52 * F
    x, y = xy
    key = (int(w), int(hgt))
    if key not in PBC:
        m = 16; bi = Image.new("RGBA", (int(w) + 2 * m, int(hgt) + 2 * m), (0, 0, 0, 0))
        ImageDraw.Draw(bi).rounded_rectangle([m, m, m + w, m + hgt], radius=18 * F, outline=INK + (255,), width=int(2 * F))
        PBC[key] = rough(bi, 0.55, 14, seed=61 + len(PBC), fine=0.05)          # v8 softened (v7: 0.9, fine 0.1)
    lay.alpha_composite(PBC[key], (int(x) - 16, int(y) - 16))
    tx, ty = x + 32 * F, y + 26 * F
    if highlight is not None and highlight[1] > 0:
        word, p = highlight; padl, padr = 5 * F, 5.5 * F
        for i, ln in enumerate(lines):
            mt = re.search(r"\b%s\b" % re.escape(word), ln)
            if mt:
                left = tx + dr.textlength(ln[:mt.start()], font=fnt) - padl
                wd = dr.textlength(mt.group(0), font=fnt) + padl + padr
                top = ty + i * lh + 0.02 * size * F
                dr.rounded_rectangle([left, top, left + max(2, min(1, p) * wd), top + 1.28 * size * F], radius=min(3 * F, min(1, p) * wd / 2), fill=HL + (255,))
                break
    text_block(lay, (tx, ty), text, fnt, w - 64 * F, lh, nchars=nchars)
    return (x, y, x + w, y + hgt)


# ------------------------------------------------------------------ s4 and s6 (§4.7.2, §4.7.3)
LETTER1 = "Dear Uncle, what can I cook tonight with eggs and spinach? Love, Sam"
REPLY = "A spinach omelette. Wilt the spinach in butter, pour in three beaten eggs, fold it over and serve."
REPLY_DOTS = 0.4          # measured: the bold "..." shows from 0.4 s until the first character (0.6 s)

def scene_reply(lt, static=False):
    """s4 on the yellow sheet. static=True: everything typed, cursor showing (the outgoing frame of w5)."""
    lt = twos(lt)
    lay = blank()
    hb = prompt_box(lay, (240 * F, 150 * F), 800 * F, LETTER1, 28)
    org = (244 * F, hb[3] + 40 * F); fnt = font("serif_b", 34 * F); lh = 48 * F      # measured: 72 px between the reply's lines
    if static:
        text_block(lay, org, REPLY, fnt, 800 * F, lh, cursor=True)
    elif lt >= REPLY_TYPE[0] or lt > REPLY_DOTS:
        m = int((lt - REPLY_TYPE[0]) * REPLY_TYPE[1])
        if m <= 0:
            text_block(lay, org, "…", fnt, 800 * F, lh)
        else:   # the cursor blinks at 1 Hz on the scene clock (measured: on for the first half of each second)
            text_block(lay, org, REPLY, fnt, 800 * F, lh, nchars=min(m, len(REPLY)), cursor=int(lt * 2) % 2 == 0)
    return _f32(comp(load("paper_yellow.jpg"), lay))

Q2 = "Thanks! Can you make it without eggs?"
ANS = "Make what, dear?"

def scene_second(lt, static=False):
    """s6 on the pink sheet. static=True = everything complete (the outgoing frame of w7)."""
    lt = twos(lt)
    lay = blank()
    n = len(Q2) if static else max(0, int((lt - Q2_TYPE[0]) * Q2_TYPE[1]))
    p_it = 1 if static else ease((lt - IT_SWEEP) / 0.4)
    hb = prompt_box(lay, (240 * F, 190 * F), 800 * F, Q2, 30, highlight=("it", p_it), nchars=n)
    org = (244 * F, hb[3] + 44 * F); fnt = font("serif_b", 40 * F); lh = 40 * F * 1.35
    if static or lt > ANS_DOTS:
        m = len(ANS) if static else int((lt - ANS_TYPE[0]) * ANS_TYPE[1])
        if not static and lt < ANS_TYPE[0]: text_block(lay, org, "…", fnt, 800 * F, lh)
        elif m > 0: text_block(lay, org, ANS, fnt, 800 * F, lh, nchars=m)
    return _f32(comp(load("paper_pink.jpg"), lay))


# ------------------------------------------------------------------ paper edges, cards, tape, envelope (§4.8)
def _torn_mask(w, h, M, seed, step=5, amp=1.3, wob=1.2):
    """alpha mask (h+2M x w+2M) of a w x h sheet whose edges are slightly torn: a slow wobble plus short ragged jags"""
    r = np.random.default_rng(1000 + seed)
    def edge(n):
        k = n // step + 3
        jag = ndi.gaussian_filter1d(r.standard_normal(k), 0.7) * amp
        slow = ndi.gaussian_filter1d(r.standard_normal(k), 8) ; slow = slow / (slow.std() + 1e-6) * wob
        return np.interp(np.arange(n), np.arange(k) * step, jag + slow)
    top, bot = edge(w), edge(w); lef, rig = edge(h), edge(h)
    Hh, Ww = h + 2 * M, w + 2 * M
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    xi = np.clip(xx - M, 0, w - 1).astype(int); yi = np.clip(yy - M, 0, h - 1).astype(int)
    d = np.minimum.reduce([yy - (M + top[xi]), (M + h + bot[xi]) - yy, xx - (M + lef[yi]), (M + w + rig[yi]) - xx])
    return np.clip(d + 0.5, 0, 1).astype(np.float32), d

def _sheet_image(w, h, M, seed, paper, shadow=(0.30, 13, 9), rim=0.30):
    """a torn sheet of paper with a deckle lip, a dark hairline rim and a soft drop shadow, as RGBA (unroughened)"""
    a, d = _torn_mask(w, h, M, seed)
    ink = np.array(INK, np.float32) / 255
    sa, ss, soff = shadow
    sh = ndi.shift(ndi.gaussian_filter(a, ss), (soff, 1.5), order=1) * sa       # soft drop shadow, mostly downward
    hair = ndi.gaussian_filter(a, 1.2) * rim                                     # the hairline just outside the edge
    shadow_a = np.clip(np.maximum(sh, hair) * (1 - a), 0, 1)
    pap = np.array(paper, np.float32) / 255
    lip = np.clip(1 - np.abs(d - 1.2) / 1.2, 0, 1)[..., None] * 0.55            # the bright torn fibre lip
    col = pap[None, None, :] * (1 - lip) + np.array([0.99, 0.97, 0.93], np.float32) * lip
    alpha = a + shadow_a
    rgb = (col * a[..., None] + ink * shadow_a[..., None]) / np.maximum(alpha, 1e-6)[..., None]
    out = np.dstack([rgb, alpha]); return out

def _marker(dr, x0, x1, top, bot, p, seed):
    """a marker sweep from x0 to x0 + p (x1 - x0), with slightly irregular top and bottom edges"""
    if p <= 0: return
    r = np.random.default_rng(300 + seed)
    xe = x0 + (x1 - x0) * min(1.0, p)
    n = max(2, int((x1 - x0) / 14) + 2)
    xs = np.linspace(x0, x1, n)
    tj = r.uniform(-2.0, 2.0, n); bj = r.uniform(-2.0, 2.0, n)
    keep = xs < xe
    pts = [(x0, top + tj[0])] + [(x, top + tj[i]) for i, x in enumerate(xs) if keep[i] and i > 0]
    pts += [(xe, top + np.interp(xe, xs, tj) + 1), (xe + 2, (top + bot) / 2), (xe, bot + np.interp(xe, xs, bj) - 1)]
    pts += [(x, bot + bj[i]) for i, x in reversed(list(enumerate(xs))) if keep[i] and i > 0] + [(x0, bot + bj[0])]
    dr.polygon(pts, fill=HL + (255,))

CARD_CACHE = {}
def card(text_lines, w, rot, label=None, bold=False, size=30, marks=None, seed=0, anchors=None):
    """a letter card: lays out first, draws marker sweeps {phrase: progress} via regex \\b...\\b, roughens, draws text,
    rotates, and optionally returns word anchors (left, right, top, bottom) mapped through the rotation.
    anchors: list of words whose (left, right, mid-y) positions in the rotated image are returned as well."""
    key = (repr(text_lines), int(w), rot, label, bold, size, repr(sorted((marks or {}).items())), seed)
    fs = size * F
    if key not in CARD_CACHE:
        M = 40; padx, pady = 42 * F, 42 * F                 # measured against the reference: text inset 63 px, label 63 px down
        lh, pgap = 1.48 * fs, 0.62 * fs
        lab_f = font("mono", 13 * F); lab_tr = 13 * F * 0.14; lab_h = 13 * F * 1.25 + 5.5 * F
        tw = w - 2 * padx
        meas = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        items = []                                           # (font, text, x, y) per laid-out line
        y = M + pady + (lab_h if label else 0)
        for k, tl in enumerate(text_lines):
            st, tx = ("r", tl) if isinstance(tl, str) else tl
            fnt = font("serif_i" if st == "i" else ("serif_b" if bold else "serif"), fs)
            if k: y += pgap
            for ln in wrap(meas, tx, fnt, tw):
                items.append((fnt, ln, M + padx, y)); y += lh
        h = int(round(y - M + pady - 1))                     # measured paper heights: 252 / 321 / 204 px
        def find(word):
            for fnt, ln, x, yy_ in items:
                mt = re.search(r"\b%s\b" % re.escape(word), ln)
                if mt:
                    x0 = x + meas.textlength(ln[:mt.start()], font=fnt)
                    return x0, x0 + meas.textlength(mt.group(0), font=fnt), yy_
            return None
        arr = _sheet_image(int(w), h, M, seed, CARD_PAPER)
        im = Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
        dr = ImageDraw.Draw(im)
        for i, (ph, p) in enumerate((marks or {}).items()):
            f_ = find(ph)
            if f_:
                x0, x1, yy_ = f_
                _marker(dr, x0 - 5, x1 + 7, yy_ + 0.05 * fs, yy_ + 1.25 * fs, p, seed * 10 + i)
        im = rough(im, 0.8, 12, seed=101 + seed, fine=0.15)
        dr = ImageDraw.Draw(im)
        if label: tracked(dr, (M + padx, M + pady), label, lab_f, CARD_LABEL, lab_tr)
        for fnt, ln, x, yy_ in items: dr.text((x, yy_), ln, font=fnt, fill=INK)
        W0, H0 = im.size
        out = im.rotate(rot, expand=True, resample=Image.BICUBIC)
        W1, H1 = out.size; ar = math.radians(rot)
        def rp(px, py):
            dx, dy = px - W0 / 2, py - H0 / 2
            return (W1 / 2 + dx * math.cos(ar) + dy * math.sin(ar), H1 / 2 - dx * math.sin(ar) + dy * math.cos(ar))
        CARD_CACHE[key] = (out, find, rp)
    out, find, rp = CARD_CACHE[key]
    if anchors is None: return out
    res = {}
    for word in anchors:
        f_ = find(word)
        if f_:
            x0, x1, yy_ = f_; ym = yy_ + 0.62 * fs
            res[word] = dict(left=rp(x0, ym), right=rp(x1, ym), top=rp((x0 + x1) / 2, yy_ + 0.05 * fs), bottom=rp((x0 + x1) / 2, yy_ + 1.25 * fs))
    return out, res

def tape(w, h, rot, seed):
    """a strip of paper tape: translucent, torn ends"""
    r = np.random.default_rng(500 + seed)
    m = 6; Hh, Ww = h + 2 * m, w + 2 * m
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    def end(n):                                              # a ragged short end: zig-zag tear plus a slight slant
        z = ndi.gaussian_filter1d(r.standard_normal(n // 2 + 2), 0.6) * 1.8
        return np.interp(np.arange(n), np.arange(len(z)) * 2, z) + np.linspace(-1, 1, n) * r.uniform(-3, 3)
    yi = np.clip(yy - m, 0, h - 1).astype(int)
    le, ri = end(h), end(h)
    d = np.minimum.reduce([xx - (m + 2 + le[yi]), (m + w - 2 + ri[yi]) - xx, yy - m + 0.5, (m + h - 0.5) - yy])
    a = np.clip(d + 0.5, 0, 1)
    fib = ndi.gaussian_filter(r.standard_normal((Hh, Ww)), (0.6, 5.0)); fib /= fib.std() + 1e-6   # faint lengthwise fibres
    blot = ndi.gaussian_filter(r.standard_normal((Hh, Ww)), 6); blot /= blot.std() + 1e-6
    base = np.array(TAPE[:3], np.float32)
    shade = (-4.0 + 1.6 * fib + 1.4 * blot)[..., None]                        # measured: tape reads a touch darker than its flat colour
    rgb = np.clip(base + shade, 0, 255)
    alpha = a * (TAPE[3] + 6 * blot)
    im = Image.fromarray(np.dstack([rgb, np.clip(alpha, 0, 255)]).astype(np.uint8), "RGBA")
    return im.rotate(rot, expand=True, resample=Image.BICUBIC)

def envelope(w=320):
    """the letter as an envelope sprite (w px wide, aspect ~1.55): paper, thin border, flap V, lower folds, red stamp,
    soft shadow. Use ENV (roughened) for the standard 320 px sprite."""
    h = int(round(w / 1.55)); m = int(0.12 * w)
    S = 3; Ws, Hs = (w + 2 * m) * S, (h + 2 * m) * S
    big = Image.new("RGBA", (Ws, Hs), (0, 0, 0, 0)); dr = ImageDraw.Draw(big)
    x0, y0, x1, y1 = m * S, m * S, (m + w) * S, (m + h) * S
    lw = max(1, int(round(w / 160))) * S
    dr.rectangle([x0, y0, x1, y1], fill=ENV_PAPER + (255,), outline=ENV_FOLD + (255,), width=lw)
    cx, cy = (x0 + x1) / 2, y0 + 0.60 * (y1 - y0)
    dr.line([(x0, y1), (cx - 0.04 * (x1 - x0), y0 + 0.52 * (y1 - y0))], fill=ENV_FOLD + (255,), width=lw)
    dr.line([(x1, y1), (cx + 0.04 * (x1 - x0), y0 + 0.52 * (y1 - y0))], fill=ENV_FOLD + (255,), width=lw)
    dr.line([(x0 + lw, y0 + lw), (cx, cy), (x1 - lw, y0 + lw)], fill=ENV_FLAP + (255,), width=lw, joint="curve")
    sw, sh_ = 0.13 * (x1 - x0), 0.25 * (y1 - y0); sx1, sy0 = x1 - 0.07 * (x1 - x0), y0 + 0.07 * (x1 - x0)
    st = Image.new("RGBA", big.size, (0, 0, 0, 0))
    ImageDraw.Draw(st).rectangle([sx1 - sw, sy0, sx1, sy0 + sh_], fill=ENV_STAMP)
    big.alpha_composite(st)
    im = big.resize((w + 2 * m, h + 2 * m), Image.LANCZOS)
    a = np.asarray(im.getchannel("A"), np.float32) / 255
    sh = ndi.shift(ndi.gaussian_filter(a, max(2.0, w / 40)), (w / 45, w / 90), order=1) * 0.22 * (1 - a)
    rgb = np.asarray(im.convert("RGB"), np.float32)
    ink = np.array(INK, np.float32)
    al = a + sh
    rgb = (rgb * a[..., None] + ink * sh[..., None]) / np.maximum(al, 1e-6)[..., None]
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.clip(al * 255, 0, 255)]).astype(np.uint8), "RGBA")

ENV = rough(envelope(320), 0.6, 10, seed=7, fine=0.15)


# ------------------------------------------------------------------ the ink arrow (§4.8.5, recovered)
def ink_arrow(lay, pts, prog, seed=5, width=3.6):
    """a hand-drawn ink arrow along a curve, drawn on progressively; head appears when the line arrives"""
    if prog <= 0: return
    r = np.random.default_rng(seed); n = 90
    us = np.linspace(0, 1, n)
    if len(pts) == 4: P = np.array([bez(*pts, u) for u in us])
    else:             # a smooth Catmull-Rom curve through the waypoints, resampled evenly along its length
        Q = np.array(pts, np.float64); Q = np.vstack([2 * Q[0] - Q[1], Q, 2 * Q[-1] - Q[-2]]); fine_ = []
        for i in range(1, len(Q) - 2):
            p0, p1_, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
            for u in np.linspace(0, 1, 40, endpoint=False):
                fine_.append(0.5 * (2 * p1_ + (-p0 + p2) * u + (2 * p0 - 5 * p1_ + 4 * p2 - p3) * u * u + (-p0 + 3 * p1_ - 3 * p2 + p3) * u ** 3))
        fine_.append(Q[-2]); fine_ = np.array(fine_)
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(fine_, axis=0), axis=1))])
        P = np.stack([np.interp(us * L[-1], L, fine_[:, c]) for c in range(2)], 1)
        ends = P[[0, -1]].copy(); P = ndi.gaussian_filter1d(P, 3.0, axis=0, mode="nearest")    # round the corners like a hand would
        w_ = np.clip(np.minimum(np.arange(n), n - 1 - np.arange(n)) / 6, 0, 1)[:, None]
        P[:n // 2] = P[:n // 2] * w_[:n // 2] + ends[0] * (1 - w_[:n // 2]); P[n // 2:] = P[n // 2:] * w_[n // 2:] + ends[1] * (1 - w_[n // 2:])
    d = np.gradient(P, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6
    P = P + nrm * (ndi.gaussian_filter(r.standard_normal(n), 4) * 1.6)[:, None]       # a slightly wavering hand
    m = max(2, int(n * min(1, prog)))
    x0, y0 = P.min(0) - 40; x1, y1 = P.max(0) + 40; k = 3
    im = Image.new("RGBA", (int((x1 - x0) * k), int((y1 - y0) * k)), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    Q = [((x - x0) * k, (y - y0) * k) for x, y in P[:m]]
    for j in range(len(Q) - 1):
        wj = width * k * (0.75 + 0.35 * math.sin(j / n * math.pi))
        dr.line([Q[j], Q[j + 1]], fill=INK + (235,), width=int(wj))
        dr.ellipse([Q[j + 1][0] - wj / 2, Q[j + 1][1] - wj / 2, Q[j + 1][0] + wj / 2, Q[j + 1][1] + wj / 2], fill=INK + (235,))
    if prog >= 1:
        tip = np.array(Q[-1]); back = np.array(Q[-6]); v = (tip - back) / (np.linalg.norm(tip - back) + 1e-6)
        for ang in (0.5, -0.5):
            c_, s_ = math.cos(ang), math.sin(ang); wv = np.array([v[0] * c_ - v[1] * s_, v[0] * s_ + v[1] * c_])
            dr.line([tuple(tip), tuple(tip - wv * 17 * F * k)], fill=INK + (235,), width=int(width * k))
    lay.alpha_composite(im.resize((int(x1 - x0), int(y1 - y0)), Image.LANCZOS), (int(x0), int(y0)))


# ------------------------------------------------------------------ s7, the history (§4.8.4, recovered)
C1_ARGS = ([("r", "What can I cook tonight with eggs and spinach?")], 500 * F, 3, "YOUR FIRST LETTER")
C2_ARGS = (["A spinach omelette.", "Wilt the spinach in butter, pour in three beaten eggs…"], 500 * F, -1.5, "HIS REPLY", True)
C3_ARGS = ([("r", "Thanks! Can you make it without eggs?")], 500 * F, 1, "YOUR NEW LETTER")
CARD_POS = [(110 * F - 40, 140 * F - 40), (150 * F - 40, 300 * F - 40), (125 * F - 40, 470 * F - 40)]
ANS2 = "Without eggs? Try spinach and cheese on toast."
CARDS = TAPES = ANC2 = ANC3 = None
CARD_HL = {}

def _history_assets():
    global CARDS, TAPES, ANC2, ANC3
    if CARDS is None:
        CARDS = [card(*C1_ARGS, size=22, seed=1), card(*C2_ARGS, size=22, seed=2), card(*C3_ARGS, size=22, seed=3)]
        _, ANC2 = card(*C2_ARGS, size=22, seed=2, anchors=["omelette", "spinach"])
        _, ANC3 = card(*C3_ARGS, size=22, seed=3, anchors=["it"])
        TAPES = [(tape(120, 36, 6, 1), (110 * F + 300, 140 * F - 26)), (tape(120, 36, -8, 2), (150 * F + 360, 300 * F - 26)),
                 (tape(120, 36, 4, 3), (125 * F + 320, 470 * F - 26))]

def card_marked(i, p_it, p_om):
    key = (i, round(p_it, 2), round(p_om, 2))
    if key not in CARD_HL:
        CARD_HL[key] = card(*C2_ARGS, size=22, seed=2, marks={"spinach omelette": p_om}) if i == 1 else card(*C3_ARGS, size=22, seed=3, marks={"it": p_it})
    return CARD_HL[key]

def arrow_points():
    """waypoints of the it -> omelette arrow (frame px): up out of the middle of "it", right through the clear band
    under his reply, round the card's right edge and back in to the end of "spinach omelette" """
    _history_assets()
    it = ANC3["it"]["top"]; om = ANC2["omelette"]["right"]
    a0 = (CARD_POS[2][0] + it[0], CARD_POS[2][1] + it[1] - 10)      # rises straight out of the middle of "it"
    a3 = (CARD_POS[1][0] + om[0] + 16, CARD_POS[1][1] + om[1])
    R = CARD_POS[1][0] + CARDS[1].width - 20
    ym = (a0[1] - 100 + a3[1]) / 2
    return (a0, (a0[0] + 10, a0[1] - 40), (a0[0] + 100, a0[1] - 68), (R - 30, a0[1] - 76), (R + 30, a0[1] - 90), (R + 62, a0[1] - 116),
            (R + 74, ym), (R + 60, a3[1] + 24), (R + 22, a3[1] + 9), (a3[0] + 90, a3[1] + 3), a3)

def scene_history(t, static=False):
    """s7 on the cream sheet; t = seconds since the start of s7"""
    _history_assets()
    lt = twos(t)
    lay = blank()
    # sweep lengths measured from the reference (the recovered code says 0.45 / 0.5 s, but the v9 render sweeps "it" in
    # two steps and "spinach omelette" in three: 0.79, 1.0 and 0.47, 0.91, 0.99 of the width per step)
    p_it = 1 if static else ease((lt - ANNOT[0]) / 0.17)
    p_ar = 1 if static else (lt - ANNOT[1]) / 0.65
    p_om = 1 if static else ease((lt - ANNOT[2]) / 0.18)
    for i, (c, pos) in enumerate(zip(CARDS, CARD_POS)):
        if i == 1 and p_om > 0: c = card_marked(1, 0, p_om)
        if i == 2 and p_it > 0: c = card_marked(2, p_it, 0)
        p = 1 if static else ease((lt - CARD0 - CARD_GAP * i) / 0.45)
        if p <= 0: continue
        cc = c if p >= 1 else c.resize((int(c.width * (1.08 - 0.08 * p)), int(c.height * (1.08 - 0.08 * p))), Image.LANCZOS)
        x = pos[0] - (cc.width - c.width) / 2; y = pos[1] - (cc.height - c.height) / 2 - 60 * (1 - p)
        if p < 1:
            cc = cc.copy(); cc.putalpha(cc.getchannel("A").point(lambda v: int(v * min(1, p * 2))))
        lay.alpha_composite(cc, (int(x), int(y)))
        tp, tpos = TAPES[i]
        if static or lt > CARD0 + CARD_GAP * i + 0.5: lay.alpha_composite(tp, (int(tpos[0]), int(tpos[1])))
    if p_ar > 0:      # from "it" in the new letter, round to the end of "spinach omelette" in his reply
        ink_arrow(lay, arrow_points(), ease_io(p_ar))
    if static or lt > ANS2_DOTS:
        fnt = font("serif_b", 34 * F); org = (760 * F, 300 * F)
        m = len(ANS2) if static else int((lt - ANS2_TYPE[0]) * ANS2_TYPE[1])
        if not static and lt < ANS2_TYPE[0]: text_block(lay, org, "…", fnt, 420 * F, 34 * F * 1.35)
        elif m > 0: text_block(lay, org, ANS2, fnt, 420 * F, 34 * F * 1.35, nchars=m)
    return _f32(comp(load("paper_cream.jpg"), lay))
