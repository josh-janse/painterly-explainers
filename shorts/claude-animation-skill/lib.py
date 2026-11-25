"""Shared helpers for the Short's beats: 1080 x 1920 at 24 fps, Episode 4's palette and fonts."""
import os
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import scipy.ndimage as ndi

W, H, FPS = 1080, 1920, 24
HERE = Path(__file__).resolve().parent
REPO = str(HERE.parents[1])
OUT = str(HERE / "out")              # gitignored: plates, snapshots, stems, beats, previews
FONTS = os.path.join(REPO, "assets", "fonts")
SAFE = (60, 250, 960, 1470)               # Shorts / Reels safe box, as in docs/REEL_LAYOUT.md
INK = (46, 44, 45)
TAG_LIGHT = (238, 238, 236)
HL = (245, 212, 74)
CARD = (242, 233, 217)
PAPER = (241, 236, 225)

_F = {}
def font(key, px):
    k = (key, int(px))
    if k not in _F:
        _F[k] = ImageFont.truetype(os.path.join(FONTS, f"{key}.ttf"), int(px))
    return _F[k]

def ease(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)

def text_w(dr, s, f, track=0.0):
    if not track:
        return dr.textlength(s, font=f)
    return sum(dr.textlength(c, font=f) for c in s) + track * f.size * (len(s) - 1)

def draw_tracked(dr, xy, s, f, fill, track=0.0):
    x, y = xy
    for c in s:
        dr.text((x, y), c, font=f, fill=fill)
        x += dr.textlength(c, font=f) + track * f.size

def step_tag(img, text, p=1.0, x=72, y=300, px=40, dark=True):
    """Episode 4's tag look: a sharp-cornered block, IBM Plex Mono 500 caps, tracked. p 0..1 wipes it in left to right."""
    if p <= 0:
        return img
    text = text.upper()
    f = font("mono5", px)
    tmp = ImageDraw.Draw(img)
    tw = text_w(tmp, text, f, 0.08)
    padx, pady = int(px * 0.6), int(px * 0.42)
    bw, bh = int(tw + 2 * padx), int(px + 2 * pady)
    tag = Image.new("RGBA", (bw, bh), (INK if dark else TAG_LIGHT) + (255,))
    dr = ImageDraw.Draw(tag)
    draw_tracked(dr, (padx, pady - int(px * 0.12)), text, f, TAG_LIGHT if dark else INK, 0.08)
    vis = int(bw * ease(p))
    if vis < 2:
        return img
    img.alpha_composite(tag.crop((0, 0, vis, bh)), (x, y))
    return img

def tag_p(i, start=3, hold=33):
    """Step labels wipe in, sit for about 1.4 s, then wipe out, so they never compete with the picture."""
    return min(ease((i - start) / 6), ease((start + hold - i) / 6))

def noise_field(shape, sigma, seed):
    r = np.random.default_rng(seed).standard_normal(shape).astype(np.float32)
    r = ndi.gaussian_filter(r, sigma)
    r -= r.min(); r /= max(r.max(), 1e-6)
    return r

class Writer:
    """Pipe RGB frames to ffmpeg as H.264."""
    def __init__(self, path, fps=FPS, w=W, h=H, crf=18):
        self.p = subprocess.Popen(
            ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
             "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-pix_fmt", "yuv420p", path],
            stdin=subprocess.PIPE)
        self.n = 0
    def add(self, frame):
        if isinstance(frame, Image.Image):
            frame = np.asarray(frame.convert("RGB"))
        self.p.stdin.write(np.ascontiguousarray(frame, dtype=np.uint8).tobytes()); self.n += 1
    def close(self):
        self.p.stdin.close(); self.p.wait()
        return self.n

def push(img, z, cx, cy):
    """Zoom an RGB(A) PIL image by z about (cx, cy), keeping the frame size."""
    if z <= 1.0001:
        return img.copy()
    w, h = img.size
    cw, ch = w / z, h / z
    x0 = min(max(cx - cw / 2, 0), w - cw); y0 = min(max(cy - ch / 2, 0), h - ch)
    return img.resize((w, h), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))
