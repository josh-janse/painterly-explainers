"""Step 1 · study: a slow scroll through Josh's swatch book of explainer techniques, recorded at 9:16 (6 s).

Starts at the first technique group, so the page title and the research notes (which name the studio) stay off screen.
"""
import io
import os
from PIL import Image
from playwright.sync_api import sync_playwright
from lib import FPS, Writer, ease, step_tag, OUT

N = 6 * FPS
w = Writer(f"{OUT}/beats/s1_study.mp4")
with sync_playwright() as pw:
    b = pw.chromium.launch(executable_path=os.environ.get("CHROMIUM") or None)
    pg = b.new_page(viewport={"width": 432, "height": 768}, device_scale_factor=2.5, color_scheme="light")
    pg.goto("file://" + os.path.abspath(os.environ["SWATCH_HTML"]))
    pg.wait_for_load_state("networkidle")
    pg.evaluate("document.fonts.ready")
    y0 = pg.evaluate("document.getElementById('g1').getBoundingClientRect().top + scrollY - 10")
    y1 = pg.evaluate("[...document.querySelectorAll('h3')].find(h => h.textContent.startsWith('Muted palette')).getBoundingClientRect().top + scrollY - 300")
    pg.evaluate(f"scrollTo(0,{y0})"); pg.wait_for_timeout(600)
    for i in range(N):
        t = i / (N - 1)
        pg.evaluate(f"scrollTo(0,{y0 + (y1 - y0) * ease(t)})")
        pg.wait_for_timeout(30)
        im = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("RGBA")
        step_tag(im, "Step 1 · study", p=(i - 3) / 6)
        w.add(im)
    b.close()
print("frames", w.close())
