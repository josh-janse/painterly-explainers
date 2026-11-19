"""Side-by-side check sheet of the ep4 backdrops against reference frames -> out/ep4/check_backdrops.jpg

    python3 -m ep4.check_backdrops [REF_VIDEO]

Each row: our plate (left) next to the matching frame of the approved reference video (right). Camera moves and
overlays differ, so compare composition, colours and shapes. The last rows show the derived layers the video builds
by subtraction (cloud = dusk - dusk_nc, light = dusk - dusk_off), the land masks and the uncle layers with geo marks.
Also prints how far the _nc / _off variants differ from the full render outside the clouds / the window light.
"""
import os, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw

from ep4.common import A, W, H, font

REF = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/ref/ep4_v9_track.mp4"
TW, TH = 800, 450
PAIRS = [("dusk.jpg", 120, "dusk  vs  ref 5.000 s"), ("night.jpg", 1512, "night  vs  ref 63.000 s"),
         ("uncle.jpg", 972, "uncle  vs  ref 40.500 s (solid head)"), ("uncle.jpg", 446, "uncle  vs  ref 18.583 s (hole cut live)"),
         ("paper_yellow.jpg", 600, "paper_yellow  vs  ref 25.000 s"), ("paper_pink.jpg", 1008, "paper_pink  vs  ref 42.000 s"),
         ("paper_cream.jpg", 1250, "paper_cream  vs  ref 52.083 s")]


def ref_frame(n):
    cache = os.path.join(A, "ref", f"f{n}.png")
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", REF, "-vf", f"select=eq(n\\,{n})", "-frames:v", "1", cache], check=True)
    return Image.open(cache).convert("RGB")


def arr(name): return np.asarray(Image.open(os.path.join(A, name)).convert("RGB"), np.float32)


def thumb(im): return im.convert("RGB").resize((TW, TH), Image.LANCZOS)


def label(im, text):
    d = ImageDraw.Draw(im); f = font("mono", 20)
    w = d.textlength(text, font=f)
    d.rectangle([8, 8, 20 + w, 38], fill=(238, 238, 236)); d.text((14, 11), text, font=f, fill=(46, 44, 45))
    return im


def main():
    rows = []
    for name, n, text in PAIRS:
        rows.append((label(thumb(Image.open(os.path.join(A, name))), "ours: " + text), label(thumb(ref_frame(n)), f"ref frame {n}")))

    # derived layers
    dusk, nc, off = arr("dusk.jpg"), arr("dusk_nc.jpg"), arr("dusk_off.jpg")
    cloud = np.abs(dusk - nc).max(2); light = np.abs(dusk - off).max(2)
    m = np.load(os.path.join(A, "dusk_masks.npz"))
    wx, wy = m["win"] * np.array([W, H])
    near_win = np.hypot(*np.mgrid[0:H, 0:W][::-1] - np.array([wx, wy])[:, None, None]) < 160
    sea_dashes = (np.arange(H)[:, None] > m["hz"] * H) & (np.abs(np.arange(W)[None, :] - wx) < 260)
    print(f"dusk_nc  vs dusk: max diff {cloud.max():.0f}; outside the sky above y={int(0.5 * H)}: "
          f"{cloud[int(0.5 * H) + 8:].max():.0f} (want ~0: JPEG blocks only)")
    print(f"dusk_off vs dusk: max diff {light.max():.0f}; away from window + reflection: "
          f"{light[~(near_win | sea_dashes)].max():.0f} (want ~0)")
    n_nc = arr("night_nc.jpg"); nd = np.abs(arr("night.jpg") - n_nc).max(2)
    print(f"night_nc vs night: below y={int(0.5 * H)}: {nd[int(0.5 * H) + 8:].max():.0f}")
    vis_c = Image.fromarray(np.clip(cloud * 4, 0, 255).astype(np.uint8)).convert("RGB")
    vis_l = Image.fromarray(np.clip(light * 2, 0, 255).astype(np.uint8)).convert("RGB")
    rows.append((label(thumb(vis_c), "cloud layer |dusk - dusk_nc| x4"), label(thumb(vis_l), "light layer |dusk - dusk_off| x2")))
    land = np.dstack([m["land"], m["land_shape"], np.zeros_like(m["land"])])
    lim = Image.fromarray(land); d = ImageDraw.Draw(lim); d.ellipse([wx - 8, wy - 8, wx + 8, wy + 8], outline=(0, 160, 255), width=3)
    d.line([0, m["hz"] * H, W, m["hz"] * H], fill=(0, 90, 255), width=2)
    rows.append((label(thumb(lim), "masks: R land (faded), G land_shape, blue = hz, win"),
                 label(thumb(Image.fromarray(np.clip(arr("dusk.jpg") * 0.4 + land * 0.6, 0, 255).astype(np.uint8))), "masks over dusk")))

    # uncle layers on a checker with pivot / split / lens / WIN_C
    g = np.load(os.path.join(A, "uncle_geo.npz"))
    chk = ((np.indices((H, W)) // 24).sum(0) % 2 * 40 + 180).astype(np.uint8)
    base = Image.fromarray(np.dstack([chk] * 3)).convert("RGBA")
    fig = Image.open(os.path.join(A, "uncle_fig.png")); col = Image.open(os.path.join(A, "uncle_collar.png"))
    base.alpha_composite(fig); base.alpha_composite(col)
    d = ImageDraw.Draw(base)
    px, py = g["pivot"]; lx, ly = g["lens"]; sp = float(g["split"])
    d.line([0, sp, W, sp], fill=(255, 0, 0), width=2)
    d.ellipse([px - 9, py - 9, px + 9, py + 9], outline=(255, 0, 0), width=3)
    d.ellipse([lx - 6, ly - 6, lx + 6, ly + 6], outline=(0, 200, 255), width=3)
    wc, wr = (537.1, 315.8), 93
    d.ellipse([wc[0] - wr, wc[1] - wr, wc[0] + wr, wc[1] + wr], outline=(255, 220, 0), width=3)
    ub = Image.open(os.path.join(A, "uncle_bg.jpg"))
    rows.append((label(thumb(base), "uncle_fig + collar; red split/pivot, cyan lens, yellow WIN_C r93"), label(thumb(ub), "uncle_bg")))

    sheet = Image.new("RGB", (2 * TW + 30, len(rows) * (TH + 10) + 10), (30, 30, 30))
    for i, (a, b) in enumerate(rows):
        sheet.paste(a, (10, 10 + i * (TH + 10))); sheet.paste(b, (20 + TW, 10 + i * (TH + 10)))
    out = os.path.join(A, "check_backdrops.jpg")
    sheet.save(out, quality=88)
    print("saved", out)


if __name__ == "__main__":
    main()
