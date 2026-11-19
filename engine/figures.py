# Figure kit (exec after engine.py + marks.py). Poster-style people: tiny, faceless, tapered limbs,
# slightly long legs, one clothing accent. Every shape is an anti-aliased mask; the cast shadow is the
# figure's own silhouette sheared along the poster's SUN, so all shadows in a poster agree.

def make_sun(azimuth_deg, elevation_deg, persp=0.35):
    """azimuth: direction the SHADOWS fall on screen (0 = right, 90 = toward the viewer, 180 = left).
    elevation: sun height above the horizon. persp squashes the ground plane (how flat we see the sand)."""
    a, e = np.radians(azimuth_deg), np.radians(elevation_deg)
    L = 1 / np.tan(e)
    return {"sx": np.cos(a) * L, "sy": np.sin(a) * L * persp, "light_x": -np.sign(np.cos(a)) if abs(np.cos(a)) > 1e-3 else 0.0}

SKINS = {"fair": (234, 192, 162), "light": (210, 156, 120), "medium": (170, 116, 84), "brown": (122, 80, 58), "deep": (82, 54, 42)}
HAIRS = {"black": (32, 26, 28), "brown": (64, 42, 32), "auburn": (196, 78, 44), "blonde": (222, 182, 112), "grey": (190, 186, 182)}

def capsule_px(p0, p1, r0, r1, n=9):
    (x0, y0), (x1, y1) = p0, p1; ang = np.arctan2(y1 - y0, x1 - x0)
    a = [(x0 + r0 * np.cos(t), y0 + r0 * np.sin(t)) for t in np.linspace(ang + np.pi / 2, ang + 3 * np.pi / 2, n)]
    b = [(x1 + r1 * np.cos(t), y1 + r1 * np.sin(t)) for t in np.linspace(ang - np.pi / 2, ang + np.pi / 2, n)]
    return a + b

def fill(mask, col, alpha=1.0, tex=0.03):
    global canvas
    A = (mask * alpha)[..., None]
    c = col[None, None, :] * (1 + tex * 0.5 * grain2[..., None])
    canvas = canvas * (1 - A) + c * A

