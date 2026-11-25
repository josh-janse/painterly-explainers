"""Step 4 · paint: the 9:16 dusk plate painting itself, pass by pass, from bare paper (6 s)."""
import glob
import numpy as np
from PIL import Image
from lib import W, H, FPS, PAPER, Writer, ease, noise_field, push, step_tag, REPO, OUT

snaps = sorted(glob.glob(f"{OUT}/tl/*.jpg"))
load = lambda i: np.asarray(Image.open(snaps[i]).convert("RGB"), np.float32)

# bare paper: the cream ground with the scan's tooth, so the first frame is a sheet, not a flat fill
tex = Image.open(f"{REPO}/engine/tex/Paper001_2K-JPG_Color.jpg").convert("L").resize((W, H))
t = np.asarray(tex, np.float32) / 255; t = (t - t.mean()) * 0.18
paper = np.clip(np.array(PAPER, np.float32)[None, None] * (1 + t[..., None]), 0, 255)

# key states and how many frames each reveal takes (the run's own order: sky, clouds, hills, cottage, sea, strokes)
keys = [(paper, 0), (load(0), 12), (load(6), 10), (load(7), 6), (load(8), 10), (load(11), 6),
        (load(16), 14), (load(18), 12), (load(20), 8), (load(24), 14)]
HOLD_BETWEEN = 2
TOTAL = 6 * FPS

xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]

w = Writer(f"{OUT}/beats/s4_paint.mp4")
frames = []
for k in range(1, len(keys)):
    a, b, n = keys[k - 1][0], keys[k][0], keys[k][1]
    # each pass sweeps in like a brush: a soft noisy front moving left to right and slightly down
    field = 0.55 * noise_field((H // 8, W // 8), 3, 100 + k)
    field = np.asarray(Image.fromarray((field * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), np.float32) / 255
    field = field + 0.35 * xx + 0.10 * yy
    field = (field - field.min()) / (field.max() - field.min())
    for i in range(n):
        p = ease((i + 1) / n) * 1.3 - 0.15
        al = np.clip((p - field) / 0.12 + 0.5, 0, 1)[..., None]
        frames.append(a + (b - a) * al)
    frames += [b] * HOLD_BETWEEN
final = keys[-1][0]
hold = TOTAL - len(frames)
for i, f in enumerate(frames):
    im = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)).convert("RGBA")
    step_tag(im, "Step 4 · paint", p=(i - 4) / 6)
    w.add(im)
fin = Image.fromarray(final.astype(np.uint8)).convert("RGBA")
for i in range(hold):
    z = 1 + 0.045 * ease(i / max(hold - 1, 1))
    im = push(fin, z, 680, 980)
    step_tag(im, "Step 4 · paint", p=1)
    w.add(im)
print("frames", w.close())
