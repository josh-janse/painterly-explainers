"""Check sheet for ep4/cards.py and ep4/sheets.py against the reference video -> out/ep4/check_cards.jpg

    python3 -m ep4.test_cards [--clip]

Rows: our still (left) | reference frame (right) at the SPEC §8 timestamps for the title, s4, s6, s7 and the wipes
w4-w7, then 3x nearest-neighbour crops (ours above the reference) of a rough card edge, the arrow and the highlight.
The uncle frames under the wipes are stood in by the uncle plate (out/ep4/uncle.jpg); the title is laid on the dusk
plate (the real s1 frame has the camera move). --clip also writes out/ep4/check_s7_annot.mp4 (56.5-61.0 s).

    EP4_FORMAT=reel python3 -m ep4.test_cards            -> out/ep4_reel/check_cards.jpg

Reel (docs/REEL_LAYOUT.md): the real frames from ep4.video at the card/title/wipe moments, with the safe box (green),
the 3:4 grid crop (orange) and the button column (red) drawn on, each beside its blockout (out/ep4_reel/blockouts/),
then 1:1 crops of the smallest text (title tag, s4 reply, s6 highlight, s7 label + tape, arrow at the right edge).
Every text box is also checked against the safe box and the arrow against x 926 (printed).
"""
import os, subprocess, sys, time

import numpy as np
from PIL import Image, ImageDraw

from ep4.common import A, W, H, REEL, font, load, comp, to_pil
from ep4.timeline import T, TITLE
from ep4 import cards, sheets

REF = "/home/claude/ref/ep4_v9_track.mp4"
TW, TH = 800, 450


def ref_frame(n):
    cache = os.path.join(A, "ref", f"f{n}.png")
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", REF, "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", cache], check=True)
    return Image.open(cache).convert("RGB")


def frame(t):
    """our picture at absolute time t, for the segments this module owns"""
    s = lambda k: t - T[k][0]
    uncle = load("uncle.jpg")
    if T["s1"][0] <= t < T["s2"][1]:
        return np.asarray(comp(load("dusk.jpg"), cards.title_reveal(t - TITLE[0], TITLE[1] - TITLE[0])).convert("RGB"), np.float32) / 255
    if T["w4"][0] <= t < T["w4"][1]: return sheets.sheet(uncle, cards.scene_reply(0), (t - T["w4"][0]) / 0.6, "left", 12)
    if T["s4"][0] <= t < T["s4"][1]: return cards.scene_reply(s("s4"))
    if T["w5"][0] <= t < T["w5"][1]: return sheets.sheet(cards.scene_reply(0, static=True), uncle, (t - T["w5"][0]) / 0.7, "down", 13)
    if T["w6"][0] <= t < T["w6"][1]: return sheets.sheet(uncle, cards.scene_second(0), (t - T["w6"][0]) / 0.6, "up", 14)
    if T["s6"][0] <= t < T["s6"][1]: return cards.scene_second(s("s6"))
    if T["w7"][0] <= t < T["w7"][1]: return sheets.sheet(cards.scene_second(0, static=True), cards.scene_history(0), (t - T["w7"][0]) / 0.6, "left", 15)
    if T["s7"][0] <= t < T["s7"][1]: return cards.scene_history(s("s7"))
    raise ValueError(t)


def lab(im, text):
    d = ImageDraw.Draw(im); f = font("mono", 18)
    d.rectangle([0, 0, d.textlength(text, font=f) + 12, 26], fill=(20, 20, 20)); d.text((6, 3), text, font=f, fill=(240, 240, 240))
    return im


FRAMES = [156, 583, 600, 616, 696, 710, 984, 1008, 1104, 1164, 1187, 1272, 1344, 1380, 1416, 1464]
CROPS = [(1464, (160, 190, 400, 330), "card edge + tape (card 1, top-left)"),
         (1464, (590, 560, 1090, 840), "arrow"),
         (1464, (280, 540, 640, 610), "highlight 'spinach omelette'"),
         (1164, (840, 310, 960, 400), "highlight 'it' (s6)"),
         (696, (340, 200, 640, 300), "prompt-box outline"),
         (1187, (1140, 480, 1250, 600), "w7 torn edge")]


