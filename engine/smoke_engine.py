# Smoke test for the vendored engine. Run from engine/:  python3 smoke_engine.py [DPI] [OUT]
# Execs the core modules in the fixed order, paints one paint() layer and saves a PNG.
import os, sys
D = os.path.dirname(os.path.abspath(__file__))
dpi = sys.argv[1] if len(sys.argv) > 1 else "40"
out = sys.argv[2] if len(sys.argv) > 2 else "out_smoke.png"
sys.argv = [sys.argv[0], dpi, out]

SEED = 7
PAPER_RGB = (247, 241, 228)
EDGE_TOOTH = 0.35
TEX = {"tooth":  ("tex/Paper001_2K-JPG_Displacement.jpg", 5, 0.45),
       "mottle": ("gen", 300, 2.0),
       "grain2": ("tex/Paper002_2K-JPG_Roughness.jpg", 8, 0.6),
       "linen":  ("tex/Paper006_2K-JPG_Roughness.jpg", 8, 0.6)}
exec(open(os.path.join(D, "engine.py")).read())
exec(open(os.path.join(D, "marks.py")).read())
exec(open(os.path.join(D, "figures.py")).read()); exec(open(os.path.join(D, "figures2.py")).read())
exec(open(os.path.join(D, "perspective.py")).read())

# one flat gouache-like block on paper
m = poly_mask([(X(0.15), Y(0.20)), (X(0.85), Y(0.25)), (X(0.80), Y(0.70)), (X(0.20), Y(0.65))])
paint(m, rgb(52, 104, 196), rgb(70, 132, 210), soft=2, wob=0.8, wob_scale=50, width=0.06, dry=0.04, dry_edge=0.45,
      mot=0.4, rim=0.03, seed=101, valvar=0.02, edge_tex=0.9)

Image.fromarray((np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT, dpi=(DPI, DPI))
print("wrote", OUT, canvas.shape)
