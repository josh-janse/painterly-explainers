import sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

DPI = int(sys.argv[1]) if len(sys.argv) > 1 else 100
OUT = sys.argv[2] if len(sys.argv) > 2 else f"out_{DPI}.png"
PAGE_MM = globals().get('PAGE_MM', (297, 420))     # A3 portrait unless a script overrides it
W = int(round(PAGE_MM[0] / 25.4 * DPI)); H = int(round(PAGE_MM[1] / 25.4 * DPI))
K = DPI / 300.0            # scale factor relative to 300 dpi
SEED = globals().get('SEED', 7)
rng = np.random.default_rng(SEED)
f32 = np.float32
print("canvas", W, H)

# ---- layouts must not change with DPI (RULES 56) ----
# Drafts are approved at 80 dpi, so every draw whose count or shape would follow the canvas size is pinned to the 80 dpi
# page: the shared rng makes exactly the draws an 80 dpi render makes (so every later mark lands in the same place), noise
# grids are laid out on the 80 dpi page, and random picks from a mask are made on the 80 dpi grid. At 80 dpi every helper
# below is exactly the old code path.
REF_DPI = 80
AT_REF = DPI == REF_DPI
K_REF = REF_DPI / 300.0
W_REF = int(round(PAGE_MM[0] / 25.4 * REF_DPI)); H_REF = int(round(PAGE_MM[1] / 25.4 * REF_DPI))

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def fastblur(a, s):
    if s < 3: return ndi.gaussian_filter(a, s)
    f = s / 2.0
    small = ndi.zoom(a, 1 / f, order=1)
    small = ndi.gaussian_filter(small, 2.0)
    out = ndi.zoom(small, (a.shape[0] / small.shape[0], a.shape[1] / small.shape[1]), order=1)
    return out[:a.shape[0], :a.shape[1]].astype(f32)

def zoom_ref(n, s):
    """cubic upsample of a noise grid laid out on the 80 dpi page (s = 80 dpi px per cell, scalar or (sy, sx)) onto this
    canvas: the same field in page coordinates at every DPI (to within a pixel). At 80 dpi this is ndi.zoom(n, s)."""
    if AT_REF: return ndi.zoom(n, s, order=3)
    s = np.broadcast_to(np.asarray(s, float), (2,))
    n80 = [int(round(a * b)) for a, b in zip(n.shape, s)]                       # the size ndi.zoom makes at 80 dpi
    out = [int(round((m - 1) * c / c80)) + 1 for m, c, c80 in zip(n80, (H, W), (H_REF, W_REF))]
    z = ndi.zoom(n, [o / a for o, a in zip(out, n.shape)], order=3)
    if z.shape[0] < H or z.shape[1] < W:
        z = np.pad(z, ((0, max(0, H - z.shape[0])), (0, max(0, W - z.shape[1]))), mode="edge")
    return z

def lowfreq(scale_px, seed, octaves=3):
    r = np.random.default_rng(seed); acc = np.zeros((H, W), f32); amp = 1; tot = 0
    sr = scale_px if AT_REF else round(scale_px * REF_DPI / DPI, 9)              # cell size in 80 dpi px (rounded: 6 * K * 3.75 * 80 / DPI must stay 6)
    for o in range(octaves):
        s = max(2, sr / (2 ** o))
        n = r.standard_normal((int(H_REF / s) + 3, int(W_REF / s) + 3)).astype(f32)
        n = ndi.gaussian_filter(n, 0.8)
        z = zoom_ref(n, s)[:H, :W]
        acc += amp * z; tot += amp; amp *= 0.5
    acc /= tot; acc /= acc.std() + 1e-6
    return acc

