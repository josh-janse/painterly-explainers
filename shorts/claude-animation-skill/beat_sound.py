"""Step 6 · sound: Episode 4's real voice, effects and sea stems as three lanes scrolling under a playhead (5 s).
Also writes the matching 5 s of the mix (no music) so the lanes line up with what's heard."""
import subprocess
import numpy as np
from PIL import Image, ImageDraw
from scipy.io import wavfile
from lib import tag_p, W, H, FPS, INK, HL, PAPER, Writer, ease, font, step_tag, draw_tracked, REPO, OUT

A = f"{OUT}/audio"
def env(name, hop):
    sr, x = wavfile.read(f"{A}/mix_{name}.wav")
    x = x.astype(np.float32)
    if x.ndim > 1: x = x.mean(1)
    x /= max(np.abs(x).max(), 1)
    n = len(x) // hop
    return sr, np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1))

HOP_S = 1 / 48                                     # one bar every ~21 ms
sr, vo = env("vo", int(48000 * HOP_S))
_, fx = env("fx", int(48000 * HOP_S))
_, amb = env("amb", int(48000 * HOP_S))
# pick the 5 s with the most going on in both voice and effects
win = int(5 / HOP_S)
score = np.convolve(np.minimum(vo / vo.max(), 1) + 2 * np.minimum(fx / max(fx.max(), 1e-6), 1), np.ones(win), "valid")
s0 = int(np.argmax(score[: len(score) - win]))
T0 = s0 * HOP_S
print("window starts at", round(T0, 2), "s")

lanes = [("Voice", vo, INK, 220), ("Effects · real recordings", fx, (214, 120, 40), 200)]
PX_PER_S = 360                                     # scroll speed: the playhead sits at x 540
BAR = PX_PER_S * HOP_S
tex = Image.open(f"{REPO}/engine/tex/Paper001_2K-JPG_Color.jpg").convert("L").resize((W, H))
t = (np.asarray(tex, np.float32) / 255 - 0.5) * 0.16
bg = Image.fromarray(np.clip(np.array(PAPER, np.float32)[None, None] * (1 + t[..., None]), 0, 255).astype(np.uint8)).convert("RGBA")

w = Writer(f"{OUT}/beats/s6_sound.mp4")
N = 5 * FPS
ys = [700, 1060]
for i in range(N):
    I = i
    now = T0 + i / FPS
    im = bg.copy(); d = ImageDraw.Draw(im)
    for (label, e, col, amp), yc in zip(lanes, ys):
        draw_tracked(d, (72, yc - amp // 2 - 64), label.upper(), font("mono5", 30), (90, 88, 92), 0.08)
        ref = np.percentile(e[e > 0], 99) if (e > 0).any() else 1
        k0 = int((now - 540 / PX_PER_S) / HOP_S); k1 = int((now + 540 / PX_PER_S) / HOP_S) + 1
        for k in range(max(k0, 0), min(k1, len(e))):
            x = 540 + (k * HOP_S - now) * PX_PER_S
            h = max(3, min(1.0, e[k] / ref) * amp)
            played = x <= 540
            c = col if played else tuple(int(v * 0.35 + 235 * 0.65) for v in col)
            d.rounded_rectangle((x, yc - h / 2, x + BAR * 0.62, yc + h / 2), radius=2, fill=c)
    d.rectangle((539, 520, 542, 1220), fill=INK)
    step_tag(im, "Step 6 · sound", p=tag_p(I))
    w.add(im)
print("frames", w.close())
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{T0:.3f}", "-t", "5", "-i", f"{A}/mix.wav", "-c:a", "pcm_s16le",
                f"{OUT}/beats/s6_sound.wav"], check=True)
