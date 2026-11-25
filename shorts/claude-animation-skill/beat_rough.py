"""Step 3 · rough cut: five flat 9:16 blockouts, full screen, one second each, like a silent cut (5 s).
Built from the clean blockouts (no guides, labels or zones): run `python3 prep.py clean` first."""
from PIL import Image
from lib import tag_p, FPS, Writer, ease, push, step_tag, OUT

order = ["02_s1_tilt", "04_s2_letter_out", "07_s3_reads", "09_s4_reply", "18_s8_reply_home"]
blk = [Image.open(f"{OUT}/clean/blockouts/{n}.png").convert("RGBA") for n in order]

w = Writer(f"{OUT}/beats/s3_rough.mp4")
per = FPS                                   # one second a frame, hard cuts
for i in range(per * len(blk)):
    k, j = divmod(i, per)
    im = push(blk[k], 1 + 0.03 * ease(j / (per - 1)), 540, 960)
    step_tag(im, "Step 3 · rough cut", p=tag_p(i))
    w.add(im)
print("frames", w.close())
