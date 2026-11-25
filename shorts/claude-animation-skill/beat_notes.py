"""Step 5 · notes: four of Josh's notes, word for word from the Episode 4 chat, each on the plate it changed,
with a ringed target and a version counter ticking from v1 to v9 (8 s)."""
import math
import numpy as np
from PIL import Image, ImageDraw
from lib import tag_p, W, H, FPS, INK, HL, CARD, Writer, ease, font, step_tag, push, OUT

P = f"{OUT}/plates"
dusk = Image.open(f"{P}/dusk.jpg").convert("RGBA")
uncle = Image.open(f"{P}/uncle.jpg").convert("RGBA")
LABEL = (109, 106, 111)

# (plate, note verbatim, ring centre, ring radii, card y)
notes = [
    (dusk, "The left side of the hill probably needs to blend into the horizon more cleanly...", (250, 1128), (190, 52), 430),
    (uncle, "There was something about the sharp corners uncle that I liked.", (250, 640), (110, 110), 1110),
    (dusk, "Ok. what are those downward arrows on the water?", (680, 1290), (120, 90), 430),
    (uncle, "The blink should feel less glowy.", (470, 843), (95, 60), 1110),
]

def wrap(d, text, f, width):
    lines, cur = [], ""
    for wd in text.split():
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=f) <= width: cur = t
        else: lines.append(cur); cur = wd
    return lines + [cur]

def card(text, rot):
    f = font("serif", 46); lab = font("mono5", 26)
    tmp = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    lines = wrap(tmp, text, f, 700)
    cw, ch = 780, 70 + 58 * len(lines) + 40
    im = Image.new("RGBA", (cw, ch), CARD + (255,))
    d = ImageDraw.Draw(im)
    d.text((40, 30), "MY NOTE", font=lab, fill=LABEL)
    for j, ln in enumerate(lines):
        d.text((40, 76 + 58 * j), ln, font=f, fill=INK)
    sh = Image.new("RGBA", (cw + 40, ch + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle((24, 28, cw + 24, ch + 28), fill=(0, 0, 0, 60))
    from PIL import ImageFilter
    sh = sh.filter(ImageFilter.GaussianBlur(10)); sh.alpha_composite(im, (20, 20))
    return sh.rotate(rot, resample=Image.BICUBIC, expand=True)

cards = [card(n[1], r) for n, r in zip(notes, (-1.6, 1.2, -1.0, 1.5))]
SEG = 48
w = Writer(f"{OUT}/beats/s5_notes.mp4")
for i in range(SEG * len(notes)):
    I = i
    k, j = divmod(i, SEG)
    plate, _, (cx, cy), (rx, ry), cy_card = notes[k]
    z = 1 + 0.05 * ease(j / (SEG - 1))
    im = push(plate, z, cx, cy)
    # the ring sits where the target lands after the push
    x0 = (W - W / z) * (cx / W) if False else None
    cw0, ch0 = W / z, H / z
    ox = min(max(cx - cw0 / 2, 0), W - cw0); oy = min(max(cy - ch0 / 2, 0), H - ch0)
    tx, ty = (cx - ox) * z, (cy - oy) * z
    d = ImageDraw.Draw(im)
    pr = ease((j - 10) / 12)
    if pr > 0:
        d.arc((tx - rx * z, ty - ry * z, tx + rx * z, ty + ry * z), -100, -100 + 360 * pr, fill=HL, width=6)
    c = cards[k]
    pc = ease(j / 8)
    if pc > 0:
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        layer.alpha_composite(c, ((W - c.width) // 2, int(cy_card - 50 * (1 - pc))))
        if pc < 1:
            a = np.asarray(layer).copy(); a[..., 3] = (a[..., 3] * pc).astype(np.uint8); layer = Image.fromarray(a)
        im.alpha_composite(layer)
    step_tag(im, "Step 5 · notes", p=tag_p(I))
    w.add(im)
print("frames", w.close())