def ink_line(pts_px, width_px, col, alpha=1.0):
    """fine drawn line (rods, strings, rails): one anti-aliased ribbon, no dry-brush dropouts"""
    p = np.asarray(pts_px, np.float64)
    for _ in range(3):                                   # Chaikin smoothing: drawn curves, not polyline corners
        if len(p) < 3: break
        q = [p[0]]
        for a, b in zip(p[:-1], p[1:]): q += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        p = np.array(q + [p[-1]])
    w = max(width_px, 0.9) / 2
    d = np.gradient(p, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    poly = [tuple(q) for q in (p + nrm * w)] + [tuple(q) for q in (p - nrm * w)[::-1]]
    fill(poly_mask(poly), col, alpha, tex=0.0)

# ---------------------------------------------------------------- poses
# joints in units of standing height; x right, y UP from the ground at the feet. Parts listed back-to-front.
HEAD_R = 0.062
def _legs_stand(spread=0.045):
    return [("cap", (-spread, 0.50), (-spread - 0.004, 0.26), 0.040, 0.032, "skin"), ("cap", (-spread - 0.004, 0.26), (-spread - 0.006, 0.015), 0.032, 0.024, "skin"),
            ("cap", (spread, 0.50), (spread + 0.004, 0.26), 0.040, 0.032, "skin"), ("cap", (spread + 0.004, 0.26), (spread + 0.006, 0.015), 0.032, 0.024, "skin")]
def _shorts(w=0.092):
    return [("poly", [(-w, 0.53), (w, 0.53), (w + 0.006, 0.40), (0.008, 0.40), (0, 0.45), (-0.008, 0.40), (-w - 0.006, 0.40)], "bottom")]
def _torso_back(top=0.80):
    return [("poly", [(-0.097, top), (0.097, top), (0.076, 0.62), (0.088, 0.50), (-0.088, 0.50), (-0.076, 0.62)], "top")]
def _head_back(style):
    parts = [("cap", (0, 0.80), (0, 0.86), 0.026, 0.026, "skin"), ("circ", (0, 0.925), HEAD_R, "hair")]
    if style == "long": parts.append(("poly", [(-0.058, 0.93), (0.058, 0.93), (0.066, 0.76), (-0.066, 0.76)], "hair"))
    if style == "bun": parts.append(("circ", (0, 0.995), 0.032, "hair"))
    return parts
def _head_side(style, cx=0.012, cy=0.925):
    parts = [("cap", (cx - 0.012, 0.80), (cx - 0.008, 0.86), 0.024, 0.024, "skin"), ("circ", (cx, cy), HEAD_R, "skin")]
    t = np.linspace(np.radians(70), np.radians(265), 14)                     # hair covers the back and top of the head
    hair = [(cx + HEAD_R * 1.04 * np.cos(a), cy + HEAD_R * 1.04 * np.sin(a)) for a in t] + [(cx + 0.012, cy + 0.01)]
    parts.append(("poly", hair, "hair"))
    if style == "long": parts.append(("poly", [(cx - 0.062, cy), (cx - 0.02, cy), (cx - 0.03, cy - 0.165), (cx - 0.072, cy - 0.145)], "hair"))
    if style == "bun": parts.append(("circ", (cx - 0.05, cy + 0.04), 0.03, "hair"))
    return parts

def pose_parts(pose, hair="short"):
    if pose == "stand":        # back view, looking out
        return (_legs_stand() + _shorts() + _torso_back() +
                [("cap", (-0.097, 0.785), (-0.118, 0.63), 0.028, 0.024, "skin"), ("cap", (-0.118, 0.63), (-0.122, 0.47), 0.024, 0.020, "skin"),
                 ("cap", (0.097, 0.785), (0.118, 0.63), 0.028, 0.024, "skin"), ("cap", (0.118, 0.63), (0.122, 0.47), 0.024, 0.020, "skin")] + _head_back(hair))
    if pose == "arms_out":     # back view, arms flung up: joy at the view
        return ([("poly", [(-0.097, 0.80), (0.097, 0.80), (0.17, 0.40), (-0.17, 0.40)], "top")] +
                [("cap", (-0.05, 0.42), (-0.058, 0.20), 0.034, 0.028, "skin"), ("cap", (-0.058, 0.20), (-0.062, 0.015), 0.028, 0.022, "skin"),
                 ("cap", (0.05, 0.42), (0.058, 0.20), 0.034, 0.028, "skin"), ("cap", (0.058, 0.20), (0.062, 0.015), 0.028, 0.022, "skin")][::1] +
                [("cap", (-0.095, 0.785), (-0.20, 0.885), 0.026, 0.022, "skin"), ("cap", (-0.20, 0.885), (-0.30, 0.995), 0.022, 0.018, "skin"),
                 ("cap", (0.095, 0.785), (0.20, 0.885), 0.026, 0.022, "skin"), ("cap", (0.20, 0.885), (0.30, 0.995), 0.022, 0.018, "skin")] + _head_back(hair))
    if pose in ("walk", "carry_board"):   # side view, facing right
        back_arm = [("cap", (-0.004, 0.785), (0.05, 0.63), 0.026, 0.022, "skin2"), ("cap", (0.05, 0.63), (0.085, 0.49), 0.022, 0.018, "skin2")]
        front_arm = [("cap", (0.004, 0.785), (-0.04, 0.63), 0.026, 0.022, "skin"), ("cap", (-0.04, 0.63), (-0.07, 0.49), 0.022, 0.018, "skin")]
        if pose == "carry_board":
            front_arm = [("cap", (0.004, 0.785), (0.012, 0.64), 0.026, 0.022, "skin"), ("cap", (0.012, 0.64), (0.07, 0.58), 0.022, 0.018, "skin")]
        legs_b = [("cap", (0.0, 0.50), (-0.06, 0.27), 0.040, 0.032, "skin2"), ("cap", (-0.06, 0.27), (-0.125, 0.035), 0.032, 0.024, "skin2"),
                  ("poly", [(-0.15, 0.01), (-0.10, 0.012), (-0.11, 0.045), (-0.14, 0.04)], "skin2")]
        legs_f = [("cap", (0.01, 0.50), (0.06, 0.275), 0.040, 0.032, "skin"), ("cap", (0.06, 0.275), (0.095, 0.02), 0.032, 0.024, "skin"),
                  ("poly", [(0.08, 0.0), (0.14, 0.0), (0.13, 0.03), (0.09, 0.035)], "skin")]
        torso = [("poly", [(-0.052, 0.80), (0.05, 0.80), (0.045, 0.62), (0.055, 0.50), (-0.05, 0.50), (-0.045, 0.62)], "top")]
        shorts = [("poly", [(-0.056, 0.53), (0.058, 0.53), (0.075, 0.40), (-0.06, 0.40)], "bottom")]
        board = []
        if pose == "carry_board":
            t = np.linspace(0, 2 * np.pi, 40); bl, bw, ba = 0.40, 0.055, -0.10
            bx, by = 0.03 + bl * np.cos(t) * (1 + 0.15 * np.cos(t)), 0.60 + bw * np.sin(t)
            board = [("poly", [(0.02 + (px - 0.03) * np.cos(ba) - (py - 0.60) * np.sin(ba), 0.60 + (px - 0.03) * np.sin(ba) + (py - 0.60) * np.cos(ba)) for px, py in zip(bx, by)], "accent")]
        return back_arm + legs_b + shorts + torso + legs_f + board + front_arm + _head_side(hair)
    if pose == "sit":          # side view, facing right, hugging knees
        return ([("cap", (-0.01, 0.15), (0.045, 0.47), 0.072, 0.058, "top"),
                 ("cap", (0.02, 0.15), (0.20, 0.33), 0.046, 0.036, "skin"), ("cap", (0.20, 0.33), (0.245, 0.03), 0.036, 0.026, "skin"),
                 ("poly", [(0.23, 0.0), (0.29, 0.0), (0.28, 0.03), (0.235, 0.035)], "skin"),
                 ("cap", (0.035, 0.48), (0.11, 0.34), 0.026, 0.022, "skin"), ("cap", (0.11, 0.34), (0.205, 0.30), 0.022, 0.018, "skin")] +
                [p for p in _head_side(hair, 0.075, 0.615) if p[0] != "cap"])
    if pose == "lie_read":     # on the front, propped on elbows, one foot kicked up; head to the right
        return ([("cap", (0.41, 0.065), (0.20, 0.050), 0.045, 0.035, "skin2"), ("cap", (0.20, 0.050), (0.02, 0.035), 0.033, 0.025, "skin2"),
                 ("cap", (0.40, 0.075), (0.21, 0.060), 0.045, 0.035, "skin"), ("cap", (0.21, 0.060), (0.14, 0.24), 0.033, 0.025, "skin"),
                 ("poly", [(0.39, 0.025), (0.39, 0.115), (0.70, 0.19), (0.72, 0.10)], "top"),
                 ("cap", (0.70, 0.145), (0.745, 0.025), 0.027, 0.023, "skin"), ("cap", (0.745, 0.025), (0.86, 0.055), 0.023, 0.019, "skin"),
                 ("poly", [(0.835, 0.03), (0.93, 0.025), (0.955, 0.10), (0.86, 0.115)], "accent")] +
                [p for p in _head_side("short" if hair == "long" else hair, 0.80, 0.215) if p[0] != "cap"] +
                ([("poly", [(0.77, 0.26), (0.83, 0.27), (0.86, 0.13), (0.82, 0.12)], "hair")] if hair == "long" else []))
    if pose == "float":        # seen from above, starfish in the water
        return ([("cap", (-0.04, 0.50), (-0.16, 0.06), 0.040, 0.026, "skin"), ("cap", (0.04, 0.50), (0.16, 0.06), 0.040, 0.026, "skin"),
                 ("cap", (-0.09, 0.78), (-0.30, 0.94), 0.026, 0.018, "skin"), ("cap", (0.09, 0.78), (0.30, 0.94), 0.026, 0.018, "skin"),
                 ("poly", [(-0.095, 0.80), (0.095, 0.80), (0.08, 0.48), (-0.08, 0.48)], "top"), ("circ", (0, 0.90), HEAD_R, "hair")])
    if pose == "fish":         # side view facing right, rod raised over the water
        return ([("cap", (0.0, 0.50), (-0.02, 0.27), 0.040, 0.032, "skin2"), ("cap", (-0.02, 0.27), (-0.05, 0.02), 0.032, 0.024, "skin2"),
                 ("cap", (0.01, 0.50), (0.035, 0.27), 0.040, 0.032, "skin"), ("cap", (0.035, 0.27), (0.06, 0.02), 0.032, 0.024, "skin"),
                 ("poly", [(-0.056, 0.53), (0.058, 0.53), (0.07, 0.40), (-0.06, 0.40)], "bottom"),
                 ("poly", [(-0.052, 0.80), (0.05, 0.80), (0.045, 0.62), (0.055, 0.50), (-0.05, 0.50), (-0.045, 0.62)], "top"),
                 ("cap", (0.0, 0.78), (0.06, 0.66), 0.026, 0.022, "skin"), ("cap", (0.06, 0.66), (0.13, 0.69), 0.022, 0.018, "skin"),
                 ("ink", [(0.06, 0.56), (0.13, 0.69), (0.40, 0.98), (0.70, 1.18)], 0.014, "rod"),
                 ("ink", [(0.70, 1.18), (0.80, 0.90), (0.88, 0.50), (0.93, 0.0)], 0.006, "line")] + _head_side(hair) +
                [("poly", [(-0.07, 0.955), (0.09, 0.955), (0.06, 1.02), (-0.04, 1.02)], "accent")])          # bucket hat
    raise ValueError(pose)

def figure(pose, x, y, h_mm, outfit, sun=None, flip=False, shadow=True, shadow_col=None, lit_tint=0.18):
    """x, y: page position of the feet (normalised). h_mm: standing height in mm (A3 posters: ~10-25 mm)."""
    hp = h_mm / 25.4 * DPI; fx, fy = X(x), Y(y); sgn = -1 if flip else 1
    cols = {k: rgb(*v) if isinstance(v, tuple) else v for k, v in outfit.items()}
    cols.setdefault("skin2", cols["skin"] * 0.88)
    to_px = lambda p: (fx + sgn * p[0] * hp, fy - p[1] * hp)
    shapes = []
    for part in pose_parts(pose, outfit.get("hair_style", "short")):
        kind, key = part[0], part[-1]
        if kind == "cap": poly = capsule_px(to_px(part[1]), to_px(part[2]), part[3] * hp, part[4] * hp)
        elif kind == "circ":
            c = to_px(part[1]); r = part[2] * hp; poly = [(c[0] + r * np.cos(t), c[1] + r * np.sin(t)) for t in np.linspace(0, 2 * np.pi, 24)]
        elif kind == "poly": poly = [to_px(p) for p in part[1]]
        elif kind == "ink": shapes.append(("ink", [to_px(p) for p in part[1]], part[2] * hp, key)); continue
        shapes.append(("poly", poly, None, key))
    if shadow and sun is not None:
        m = np.zeros((H, W), f32)
        for kind, poly, _, key in shapes:
            if kind != "poly": continue
            g = [(px + (fy - py) * sun["sx"], fy + (fy - py) * sun["sy"]) for px, py in poly]
            m = np.maximum(m, poly_mask(g))
        fill(fastblur(m, 0.5 * K * 3 + 0.4), shadow_col if shadow_col is not None else rgb(150, 120, 110), 0.45, tex=0.0)
    off = (sun["light_x"] if sun else 0) * max(0.5, hp * 0.012)
    for kind, poly, wd, key in shapes:
        c = cols.get(key, cols.get("top"))
        if kind == "ink": ink_line(poly, wd, c); continue
        if off and key not in ("line",):          # lit edge on the sun side: a lighter copy nudged toward the light
            fill(poly_mask([(px + off, py) for px, py in poly]), c + (1 - c) * lit_tint, 1.0, tex=0.0)
        fill(poly_mask(poly), c, 1.0)
