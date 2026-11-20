"""Side-by-side check sheet of the ep4 backdrops against reference frames -> out/ep4/check_backdrops.jpg

    python3 -m ep4.check_backdrops [REF_VIDEO]

Each row: our plate (left) next to the matching frame of the approved reference video (right). Camera moves and
overlays differ, so compare composition, colours and shapes. The last rows show the derived layers the video builds
by subtraction (cloud = dusk - dusk_nc, light = dusk - dusk_off), the land masks and the uncle layers with geo marks.
Also prints how far the _nc / _off variants differ from the full render outside the clouds / the window light.

With EP4_FORMAT=reel it checks the 9:16 plates instead -> out/ep4_reel/check_backdrops.jpg: each portrait plate with
the safe box (cyan), the 3:4 grid crop (magenta), the horizon and the focus points drawn over it, next to its blockout
(out/ep4_reel/blockouts/), then the derived layers and masks, then 1:1 crops beside the landscape plates (the uncle
landscape crop is enlarged 1.25x, i.e. what an upscale would have looked like) to judge the paint and paper texture.
"""
import os, subprocess, sys

import numpy as np
from PIL import Image, ImageDraw

from ep4.common import A, A_LANDSCAPE, W, H, ROOT, FORMAT, SAFE, font

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


# ---------------------------------------------------------------------------------------------------- reel (9:16)
GRID = (0, 240, 1080, 1680)
PW, PH = 360, 640                       # panel size (1080 x 1920 / 3)


def _blockout(num):
    """blockout frame NN from out/ep4_reel/blockouts (frame 18 is drawn on the fly by scripts/reel_blockouts.py)"""
    d = os.path.join(A, "blockouts")
    for f in sorted(os.listdir(d)):
        if f.startswith(f"{num:02d}_"): return Image.open(os.path.join(d, f)).convert("RGB")
    import importlib.util
    spec = importlib.util.spec_from_file_location("reel_blockouts", os.path.join(ROOT, "scripts", "reel_blockouts.py"))
    rb = importlib.util.module_from_spec(spec); spec.loader.exec_module(rb)
    for n, slug, when, cap, fn in rb.FRAMES:
        if n == num: return rb.overlays(fn().convert("RGBA"), n, when, cap).convert("RGB")
    raise FileNotFoundError(f"blockout {num}")


def _guides(im, hz=None, rings=()):
    im = im.convert("RGB").copy(); d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = SAFE
    d.rectangle([x0, y0, x1, y1], outline=(0, 200, 230), width=6)
    for y in (GRID[1], GRID[3]):
        for x in range(0, W, 46): d.line([x, y, x + 28, y], fill=(230, 0, 200), width=5)
    if hz is not None: d.line([0, hz, W, hz], fill=(40, 90, 255), width=3)
    for (cx, cy, r, col) in rings: d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=5)
    return im


def _panel(im, text):
    p = im.convert("RGB").resize((PW, PH), Image.LANCZOS)
    d = ImageDraw.Draw(p); f = font("mono", 15)
    w = d.textlength(text, font=f)
    d.rectangle([4, PH - 28, 14 + w, PH - 4], fill=(238, 238, 236)); d.text((9, PH - 25), text, font=f, fill=(46, 44, 45))
    return p


