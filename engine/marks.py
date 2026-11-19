import os
# Extra mark-making vocabulary (exec'd after engine.py, shares its globals).
# Each poster mixes these differently so the series shares a hand but not a surface.
from scipy.special import ndtri

SRC_CRAYON = streak_src(512, 7, 1.1, SEED * 10 + 5)          # short, stubby crayon marks

def load_colour_detail(path, hp_sigma, scale, seed=0):
    """high-passed RGB detail of a real scan (coloured paper fibres), tiled to canvas"""
    a = np.array(Image.open(path).convert("RGB")).astype(f32) / 255
    a = a - np.stack([ndi.gaussian_filter(a[..., i], hp_sigma, mode='wrap') for i in range(3)], -1)
    if scale != 1: a = ndi.zoom(a, (scale, scale, 1), order=1)
    r = np.random.default_rng(seed)
    t = np.tile(a, (H // a.shape[0] + 2, W // a.shape[1] + 2, 1))
    oy, ox = r.integers(0, a.shape[0]), r.integers(0, a.shape[1])
    return t[oy:oy + H, ox:ox + W].astype(f32)

def pastel_sky(stops_y, stops_c, seed, coverage=0.86, band_wobble=0.025, under=0.55, angle=-0.2):
    """Crayon / soft-pastel gradient: an even pale underlayer, then pigment caught on the
    paper's peaks, so tiny flecks of lighter colour show through. Open, not streaky."""
    global canvas
    yw = (yy + band_wobble * lowfreq(700 * K, seed, 2) * (0.4 + yy)).astype(f32)
    col = np.stack([np.interp(yw, stops_y, [c[i] for c in stops_c]) for i in range(3)], -1).astype(f32) / 255
    base = col * (1 - under) + PAPER * under
    cray = streaks(SRC_CRAYON, angle=angle, su=0.55, sv=0.55, seed=seed + 1)
    f = tooth * 1.0 + cray * 0.35 + lowfreq(160 * K, seed + 2, 3) * 0.18 + lowfreq(30 * K, seed + 3, 2) * 0.12
    cov = coverage + 0.03 * lowfreq(500 * K, seed + 4, 2)                 # patches of lighter pressure
    thr = ndtri(np.clip(1 - cov, 0.01, 0.99)).astype(f32) * f.std()
    A = smooth(thr - 0.25, thr + 0.25, f)[..., None]
    canvas = base * (1 - A) + col * A
    canvas = canvas * (1 + 0.025 * mottle * 0.5)[..., None]

def scumble(mask, color, coverage, seed, angle=-0.2, scale=1.0):
    """light dry-crayon pass over an area (pigment only on paper peaks)"""
    global canvas
    cray = streaks(SRC_CRAYON, angle=angle, su=0.6 * scale, sv=0.6 * scale, seed=seed)
    f = tooth * 0.8 + cray * 0.5 + lowfreq(90 * K, seed + 1, 2) * 0.4
    thr = ndtri(np.clip(1 - coverage, 0.01, 0.99)) * f.std()
    A = (smooth(thr - 0.2, thr + 0.2, f) * mask)[..., None]
    canvas = canvas * (1 - A) + color * A

def riso(mask, color, density, seed, size=1.5, alpha=1.0):
    """Risograph-style coloured speckle; density can be a scalar or a per-pixel map (0-1)."""
    global canvas
    r = np.random.default_rng(seed)
    n = ndi.gaussian_filter(r.standard_normal((H, W)).astype(f32), size * K + 0.35); n /= n.std() + 1e-6
    thr = ndtri(np.clip(1 - np.asarray(density, f32), 0.0005, 0.9995)).astype(f32)
    A = (smooth(thr - 0.12, thr + 0.12, n) * mask * alpha)[..., None]
    canvas = canvas * (1 - A) + color * A

def dash_tuft(dr, cx, cy, n, h, lean, fan=1.1, wd=None):
    """grass as a fan of straight, blunt dashes (stamped look), not tapered curves"""
    wd = wd or max(1.2, h * 0.07)
    for i in range(n):
        a = lean + (i / max(1, n - 1) - 0.5) * fan + rng.normal(0, 0.07)
        L = h * rng.uniform(0.45, 1.0)
        x0 = cx + rng.normal(0, h * 0.06); y0 = cy + rng.uniform(0, h * 0.05)
        pts = np.stack([np.linspace(x0, x0 + np.sin(a) * L, 8), np.linspace(y0, y0 - np.cos(a) * L, 8)], 1)
        draw_stroke(dr, pts, wd * rng.uniform(0.8, 1.2), wd * rng.uniform(0.6, 0.9), 1.0, 0.8)

def paper_fibres(path, weight, seed, hp=4, scale=0.5, thresh=0.04):
    """transfer the real coloured fibres of a recycled-paper scan onto the finished image"""
    global canvas
    dev = load_colour_detail(path, hp, scale * K, seed)
    mag = np.abs(dev).max(-1)
    m = smooth(thresh, thresh * 2.5, mag)[..., None]
    canvas = canvas + dev * weight * m

# ---- added for the Durban pair ----
def knife_planes(mask, bbox, colours, n, seed, angle=0.6, alpha=0.9, size=(0.25, 0.6)):
    """palette-knife planes: irregular flat facets, each with scraped directional texture and a hard edge"""
    x0, y0, x1, y1 = bbox; r = np.random.default_rng(seed)
    for i in range(n):
        cx, cy = r.uniform(x0, x1), r.uniform(y0, y1)
        sw = (x1 - x0) * r.uniform(*size) / 2; sh = (y1 - y0) * r.uniform(*size) / 2
        a0 = r.uniform(0, np.pi); k = int(r.integers(4, 7))
        ang = np.sort(r.uniform(0, 2 * np.pi, k))
        pts = [(X(cx + sw * np.cos(t + a0) * r.uniform(0.6, 1)), Y(cy + sh * np.sin(t + a0) * r.uniform(0.6, 1))) for t in ang]
        c = colours[i % len(colours)]
        S = streaks(SRC_BROAD, angle=angle + r.normal(0, 0.25), su=0.9, sv=0.5, seed=seed * 100 + i)
        paint(poly_mask(pts) * mask, c, c * 0.93, S=S, soft=0.8, wob=0.8, wob_scale=30, width=0.1, dry=0.28, dry_edge=0.6,
              mot=0.3, rim=0.0, seed=seed * 100 + i, valvar=0.06, edge_tex=0.9, alpha=alpha)

def stamp_dashes(dr, region_fn, n, length, width, angle, jitter=0.4):
    """rows of short stamped dashes (leaf marks); region_fn() returns a random (x,y) px inside the area"""
    for _ in range(n):
        x, y = region_fn(); a = angle + rng.normal(0, jitter); L = length * rng.uniform(0.6, 1.2)
        pts = np.stack([np.linspace(x, x + np.cos(a) * L, 6), np.linspace(y, y + np.sin(a) * L, 6)], 1)
        draw_stroke(dr, pts, width, width * 0.8, 1.0, 0.9)

def spatter(mask, color, density, seed, rmin=0.6, rmax=2.2, alpha=0.9):
    """toothbrush spatter: sparse round dots of varied size"""
    global canvas
    r = np.random.default_rng(seed)
    n = int(density * W_REF * H_REF / (K_REF * K_REF * 400) * K_REF * K_REF)    # count from the 80 dpi page: same dots at every DPI
    lay = Image.new("L", (W, H), 0); d = ImageDraw.Draw(lay)
    for _ in range(n):
        x, y = r.uniform(0, W), r.uniform(0, H); rad = r.uniform(rmin, rmax) ** 1.5 * K * 1.4
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=int(r.uniform(150, 255)))
    A = (np.asarray(lay, f32) / 255 * mask * alpha)[..., None]
    canvas = canvas * (1 - A) + color * A

# ---- richer vocabulary (from the reference study) ----
def flicks(region, color, n, angle, length_mm, seed, spread=0.35, alpha=0.95, size_mm=(0.35, 1.0)):
    """paint flicks: a round head with a tapering tail, all thrown in roughly one direction"""
    global canvas
    r = np.random.default_rng(seed); ss = 4 if W * H < 5e6 else 2
    lay = Image.new("L", (W * ss, H * ss), 0); d = ImageDraw.Draw(lay)
    region, ys, xs_ = pick_list(region)               # listed as at 80 dpi: the same spots at every DPI (pass region as a function: exact)
    if len(xs_) == 0: return
    mm = DPI / 25.4 * ss
    for _ in range(n):
        i = r.integers(len(xs_)); px, py = xs_[i] * ss, ys[i] * ss
        a = angle + r.normal(0, spread); L = length_mm * r.uniform(0.3, 1.2) * mm; rad = r.uniform(*size_mm) / 2 * mm
        tip = (px + np.cos(a) * L, py + np.sin(a) * L)
        nx, ny = -np.sin(a), np.cos(a)
        tail = [(px + nx * rad * 0.9, py + ny * rad * 0.9), (tip[0], tip[1]), (px - nx * rad * 0.9, py - ny * rad * 0.9)]
        d.polygon(tail, fill=255); d.ellipse([px - rad, py - rad, px + rad, py + rad], fill=255)
    A = (np.asarray(lay.reduce(ss), f32) / 255 * alpha)[..., None]
    canvas = canvas * (1 - A) + color * A

def broken_colour(mask, cols, seed, scale_px=120, alpha=1.0):
    """hue variation inside one shape: three neighbouring colours mixed by two low-frequency fields"""
    global canvas
    a = smooth(-0.8, 0.8, lowfreq(scale_px * K, seed, 3)); b = smooth(-0.6, 1.0, lowfreq(scale_px * 0.5 * K, seed + 1, 2))
    c0, c1, c2 = cols
    col = (c0 * (1 - a)[..., None] + c1 * a[..., None]) * (1 - 0.6 * b)[..., None] + c2 * (0.6 * b)[..., None]
    A = (mask * alpha)[..., None]
    canvas = canvas * (1 - A) + col * A

def cut_halo(mask, gap_px=1.4, alpha=0.85):
    """paper showing in a hairline gap around a cut shape (call before painting the shape)"""
    global canvas
    ring = smooth(0.04, 0.25, fastblur(mask, gap_px)) * (1 - smooth(0.4, 0.6, mask))
    A = (ring * alpha)[..., None]
    canvas = canvas * (1 - A) + PAPER * A

# ---- painted surface: real brushed-paint height scans (ambientCG Paint001-006, CC0) ----
_HT = {}
# native stroke direction of each scan, so `angle` always means "the direction the strokes run on the page"
NATIVE = {"Paint": np.pi / 2, "Smear": 0.0}
def height_tile(path, hp=24, blur=1.6):
    """keep the broad ridges of a paint scan (stroke body), drop the fine crinkle that reads as embossed plastic"""
    key = (path, hp, blur)
    if key not in _HT:
        a = np.array(Image.open(path).convert("L")).astype(f32)
        a = ndi.gaussian_filter(a, blur, mode="wrap") - ndi.gaussian_filter(a, hp, mode="wrap"); _HT[key] = a / (a.std() + 1e-6)
    return _HT[key]
def _native(path): return next((v for k, v in NATIVE.items() if k in os.path.basename(path)), 0.0)

def sample_rot(tile, angle, mm_per_tile, box=None, ox=0.0, oy=0.0):
    """sample a tileable map rotated by `angle` (radians, stroke direction) at a physical scale; box=(y0,y1,x0,x1) for a crop"""
    y0, y1, x0, x1 = box if box else (0, H, 0, W)
    yy_, xx_ = np.mgrid[y0:y1, x0:x1].astype(f32)
    s = tile.shape[0] / (mm_per_tile / 25.4 * DPI)
    c, sn = np.cos(angle), np.sin(angle)
    u = (xx_ * c + yy_ * sn) * s + ox; v = (-xx_ * sn + yy_ * c) * s + oy
    return ndi.map_coordinates(tile, [v % tile.shape[0], u % tile.shape[1]], order=1, mode="grid-wrap").astype(f32)

def paint_body(mask, path, angle, mm_per_tile=40, strength=0.07, light=(-0.6, -0.8), cavity=0.03, seed=0):
    """light a real paint height map across a zone: ridges catch the sun, valleys darken. light = direction TO the sun on screen"""
    global canvas
    Hm = sample_rot(height_tile(path), angle - _native(path), mm_per_tile, ox=seed * 37.0, oy=seed * 91.0)
    gy, gx = np.gradient(Hm)
    sh = -(gx * light[0] + gy * light[1]); sh /= sh.std() + 1e-6
    f = 1 + (strength * np.clip(sh, -2.5, 2.5) - cavity * smooth(0.5, 2.0, -Hm)) * mask
    canvas = canvas * f[..., None]
    return Hm

SMEAR = "tex/Smear007_1K-JPG_Color.jpg"
def smear_pass(mask, color, angle, mm_per_tile=60, coverage=0.45, alpha=0.85, light=(-0.6, -0.8), relief=0.08, seed=0):
    """palette-knife passes: colour deposited where the scanned smear surface is high, with its own relief"""
    global canvas
    Hm = sample_rot(height_tile(SMEAR, hp=30, blur=1.0), angle - _native(SMEAR), mm_per_tile, ox=seed * 53.0, oy=seed * 29.0)
    thr = ndtri(np.clip(1 - coverage, 0.01, 0.99))
    A = smooth(thr - 0.35, thr + 0.35, Hm) * mask * alpha
    gy, gx = np.gradient(Hm); sh = -(gx * light[0] + gy * light[1]); sh /= sh.std() + 1e-6
    col = color[None, None, :] * (1 + relief * np.clip(sh, -2.5, 2.5))[..., None]
    canvas = canvas * (1 - A[..., None]) + col * A[..., None]

def flicks2(region, color, clusters, per, angle, length_mm, seed, spread=0.25, alpha=0.95, size_mm=(0.4, 1.1)):
    """paint flicks thrown from a loaded brush: irregular heads, tails that thin, break and leave droplets; clustered"""
    global canvas
    r = np.random.default_rng(seed); ss = 4 if W * H < 5e6 else 2
    lay = Image.new("L", (W * ss, H * ss), 0); d = ImageDraw.Draw(lay)
    region, ys, xs_ = pick_list(region)               # listed as at 80 dpi: the same spots at every DPI (pass region as a function: exact)
    if len(xs_) == 0: return
    mm = DPI / 25.4 * ss
    for _ in range(clusters):
        i = r.integers(len(xs_)); cx0, cy0 = xs_[i] * ss, ys[i] * ss; ca = angle + r.normal(0, spread * 0.5)
        for _ in range(per):
            px, py = cx0 + r.normal(0, 3.0 * mm), cy0 + r.normal(0, 1.6 * mm)
            a = ca + r.normal(0, spread * 0.4); L = length_mm * mm * r.uniform(0.2, 1.3); rad = r.uniform(*size_mm) / 2 * mm
            op = int(255 * r.uniform(0.55, 1.0))
            k = 7; th = np.linspace(0, 2 * np.pi, k, endpoint=False) + r.uniform(0, 1)
            rr = rad * r.uniform(0.65, 1.25, k)
            d.polygon([(px + q * np.cos(t) * 1.15, py + q * np.sin(t) * 0.9) for q, t in zip(rr, th)], fill=op)        # irregular head
            nx, ny = -np.sin(a), np.cos(a); bend = r.normal(0, 0.15)
            seg_end = r.uniform(0.45, 1.0) if r.uniform() < 0.45 else 1.0
            ts = np.linspace(0, seg_end, 10)
            cxs = px + np.cos(a) * L * ts + nx * bend * L * ts ** 2; cys = py + np.sin(a) * L * ts + ny * bend * L * ts ** 2
            wds = rad * 0.85 * (1 - ts / max(seg_end, 1e-3) * 0.95)
            d.polygon([(x_ + nx * w_, y_ + ny * w_) for x_, y_, w_ in zip(cxs, cys, wds)] + [(x_ - nx * w_, y_ - ny * w_) for x_, y_, w_ in zip(cxs, cys, wds)][::-1], fill=op)
            if seg_end < 1.0:                                       # the tail broke: droplets carry on along the throw
                for j in range(r.integers(1, 4)):
                    tt = seg_end + (1 - seg_end) * r.uniform(0.2, 1.4); dr_ = rad * r.uniform(0.15, 0.4)
                    qx, qy = px + np.cos(a) * L * tt, py + np.sin(a) * L * tt
                    d.ellipse([qx - dr_, qy - dr_, qx + dr_, qy + dr_], fill=op)
            for _ in range(r.integers(0, 3)):                      # satellites around the head
                qx, qy = px + r.normal(0, rad * 3), py + r.normal(0, rad * 3); dr_ = rad * r.uniform(0.1, 0.3)
                d.ellipse([qx - dr_, qy - dr_, qx + dr_, qy + dr_], fill=int(op * 0.8))
    A = np.asarray(lay.reduce(ss), f32) / 255 * alpha * (1 - 0.3 * smooth(1.0, 2.5, tooth))
    canvas = canvas * (1 - A[..., None]) + color * A[..., None]

def gouache(strokes, color, seed, opacity=0.97, bristle="tex/Paint003_1K-JPG_Displacement.jpg", bristle_mm=18):
    """opaque gouache strokes: pressure swell, ragged edges, bristle tracks, paint running dry toward the end.
    strokes: list of (pts_px Nx2 along the stroke, width_px)"""
    global canvas
    r = np.random.default_rng(seed); ss = 4 if W * H < 5e6 else 2; bt = height_tile(bristle, hp=10, blur=0.8)
    for pts, wd in strokes:
        p = np.asarray(pts, np.float64); n = len(p)
        if n < 2: continue
        t = np.linspace(0, 1, n)
        prof = wd * np.sin(np.pi * np.clip(t, 0, 1) ** 0.75) ** 0.55 * (1 + 0.12 * np.sin(t * r.uniform(4, 9) + r.uniform(0, 6)))
        dd = np.gradient(p, axis=0); nr = np.stack([-dd[:, 1], dd[:, 0]], 1); nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-9
        rag = 1 + 0.12 * r.standard_normal((n, 2))
        Lp = p + nr * (prof * rag[:, 0] / 2)[:, None]; Rp = p - nr * (prof * rag[:, 1] / 2)[:, None]
        allp = np.vstack([Lp, Rp]); bx0, by0 = int(max(0, allp[:, 0].min() - 3)), int(max(0, allp[:, 1].min() - 3))
        bx1, by1 = int(min(W, allp[:, 0].max() + 3)), int(min(H, allp[:, 1].max() + 3))
        a80 = allp * (W_REF / W, H_REF / H)                                     # off the page? decided on the 80 dpi page, so the draws stay in step
        if int(min(W_REF, a80[:, 0].max() + 3)) <= int(max(0, a80[:, 0].min() - 3)) or int(min(H_REF, a80[:, 1].max() + 3)) <= int(max(0, a80[:, 1].min() - 3)): continue
        if bx1 <= bx0 or by1 <= by0: r.uniform(0, 999); r.uniform(0, 999); continue
        im = Image.new("L", ((bx1 - bx0) * ss, (by1 - by0) * ss), 0)
        ImageDraw.Draw(im).polygon([((x - bx0) * ss, (y - by0) * ss) for x, y in np.vstack([Lp, Rp[::-1]])], fill=255)
        cov = np.asarray(im.reduce(ss), f32)[: by1 - by0, : bx1 - bx0] / 255
        ang = np.arctan2(p[-1, 1] - p[0, 1], p[-1, 0] - p[0, 0])
        br = sample_rot(bt, ang - _native(bristle), bristle_mm, box=(by0, by1, bx0, bx1), ox=r.uniform(0, 999), oy=r.uniform(0, 999))
        yy_, xx_ = np.mgrid[by0:by1, bx0:bx1].astype(f32)
        tp = np.clip(((xx_ - p[0, 0]) * np.cos(ang) + (yy_ - p[0, 1]) * np.sin(ang)) / (np.hypot(*(p[-1] - p[0])) + 1e-6), 0, 1)
        thr = -1.6 + 2.6 * tp ** 1.5                                   # more bristle gaps as the brush runs dry
        A = cov * smooth(thr - 0.5, thr + 0.5, br) * opacity
        A *= 0.85 + 0.15 * smooth(-1, 1, br)                          # thin paint lets a little colour through
        reg = canvas[by0:by1, bx0:bx1]
        canvas[by0:by1, bx0:bx1] = reg * (1 - A[..., None]) + color * A[..., None]

def paint_body_blend(mask, path, angle, mm_per_tile=30, strength=0.07, light=(-0.6, -0.8), seed=0, feather_mm=3.0,
                     patch_mm=25, warm=(255, 238, 214), cool=(70, 72, 120), tint=0.45):
    """paint body that melts into the shape: feathered from the edge, strongest where the form is lit,
    appearing in patches (like real impasto), and tinting ridges warm / hollows cool instead of only shading"""
    global canvas
    Hm = sample_rot(height_tile(path), angle - _native(path), mm_per_tile, ox=seed * 37.0, oy=seed * 91.0)
    gy, gx = np.gradient(Hm); sh = -(gx * light[0] + gy * light[1]); sh = np.clip(sh / (sh.std() + 1e-6), -2.5, 2.5)
    fpx = feather_mm / 25.4 * DPI
    inner = mask * smooth(0.5, 0.98, fastblur(mask, fpx))                      # fades in from the edge
    lum = canvas.mean(-1); m = mask > 0.5
    lo, hi = (np.percentile(lum[m], 15), np.percentile(lum[m], 90)) if m.any() else (0.2, 0.8)
    lit = smooth(lo, hi, lum)                                                   # catches where the form is lit
    patches = smooth(-0.4, 0.9, lowfreq(patch_mm / 25.4 * DPI, seed + 3, 2))    # comes and goes in patches
    wgt = inner * (0.2 + 0.8 * lit) * (0.3 + 0.7 * patches)
    d = (strength * wgt * sh)[..., None]
    up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
    canvas = canvas * (1 + 0.6 * d) + up * tint * (rgb(*warm) - canvas) + dn * tint * (rgb(*cool) - canvas)

# ================= SHORELINES: where water meets sand. Three layered methods, each studied from a style reference
# (docs/METHOD.md, "Shorelines"; build-up board: swatch_board_shore.py). Shared principle: every layer between water and dry sand
# is LIGHTER or translucent, never a dark wet band. Each method takes WATER (H x W mask, 1 = water; extend it past the painted
# area so the frame edge is not read as a shore) and LINE (N x 2 page points along the waterline). Widths are mm at the reference
# row; taper=(HZ, ref_y) narrows them toward the horizon. pal overrides SHORE_PAL colours. upto stops after that layer (for the board).
SHORE_PAL = dict(foam=(253, 252, 248), under=(220, 240, 236), light=(198, 236, 224), bottom=(190, 160, 120), fleck=(104, 190, 184),
                 speck=(52, 128, 158), veil=(196, 214, 218), veil2=(218, 208, 210), dark=(40, 128, 140),
                 lobe=((250, 241, 226), (245, 229, 208)), through=(244, 224, 208), grain=((204, 160, 130), (254, 244, 224)))
def _pal(p):
    q = dict(SHORE_PAL); q.update(p or {})
    return {k: (tuple(rgb(*c) for c in v) if isinstance(v[0], tuple) else rgb(*v)) for k, v in q.items()}

def shore_dist(WATER):
    """signed distance to the waterline in mm: negative in the water, positive on the sand"""
    b = WATER > 0.5
    return ((ndi.distance_transform_edt(~b) - ndi.distance_transform_edt(b)) * 25.4 / DPI).astype(f32)

def _taper(y, taper):
    y = np.asarray(y, f32)
    if taper is None: return np.ones_like(y)
    hz, ref = taper; return np.clip((y - hz) / (ref - hz), 0.08, 2.5).astype(f32)

def _band(sd, lo, hi, e): return smooth(lo - e, lo + e, sd) * smooth(hi + e, hi - e, sd)

def _shore_frame(LINE, WATER, taper):
    """waterline resampled every ~1 mm, in px, with unit normals pointing onto the sand, unit tangents, and the taper at each point"""
    L = np.asarray(LINE, np.float64); p = np.stack([L[:, 0] * W, L[:, 1] * H], 1)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]; MM = DPI / 25.4
    p80 = np.stack([L[:, 0] * W_REF, L[:, 1] * H_REF], 1)                       # point count from the 80 dpi page: same strokes at every DPI
    n80 = max(8, int(np.r_[0, np.cumsum(np.linalg.norm(np.diff(p80, axis=0), axis=1))][-1] / (REF_DPI / 25.4)))
    t = np.linspace(0, s[-1], n80); p = np.stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])], 1)
    d = np.gradient(p, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-9; n = np.stack([-d[:, 1], d[:, 0]], 1)
    q = np.clip(np.round(p + n * 2.0 * MM).astype(int), 0, [W - 1, H - 1])
    if WATER[q[:, 1], q[:, 0]].mean() > 0.5: n = -n
    return p, n, d, _taper(p[:, 1] / H, taper)

def _shore_strokes(p, n, sc, off_mm, width_mm, seed, cover=0.8, seg=(0.10, 0.35), wob_mm=0.6, split=None):
    """long strokes running along the waterline at offset off_mm (negative = into the water), broken into runs.
    split: cut a run short when the taper along it changes by more than this ratio, so its width follows the perspective"""
    r = np.random.default_rng(seed); MM = DPI / 25.4; N = len(p); out = []
    i = int(r.uniform(0, 0.12) * N)
    while i < N - 2:
        ln = max(3, int(r.uniform(*seg) * N)); j = min(N, i + ln)
        while split and j - i > 4 and sc[i:j].max() / max(sc[i:j].min(), 1e-3) > split: j = i + max(4, (j - i) * 2 // 3)
        o = (off_mm + r.uniform(-0.3, 0.3) * abs(width_mm)) * sc[i:j, None] * MM
        wob = np.cumsum(r.normal(0, 0.15, j - i))[:, None] * wob_mm * MM * 0.3
        out.append((p[i:j] + n[i:j] * (o + wob), width_mm * r.uniform(0.6, 1.1) * float(sc[i:j].mean()) * MM))
        i = j + int(r.uniform(0.0, 2 * (1 - cover)) * ln)
    return out

def _tongues(p, n, d, sc, length_mm, width_mm, count, seed):
    """foam tongues that leave the edge and curl along the shore as they run out into the water"""
    r = np.random.default_rng(seed); MM = DPI / 25.4; out = []
    for _ in range(count):
        i = int(r.integers(2, len(p) - 2)); L = length_mm * sc[i] * MM * r.uniform(0.6, 1.3); sg = r.choice([-1, 1])
        a = p[i]; b = a - n[i] * L * 0.45 + d[i] * sg * L * 0.5; c = a - n[i] * L * 0.6 + d[i] * sg * L * 1.1
        out.append((np.asarray(bez(tuple(a), tuple(b), tuple(c), 18)), width_mm * sc[i] * MM * r.uniform(0.6, 1.1)))
    return out

def _dabs(mask, ang, len_mm, w_mm, count, seed, mask80=None):
    """short dry-brush dabs laid along angle ang inside mask (sand seen under shallow water); mask80: the mask as at 80 dpi"""
    r = np.random.default_rng(seed); MM = DPI / 25.4; out = []
    if AT_REF or mask80 is None: ys, xs = ref_nonzero(mask)
    else: ys, xs = np.nonzero(mask80 > 0.5); ys, xs = ys * (H / H_REF), xs * (W / W_REF)
    if len(xs) == 0: return out
    for k in r.choice(len(xs), size=min(count, len(xs)), replace=False):
        L = len_mm * MM * r.uniform(0.5, 1.4); a = ang + r.normal(0, 0.12); c = np.array([xs[k], ys[k]], np.float64)
        u = np.linspace(-0.5, 0.5, 6)[:, None] * L * np.array([np.cos(a), np.sin(a)])
        out.append((c + u, w_mm * MM * r.uniform(0.6, 1.3)))
    return out

def _pnoise(scale_mm, seed, sc, taper):
    """low-frequency noise whose features grow toward the viewer when the shore is in perspective"""
    MM = DPI / 25.4
    if taper is None: return lowfreq(scale_mm * MM, seed, 2)
    w = np.clip((sc - 0.3) / 0.9, 0, 1)
    a = lowfreq(scale_mm * 0.5 * MM, seed, 2); b = lowfreq(scale_mm * 1.4 * MM, seed + 1, 2)
    return (a * (1 - w) + b * w) / np.sqrt(w ** 2 + (1 - w) ** 2 + 1e-6)

def _sand_grain(DRY, grain, seed, coarse=1.0):
    spatter(DRY, grain[0], 0.55 * coarse, seed, rmin=0.5, rmax=1.3 * coarse, alpha=0.7)
    spatter(DRY, grain[1], 0.45 * coarse, seed + 1, rmin=0.5, rmax=1.3 * coarse, alpha=0.8)

def shore_ribbon(WATER, LINE, pal=None, width_mm=4.5, seed=0, taper=None, grain=True, upto=9):
    """1. CUT-PAPER RIBBON (after Surf Beach ii). A white ribbon pasted along the water's edge. Layers:
       1 the water darkens into a crisp rim where it meets the ribbon (a watercolour edge)
       2 a pale aqua under-layer: the whole ribbon, its SAND-side edge torn
       3 the white top layer, a little narrower, leaving an aqua fringe against the water
       4 the tear: a hairline shadow under it and a few paper fibres on the sand
       5 dry sand grain right up to the ribbon (no wet band). Best for flat, graphic posters and deep water."""
    global canvas
    if callable(WATER): WATER = WATER()
    P = _pal(pal); sd = shore_dist(WATER); sc = _taper(yy, taper); MM = DPI / 25.4; e = 25.4 / DPI
    w = width_mm * sc * (1 + 0.18 * lowfreq(22 * MM, seed, 2))
    tear = sc * (0.5 + 0.45 * (0.6 * lowfreq(2.5 * MM, seed + 1, 2) + 0.4 * lowfreq(0.8 * MM, seed + 2, 1)))
    if upto >= 1:
        canvas = canvas * (1 - 0.16 * smooth(-w - 1.8 * sc, -w, sd) * smooth(-w + e, -w - e, sd))[..., None]
    if upto >= 2:
        paint(smooth(-w - e, -w + e, sd) * smooth(tear + e, tear - e, sd), P["under"], P["under"] * 0.98, soft=0.4, wob=0.2, wob_scale=20,
              width=0.08, dry=0.02, dry_edge=0.2, mot=0.4, rim=0.0, seed=seed + 3, valvar=0.02, edge_tex=0.3)
    if upto >= 3:
        paint(smooth(-0.68 * w - e, -0.68 * w + e, sd) * smooth(0.8 * tear + e, 0.8 * tear - e, sd), P["foam"], P["foam"] * 0.98, soft=0.4, wob=0.3,
              wob_scale=20, width=0.08, dry=0.03, dry_edge=0.3, mot=0.4, rim=0.0, seed=seed + 4, valvar=0.02, gran=0.04, edge_tex=0.5)
    if upto >= 4:
        canvas = canvas * (1 - 0.10 * _band(sd, tear, tear + 0.45 * sc, e))[..., None]
        riso(_band(sd, tear, tear + 1.6 * sc, e), P["foam"], 0.06, seed + 5, size=1.0, alpha=0.9)
    if upto >= 5 and grain:
        _sand_grain(smooth(tear + 1.0, tear + 3.0, sd) * (1 - WATER), P["grain"], seed + 6)

def _shallows(WATER, taper, seed, lobe_mm, foam_mm):
    """where sand shows under the shallows (shore_gouache_veil layer 1), from the canvas globals"""
    sd = shore_dist(WATER); sc = _taper(yy, taper); MM = DPI / 25.4
    wf = foam_mm * sc * (0.45 + 0.55 * smooth(-1.2, 1.2, lowfreq(lobe_mm * 0.8 * MM, seed + 2, 2)))
    return smooth(-30 * sc, -6 * sc, sd) * smooth(-wf, -wf - 2 * sc, sd) * smooth(0.1, 0.9, lowfreq(16 * MM, seed + 3, 2)) * smooth(0.2, 0.5, sc)

def shore_gouache_veil(WATER, LINE, pal=None, foam_mm=7.0, veil_mm=15.0, seed=0, taper=None, lobe_mm=30, rows=3, grain=True, upto=9, bottom=1.0, swash=1.0):
    """2. GOUACHE FOAM + SWASH VEIL (after Morning Surf). Layers:
       1 sand under the shallows: warm dabs in patches, thinning out to sea
       2 the water pales as it shallows into the foam; thin broken swash lines further out
       3 the veil: retreating water over the sand, cool blue-grey at the foam, lilac-grey at its lobed edge, sand grain through it
       4 the foam: a bold opaque dry-brushed band that swells and thins, bristle tracks on top
       5 the water broken into the foam's sea side: turquoise flecks and a few deep specks
       6 dry sand grain beyond the veil
    bottom: how much of the sand under the shallows shows (1 = as on the board; lower for big, calm water seen from afar).
    swash: strength of the thin swash lines (0 drops them: on a long receding shore they turn into ruled scratches)
    WATER may be a function that builds the mask: then the dabs under the shallows sit exactly where an 80 dpi render puts them"""
    global canvas
    WATER, W80 = mask_and_80(WATER)
    P = _pal(pal); sd = shore_dist(WATER); sc = _taper(yy, taper); MM = DPI / 25.4; e = 25.4 / DPI
    p, n, d, s1 = _shore_frame(LINE, WATER, taper); ang = float(np.arctan2(*(p[-1] - p[0])[::-1]))
    reach = veil_mm * sc * (0.2 + 0.8 * smooth(-1.2, 1.2, lowfreq(lobe_mm * MM, seed, 2)))
    wf = foam_mm * sc * (0.45 + 0.55 * smooth(-1.2, 1.2, lowfreq(lobe_mm * 0.8 * MM, seed + 2, 2)))
    if upto >= 1:
        Bm = smooth(-30 * sc, -6 * sc, sd) * smooth(-wf, -wf - 2 * sc, sd) * smooth(0.1, 0.9, lowfreq(16 * MM, seed + 3, 2)) * smooth(0.2, 0.5, sc)   # dabs are a fixed size: none far off
        canvas = canvas + (P["bottom"] - canvas) * (Bm * 0.14 * bottom)[..., None]
        Bm80 = None
        if not AT_REF and W80 is not None:
            with ref_canvas(): Bm80 = _shallows(W80, taper, seed, lobe_mm, foam_mm)
        n_d = int((ref_grid(Bm) if Bm80 is None else Bm80).sum() / (REF_DPI / 25.4) ** 2 * 0.35 * bottom)   # area in mm2, as at 80 dpi
        gouache(_dabs(Bm, ang, 2.2, 0.55, n_d, seed + 4, Bm80), P["bottom"], seed + 25, opacity=0.55 * min(1.0, bottom * 1.5))
    if upto >= 2:
        Lm = smooth(-12 * sc, 0, sd) * (sd < 0)
        canvas = canvas + (P["light"] - canvas) * ((Lm ** 1.5) * 0.55)[..., None]
        st = _shore_strokes(p, n, s1, -16, 0.4, seed + 5, cover=0.7, seg=(0.4, 0.9), wob_mm=0.8)
        st += _shore_strokes(p, n, s1, -27, 0.3, seed + 6, cover=0.4, seg=(0.3, 0.7), wob_mm=0.8)
        if swash > 0: gouache(st, P["light"] * 0.5 + P["foam"] * 0.5, seed + 7, opacity=0.6 * swash)
    if upto >= 3:
        V = smooth(reach + 1.5 * e, reach - 1.5 * e, sd) * smooth(-2 * e, 0, sd)
        gr = smooth(-0.6, 0.9, tooth * 0.9 + lowfreq(1.2 * MM, seed + 8, 2) * 0.6)
        tt = np.clip(sd / np.maximum(reach, e), 0, 1)
        vc = P["veil"] * (1 - tt[..., None]) + P["veil2"] * tt[..., None]
        canvas = canvas + (vc - canvas) * (V * (0.40 + 0.50 * gr) * (1 - 0.35 * tt))[..., None]
    F = smooth(-wf - e, -wf + e, sd) * smooth(2 * e, -0.5 * e, sd)
    if upto >= 4:
        S = streaks(SRC_BROAD, angle=ang, su=1.0, sv=0.6, seed=seed + 9)
        paint(F, P["foam"], P["foam"] * 0.98, S=S, soft=0.6, wob=0.5, wob_scale=25, width=0.25, dry=0.30, dry_edge=0.9, mot=0.4, rim=0.0,
              seed=seed + 10, valvar=0.02, edge_tex=0.8)
        st = []
        for k in range(rows):
            f = (k + 0.5) / rows
            st += _shore_strokes(p, n, s1, -foam_mm * (0.2 + 0.8 * f), foam_mm * (0.6 - 0.3 * f), seed + 11 + k, cover=0.8 - 0.3 * f)
        gouache(st, P["foam"], seed + 20, opacity=0.9)
    if upto >= 5:
        Fs = F * smooth(-0.25 * wf, -0.8 * wf, sd) * smooth(0.15, 0.4, sc)            # flecks are a fixed size: none where the foam is tiny
        riso(Fs * smooth(-0.3, 0.8, lowfreq(6 * MM, seed + 21, 2)), P["fleck"], 0.22, seed + 22, size=1.1, alpha=0.9)
        riso(Fs, P["speck"], 0.010, seed + 23, size=0.8, alpha=0.8)
    if upto >= 6 and grain:
        _sand_grain(smooth(reach + 1.0, reach + 4.0, sd) * (1 - WATER), P["grain"], seed + 24)

def shore_brush_lobes(WATER, LINE, pal=None, foam_mm=4.5, lobe_mm=(7, 16), seed=0, taper=None, scallop_mm=30, grain=True, upto=9):
    """3. BRUSHY SWASH LOBES (after Portugal). Layers:
       1 brushed water: fine dry-brush streaks plus faint bristle tracks along the shore, darker and lighter by turns, strongest near the edge
       2 a translucent white glaze where the water thins toward the shore, dragged with the same brush
       3 nested scalloped cream lobes on the sand, smooth and lighter than it (lobe colours, nearest the water first)
       4 the foam: a translucent wide pass, an opaque narrower pass, and soft tongues that curl out into the water
       5 sand seen through the thinnest water: long pink-cream patches along the edge
       6 coarse dry sand grain beyond the lobes (the swash zone stays smooth)
    In perspective the scallops and patches grow toward the viewer and the strokes are cut so their width follows the taper."""
    global canvas
    if callable(WATER): WATER = WATER()
    P = _pal(pal); sd = shore_dist(WATER); sc = _taper(yy, taper); MM = DPI / 25.4; e = 25.4 / DPI
    p, n, d, s1 = _shore_frame(LINE, WATER, taper); ang = float(np.arctan2(*(p[-1] - p[0])[::-1])); sp = 1.35 if taper else None
    S1 = streaks(SRC_FINE, angle=ang, su=0.5, sv=1.8, seed=seed); S2 = streaks(SRC_FINE, angle=ang, su=0.5, sv=1.8, seed=seed + 1)
    reaches = [lobe_mm[j] * sc * (0.25 + 0.75 * smooth(-1.2, 1.2, _pnoise(scallop_mm, seed + 2 + 2 * j, sc, taper))) for j in range(len(lobe_mm))]
    if upto >= 1:
        Wb = smooth(-45 * sc, -4 * sc, sd) * (sd < 0)
        paint(Wb, P["dark"], P["dark"] * 0.95, S=S1, soft=2, wob=0.5, wob_scale=40, width=0.3, dry=0.75, dry_edge=0.7, mot=0.4, rim=0.0,
              seed=seed + 5, alpha=0.24, edge_tex=0.2)
        paint(Wb, P["light"], P["light"] * 0.97, S=S2, soft=2, wob=0.5, wob_scale=40, width=0.3, dry=0.70, dry_edge=0.7, mot=0.4, rim=0.0,
              seed=seed + 6, alpha=0.28, edge_tex=0.2)
        st = []
        for k, off in enumerate(np.arange(-3.0, -40.0, -3.2)):
            st += _shore_strokes(p, n, s1, off, 5.0, seed + 30 + k, cover=0.95, seg=(0.5, 1.0), wob_mm=0.8, split=sp)
        gouache(st[::2], P["dark"], seed + 50, opacity=0.11 if taper else 0.14); gouache(st[1::2], P["light"], seed + 51, opacity=0.16)
    if upto >= 2:
        Gm = smooth(-14 * sc, 0, sd) * (sd < 0)
        paint(Gm, P["foam"], P["light"], S=S1, soft=2, wob=0.5, wob_scale=40, width=0.3, dry=0.55, dry_edge=0.7, mot=0.4, rim=0.0,
              seed=seed + 7, alpha=0.30, edge_tex=0.2)
        st = _shore_strokes(p, n, s1, -3.5, 6.0, seed + 8, cover=0.9, seg=(0.3, 0.8), wob_mm=0.8, split=sp)
        gouache(st, P["foam"], seed + 52, opacity=0.26)
    if upto >= 3:
        S3 = streaks(SRC_BROAD, angle=ang, su=1.2, sv=0.7, seed=seed + 9)
        for j in reversed(range(len(lobe_mm))):
            c = P["lobe"][min(j, len(P["lobe"]) - 1)]
            paint(smooth(reaches[j] + 1.5 * e, reaches[j] - 1.5 * e, sd) * smooth(-2 * e, 0, sd), c, c * 0.98, S=S3, soft=0.6, wob=0.4,
                  wob_scale=30, width=0.15, dry=0.12, dry_edge=0.45, mot=0.5, rim=0.0, seed=seed + 10 + j, alpha=0.85, valvar=0.03, edge_tex=0.6)
    if upto >= 4:
        gouache(_shore_strokes(p, n, s1, -foam_mm * 0.5, foam_mm * 1.2, seed + 12, cover=0.9, split=sp), P["foam"], seed + 13, opacity=0.5)
        gouache(_shore_strokes(p, n, s1, -foam_mm * 0.35, foam_mm * 0.7, seed + 14, cover=0.75, split=sp), P["foam"], seed + 15, opacity=0.92)
        gouache(_tongues(p, n, d, s1, foam_mm * 4.8, foam_mm * 0.7, max(2, len(p) // 45), seed + 16), P["foam"], seed + 17, opacity=0.65)
    if upto >= 5:
        Sl = streaks(SRC_BROAD, angle=ang, su=2.5, sv=0.5, seed=seed + 18)          # long along the shore, narrow across it
        Tm = _band(sd, -6 * sc, 1.0 * sc, e) * smooth(0.2, 0.9, 0.6 * Sl + 0.5 * _pnoise(12, seed + 19, sc, taper))
        paint(Tm, P["through"], P["through"] * 0.98, soft=0.8, wob=0.6, wob_scale=15, width=0.15, dry=0.1, dry_edge=0.3, mot=0.4, rim=0.0,
              seed=seed + 20, alpha=0.62, edge_tex=0.5)
    if upto >= 6 and grain:
        _sand_grain(smooth(reaches[-1] + 1.0, reaches[-1] + 4.0, sd) * (1 - WATER), P["grain"], seed + 21, coarse=1.4)