def main():
    os.makedirs(A, exist_ok=True)
    rows, ours, times = [], {}, []
    for n in FRAMES:
        t = n / 24; t0 = time.time(); im = to_pil(frame(t)).convert("RGB"); times.append(time.time() - t0)
        ours[n] = im
        row = Image.new("RGB", (2 * TW + 10, TH), (255, 255, 255))
        row.paste(lab(im.resize((TW, TH), Image.LANCZOS), f"ours {t:.3f}s  (f{n})"), (0, 0))
        row.paste(lab(ref_frame(n).resize((TW, TH), Image.LANCZOS), f"ref {t:.3f}s"), (TW + 10, 0))
        rows.append(row)
    for n, (x0, y0, x1, y1), name in CROPS:
        k = 3 if (x1 - x0) <= 270 else (2 if (x1 - x0) <= 400 else 1.6)
        a = ours[n].crop((x0, y0, x1, y1)); b = ref_frame(n).crop((x0, y0, x1, y1))
        sz = (int((x1 - x0) * k), int((y1 - y0) * k))
        row = Image.new("RGB", (2 * TW + 10, max(TH, sz[1])), (255, 255, 255))
        row.paste(lab(a.resize(sz, Image.NEAREST), f"ours {name} {k}x"), (0, 0))
        row.paste(lab(b.resize(sz, Image.NEAREST), f"ref {k}x"), (TW + 10, 0))
        rows.append(row)
    sheet = Image.new("RGB", (2 * TW + 10, sum(r.height + 10 for r in rows)), (255, 255, 255))
    y = 0
    for r in rows: sheet.paste(r, (0, y)); y += r.height + 10
    sheet.save(os.path.join(A, "check_cards.jpg"), quality=86)
    print("frames: mean %.2f s, max %.2f s (first call includes card/tape setup)" % (np.mean(times[1:]), max(times)))
    if "--clip" in sys.argv:
        out = os.path.join(A, "check_s7_annot.mp4")
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24", "-i", "-",
                              "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        t0 = time.time(); ns = range(int(56.5 * 24), int(61.0 * 24) + 1)
        for n in ns: p.stdin.write((np.clip(frame(n / 24), 0, 1) * 255 + 0.5).astype(np.uint8).tobytes())
        p.stdin.close(); p.wait()
        print("clip: %d frames, %.2f s/frame -> %s" % (len(ns), (time.time() - t0) / len(ns), out))


# ------------------------------------------------------------------ reel check sheet
BLOCK = os.path.join(A, "blockouts")
REEL_FRAMES = [(5.8, "03_s1_title"), (6.5, "03_s1_title"), (10.45, "03_s1_title"), (24.4, "08_w4_yellow_from_right"),
               (25.5, "09_s4_reply"), (28.0, "09_s4_reply"), (29.85, "10_w5_yellow_slides_down"), (30.0, "10_w5_yellow_slides_down"),
               (41.2, "13_w6_pink_from_left"), (44.0, "14_s6_make_what"), (47.0, "14_s6_make_what"), (48.5, "14_s6_make_what"),
               (49.7, "15_w7_cream_from_right"), (53.0, "16_s7_cards_drop"), (56.5, "16_s7_cards_drop"),
               (58.5, "17_s7_annotate_reply"), (61.0, "17_s7_annotate_reply"), (61.5, "18_s8_reply_home")]
# (time, crop box, label): 1:1, so the type reads at its real size on a 1080-wide phone
REEL_CROPS = [(6.5, (80, 385, 740, 575), "title tag 46 px"),
              (28.0, (70, 540, 950, 900), "s4 prompt 44 px + reply 56 px"),
              (48.5, (70, 650, 950, 1040), "s6 52 px, 'it' sweep, 76 px answer"),
              (61.0, (60, 280, 960, 640), "s7 card 1: 28 px label, 40 px text, tapes"),
              (61.0, (500, 660, 1080, 1000), "arrow at the right edge (x 926 limit)"),
              (61.0, (60, 1120, 960, 1400), "s7 reply 60 px")]