# ---------- real scanned textures (Poly Haven, CC0) ----------
def load_detail(path, hp_sigma, scale):
    a = np.array(Image.open(path)).astype(f32)
    if a.ndim == 3: a = a[..., :3].mean(2)
    a = a - ndi.gaussian_filter(a, hp_sigma, mode="wrap")      # scans are tileable: wrap, no edge seams
    a /= a.std() + 1e-6
    a0_shape = a.shape
    if scale != 1:
        a = ndi.zoom(a, scale, order=1, mode="grid-wrap")
    reps = (H // a.shape[0] + 2, W // a.shape[1] + 2)
    t = np.tile(a, reps)
    # offsets drawn over the tile's 80 dpi size (same draws as an 80 dpi render), then scaled: the same offset in mm
    n80 = a.shape if AT_REF or scale == 1 else tuple(int(round(d * scale * REF_DPI / DPI)) for d in a0_shape)
    off = lambda: tuple(int(rng.integers(0, m80) * m // m80) for m, m80 in zip(a.shape, n80))
    oy, ox = off()
    t1 = t[oy:oy + H, ox:ox + W]
    # second copy, flipped and offset, blended through soft noise so the tile repeat can't be read
    t2 = np.tile(a[::-1, ::-1], reps)
    oy, ox = off()
    t2 = t2[oy:oy + H, ox:ox + W]
    m = smooth(-0.6, 0.6, lowfreq(a.shape[0] * 0.7, int(rng.integers(1e6)), 2))
    out = t1 * (1 - m) + t2 * m
    return (out / (out.std() + 1e-6)).astype(f32)

def gen_mottle(scale_px, seed, stretch=2.0):
    """pigment mottle from float noise (no 8-bit terracing, no creases), stretched along the wash"""
    r = np.random.default_rng(seed); a = np.zeros((H, W), f32)
    for s_, amp in [(scale_px, 1.0), (scale_px * 0.42, 0.55), (scale_px * 0.17, 0.3)]:
        sy, sx = max(2, s_ * K_REF * 0.8), max(2, s_ * K_REF * 0.8 * stretch)     # cell size in 80 dpi px
        n = r.standard_normal((int(H_REF / sy) + 3, int(W_REF / sx) + 3)).astype(f32)
        z = zoom_ref(ndi.gaussian_filter(n, 0.8), (sy, sx))[:H, :W]
        a[:z.shape[0], :z.shape[1]] += amp * z
    return a / (a.std() + 1e-6)

# Per-poster materials: each script may define TEX before exec'ing the engine.
TEX = globals().get("TEX", {
    "tooth":  ("tex/white_stucco_Displacement.png", 6, 0.6),
    "mottle": ("tex/plaster_grey_04_Rough.png", 60, 1.2),
    "grain2": ("tex/white_plaster_02_Rough.png", 10, 0.8),
    "linen":  ("tex/rough_linen_Rough.png", 8, 0.5)})
def _load_textures():
    tooth = load_detail(TEX["tooth"][0], TEX["tooth"][1], TEX["tooth"][2] * K)
    if TEX["mottle"][0] == "gen":
        mottle = gen_mottle(TEX["mottle"][1], SEED * 10 + 7, TEX["mottle"][2])
    else:
        mottle = load_detail(TEX["mottle"][0], TEX["mottle"][1], TEX["mottle"][2] * K)
        mottle = fastblur(mottle, 3 * K + 0.5); mottle /= mottle.std() + 1e-6
    grain2 = load_detail(TEX["grain2"][0], TEX["grain2"][1], TEX["grain2"][2] * K)
    linen = load_detail(TEX["linen"][0], TEX["linen"][1], TEX["linen"][2] * K)
    return dict(tooth=tooth, mottle=mottle, grain2=grain2, linen=linen)
_RNG_TEX = rng.bit_generator.state                    # the scans' offsets are the first shared draws: ref_canvas replays them
_TEX_REF = None
globals().update(_load_textures())

# anisotropic bristle-streak source texture (wraps)
def streak_src(n, along, across, seed):
    r = np.random.default_rng(seed)
    t = r.standard_normal((n, n)).astype(f32)
    t = ndi.gaussian_filter(t, (across, along), mode="wrap")
    t2 = ndi.gaussian_filter(r.standard_normal((n, n)).astype(f32), (across * 3, along * 2.5), mode="wrap")
    t = t / t.std() + 0.6 * t2 / t2.std()
    return (t / t.std()).astype(f32)

SRC_FINE = streak_src(1024, 40, 0.9, SEED * 10 + 1)
SRC_BROAD = streak_src(1024, 60, 2.5, SEED * 10 + 2)

def streaks(src, contour=None, angle=0.0, su=1.0, sv=1.0, wob=0.0, seed=0, offs=(0, 0)):
    """sample streak texture along a direction. contour(x_px)->y_px makes streaks follow a curve."""
    out = np.empty((H, W), f32)
    xs = np.arange(W, dtype=f32)
    off = contour(xs) if contour is not None else np.zeros(W, f32)
    wobble = lowfreq(1400 * K, seed + 99, 2) * (wob * 0.15 * K) if wob else None
    step = 256
    for y0 in range(0, H, step):
        y1 = min(H, y0 + step)
        yy, xx = np.mgrid[y0:y1, 0:W].astype(f32)
        v0 = (yy - off[None, :])
        if wobble is not None: v0 = v0 + wobble[y0:y1]
        ca, sa = np.cos(angle), np.sin(angle)
        u = (xx * ca + v0 * sa) / (K * su) + offs[0]
        v = (-xx * sa + v0 * ca) / (K * sv) + offs[1]
        out[y0:y1] = ndi.map_coordinates(src, [v, u], order=1, mode="wrap")
    return out

def brushwork(src, contour=None, su=1.0, sv=1.0, wob=10, seed=0, spread=0.12, patch=450, n=6, cover=0.55, base=0.0):
    """layer n stroke-patches, each with its own angle, offset and pigment offset (C)."""
    r = np.random.default_rng(seed)
    S = streaks(src, contour, base + r.normal(0, spread * 0.3), su, sv, wob, seed, (r.uniform(0, 999), r.uniform(0, 999)))
    C = np.full((H, W), r.uniform(-1, 1), f32)
    for i in range(n):
        Si = streaks(src, contour, base + r.normal(0, spread), su * r.uniform(0.8, 1.25), sv * r.uniform(0.8, 1.25),
                     wob, seed + 7 * i + 3, (r.uniform(0, 999), r.uniform(0, 999)))
        N = lowfreq(patch * K * r.uniform(0.7, 1.4), seed + 13 * i + 1, 3)
        th = np.quantile(N[::8, ::8], 1 - cover * r.uniform(0.6, 1.1))
        m = smooth(th - 0.12, th + 0.12, N + 0.25 * Si)
        S = S * (1 - m) + Si * m
        C = C * (1 - m) + r.uniform(-1, 1) * m
        del Si, N, m
    return S, C


# ======================= per-zone media =======================
PAPER = np.array(globals().get('PAPER_RGB', (241, 233, 217)), f32) / 255
canvas = np.ones((H, W, 3), f32) * PAPER
def rgb(*c): return np.array(c, f32) / 255
X = lambda x: x * W
Y = lambda y: y * H
yy = (np.arange(H, dtype=f32) / H)[:, None]
xx = (np.arange(W, dtype=f32) / W)[None, :]

SS = 4 if W * H < 5e6 else 2           # supersampling factor (anti-aliased edges); lower on very large canvases
EDGE_TOOTH = globals().get("EDGE_TOOTH", 1.0)   # 1.0 = ragged hand-cut edge; lower = cleaner drawn edge

def poly_mask(pts):
    """anti-aliased polygon coverage: drawn at SS x inside the shape's bounding box, then box-filtered down"""
    p = np.array([(float(x), float(y)) for x, y in pts], dtype=np.float64)
    x0 = int(max(0, np.floor(p[:, 0].min()) - 2)); x1 = int(min(W, np.ceil(p[:, 0].max()) + 2))
    y0 = int(max(0, np.floor(p[:, 1].min()) - 2)); y1 = int(min(H, np.ceil(p[:, 1].max()) + 2))
    out = np.zeros((H, W), f32)
    if x1 <= x0 or y1 <= y0: return out
    im = Image.new("L", ((x1 - x0) * SS, (y1 - y0) * SS), 0)
    ImageDraw.Draw(im).polygon([((x - x0) * SS, (y - y0) * SS) for x, y in p], fill=255)
    im = im.reduce(SS)
    out[y0:y1, x0:x1] = np.asarray(im, dtype=f32)[: y1 - y0, : x1 - x0] / 255
    return out

def _min_edge(field):
    """half-width (in field units) that spans ~1.5 px across an edge, so thresholds never alias"""
    gy, gx = np.gradient(field)
    return 0.75 * np.sqrt(gx * gx + gy * gy)

def curve_poly(fy, x0=-0.05, x1=1.05, n=600, bottom=1.1):
    xs = np.linspace(x0, x1, n)
    return [(x * W, fy(x) * H) for x in xs] + [(x1 * W, bottom * H), (x0 * W, bottom * H)]

def ref_grid(a):
    """a canvas-sized map sampled on the 80 dpi page grid (area-weighted when this canvas is finer). At 80 dpi: a itself."""
    if AT_REF: return a
    ry, rx = H / H_REF, W / W_REF
    if ry > 1: a = ndi.gaussian_filter(a, (ry / 12 ** 0.5, rx / 12 ** 0.5))
    gy = (np.arange(H_REF) + 0.5) * ry - 0.5; gx = (np.arange(W_REF) + 0.5) * rx - 0.5
    return ndi.map_coordinates(a, np.meshgrid(gy, gx, indexing="ij"), order=1, mode="nearest").astype(f32)

def ref_nonzero(a, thr=0.5):
    """np.nonzero(a > thr) taken on the 80 dpi grid and returned in this canvas's px, so a random index into it picks
    the same spot at every DPI. At 80 dpi: exactly np.nonzero(a > thr)."""
    ys, xs = np.nonzero(ref_grid(a) > thr)
    if AT_REF: return ys, xs
    return ys * (H / H_REF), xs * (W / W_REF)

class ref_canvas:
    """`with ref_canvas(): M80 = build_mask()` evaluates code as an 80 dpi render would (W, H, K, DPI, SS, xx, yy, X, Y,
    poly_mask, lowfreq all at 80 dpi), so a test that decides whether a draw happens gets the 80 dpi answer exactly, not an
    interpolated one. Only for masks and fields: never touch canvas or the scans inside. The shared rng is put back."""
    KEYS = ("DPI", "W", "H", "K", "SS", "xx", "yy", "AT_REF", "tooth", "mottle", "grain2", "linen")
    def __init__(self, textures=False): self.textures = textures       # textures=True: the paper scans as loaded at 80 dpi too
    def __enter__(self):
        global _TEX_REF
        g = globals(); self.saved = {k: g[k] for k in self.KEYS}; self.state = rng.bit_generator.state
        g.update(DPI=REF_DPI, W=W_REF, H=H_REF, K=K_REF, AT_REF=True, SS=4 if W_REF * H_REF < 5e6 else 2,
                 xx=(np.arange(W_REF, dtype=f32) / W_REF)[None, :], yy=(np.arange(H_REF, dtype=f32) / H_REF)[:, None])
        if self.textures:
            if _TEX_REF is None:                                       # loaded once, with the draws an 80 dpi render made for them
                rng.bit_generator.state = _RNG_TEX; _TEX_REF = _load_textures()
            g.update(_TEX_REF)
        return self
    def __exit__(self, *a):
        if rng.bit_generator.state != self.state: rng.bit_generator.state = self.state
        globals().update(self.saved)

def mask_and_80(region):
    """region: a mask, or a function that builds it from the canvas globals. Returns (mask, the mask as at 80 dpi or None):
    with a function the 80 dpi mask is exact (built again under ref_canvas); with an array it is not known off 80 dpi."""
    if not callable(region): return region, (region if AT_REF else None)
    M = region()
    if AT_REF: return M, M
    with ref_canvas(): M80 = region()
    return M, M80

def pick_list(region, thr=0.5):
    """(mask, ys, xs): the spots inside region as an 80 dpi render lists them, in this canvas's px, so a random index picks
    the same spot at every DPI. Exact when region is a function (see mask_and_80); close (ref_nonzero) for an array."""
    M, M80 = mask_and_80(region)
    if AT_REF: ys, xs = np.nonzero(M > thr)
    elif M80 is None: ys, xs = ref_nonzero(M, thr)
    else:
        ys, xs = np.nonzero(M80 > thr); ys, xs = ys * (H / H_REF), xs * (W / W_REF)
    return M, ys, xs

def grain_normal(shape, shape80, salt):
    """a resolution-sized normal field for fine grain. The shared rng makes the draws an 80 dpi render makes here, so
    nothing after it moves; above or below 80 dpi the field itself comes from its own generator (SEED, salt)."""
    own = np.random.default_rng([SEED, salt])                    # made at every DPI (it draws nothing from rng), so traces line up
    n80 = rng.standard_normal(shape80)
    return n80 if AT_REF else own.standard_normal(shape)

# speckle maps for granular / chalky media
_n1 = ndi.gaussian_filter(grain_normal((H, W), (H_REF, W_REF), 1).astype(f32), 0.5 * K + 0.45); _n1 /= _n1.std()
_n2 = ndi.zoom(ndi.gaussian_filter(grain_normal((H // 3 + 2, W // 3 + 2), (H_REF // 3 + 2, W_REF // 3 + 2), 2).astype(f32), 0.6), 3, order=1)[:H, :W]; _n2 /= _n2.std()
SPK_D = np.clip(smooth(2.1, 2.7, _n1) + 0.8 * smooth(2.5, 3.1, _n2), 0, 1).astype(f32)
SPK_L = np.clip(smooth(2.1, 2.7, -_n1) + 0.8 * smooth(2.5, 3.1, -_n2), 0, 1).astype(f32)
del _n1, _n2
ZERO = np.zeros((H, W), f32)

def paint(mask, c1, c2=None, S=None, C=None, soft=6, wob=10, wob_scale=120, width=0.06, dry=0.25, dry_edge=0.6,
          mot=0.5, rim=0.07, alpha=1.0, seed=0, valvar=0.05, cvar=0.35, gran=0.0, speck=0.0, sd=None, sl=None,
          edge_tex=1.0):
    global canvas
    if S is None: S = ZERO
    sft = fastblur(mask, soft * K + 0.5)
    en = lowfreq(wob_scale * K, seed, 3) * (wob * 0.01) + (tooth * 0.035 + grain2 * 0.02) * edge_tex * EDGE_TOOTH + S * 0.03 * EDGE_TOOTH
    we = np.maximum(width, _min_edge(sft))
    A = smooth(0.5 - we, 0.5 + we, sft + en)
    edgeness = 1 - smooth(0.5, 0.95, sft)
    field = tooth * 0.55 + S * 0.7 + lowfreq(80 * K, seed + 5, 2) * 0.45
    thr = 2.7 - 2.1 * (dry + dry_edge * edgeness)
    A = A * (1 - smooth(thr - 0.35, thr + 0.35, field)) * alpha
    cc = C if C is not None else 0
    if c2 is None: c2 = c1 * 0.93
    m = np.clip(0.5 + 0.22 * mottle * mot + 0.14 * lowfreq(260 * K, seed + 11, 2) + cvar * cc, -0.3, 1.3)[..., None]
    col = c1 * (1 - m) + c2 * m
    val = 1 + valvar * S + 0.015 * grain2
    if gran: val = val * (1 - gran * smooth(0.2, 2.0, -tooth))
    rb = smooth(0.5, 0.58, sft) * (1 - smooth(0.6, 0.9, sft))
    col = col * (val * (1 - rim * rb))[..., None]
    if speck:
        if sd is not None: col = col + (sd - col) * (speck * SPK_D)[..., None]
        if sl is not None: col = col + (sl - col) * (speck * SPK_L)[..., None]
    A = A[..., None]
    canvas = canvas * (1 - A) + col * A


def stroke_layer():
    return Image.new("L", (W, H), 0)

def draw_stroke(dr, pts, w0, w1, p0=1.0, p1=0.4, segs=None):
    pts = np.asarray(pts, f32); n = len(pts)
    d = np.gradient(pts, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6
    t = np.linspace(0, 1, n)
    w = w0 + (w1 - w0) * t
    w *= 1 + 0.18 * np.sin(t * np.pi * rng.uniform(1, 3) + rng.uniform(0, 6))
    L = pts + nrm * w[:, None] / 2; R = pts - nrm * w[:, None] / 2
    step = max(2, n // 6)
    for i in range(0, n - 1, step):
        j = min(n, i + step + 1)
        p = p0 + (p1 - p0) * (i / n)
        poly = [tuple(q) for q in L[i:j]] + [tuple(q) for q in R[i:j][::-1]]
        dr.polygon(poly, fill=int(max(20, p * 255)))

def apply_strokes(layer, c1, c2, S, dry=0.3, soft=1.2, seed=0, mot=0.5, rim=0.06, aa=False):
    global canvas
    P = np.asarray(layer, f32) / 255
    M = smooth(0.0, 0.2, P) if aa else (P > 0).astype(f32)
    sft = fastblur(M, max(soft * K + 0.3, 0.9))
    we = np.maximum(0.125, _min_edge(sft))
    A = smooth(0.475 - we, 0.475 + we, sft + (tooth * 0.05 + S * 0.05) * EDGE_TOOTH)
    Pb = ndi.grey_dilation(P, size=3)
    field = tooth * 0.6 + S * 0.8
    thr = 0.3 + 1.8 * Pb - dry
    A = A * (1 - smooth(thr - 0.3, thr + 0.3, field))
    m = np.clip(0.5 + 0.35 * mottle * mot + 0.25 * lowfreq(120 * K, seed, 2), 0, 1)[..., None]
    col = c1 * (1 - m) + c2 * m
    rb = smooth(0.35, 0.5, sft) * (1 - smooth(0.5, 0.8, sft))
    col = col * (1 + 0.06 * S - rim * rb)[..., None]
    A = A[..., None]
    canvas = canvas * (1 - A) + col * A

def ss_layer():
    """supersampled stroke layer: draw with draw_stroke_ss, then ss_down() and apply_strokes(..., aa=True)"""
    return Image.new("L", (W * SS, H * SS), 0)

def draw_stroke_ss(dr, pts, w0, w1, p0=1.0, p1=0.4):
    draw_stroke(dr, np.asarray(pts, f32) * SS, w0 * SS, w1 * SS, p0, p1)

def ss_down(layer):
    return layer.reduce(SS)

def bez(p0, p1, p2, n=40):
    t = np.linspace(0, 1, n)[:, None]
    return (1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(p1) + t ** 2 * np.array(p2)



def soft_strokes(layer, color, alpha, blur):
    """very soft, low-opacity strokes (sky wisps, haze, shadow sweeps)"""
    global canvas
    P = np.asarray(layer, f32) / 255
    A = fastblur(P, blur * K + 0.5) * alpha
    A = A * (1 - 0.25 * smooth(0.5, 2.0, tooth))
    canvas = canvas + (color - canvas) * A[..., None]