def reel_main():
    import json
    rows = []
    mD = np.load(os.path.join(A, "dusk_masks.npz")); mN = np.load(os.path.join(A, "night_masks.npz"))
    hzD = float(mD["hz"]) * H; wD = tuple(mD["win"] * np.array([W, H]))
    hzN = float(mN["hz"]) * H; wN = tuple(mN["win"] * np.array([W, H]))
    g = np.load(os.path.join(A, "uncle_geo.npz"))
    lay = json.load(open(os.path.join(A, "layout.json")))["_meta"]
    wc, wr = lay["WIN_C"], lay["WIN_R"]
    win_ring = lambda w: [(w[0], w[1], 22, (255, 200, 0))]
    op = lambda n: Image.open(os.path.join(A, n))
    pairs = [
        (_guides(op("dusk.jpg"), hzD, win_ring(wD)), f"dusk  hz {hzD:.0f}  win ({wD[0]:.0f},{wD[1]:.0f})", 3),
        (_guides(op("dusk_off.jpg"), hzD, win_ring(wD)), "dusk_off (window dark)", 2),
        (_guides(op("night.jpg"), hzN, win_ring(wN)), f"night  win ({wN[0]:.0f},{wN[1]:.0f})", 18),
        (_guides(op("uncle.jpg"), None, [(wc[0], wc[1], wr, (255, 200, 0))]), "uncle  (yellow = WIN_C, r 116)", 6),
        (None, "uncle layers", 7),
        (_guides(op("paper_yellow.jpg")), "paper_yellow (landscape sheet, 90 deg)", 9),
        (_guides(op("paper_pink.jpg")), "paper_pink", 14),
        (_guides(op("paper_cream.jpg")), "paper_cream", 16),
        (_guides(op("dusk_nc.jpg"), hzD), "dusk_nc (no clouds)", 1),
    ]
    # uncle layers on a checker with pivot / split / lens / WIN_C
    chk = ((np.indices((H, W)) // 24).sum(0) % 2 * 40 + 180).astype(np.uint8)
    base = Image.fromarray(np.dstack([chk] * 3)).convert("RGBA")
    base.alpha_composite(op("uncle_body.png").convert("RGBA")); base.alpha_composite(op("uncle_head.png").convert("RGBA"))
    base.alpha_composite(op("uncle_collar.png").convert("RGBA"))
    d = ImageDraw.Draw(base)
    px, py = g["pivot"]; lx, ly = g["lens"]; sp = float(g["split"])
    d.line([0, sp, W, sp], fill=(255, 0, 0), width=3)
    d.ellipse([px - 12, py - 12, px + 12, py + 12], outline=(255, 0, 0), width=4)
    d.ellipse([lx - 8, ly - 8, lx + 8, ly + 8], outline=(0, 200, 255), width=4)
    d.ellipse([wc[0] - wr, wc[1] - wr, wc[0] + wr, wc[1] + wr], outline=(255, 220, 0), width=4)
    pairs[4] = (_guides(base), f"head+body+collar  pivot ({px:.0f},{py:.0f}) split {sp:.0f}", 7)
    for im, text, bnum in pairs:
        rows.append((_panel(im, "ours: " + text), _panel(_blockout(bnum), f"blockout {bnum:02d}")))

    # derived layers and masks
    arr_ = lambda n: np.asarray(op(n).convert("RGB"), np.float32)
    dusk, nc, off = arr_("dusk.jpg"), arr_("dusk_nc.jpg"), arr_("dusk_off.jpg")
    cloud = np.abs(dusk - nc).max(2); light = np.abs(dusk - off).max(2)
    yy, xx = np.mgrid[0:H, 0:W]
    near_win = np.hypot(xx - wD[0], yy - wD[1]) < 160
    sea_dashes = (yy > hzD) & (np.abs(xx - wD[0]) < 200)
    print(f"dusk_nc  vs dusk: max diff {cloud.max():.0f}; below the hill top (y > {int(wD[1]) - 80}): "
          f"{cloud[int(wD[1]) - 80:].max():.0f} (want ~0: JPEG blocks only)")
    print(f"dusk_off vs dusk: max diff {light.max():.0f}; away from window + reflection: "
          f"{light[~(near_win | sea_dashes)].max():.0f} (want ~0)")
    nd = np.abs(arr_("night.jpg") - arr_("night_nc.jpg")).max(2)
    print(f"night_nc vs night: below y={int(hzN) - 300}: {nd[int(hzN) - 300:].max():.0f}")
    vis_c = Image.fromarray(np.clip(cloud * 4, 0, 255).astype(np.uint8)).convert("RGB")
    vis_l = Image.fromarray(np.clip(light * 2, 0, 255).astype(np.uint8)).convert("RGB")
    land = np.dstack([mD["land"], mD["land_shape"], np.zeros_like(mD["land"])])
    lim = Image.fromarray(land); dl = ImageDraw.Draw(lim)
    dl.ellipse([wD[0] - 12, wD[1] - 12, wD[0] + 12, wD[1] + 12], outline=(0, 160, 255), width=4)
    dl.line([0, hzD, W, hzD], fill=(0, 90, 255), width=3)
    over = Image.fromarray(np.clip(dusk * 0.4 + land * 0.6, 0, 255).astype(np.uint8))
    rows.append((_panel(vis_c, "cloud |dusk - dusk_nc| x4"), _panel(vis_l, "light |dusk - dusk_off| x2")))
    rows.append((_panel(lim, "masks R land G land_shape"), _panel(over, "masks over dusk")))

    # 1:1 crops beside landscape (texture check): cottage, hill toe, head, paper corner
    L_ = lambda n: Image.open(os.path.join(A_LANDSCAPE, n)).convert("RGB")
    ow = PW * 2 + 10
    def crop_pair(a, b, ta, tb):
        a = a.resize((PW, PH // 2), Image.NEAREST) if a.size != (PW, PH // 2) else a
        b = b.resize((PW, PH // 2), Image.NEAREST) if b.size != (PW, PH // 2) else b
        im = Image.new("RGB", (PW, PH), (30, 30, 30)); im.paste(a, (0, 0)); im.paste(b, (0, PH // 2))
        dd = ImageDraw.Draw(im); f = font("mono", 14)
        for (t, y) in ((ta, 4), (tb, PH // 2 + 4)):
            dd.rectangle([4, y, 10 + dd.textlength(t, font=f), y + 20], fill=(238, 238, 236)); dd.text((7, y + 2), t, font=f, fill=(46, 44, 45))
        return im
    cx, cy = int(wD[0]), int(wD[1])
    lw = tuple(np.load(os.path.join(A_LANDSCAPE, "dusk_masks.npz"))["win"] * np.array([1920, 1080]))
    c1 = crop_pair(op("dusk.jpg").convert("RGB").crop((cx - 180, cy - 90, cx + 180, cy + 230)).crop((0, 0, 360, 320)),
                   L_("dusk.jpg").crop((int(lw[0]) - 180, int(lw[1]) - 90, int(lw[0]) + 180, int(lw[1]) + 230)),
                   "reel cottage 1:1", "landscape cottage 1:1")
    inv = lambda x, y: (int(round(393 + (x - 60) / 1.25)), int(round(172 + (y - 600) / 1.25)))   # reel px -> landscape px
    c2 = crop_pair(op("uncle.jpg").convert("RGB").crop((300, 700, 660, 1020)),
                   L_("uncle.jpg").crop(inv(300, 700) + inv(660, 1020)).resize((360, 320), Image.LANCZOS),
                   "reel head 1:1 (repainted 1.25x)", "landscape head x1.25 (upscale)")
    c3 = crop_pair(op("night.jpg").convert("RGB").crop((cx - 180, cy - 90, cx + 180, cy + 230)),
                   L_("night.jpg").crop((int(lw[0]) - 180, int(lw[1]) - 90, int(lw[0]) + 180, int(lw[1]) + 230)),
                   "reel night 1:1", "landscape night 1:1")
    c4 = crop_pair(op("dusk.jpg").convert("RGB").crop((0, 960, 360, 1280)), L_("dusk.jpg").crop((600, 440, 960, 760)),
                   "reel hill toe / horizon 1:1", "landscape hill toe 1:1")
    rows.append((c1, c2)); rows.append((c3, c4))

    per = 3                                  # pairs per row
    nrow = (len(rows) + per - 1) // per
    gap = 12
    sheet = Image.new("RGB", (per * (2 * PW + gap) + (per + 1) * gap * 2, nrow * (PH + gap) + gap + 50), (28, 28, 30))
    dd = ImageDraw.Draw(sheet)
    dd.text((gap * 2, 12), "EP4 REEL BACKDROPS 1080 x 1920  |  cyan safe box  magenta 3:4 grid  blue horizon  yellow focus",
            font=font("mono", 24), fill=(240, 240, 240))
    for i, (a, b) in enumerate(rows):
        r, c = divmod(i, per)
        x = gap * 2 + c * (2 * PW + gap + gap * 2); y = 50 + r * (PH + gap)
        sheet.paste(a, (x, y)); sheet.paste(b, (x + PW + gap, y))
    out = os.path.join(A, "check_backdrops.jpg")
    sheet.save(out, quality=88)
    print("saved", out)


if __name__ == "__main__":
    reel_main() if FORMAT == "reel" else main()
