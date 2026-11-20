"""Check sheet for ep4/cards.py and ep4/sheets.py against the reference video -> out/ep4/check_cards.jpg

    python3 -m ep4.test_cards [--clip]

Rows: our still (left) | reference frame (right) at the SPEC §8 timestamps for the title, s4, s6, s7 and the wipes
w4-w7, then 3x nearest-neighbour crops (ours above the reference) of a rough card edge, the arrow and the highlight.
The uncle frames under the wipes are stood in by the uncle plate (out/ep4/uncle.jpg); the title is laid on the dusk
plate (the real s1 frame has the camera move). --clip also writes out/ep4/check_s7_annot.mp4 (56.5-61.0 s).
"""
import os, subprocess, sys, time

import numpy as np
from PIL import Image, ImageDraw

from ep4.common import A, W, H, font, load, comp, to_pil
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


if __name__ == "__main__":
    main()
