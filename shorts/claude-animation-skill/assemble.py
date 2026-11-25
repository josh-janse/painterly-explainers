"""Silent preview of the Short: Claude's beats in order, placeholders for Josh's hook, step 2 and ending,
and the current voice-over lines burned in at the bottom (preview only) so the timing can be checked."""
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from lib import W, H, FPS, INK, TAG_LIGHT, Writer, font, step_tag, OUT

B = f"{OUT}/beats"
P = f"{OUT}/plates"
segs = [  # (source or placeholder, seconds, VO line as it stands on the storyboard)
    (("ph", "Hook · you film", "Phone at the monitor, tight on the paint with your finger on it, then pull back.", "dusk"), 4,
     "Hook line still to pick."),
    (f"{B}/s1_study.mp4", 6, "One. I pull apart a real explainer I like, frame by frame. How long each shot is, what style is used."),
    (("ph", "Step 2 · story · your call", "Visual to decide.", "uncle"), 7,
     "Two. Story. This is really important. Spend time here and the rest will fall into place."),
    (f"{B}/s3_rough.mp4", 5, "Three. Rough frames and a silent cut so I could check the feel."),
    (f"{B}/s4_paint.mp4", 6, "Four. I painted out the scenes with an engine I'd previously built for this purpose."),
    (f"{B}/s5_notes.mp4", 8, "Five, notes. Lots of them. I went through 9 iterations before I was happy."),
    (f"{B}/s6_sound.mp4", 5, "Six, sound. I went through three voices, and swapped the fake sound effects for real recordings."),
    (("ph", "Ending · you film", "Phone at the monitor, finger following the letter home.", "dusk"), 6, "Ending line still to pick."),
]

def frames_of(path, n):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    for _ in range(n):
        buf = p.stdout.read(W * H * 3)
        if len(buf) < W * H * 3: break
        yield Image.fromarray(np.frombuffer(buf, np.uint8).reshape(H, W, 3)).convert("RGBA")
    p.stdout.close(); p.wait()

def placeholder(title, sub, plate, n):
    bg = Image.open(f"{P}/{plate}.jpg").convert("RGB").filter(ImageFilter.GaussianBlur(6))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (30, 30, 32)), 0.55).convert("RGBA")
    d = ImageDraw.Draw(bg)
    f = font("sans", 44)
    words, lines, cur = sub.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) <= 860: cur = t
        else: lines.append(cur); cur = wd
    lines.append(cur)
    for j, ln in enumerate(lines):
        d.text((90, 760 + 60 * j), ln, font=f, fill=TAG_LIGHT)
    for _ in range(n):
        im = bg.copy(); step_tag(im, title, p=1, x=90, y=640, px=40, dark=False); yield im

def vo_caption(im, text):
    d = ImageDraw.Draw(im)
    f = font("sans", 34); lab = font("mono5", 22)
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) <= 900: cur = t
        else: lines.append(cur); cur = wd
    lines.append(cur)
    y = 1560
    d.rectangle((40, y - 16, W - 40, y + 40 + 46 * len(lines)), fill=(20, 20, 22, 210))
    d.text((60, y - 4), "VO, PREVIEW ONLY", font=lab, fill=(200, 196, 190))
    for j, ln in enumerate(lines):
        d.text((60, y + 30 + 46 * j), ln, font=f, fill=(250, 248, 244))
    return im

w = Writer(f"{OUT}/preview_silent.mp4")
offsets, t = [], 0.0
for src, secs, vo in segs:
    n = secs * FPS; offsets.append(t); t += secs
    gen = placeholder(*src[1:], n) if isinstance(src, tuple) else frames_of(src, n)
    k = 0
    for im in gen:
        w.add(vo_caption(im, vo)); k += 1
    while k < n:   # pad if a clip runs short
        w.add(vo_caption(im, vo)); k += 1
print("frames", w.close(), "seconds", t)
sound_at = offsets[6]
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{OUT}/preview_silent.mp4", "-i", f"{B}/s6_sound.wav",
                "-filter_complex", f"[1:a]adelay={int(sound_at*1000)}|{int(sound_at*1000)},apad[a]", "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
                f"{OUT}/short_preview_v1.mp4"], check=True)
print("wrote short_preview_v1.mp4")
