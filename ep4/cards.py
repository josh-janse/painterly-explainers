"""Cards, tags and the paper scenes of ep4 (SPEC §4.4.4-4.4.5, §4.7, §4.8).

    title_reveal(lt, dur) -> RGBA layer        the single title tag folding in / wiping out (s1)
    scene_reply(lt, static=False) -> f32       s4, yellow: Sam's letter in a prompt box, the reply types
    scene_second(lt, static=False) -> f32      s6, pink: the second letter types, "...", "Make what, dear?", "it" swept
    scene_history(t, static=False) -> f32      s7, cream: three taped letters, it -> omelette annotation, the new reply
    envelope(w), ENV, tape(w, h, rot, seed)    art other modules use

Positions, sizes and fonts come from the per-format tables in ep4/layout.py (`L.TITLE`, `L.S4`, `L.S6`, `L.S7`,
`L.LETTER`, `L.CARD_TYPE`): the landscape values are the original 1280-space numbers times F, verbatim (the landscape
render is pixel-identical); the reel values are output px from docs/REEL_LAYOUT.md. Overlays step on twos (§1.3): every
scene samples its local clock through twos(). Edge roughness uses the softened v9 amounts (§4.8.1).
"""
import math
import re

import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw

from ep4 import layout as L
from ep4.common import (W, H, F, REEL, INK, HL, TAG_LIGHT, CARD_PAPER, CARD_LABEL, TAPE, ENV_PAPER, ENV_FLAP, ENV_FOLD,
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

def tag_block(lines, px, pos, pad, gap, track_em, fg, bg):
    """several mono lines in ONE boxed tag (the reel title), top-left at pos; px = output px, pad = (x, y) px, gap =
    extra px between lines (line height 1.25 em). Returns the RGBA layer and the y (frame px) where each line after the
    first begins (half-way through the gap above it), for per-line timing."""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    fnt = font("mono", px); tr = px * track_em; lh = px * 1.25
    tw = max(sum(dr.textlength(c, font=fnt) + tr for c in s) - tr for s in lines)
    padx, pady = pad
    bw, bh = tw + 2 * padx, len(lines) * lh + (len(lines) - 1) * gap + 2 * pady
    x, y = pos
    key = (int(bw), int(bh), tuple(bg))
    if key not in TAGC:
        m = 8; bi = Image.new("RGBA", (int(bw) + 2 * m, int(bh) + 2 * m), (0, 0, 0, 0))
        ImageDraw.Draw(bi).rectangle([m, m, m + bw, m + bh], fill=tuple(bg))
        TAGC[key] = rough(bi, 0.6, 10, seed=31 + len(TAGC), fine=0.1)
    lay.alpha_composite(TAGC[key], (int(x) - 8, int(y) - 8))
    for i, s in enumerate(lines):
        tracked(dr, (x + padx, y + pady + i * (lh + gap) + 1), s, fnt, fg, tr)
    splits = [int(round(y + pady + i * (lh + gap) - gap / 2)) for i in range(1, len(lines))]
    return lay, splits

TITLE_TEXT = "THE UNCLE WHO ONLY READS LETTERS"
TITLE_LAY = None
_TITLE_BOX = None
_TITLE_SPLITS = []
def title_reveal(lt, dur):
    """the title folds in: the tag grows from its left edge in stepped, ragged jumps (on twos); on the way out it is
    wiped away left to right the same way. One tag only (owner change 2: no "EPISODE 4"). Reel: one two-line tag,
    the second line's fold-in lagging L.TITLE["line_delay"]; the wipe-out takes both lines together."""
    global TITLE_LAY, _TITLE_BOX, _TITLE_SPLITS
    TI = L.TITLE
    if TITLE_LAY is None:
        if len(TI["lines"]) == 1:
            TITLE_LAY = tag([(TI["lines"][0], TI["px"] / F, TI["fg"], TI["bg"])], TI["pos"], TI["anchor"])
        else:
            TITLE_LAY, _TITLE_SPLITS = tag_block(TI["lines"], TI["px"], TI["pos"], TI["pad"], TI["line_gap"],
                                                 TI["track_em"], TI["fg"], TI["bg"])
        a = np.asarray(TITLE_LAY.getchannel("A"))
        ys, xs = np.nonzero(a > 0); _TITLE_BOX = (xs.min(), xs.max() + 1, ys.min(), ys.max() + 1)
    x0, x1, y0, y1 = _TITLE_BOX
    lt = twos(lt); span = x1 - x0 + 24
    if lt <= 0 or lt >= dur: return blank()
    r = np.random.default_rng(int(lt * 12) + 3)
    band = np.repeat(r.uniform(-1, 1, (y1 - y0) // 5 + 2), 5)[: y1 - y0] * 5 * F   # ragged leading edge, re-cut every frame
    p_in = ease(lt / 0.42); p_out = ease((lt - (dur - 0.42)) / 0.36)
    edge_in = x0 - 12 + p_in * (span + 12) + band * (p_in < 1)
    for k, ys_ in enumerate(_TITLE_SPLITS):                      # later lines fold in a beat behind
        p2 = ease((lt - TI["line_delay"] * (k + 1)) / 0.42); j = ys_ - y0
        edge_in[j:] = x0 - 12 + p2 * (span + 12) + band[j:] * (p2 < 1)
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

def text_block(lay, xy, text, fnt, width, lh, fill=INK, nchars=None, cursor=False, cur=(6 * F, 9 * F)):
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
        dr.rectangle([cx + cur[0], cy + 0.12 * lh, cx + cur[1], cy + 0.88 * lh], fill=fill)     # cur = (gap, gap + width)
    return lines

PBC = {}
def prompt_geom(text, w, c):
    """(font, wrapped lines, line height, box height) of the prompt box for text in a box w px wide; c = L.S4 / L.S6"""
    fnt = font("sans", c["box_px"])
    lines = wrap(ImageDraw.Draw(Image.new("RGBA", (8, 8))), text, fnt, w - 2 * c["box_pad"][0])
    lh = c["box_px"] * c["box_lh_em"]
    return fnt, lines, lh, len(lines) * lh + 2 * c["box_pad"][1] - c["box_trim_em"] * c["box_px"]

def prompt_box(lay, xy, w, text, c, highlight=None, nchars=None):
    """the chat prompt box: a hand-wavy rounded outline (cached, roughened) with text typed into it. Its height comes
    from the full text so it doesn't grow while typing. highlight = (word, p): a marker sweep behind the word.
    c = the scene's layout table (L.S4 / L.S6): font px, padding, radius, outline, highlight padding."""
    dr = ImageDraw.Draw(lay); fnt, lines, lh, hgt = prompt_geom(text, w, c)
    px = c["box_px"]
    x, y = xy
    key = (int(w), int(hgt))
    if key not in PBC:
        m = 16; bi = Image.new("RGBA", (int(w) + 2 * m, int(hgt) + 2 * m), (0, 0, 0, 0))
        ImageDraw.Draw(bi).rounded_rectangle([m, m, m + w, m + hgt], radius=c["box_radius"], outline=INK + (255,), width=c["box_outline"])
        PBC[key] = rough(bi, 0.55, 14, seed=61 + len(PBC), fine=0.05)          # v8 softened (v7: 0.9, fine 0.1)
    lay.alpha_composite(PBC[key], (int(x) - 16, int(y) - 16))
    tx, ty = x + c["box_pad"][0], y + c["box_pad"][1]
    if highlight is not None and highlight[1] > 0:
        word, p = highlight; padl, padr = c.get("hl_pad", (5 * F, 5.5 * F))
        for i, ln in enumerate(lines):
            mt = re.search(r"\b%s\b" % re.escape(word), ln)
            if mt:
                left = tx + dr.textlength(ln[:mt.start()], font=fnt) - padl
                wd = dr.textlength(mt.group(0), font=fnt) + padl + padr
                top = ty + i * lh + 0.02 * px
                dr.rounded_rectangle([left, top, left + max(2, min(1, p) * wd), top + c.get("hl_h_em", 1.28) * px], radius=min(3 * F, min(1, p) * wd / 2), fill=HL + (255,))
                break
    text_block(lay, (tx, ty), text, fnt, w - 2 * c["box_pad"][0], lh, nchars=nchars)
    return (x, y, x + w, y + hgt)

def _group_y(c, text, w, gap, n_after, after_lh, after_px):
    """top of the prompt box: the table's box y, or (reel) the box + answer group centred on c["group_cy"]"""
    if c["group_cy"] is None: return c["box_xy"][1]
    hgt = prompt_geom(text, w, c)[3]
    return int(c["group_cy"] - (hgt + gap + (n_after - 1) * after_lh + after_px * 1.2) / 2)


# ------------------------------------------------------------------ s4 and s6 (§4.7.2, §4.7.3)
LETTER1 = "Dear Uncle, what can I cook tonight with eggs and spinach? Love, Sam"
REPLY = "A spinach omelette. Wilt the spinach in butter, pour in three beaten eggs, fold it over and serve."
REPLY_DOTS = 0.4          # measured: the bold "..." shows from 0.4 s until the first character (0.6 s)

def scene_reply(lt, static=False):
    """s4 on the yellow sheet. static=True: everything typed, cursor showing (the outgoing frame of w5)."""
    lt = twos(lt)
    lay = blank(); c = L.S4
    fnt = font("serif_b", c["reply_px"]); lh = c["reply_lh"]; mw = c["reply_measure"]   # landscape measured: 72 px between the reply's lines
    nrep = len(wrap(ImageDraw.Draw(lay), REPLY, fnt, mw))
    y0 = _group_y(c, LETTER1, c["box_w"], c["reply_gap"], nrep, lh, c["reply_px"])
    hb = prompt_box(lay, (c["box_xy"][0], y0), c["box_w"], LETTER1, c)
    org = (c["reply_dx"], hb[3] + c["reply_gap"])
    if static:
        text_block(lay, org, REPLY, fnt, mw, lh, cursor=True, cur=c["cursor"])
    elif lt >= REPLY_TYPE[0] or lt > REPLY_DOTS:
        m = int((lt - REPLY_TYPE[0]) * REPLY_TYPE[1])
        if m <= 0:
            text_block(lay, org, "…", fnt, mw, lh)
        else:   # the cursor blinks at 1 Hz on the scene clock (measured: on for the first half of each second)
            text_block(lay, org, REPLY, fnt, mw, lh, nchars=min(m, len(REPLY)), cursor=int(lt * 2) % 2 == 0, cur=c["cursor"])
    return _f32(comp(load("paper_yellow.jpg"), lay))

Q2 = "Thanks! Can you make it without eggs?"
ANS = "Make what, dear?"

def scene_second(lt, static=False):
    """s6 on the pink sheet. static=True = everything complete (the outgoing frame of w7)."""
    lt = twos(lt)
    lay = blank(); c = L.S6
    n = len(Q2) if static else max(0, int((lt - Q2_TYPE[0]) * Q2_TYPE[1]))
    p_it = 1 if static else ease((lt - IT_SWEEP) / 0.4)
    fnt = font("serif_b", c["ans_px"]); lh = c["ans_lh"]; mw = c["ans_measure"]
    nans = len(wrap(ImageDraw.Draw(lay), ANS, fnt, mw))
    y0 = _group_y(c, Q2, c["box_w"], c["ans_gap"], nans, lh, c["ans_px"])
    hb = prompt_box(lay, (c["box_xy"][0], y0), c["box_w"], Q2, c, highlight=("it", p_it), nchars=n)
    org = (c["ans_dx"], hb[3] + c["ans_gap"])
    if static or lt > ANS_DOTS:
        m = len(ANS) if static else int((lt - ANS_TYPE[0]) * ANS_TYPE[1])
        if not static and lt < ANS_TYPE[0]: text_block(lay, org, "…", fnt, mw, lh)
        elif m > 0: text_block(lay, org, ANS, fnt, mw, lh, nchars=m)
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
def card(text_lines, w, rot, label=None, bold=False, size=30, marks=None, seed=0, anchors=None, spec=None):
    """a letter card: lays out first, draws marker sweeps {phrase: progress} via regex \\b...\\b, roughens, draws text,
    rotates, and optionally returns word anchors (left, right, top, bottom) mapped through the rotation.
    anchors: list of words whose (left, right, mid-y) positions in the rotated image are returned as well.
    spec = None: the landscape card, sizes from `size` (1280-space) times F. spec = dict(px, pad, lh_em, para_em,
    label_px, label_track_em, label_gap, trim_em): every size in output px (the reel; see card_spec())."""
    key = (repr(text_lines), int(w), rot, label, bold, size, repr(sorted((marks or {}).items())), seed, repr(spec))
    fs = size * F if spec is None else spec["px"]
    if key not in CARD_CACHE:
        M = 40
        if spec is None:
            padx, pady = 42 * F, 42 * F                     # measured against the reference: text inset 63 px, label 63 px down
            lh, pgap = 1.48 * fs, 0.62 * fs
            lab_f = font("mono", 13 * F); lab_tr = 13 * F * 0.14; lab_h = 13 * F * 1.25 + 5.5 * F
            trim = 0.0
        else:
            padx = pady = spec["pad"]
            lh, pgap = spec["lh_em"] * fs, spec["para_em"] * fs
            lp = spec["label_px"]; lab_f = font("mono", lp); lab_tr = lp * spec["label_track_em"]; lab_h = lp * 1.25 + spec["label_gap"]
            trim = spec["trim_em"] * fs
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
        h = int(round(y - M + pady - 1 - trim))              # landscape measured paper heights: 252 / 321 / 204 px
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
        CARD_CACHE[key] = (out, find, rp, (M, int(w), h))
    out, find, rp, geom = CARD_CACHE[key]
    if anchors == "geom": return out, rp, geom
    if anchors is None: return out
    res = {}
    for word in anchors:
        f_ = find(word)
        if f_:
            x0, x1, yy_ = f_; ym = yy_ + 0.62 * fs
            res[word] = dict(left=rp(x0, ym), right=rp(x1, ym), top=rp((x0 + x1) / 2, yy_ + 0.05 * fs), bottom=rp((x0 + x1) / 2, yy_ + 1.25 * fs))
    return out, res

def card_spec(t):
    """the output-px card spec for a reel layout table (L.S7 or L.LETTER); None in landscape (cards use size * F)"""
    if t.get("pad") is None: return None
    ct, s7 = L.CARD_TYPE, L.S7
    return dict(px=t.get("px", t.get("text_px")), pad=t["pad"], lh_em=t["lh_em"], para_em=t["para_em"],
                label_px=s7["label_px"], label_track_em=s7["label_track_em"], label_gap=ct["label_gap"], trim_em=ct["trim_em"])

LETTER_LINES = [("i", "Dear Uncle,"), ("r", "What can I cook tonight with eggs and spinach?"), ("i", "Love, Sam")]
def letter_card(lines=LETTER_LINES, seed=0):
    """Sam's letter for s3 (ep4/uncle.py) from L.LETTER; landscape = card(lines, 420 * F, -2) exactly"""
    t = L.LETTER
    return card(lines, t["w"], t["rot"], size=t["size_arg"] or 30, seed=seed, spec=card_spec(t))

def __getattr__(name):              # cards.LETTER, built on first use (ep4/uncle.py looks for it)
    if name == "LETTER": return letter_card()
    raise AttributeError(name)

def _tape_strip(w, h, seed):
    """unrotated masking-tape strip (m px margin): float rgb 0-255 and alpha 0-1. Crisp long edges with a faint darker
    line, hand-torn serrated short ends with a lighter, thinner fibre rim, lengthwise fibres and a slight blotchiness."""
    r = np.random.default_rng(500 + seed)
    m = 6; Hh, Ww = h + 2 * m, w + 2 * m
    yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float32)
    def end(n):                                              # a torn short end: fine serration, a few bigger jags, a slant
        saw = np.where(np.arange(n // 2 + 2) % 2, 1.0, -1.0) * r.uniform(0.3, 1.4, n // 2 + 2) + r.normal(0, 0.5, n // 2 + 2)
        jag = ndi.gaussian_filter1d(r.standard_normal(n // 6 + 3), 0.8) * 2.0
        z = np.interp(np.arange(n), np.arange(len(saw)) * 2, saw) + np.interp(np.arange(n), np.arange(len(jag)) * 6, jag)
        return z + np.linspace(-1, 1, n) * r.uniform(-4, 4)
    yi = np.clip(yy - m, 0, h - 1).astype(int)
    le, ri = end(h), end(h)
    d_end = np.minimum(xx - (m + 2 + le[yi]), (m + w - 2 + ri[yi]) - xx)
    d_side = np.minimum(yy - m + 0.5, (m + h - 0.5) - yy)
    a = np.clip(np.minimum(d_end, d_side) + 0.5, 0, 1)
    fib = ndi.gaussian_filter(r.standard_normal((Hh, Ww)), (0.6, 5.0)); fib /= fib.std() + 1e-6   # faint lengthwise fibres
    blot = ndi.gaussian_filter(r.standard_normal((Hh, Ww)), 6); blot /= blot.std() + 1e-6
    rim = np.clip(1 - d_end / 2.5, 0, 1)                    # the torn ends: lighter, thinner fibres
    side = np.clip(1 - np.abs(d_side - 0.8) / 1.0, 0, 1) * (d_end > 1)   # the cut long edges catch a faint dark line
    base = np.array(TAPE[:3], np.float32)
    rgb = base + (1.6 * fib + 1.4 * blot)[..., None] + rim[..., None] * np.array([16, 18, 22], np.float32) - side[..., None] * 14
    alpha = a * (TAPE[3] / 255 + 0.025 * blot + 0.10 * side - 0.22 * rim)
    return np.clip(rgb, 0, 255), np.clip(alpha, 0, 1)

def tape(w, h, rot, seed):
    """a strip of masking tape: translucent, torn ends, rotated rot degrees (centre of the strip = centre of the image)"""
    rgb, a = _tape_strip(w, h, seed)
    im = Image.fromarray(np.dstack([rgb, a * 255]).astype(np.uint8), "RGBA")
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
def ink_arrow(lay, pts, prog, seed=5, width=3.6, head=17 * F):
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
            dr.line([tuple(tip), tuple(tip - wv * head * k)], fill=INK + (235,), width=int(width * k))
    lay.alpha_composite(im.resize((int(x1 - x0), int(y1 - y0)), Image.LANCZOS), (int(x0), int(y0)))


# ------------------------------------------------------------------ s7, the history (§4.8.4, recovered)
S7 = L.S7
S7_SPEC = card_spec(S7)            # None in landscape
S7_SIZE = S7["size_arg"] or 22
C1_ARGS = ([("r", "What can I cook tonight with eggs and spinach?")], S7["card_w"], S7["rots"][0], "YOUR FIRST LETTER")
C2_ARGS = (["A spinach omelette.", "Wilt the spinach in butter, pour in three beaten eggs…"], S7["card_w"], S7["rots"][1], "HIS REPLY", True)
C3_ARGS = ([("r", "Thanks! Can you make it without eggs?")], S7["card_w"], S7["rots"][2], "YOUR NEW LETTER")
CARD_POS = S7["card_pos"]          # sprite top-left per card; reel: computed by _stack() (vertical stack, centred)
ANS2 = "Without eggs? Try spinach and cheese on toast."
ANS2_ORG = S7["ans2_xy"]           # reel: computed by _stack() (below the stack)
CARDS = TAPES = ANC2 = ANC3 = None
CARD_HL = {}
PAPER_BOX = None                   # reel: rotated paper bbox per card (frame px)

# each tape: (position along the card's top edge 0-1, angle relative to the card in degrees, seed). Centred so that
# ~57 % of its width lies on the card and ~43 % on whatever is behind (backdrop, or the card above).
TAPE_SPEC = S7["tape_spec"]        # landscape: tape 3 sits right of "three beaten eggs…" so it covers no words
TAPE_WH = S7["tape_wh"]            # px (not x F); landscape a little larger than the v9 120 x 36 so it reads at 1080p
TAPE_ON = 0.57                 # share of the tape's width on the card it holds
TAPE_PAD = 30

def _card(i, **kw):
    return card(*(C1_ARGS, C2_ARGS, C3_ARGS)[i], size=S7_SIZE, seed=i + 1, spec=S7_SPEC, **kw)

def _taped(c, i, u, dang, seed):
    """the tape for one card as an RGBA sprite in the card image's own frame (offset by -TAPE_PAD): drawn on top of the
    card, straddling its top edge, with a very soft shadow on the side that is off the card only"""
    _, rp, (M, w, h) = _card(i, anchors="geom")
    rot = (C1_ARGS, C2_ARGS, C3_ARGS)[i][2]; tw, th = TAPE_WH
    off = (TAPE_ON - 0.5) * th                                     # the strip's centre sits this far inside the top edge
    cx, cy = rp(M + u * w, M + off)
    tp = tape(tw, th, rot + dang, seed)
    P = TAPE_PAD; Wc, Hc = c.width + 2 * P, c.height + 2 * P
    lay = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    lay.alpha_composite(tp, (int(round(cx + P - tp.width / 2)), int(round(cy + P - tp.height / 2))))
    ta = np.asarray(lay.getchannel("A"), np.float32) / 255
    ca = np.zeros((Hc, Wc), np.float32); ca[P:P + c.height, P:P + c.width] = np.asarray(c.getchannel("A"), np.float32) / 255
    paper = np.clip((ca - 0.45) / 0.45, 0, 1)                      # the card's paper, not its drop shadow
    sh = ndi.shift(ndi.gaussian_filter(np.minimum(ta * 3, 1), 3.0), (1.6, 0.8), order=1) * 0.17 * (1 - paper) * (1 - ta)
    ink = np.array(INK, np.float32)
    trgb = np.asarray(lay.convert("RGB"), np.float32)
    al = ta + sh * (1 - ta)
    rgb = (trgb * ta[..., None] + ink * (sh * (1 - ta))[..., None]) / np.maximum(al, 1e-6)[..., None]
    return Image.fromarray(np.dstack([np.clip(rgb, 0, 255), np.clip(al * 255, 0, 255)]).astype(np.uint8), "RGBA")

def _stack():
    """reel: the three cards stacked top to bottom (paper left edges S7["card_x"], each tucked S7["card_overlap"] px
    under the one above), the new reply below card 3; cards + reply centred on S7["stack_cy"]. Sets CARD_POS,
    PAPER_BOX and ANS2_ORG."""
    global CARD_POS, PAPER_BOX, ANS2_ORG
    fnt = font("serif_b", S7["ans2_px"])
    nrep = len(wrap(ImageDraw.Draw(Image.new("RGBA", (8, 8))), ANS2, fnt, S7["ans2_measure"]))
    def place(y_top):
        y = y_top; pos, boxes = [], []
        for i, c in enumerate(CARDS):
            _, rp, (M, w, h) = _card(i, anchors="geom")
            y -= S7["card_overlap"][i]
            ox = S7["card_x"][i] - M - (c.width - (w + 2 * M)) / 2; oy = y - M - (c.height - (h + 2 * M)) / 2
            cs = [rp(M, M), rp(M + w, M), rp(M + w, M + h), rp(M, M + h)]
            pos.append((int(round(ox)), int(round(oy))))
            boxes.append((min(ox + q[0] for q in cs), min(oy + q[1] for q in cs), max(ox + q[0] for q in cs), max(oy + q[1] for q in cs)))
            y += h
        org = (L.CARD_TYPE["ans2_x"], boxes[2][3] + S7["ans2_gap"])
        bottom = org[1] + (nrep - 1) * S7["ans2_lh"] + S7["ans2_px"] * 1.2
        return pos, boxes, org, bottom
    pos, boxes, org, bottom = place(0)
    y_top = int(S7["stack_cy"] - (bottom - boxes[0][1]) / 2)
    CARD_POS, PAPER_BOX, ANS2_ORG = place(y_top)[:3]

def _history_assets():
    global CARDS, TAPES, ANC2, ANC3
    if CARDS is None:
        CARDS = [_card(0), _card(1), _card(2)]
        _, ANC2 = _card(1, anchors=["omelette", "spinach"])
        _, ANC3 = _card(2, anchors=["it"])
        TAPES = [_taped(c, i, u, da, sd) for i, (c, (u, da, sd)) in enumerate(zip(CARDS, TAPE_SPEC))]
        if CARD_POS is None: _stack()

def card_marked(i, p_it, p_om):
    key = (i, round(p_it, 2), round(p_om, 2))
    if key not in CARD_HL:
        CARD_HL[key] = _card(1, marks={"spinach omelette": p_om}) if i == 1 else _card(2, marks={"it": p_it})
    return CARD_HL[key]

def arrow_points():
    """waypoints of the it -> omelette arrow (frame px): up out of the middle of "it", right through the clear band
    under his reply, round the card's right edge and back in to the end of "spinach omelette" """
    _history_assets()
    it = ANC3["it"]["top"]; om = ANC2["omelette"]["right"]
    if S7["arrow_waypoints"] is not None:          # reel: the REEL_LAYOUT loop, rebuilt from the anchors
        a0 = (CARD_POS[2][0] + it[0], CARD_POS[2][1] + it[1] - 12)
        a3 = (CARD_POS[1][0] + om[0] + 22, CARD_POS[1][1] + om[1])
        R = PAPER_BOX[1][2]; band = PAPER_BOX[2][1] - 4          # card 2's right edge; the clear strip above card 3
        return (a0, (a0[0] + 8, a0[1] - 34), (a0[0] + 70, band - 10), (R - 40, band - 12), (R + 30, band - 34),
                (R + 56, (band + a3[1]) / 2), (R + 40, a3[1] + 20), (R + 6, a3[1] + 6), (a3[0] + 70, a3[1] + 2), a3)
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
        tp = TAPES[i]                     # the tape lands with its card: same scale, offset and fade, drawn right after it
        if p < 1:
            sx, sy = cc.width / c.width, cc.height / c.height
            tp = tp.resize((int(round(tp.width * sx)), int(round(tp.height * sy))), Image.LANCZOS)
            fade = lambda v: int(v * min(1, p * 2))
            cc = cc.copy(); cc.putalpha(cc.getchannel("A").point(fade)); tp.putalpha(tp.getchannel("A").point(fade))
        else: sx = sy = 1
        lay.alpha_composite(cc, (int(x), int(y)))
        lay.alpha_composite(tp, (int(x) - int(round(TAPE_PAD * sx)), int(y) - int(round(TAPE_PAD * sy))))
    if p_ar > 0:      # from "it" in the new letter, round to the end of "spinach omelette" in his reply
        ink_arrow(lay, arrow_points(), ease_io(p_ar), width=S7["arrow_width"], head=S7["arrow_head"])
    if static or lt > ANS2_DOTS:
        fnt = font("serif_b", S7["ans2_px"]); org = ANS2_ORG; mw, lh = S7["ans2_measure"], S7["ans2_lh"]
        m = len(ANS2) if static else int((lt - ANS2_TYPE[0]) * ANS2_TYPE[1])
        if not static and lt < ANS2_TYPE[0]: text_block(lay, org, "…", fnt, mw, lh)
        elif m > 0: text_block(lay, org, ANS2, fnt, mw, lh, nchars=m)
    return _f32(comp(load("paper_cream.jpg"), lay))
