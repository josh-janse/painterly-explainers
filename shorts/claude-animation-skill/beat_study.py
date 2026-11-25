"""Step 1 · study: three techniques from Josh's swatch book that Episode 4 uses, one at a time, each demo playing
on its own on plain paper (6 s). Only the demo is recorded, so no page text, sources or names come with it.

Needs SWATCH_HTML (the swatch book saved as HTML) and optionally CHROMIUM."""
import io
import os
import numpy as np
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright
from lib import tag_p, W, H, FPS, PAPER, INK, Writer, ease, step_tag, draw_tracked, font, OUT, REPO

# (card title in the swatch book, plain label shown under the demo)
picks = [("Highlighter sweep", "Highlight on the word"),
         ("Paper cut-out with keyline", "Cut paper"),
         ("Camera-blur transition", "Blur between scenes")]
SEG = 2 * FPS

tex = Image.open(f"{REPO}/engine/tex/Paper001_2K-JPG_Color.jpg").convert("L").resize((W, H))
t = (np.asarray(tex, np.float32) / 255 - 0.5) * 0.16
bg = Image.fromarray(np.clip(np.array(PAPER, np.float32)[None, None] * (1 + t[..., None]), 0, 255).astype(np.uint8)).convert("RGBA")

w = Writer(f"{OUT}/beats/s1_study.mp4")
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
    pg = b.new_page(viewport={"width": 432, "height": 900}, device_scale_factor=2.5, color_scheme="light")
    pg.goto("file://" + os.path.abspath(os.environ["SWATCH_HTML"]))
    pg.wait_for_load_state("networkidle")
    pg.evaluate("document.fonts.ready")
    i = 0
    for title, label in picks:
        card = pg.locator("article.card").filter(has=pg.locator("h3", has_text=title)).first
        card.scroll_into_view_if_needed()
        card.locator("button.replay").click()
        stage = card.locator(".stage").first
        for j in range(SEG):
            pg.wait_for_timeout(int(1000 / FPS))
            demo = Image.open(io.BytesIO(stage.screenshot(type="png"))).convert("RGBA")
            s = 960 / demo.width
            demo = demo.resize((960, int(demo.height * s)), Image.LANCZOS)
            im = bg.copy()
            y = (H - demo.height) // 2 - 40
            im.alpha_composite(demo, (60, y))
            d = ImageDraw.Draw(im)
            draw_tracked(d, (60, y + demo.height + 36), label.upper(), font("mono5", 32), (96, 94, 98), 0.08)
            step_tag(im, "Step 1 · study", p=tag_p(i))
            w.add(im); i += 1
    b.close()
print("frames", w.close())