def overlay(im):
    from ep4 import layout as L
    d = ImageDraw.Draw(im, "RGBA")
    x0, y0, x1, y1 = L.SAFE; d.rectangle([x0, y0, x1, y1], outline=(40, 220, 90, 255), width=3)
    gx0, gy0, gx1, gy1 = L.GRID
    for y in (gy0, gy1): d.line([(0, y), (W, y)], fill=(255, 150, 30, 255), width=3)
    d.rectangle([960, 0, W, H], fill=(255, 60, 60, 40)); d.line([(926, 0), (926, H)], fill=(255, 60, 60, 160), width=1)
    return im


def checks():
    """text boxes vs the safe box, the arrow vs x 926 (from the layer geometry, not the picture)"""
    from ep4 import layout as L
    from PIL import Image as I
    sx0, sy0, sx1, sy1 = L.SAFE
    def bbox(lay):
        a = np.asarray(lay.getchannel("A")); ys, xs = np.nonzero(a > 8)
        return (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    def inside(b): return b[0] >= sx0 and b[1] >= sy0 and b[2] <= sx1 and b[3] <= sy1
    res = []
    lay = cards.title_reveal(2.0, 5.0); res.append(("title tag", bbox(lay)))
    cards._history_assets()
    for i, b in enumerate(cards.PAPER_BOX): res.append((f"s7 card {i + 1} paper", tuple(int(round(v)) for v in b)))
    lay = I.new("RGBA", (W, H), (0, 0, 0, 0)); cards.ink_arrow(lay, cards.arrow_points(), 1.0, width=cards.S7["arrow_width"], head=cards.S7["arrow_head"])
    ab = bbox(lay); res.append(("s7 arrow", ab))
    for name, b in res: print(f"  {name:20s} {b}  {'inside safe box' if inside(b) else 'OUTSIDE SAFE BOX'}")
    print(f"  arrow outermost x {ab[2] - 1} (limit 926): {'ok' if ab[2] - 1 <= 926 else 'TOO FAR'}")


def main_reel():
    from ep4 import video
    TW_, TH_ = 360, 640
    pairs, ours = [], {}
    for t, bk in REEL_FRAMES:
        t0 = time.time(); im = Image.fromarray(video.to_u8(video.frame(t))).convert("RGB"); dt = time.time() - t0
        ours[t] = im
        a = lab(overlay(im.copy()).resize((TW_, TH_), Image.LANCZOS), f"ours {t:.2f}s")
        b = lab(Image.open(os.path.join(BLOCK, bk + ".png")).convert("RGB").resize((TW_, TH_), Image.LANCZOS), bk[:2])
        pr = Image.new("RGB", (2 * TW_ + 4, TH_), (255, 255, 255)); pr.paste(a, (0, 0)); pr.paste(b, (TW_ + 4, 0)); pairs.append(pr)
        print(f"  {t:6.2f} s  {dt:.2f} s")
    per = 3; pw = pairs[0].width + 16
    rows = [pairs[i:i + per] for i in range(0, len(pairs), per)]
    crops = []
    for t, (x0, y0, x1, y1), name in REEL_CROPS:
        c = lab(ours[t].crop((x0, y0, x1, y1)), f"1:1 {name}"); crops.append(c)
    SW = per * pw
    hgt = len(rows) * (TH_ + 12) + sum(c.height + 12 for c in crops)
    sheet = Image.new("RGB", (SW, hgt), (255, 255, 255)); y = 0
    for r in rows:
        for j, pr in enumerate(r): sheet.paste(pr, (j * pw, y))
        y += TH_ + 12
    x = 0; rowh = 0                      # crops flow left to right
    for c in crops:
        if x + c.width > SW: x = 0; y += rowh + 12; rowh = 0
        sheet.paste(c, (x, y)); x += c.width + 12; rowh = max(rowh, c.height)
    sheet = sheet.crop((0, 0, SW, y + rowh))
    out = os.path.join(A, "check_cards.jpg"); sheet.save(out, quality=86); print("wrote", out)
    checks()


if __name__ == "__main__":
    main_reel() if REEL else main()
