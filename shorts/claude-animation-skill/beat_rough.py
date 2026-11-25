"""Step 3 · rough cut: the real v6 test frames on a canvas, then the flat 9:16 blockouts flipping through as a silent cut (5 s)."""
from PIL import Image, ImageDraw
from lib import W, H, FPS, INK, HL, Writer, ease, push, step_tag, REPO, OUT

REF = f"{REPO}/docs/ref/canvas_v6"
BLK = f"{REPO}/out/ep4_reel/blockouts"
CANVAS_BG = (236, 237, 234)

# --- part 1: the test-frames canvas (2 s) ---
names = ["dusk", "uncle", "paper_yellow", "night", "paper_pink", "paper_cream"]
tw, th, gap = 470, 264, 36
x0 = (W - (2 * tw + gap)) // 2
y0 = 540
board = Image.new("RGBA", (W, H), CANVAS_BG + (255,))
dr = ImageDraw.Draw(board)
for i, n in enumerate(names):
    im = Image.open(f"{REF}/{n}.jpg").convert("RGB").resize((tw, th), Image.LANCZOS)
    x = x0 + (i % 2) * (tw + gap); y = y0 + (i // 2) * (th + gap)
    dr.rectangle((x - 2, y - 2, x + tw + 1, y + th + 1), fill=(200, 202, 198))
    board.paste(im, (x, y))
focus = (x0 + tw // 2, y0 + th // 2)            # the dusk frame, top left

# --- part 2: the silent cut (3 s) ---
order = ["01_s1_open_sky", "03_s1_title", "04_s2_letter_out", "06_s3_envelope_lands", "07_s3_reads",
         "09_s4_reply", "12_s5_gone", "16_s7_cards_drop", "18_s8_reply_home"]
blk = [Image.open(f"{BLK}/{n}.png").convert("RGBA") for n in order]

w = Writer(f"{OUT}/beats/s3_rough.mp4")
N1, N2 = 2 * FPS, 3 * FPS
for i in range(N1):
    z = 1.25 + 0.12 * ease(i / (N1 - 1)) + (0.95 * ease((i - 34) / 13) if i > 34 else 0)   # slow drift, then dive into dusk
    im = push(board, z, *focus)
    step_tag(im, "Step 3 · rough cut", p=(i - 3) / 6)
    w.add(im)
per = N2 // len(blk)
for i in range(N2):
    k = min(i // per, len(blk) - 1)
    im = blk[k].copy()
    d = ImageDraw.Draw(im)
    p = (i + 1) / N2
    d.rectangle((60, 1430, 960, 1440), fill=(255, 255, 255, 120))
    d.rectangle((60, 1430, 60 + int(900 * p), 1440), fill=HL + (255,))
    step_tag(im, "Step 3 · rough cut", p=1)
    w.add(im)
print("frames", w.close())
