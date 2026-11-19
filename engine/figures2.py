# Figure kit v2 (exec after engine.py, marks.py and figures.py for make_sun/SKINS/HAIRS/ink_line).
# Lessons from the references: figures are flowing painted silhouettes, not jointed sticks.
#  - limbs are single curves that taper (full thigh -> tiny ankle, shoulder -> fine wrist); no visible joints
#  - clothing defines the figure: dress, wetsuit, swimsuit, rucksack, trousers are big graphic shapes
#  - each colour group is ONE mask (joints vanish) painted with grain + strokes along the garment
#  - one line of action per pose; small head; hair as a brushy mass; no hands, feet as tiny wedges

def _catmull(pts, n=12, closed=False):
    p = np.asarray(pts, np.float64)
    if closed: p = np.vstack([p[-1], p, p[0], p[1]])
    else: p = np.vstack([2 * p[0] - p[1], p, 2 * p[-1] - p[-2]])
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed: out.append(p[-2])
    return np.array(out)

def ribbon(pts, widths, cap=True):
    """a limb: smooth curve through pts with a width profile (units of figure height); round-ish ends"""
    c = _catmull(pts, 10); w = np.interp(np.linspace(0, 1, len(c)), np.linspace(0, 1, len(widths)), widths) / 2
    d = np.gradient(c, axis=0); nr = np.stack([-d[:, 1], d[:, 0]], 1); nr /= np.linalg.norm(nr, axis=1, keepdims=True) + 1e-9
    L, R = c + nr * w[:, None], c - nr * w[:, None]
    out = list(L)
    if cap:
        a = np.arctan2(d[-1, 1], d[-1, 0]); out += [c[-1] + w[-1] * np.array([np.cos(a + q), np.sin(a + q)]) for q in np.linspace(np.pi / 2, -np.pi / 2, 7)]
    out += list(R[::-1])
    if cap:
        a = np.arctan2(d[0, 1], d[0, 0]); out += [c[0] + w[0] * np.array([np.cos(a + q), np.sin(a + q)]) for q in np.linspace(-np.pi / 2, -3 * np.pi / 2, 7)]
    return out

def blob(pts):
    """a garment / hair / object shape: smooth closed curve through control points"""
    return list(_catmull(pts, 10, closed=True))

def disc(cx, cy, r, squash=1.0, wob=0.0, seed=0):
    t = np.linspace(0, 2 * np.pi, 28, endpoint=False); rr = r * (1 + wob * np.sin(3 * t + seed))
    return [(cx + q * np.cos(a), cy + q * np.sin(a) * squash) for q, a in zip(rr, t)]

def board(cx, cy, length, width, angle):
    t = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    x = np.sign(np.cos(t)) * np.abs(np.cos(t)) ** 0.85 * length / 2; y = np.sign(np.sin(t)) * np.abs(np.sin(t)) ** 1.25 * width / 2
    ca, sa = np.cos(angle), np.sin(angle)
    return [(cx + a * ca - b * sa, cy + a * sa + b * ca) for a, b in zip(x, y)]

# ------------------------------------------------------------------ poses
# returns a list of LAYERS (painted in order); each layer = (group, [shapes in units], stroke_angle_deg)
def pose_layers(pose, opts=None):
    opts = opts or {}
    if pose == "board_under_arm":           # back view, wetsuit, board tucked under the near arm
        legs = [ribbon([(-0.045, 0.52), (-0.052, 0.28), (-0.046, 0.03)], [0.092, 0.06, 0.036]),
                ribbon([(0.045, 0.52), (0.054, 0.28), (0.05, 0.03)], [0.092, 0.06, 0.036])]
        torso = [blob([(-0.105, 0.80), (-0.09, 0.64), (-0.095, 0.50), (0, 0.47), (0.095, 0.50), (0.09, 0.64), (0.105, 0.80), (0, 0.845)])]
        far_arm = [ribbon([(-0.10, 0.785), (-0.13, 0.63), (-0.125, 0.48)], [0.055, 0.04, 0.026])]
        near_arm = [ribbon([(0.10, 0.785), (0.13, 0.67), (0.08, 0.605)], [0.056, 0.042, 0.03])]
        return [("garment", legs + torso + far_arm, 90), ("hair", [disc(0, 0.915, 0.06, 1.05, 0.04)], 60),
                ("accent", [board(0.03, 0.615, 0.78, 0.13, -0.10)], 0), ("garment", near_arm, 80)]
    if pose == "surfer_walk":               # back view, springsuit, board under the near arm: arm in front of the board, hand round the bottom rail
        calves = [ribbon([(-0.05, 0.285), (-0.056, 0.03)], [0.052, 0.032]), ribbon([(0.055, 0.295), (0.072, 0.045)], [0.052, 0.032])]
        feet = [blob([(-0.08, 0.0), (-0.03, 0.0), (-0.035, 0.035), (-0.075, 0.035)]), blob([(0.05, 0.02), (0.10, 0.025), (0.095, 0.055), (0.055, 0.052)])]
        suit_legs = [ribbon([(-0.045, 0.53), (-0.05, 0.27)], [0.098, 0.064]), ribbon([(0.045, 0.53), (0.056, 0.28)], [0.098, 0.064])]
        torso = [blob([(-0.105, 0.80), (-0.09, 0.64), (-0.095, 0.50), (0, 0.47), (0.095, 0.50), (0.09, 0.64), (0.105, 0.80), (0, 0.845)])]
        far_sleeve = [ribbon([(-0.10, 0.785), (-0.125, 0.665)], [0.058, 0.046])]
        far_fore = [ribbon([(-0.125, 0.665), (-0.12, 0.49)], [0.042, 0.026])]
        neck = [ribbon([(0, 0.815), (0, 0.87)], [0.046, 0.044])]
        hair = [disc(0, 0.918, 0.06, 1.05, 0.05)]
        BL, BW, BA, BC = 1.06, 0.27, -0.08, (0.05, 0.60)                        # board: ~1.85 m x 0.47 m for a 1.75 m surfer (width ~ quarter of length)
        brd = board(BC[0], BC[1], BL, BW, BA)
        band = [p for p in brd if p[0] > BC[0] + BL * 0.40]
        ca, sa = np.cos(BA), np.sin(BA)
        along = lambda u, v=0.0: (BC[0] + u * BL / 2 * ca - v * sa, BC[1] + u * BL / 2 * sa + v * ca)
        stringer = [along(u) for u in np.linspace(-0.92, 0.92, 6)]
        rail_y = along(0.13, -BW / 2)[1]                                        # bottom rail under the hand
        near_sleeve = [ribbon([(0.10, 0.785), (0.125, 0.665)], [0.058, 0.048])]
        near_fore = [ribbon([(0.125, 0.665), (0.135, 0.59), (0.122, rail_y + 0.012)], [0.042, 0.034, 0.030])]
        hand = [blob([(0.098, rail_y + 0.016), (0.146, rail_y + 0.014), (0.150, rail_y - 0.012), (0.104, rail_y - 0.016)])]
        return [("skin", calves + far_fore + neck, 90), ("skin2", feet, 0), ("garment", suit_legs + torso + far_sleeve, 90), ("hair", hair, 60),
                ("accent", [brd], 0), ("accent2", [band], 0), ("ink", stringer, 0.008, "stringer"),
                ("garment", near_sleeve, 80), ("skin", near_fore, 80), ("skin", hand, 0)]
    if pose == "dress_arms_out":            # back view, A-line dress, arms flung out in a loose curve
        legs = [ribbon([(-0.035, 0.44), (-0.038, 0.22), (-0.042, 0.03)], [0.05, 0.036, 0.02]),
                ribbon([(0.035, 0.44), (0.04, 0.22), (0.044, 0.03)], [0.05, 0.036, 0.02])]
        arms = [ribbon([(-0.07, 0.78), (-0.19, 0.83), (-0.31, 0.90), (-0.36, 0.93)], [0.05, 0.034, 0.02, 0.01]),
                ribbon([(0.07, 0.78), (0.18, 0.87), (0.27, 0.99), (0.30, 1.03)], [0.05, 0.034, 0.02, 0.01])]
        dress = [blob([(-0.075, 0.835), (0.0, 0.85), (0.075, 0.835), (0.10, 0.74), (0.135, 0.60), (0.18, 0.43), (0.06, 0.415), (-0.06, 0.415), (-0.18, 0.43), (-0.135, 0.60), (-0.10, 0.74)])]
        sleeves = [blob([(-0.10, 0.83), (-0.05, 0.84), (-0.06, 0.76), (-0.14, 0.76)]), blob([(0.10, 0.83), (0.05, 0.84), (0.06, 0.76), (0.14, 0.78)])]
        return [("skin", legs + arms, 90), ("garment", dress + sleeves, 95), ("hair", [disc(0.0, 0.905, 0.057, 1.05, 0.05), disc(0.022, 0.968, 0.03)], 60)]
    if pose == "dive":                      # arched body thrown up and out, legs together, arms spread
        legs = [ribbon([(-0.32, 0.03), (-0.19, 0.24), (-0.06, 0.45)], [0.012, 0.062, 0.105])]
        torso = [ribbon([(-0.03, 0.52), (0.03, 0.66), (0.065, 0.78)], [0.12, 0.11, 0.075])]
        arms = [ribbon([(0.04, 0.77), (-0.07, 0.89), (-0.17, 0.99)], [0.045, 0.03, 0.012]),
                ribbon([(0.08, 0.77), (0.21, 0.83), (0.34, 0.87)], [0.045, 0.03, 0.012])]
        suit = [blob([(-0.105, 0.43), (-0.02, 0.40), (0.06, 0.53), (0.05, 0.63), (-0.03, 0.61), (-0.09, 0.51)])]
        head = [disc(0.10, 0.865, 0.052)]
        hair = [blob([(0.055, 0.88), (0.09, 0.93), (0.15, 0.925), (0.18, 0.88), (0.15, 0.85), (0.11, 0.86)])]
        return [("skin", legs + torso + arms + head, 40), ("garment", suit, 40), ("hair", hair, 20)]
    if pose == "walker_pack":               # back view, big rucksack, dark trousers, mid-stride
        legs = [ribbon([(-0.04, 0.52), (-0.046, 0.28), (-0.054, 0.05)], [0.085, 0.062, 0.05]),
                ribbon([(0.04, 0.52), (0.05, 0.29), (0.064, 0.06)], [0.085, 0.062, 0.05])]
        boots = [blob([(-0.08, 0.0), (-0.025, 0.0), (-0.03, 0.05), (-0.075, 0.05)]), blob([(0.035, 0.012), (0.09, 0.015), (0.085, 0.065), (0.04, 0.062)])]
        jacket = [blob([(-0.10, 0.81), (-0.10, 0.62), (-0.095, 0.50), (0.095, 0.50), (0.10, 0.62), (0.10, 0.81), (0, 0.84)]),
                  ribbon([(-0.10, 0.78), (-0.12, 0.64), (-0.115, 0.50)], [0.05, 0.04, 0.03]), ribbon([(0.10, 0.78), (0.12, 0.64), (0.115, 0.50)], [0.05, 0.04, 0.03])]
        pack = [blob([(-0.11, 0.87), (0.0, 0.895), (0.11, 0.87), (0.13, 0.72), (0.12, 0.53), (0.0, 0.51), (-0.12, 0.53), (-0.13, 0.72)])]
        return [("garment2", legs, 90), ("shoes", boots, 0), ("garment", jacket, 90), ("hair", [disc(0, 0.935, 0.055, 1.05, 0.03)], 60), ("accent", pack, 90)]
    if pose == "cartwheel":                 # inverted on one hand, legs flung wide
        arms = [ribbon([(0.0, 0.01), (0.02, 0.17), (0.045, 0.33)], [0.018, 0.03, 0.05]), ribbon([(0.12, 0.02), (0.105, 0.17), (0.085, 0.33)], [0.018, 0.03, 0.05])]
        head = [disc(0.06, 0.26, 0.052)]
        hair = [blob([(0.02, 0.30), (0.10, 0.30), (0.11, 0.20), (0.08, 0.08), (0.04, 0.09), (0.015, 0.20)])]
        top = [ribbon([(0.065, 0.33), (0.09, 0.47), (0.11, 0.60)], [0.11, 0.105, 0.095])]
        trousers = [ribbon([(0.10, 0.60), (0.0, 0.77), (-0.13, 0.88)], [0.075, 0.055, 0.04]), ribbon([(0.12, 0.62), (0.25, 0.75), (0.38, 0.80)], [0.075, 0.055, 0.04])]
        feet = [ribbon([(-0.13, 0.88), (-0.18, 0.90)], [0.03, 0.012]), ribbon([(0.38, 0.80), (0.43, 0.81)], [0.03, 0.012])]
        return [("skin", arms + head + feet, 80), ("hair", hair, 90), ("garment", top, 60), ("garment2", trousers, 40)]
    if pose == "board_on_head":             # walking, board balanced on the head, both arms up
        legs = [ribbon([(-0.035, 0.49), (-0.032, 0.26), (-0.025, 0.03)], [0.056, 0.042, 0.026]),
                ribbon([(0.035, 0.49), (0.05, 0.27), (0.072, 0.04)], [0.056, 0.042, 0.026])]
        shorts = [blob([(-0.088, 0.53), (0.088, 0.53), (0.10, 0.40), (0.01, 0.40), (-0.10, 0.40)])]
        top = [blob([(-0.092, 0.81), (0.092, 0.81), (0.085, 0.53), (-0.085, 0.53)]),
               ribbon([(-0.085, 0.79), (-0.125, 0.92), (-0.09, 1.02)], [0.048, 0.036, 0.026]), ribbon([(0.085, 0.79), (0.125, 0.92), (0.09, 1.02)], [0.048, 0.036, 0.026])]
        return [("skin", legs + [disc(0, 0.905, 0.056)], 90), ("garment2", shorts, 90), ("garment", top, 90), ("hair", [blob([(-0.055, 0.92), (0.0, 0.965), (0.055, 0.92), (0.03, 0.89), (-0.03, 0.89)])], 0),
                ("accent", [board(0.02, 1.05, 0.74, 0.11, 0.06)], 0)]
    if pose == "lie_read":                  # on the front, propped on elbows, one foot kicked up
        legs = [ribbon([(-0.06, 0.035), (0.17, 0.05), (0.40, 0.075)], [0.026, 0.05, 0.08]),
                ribbon([(0.02, 0.05), (0.20, 0.06), (0.38, 0.078)], [0.026, 0.05, 0.08])]
        arms = [ribbon([(0.68, 0.16), (0.735, 0.04), (0.86, 0.055)], [0.05, 0.032, 0.018])]
        suit = [blob([(0.37, 0.03), (0.38, 0.115), (0.55, 0.16), (0.68, 0.21), (0.72, 0.12), (0.60, 0.05)])]
        head = [disc(0.79, 0.215, 0.06)]
        hair = [blob([(0.735, 0.225), (0.78, 0.28), (0.845, 0.27), (0.865, 0.20), (0.855, 0.12), (0.81, 0.15)])]
        book = [blob([(0.835, 0.035), (0.895, 0.105), (0.955, 0.045), (0.895, 0.02)])]
        return [("skin", legs + arms + head, 5), ("garment", suit, 15), ("hair", hair, 60), ("accent", book, 0)]
    if pose == "fish":                      # side view, rod raised over the water
        legs = [ribbon([(0.0, 0.52), (-0.012, 0.28), (-0.035, 0.04)], [0.085, 0.06, 0.045]), ribbon([(0.02, 0.52), (0.045, 0.28), (0.07, 0.04)], [0.085, 0.06, 0.045])]
        top = [blob([(-0.06, 0.81), (0.06, 0.80), (0.07, 0.62), (0.06, 0.50), (-0.065, 0.50), (-0.07, 0.62)])]
        arms = [ribbon([(0.0, 0.78), (0.065, 0.665), (0.13, 0.70)], [0.05, 0.036, 0.022])]
        return [("garment2", legs, 90), ("garment", top, 90), ("skin", [disc(0.015, 0.905, 0.055)] + arms, 60),
                ("hair", [blob([(-0.045, 0.93), (0.0, 0.965), (0.04, 0.93), (-0.01, 0.875)])], 60), ("accent", [blob([(-0.08, 0.945), (0.10, 0.945), (0.065, 1.015), (-0.045, 1.015)])], 0),
                ("ink", [(0.06, 0.56), (0.13, 0.70)] + opts.get("rod", [(0.40, 0.98), (0.70, 1.18)]), 0.014, "rod"),
                ("ink", opts.get("line", [(0.70, 1.18), (0.82, 0.80), (0.92, 0.30), (0.98, -0.30)]), 0.006, "line")]
    if pose == "kite_flyer":                # back view, braced, holding the string out in front at chest height: the body hides the hands, only the elbows show
                                            # (draw the string BEFORE the figure, from KITE_HAND, so the body covers its start)
        legs = [ribbon([(-0.035, 0.50), (-0.055, 0.27), (-0.08, 0.03)], [0.088, 0.058, 0.034]),
                ribbon([(0.04, 0.50), (0.058, 0.27), (0.075, 0.03)], [0.088, 0.058, 0.034])]
        feet = [blob([(-0.115, 0.0), (-0.065, 0.0), (-0.07, 0.035), (-0.11, 0.032)]), blob([(0.045, 0.0), (0.098, 0.004), (0.092, 0.038), (0.052, 0.036)])]
        # fitted, mid-thigh: two leg openings that hug the thighs and a short split that stops below where the thighs meet (no skin in the fork), so the shorts never read as a flared skirt (or hot pants)
        shorts = [blob([(-0.093, 0.56), (0.0, 0.565), (0.095, 0.56), (0.094, 0.48), (0.091, 0.42), (0.088, 0.36), (0.05, 0.352), (0.015, 0.36), (0.0, 0.40),
                        (-0.012, 0.36), (-0.05, 0.352), (-0.088, 0.36), (-0.091, 0.42), (-0.093, 0.48)])]
        torso = [blob([(-0.092, 0.80), (0.0, 0.825), (0.092, 0.80), (0.099, 0.66), (0.094, 0.54), (-0.094, 0.54), (-0.099, 0.66)])]
        elbows = [ribbon([(s * 0.085, 0.775), (s * 0.118, 0.705), (s * 0.07, 0.68)], [0.05, 0.04, 0.036]) for s in (-1, 1)]   # arms forward: just the elbows show past the body
        sleeves = [ribbon([(s * 0.075, 0.79), (s * 0.108, 0.735)], [0.066, 0.058]) for s in (-1, 1)]
        return [("skin", legs + [ribbon([(0.0, 0.81), (0.0, 0.87)], [0.044, 0.042])], 90), ("skin2", feet, 0),
                ("garment2", shorts, 90), ("skin", elbows, 70), ("garment", torso + sleeves, 90),
                ("hair", [disc(0.0, 0.912, 0.06, 1.05, 0.05)], 60)]
    if pose == "float":                     # seen from above, floating on the back in a starfish, head away from the viewer (y = toward the head)
        # call with shadow=False: a body lying in water gets ripples / a waterline from the poster script, never a standing shadow.
        # h_mm = the body's foreshortened length on the page; opts["aspect"] widens x to undo that foreshortening; opts["rot"] turns the body (deg).
        legs = [ribbon([(-0.05, 0.50), (-0.11, 0.27), (-0.17, 0.05)], [0.094, 0.062, 0.034]),
                ribbon([(0.05, 0.50), (0.10, 0.28), (0.13, 0.05)], [0.094, 0.062, 0.034])]
        feet = [disc(-0.176, 0.035, 0.022, 1.3), disc(0.136, 0.035, 0.022, 1.3)]
        arms = [ribbon([(-0.095, 0.785), (-0.20, 0.885), (-0.29, 1.00)], [0.056, 0.04, 0.024]),
                ribbon([(0.095, 0.785), (0.215, 0.865), (0.32, 0.95)], [0.056, 0.04, 0.024])]
        neck = [ribbon([(0, 0.80), (0, 0.865)], [0.046, 0.044])]
        head = [disc(0, 0.915, 0.06, 1.05)]
        hair = [blob([(-0.07, 0.90), (-0.12, 0.95), (-0.13, 1.02), (-0.07, 1.08), (0.0, 1.10), (0.08, 1.075), (0.135, 1.01), (0.115, 0.94), (0.07, 0.90), (0.0, 0.93)])]   # fanned out on the water
        suit = [blob([(-0.105, 0.80), (-0.05, 0.795), (0.0, 0.765), (0.05, 0.795), (0.105, 0.80), (0.09, 0.64), (0.10, 0.50), (0.05, 0.445),
                      (0.0, 0.43), (-0.05, 0.445), (-0.10, 0.50), (-0.09, 0.64)])]
        ax = opts.get("aspect", 1.0); ra = np.radians(opts.get("rot", 0.0)); ca, sa = np.cos(ra), np.sin(ra)
        sx = lambda shapes: [[((p[0] * ca - (p[1] - 0.5) * sa) * ax, 0.5 + p[0] * sa + (p[1] - 0.5) * ca) for p in s] for s in shapes]
        return [("hair", sx(hair), 90), ("skin", sx(legs + feet + arms + neck + head), 90), ("garment", sx(suit), 90)]
    if pose == "sit":                       # back view, seated on an edge (a jetty's end), legs hanging over it; y = 0 is the SEAT, not the feet
                                            # same head / torso / limb widths as the standing poses (torso hip-to-shoulder 0.30, head r 0.06)
                                            # opts: shins=False when the edge hides the hanging legs (viewer above the seat, e.g. looking down a jetty)
        o = opts or {}
        seat = [blob([(-0.118, 0.08), (-0.124, 0.025), (-0.07, -0.004), (0.0, 0.004), (0.07, -0.004), (0.124, 0.025), (0.118, 0.08), (0.0, 0.10)])]
        torso = [blob([(-0.100, 0.330), (-0.060, 0.362), (0.0, 0.372), (0.060, 0.362), (0.100, 0.330), (0.106, 0.24), (0.108, 0.17), (0.120, 0.11), (0.118, 0.075),
                       (0.0, 0.06), (-0.118, 0.075), (-0.120, 0.11), (-0.108, 0.17), (-0.106, 0.24)])]      # sloping shoulders, the jacket flaring over the seat (no gap at the arms)
        arms = [ribbon([(s * 0.096, 0.322), (s * 0.128, 0.20), (s * 0.150, 0.06)], [0.058, 0.048, 0.042]) for s in (-1, 1)]   # sleeves to the wrist, hands on the edge
        hands = [blob([(s * 0.136, 0.05), (s * 0.172, 0.05), (s * 0.176, 0.008), (s * 0.132, 0.008)]) for s in (-1, 1)]
        neck = [ribbon([(0.0, 0.345), (0.0, 0.405)], [0.044, 0.042])]
        hair = [disc(0.0, 0.448, 0.06, 1.05, 0.05)]
        shins = []
        if o.get("shins", True):
            shins = [ribbon([(s * 0.052, 0.02), (s * 0.056, -0.13), (s * 0.062, -0.26)], [0.074, 0.054, 0.036]) for s in (-1, 1)]
        feet = [blob([(s * 0.04, -0.255), (s * 0.085, -0.255), (s * 0.08, -0.29), (s * 0.045, -0.29)]) for s in (-1, 1)] if shins else []
        out = [("skin", neck, 90)]
        if shins: out += [("garment2", shins, 90), ("skin2", feet, 0)]
        if not o.get("detail", False):
            return out + [("garment2", seat, 0), ("garment", torso + arms, 90), ("skin", hands, 0), ("hair", hair, 60)]
        # detail=True, for a larger figure (about 25 mm seated and up): an anorak with a hood lying on the back, a hem band and cuffs,
        # a few creases (ink lines), and hair gathered in a low knot with lighter strands. Groups: garment3 = the jacket's
        # deeper trim, fold = crease colour, hair2 = lit strands. Outfits without them fall back to the garment colour.
        tilt = o.get("tilt", 0.012)                                      # head turned a touch to the right, looking out
        hair = [blob([(-0.058 + tilt, 0.452), (-0.050 + tilt, 0.492), (-0.022 + tilt, 0.512), (0.012 + tilt, 0.514), (0.046 + tilt, 0.498),
                      (0.062 + tilt, 0.462), (0.058 + tilt, 0.420), (0.040 + tilt, 0.395), (0.0 + tilt, 0.388), (-0.040 + tilt, 0.396), (-0.060 + tilt, 0.418)])]
        knot = [disc(0.006 + tilt, 0.398, 0.034, 0.80, 0.06, 2)]           # a low knot at the nape
        strands = [ribbon([(0.004 + tilt, 0.506), (0.034 + tilt, 0.492), (0.050 + tilt, 0.462), (0.046 + tilt, 0.430)], [0.006, 0.010, 0.008, 0.003]),
                   ribbon([(-0.016 + tilt, 0.508), (0.006 + tilt, 0.488), (0.020 + tilt, 0.458), (0.016 + tilt, 0.426)], [0.004, 0.007, 0.005, 0.002]),
                   ribbon([(0.020 + tilt, 0.420), (0.026 + tilt, 0.406), (0.020 + tilt, 0.392)], [0.006, 0.008, 0.003])]
        hood = [blob([(-0.080, 0.352), (-0.078, 0.300), (-0.050, 0.262), (0.0, 0.250), (0.050, 0.262), (0.078, 0.300), (0.080, 0.352), (0.0, 0.372)])]
        hem = [blob([(-0.116, 0.074), (-0.113, 0.104), (-0.05, 0.097), (0.0, 0.095), (0.05, 0.097), (0.113, 0.104), (0.116, 0.074), (0.0, 0.058)])]
        cuffs = [ribbon([(s * 0.143, 0.098), (s * 0.149, 0.070)], [0.046, 0.044]) for s in (-1, 1)]
        out += [("garment2", seat, 0), ("garment", torso + arms, 90), ("garment3", hood + hem + cuffs, 0)]
        folds = [("ink", [(-0.070, 0.115), (-0.050, 0.140), (-0.026, 0.158)], 0.0055, "fold"),        # creases where the back bends over the seat
                 ("ink", [(0.060, 0.120), (0.042, 0.150), (0.020, 0.168)], 0.0050, "fold"),
                 ("ink", [(-0.010, 0.128), (0.006, 0.150)], 0.0040, "fold"),
                 ("ink", [(-0.040, 0.268), (-0.012, 0.232), (0.016, 0.228)], 0.0045, "fold"),        # the hood's shadow on the back
                 ("ink", [(-0.122, 0.215), (-0.110, 0.196)], 0.0045, "fold"),                        # elbow creases
                 ("ink", [(0.124, 0.212), (0.112, 0.193)], 0.0045, "fold")]
        return out + folds + [("skin", hands, 0), ("hair", hair + knot, 60), ("hair2", strands, 70)]
    raise ValueError(pose)

KITE_HAND = (0.0, 0.72)                     # kite_flyer: where the hands hold the string (in front of the chest), in figure units (x right, y up, 1 = standing height)

def figure2(pose, x, y, h_mm, outfit, sun=None, flip=False, shadow=True, shadow_col=None, seed=0, edge=0.8, ground=None, sunw=None):
    """x, y: page position of the feet (normalised). h_mm: standing height in mm. Painted, not filled."""
    global EDGE_TOOTH
    hp = h_mm / 25.4 * DPI; fx, fy = X(x), Y(y); sgn = -1 if flip else 1
    LYING = {"lie_read": 0.026}                                     # lift to remove so the body rests on the ground line
    drop = LYING.get(pose, 0.0)
    cols = {k: rgb(*v) for k, v in outfit.items() if isinstance(v, tuple) and len(v) == 3}
    cols.setdefault("skin2", cols.get("skin", rgb(180, 130, 100)) * 0.9)
    to_px = lambda p: (fx + sgn * p[0] * hp, fy - (p[1] - drop) * hp)
    layers = []
    for L in pose_layers(pose, outfit.get("opts")):
        if L[0] == "ink": layers.append(L); continue
        g, shapes, ang = L
        layers.append((g, [[to_px(p) for p in s] for s in shapes], ang))
    if shadow and (sun is not None or (ground is not None and sunw is not None)):
        m = np.zeros((H, W), f32)
        if ground is not None and sunw is not None:              # shadow worked out in metres on the sand, projected through the scene camera
            Xf, Zf = ground.to_world(x, y); mf = ground.m(y)
            def proj(px, py):
                dx_m = (px - fx) / H / mf; h_m = max(0.0, (fy - py) / H / mf)
                gx, gy = ground_shadow(ground, sunw, Xf + dx_m, Zf, h_m); return (X(gx), Y(gy))
        else:
            proj = lambda px, py: (px + (fy - py) * sun["sx"], fy + (fy - py) * sun["sy"])
        for L in layers:
            if L[0] == "ink": continue
            for poly in L[1]:
                m = np.maximum(m, poly_mask([proj(px, py) for px, py in poly]))
        if pose in LYING:                                          # contact shadow only: hugs the body where it meets the ground
            m = m * (1 - smooth(0.0, 0.06 * hp, (np.arange(H, dtype=f32)[:, None] * 0 + (fy - yy * H))))
            fill(fastblur(m, 0.4 * K * 3 + 0.4), shadow_col if shadow_col is not None else rgb(150, 120, 110), 0.30, tex=0.0)
        else:
            fill(fastblur(m, 0.6 * K * 3 + 0.5), shadow_col if shadow_col is not None else rgb(150, 120, 110), 0.42, tex=0.0)
    keep = EDGE_TOOTH; EDGE_TOOTH = edge                              # figures get a softer, brushier edge
    lx = sun["light_x"] if sun else -1.0
    for k, L in enumerate(layers):
        if L[0] == "ink":
            _, pts, wd, key = L; ink_line([to_px(p) for p in pts], wd * hp, cols.get(key, rgb(60, 50, 52))); continue
        g, polys, ang = L
        M = np.zeros((H, W), f32)
        for poly in polys: M = np.maximum(M, poly_mask(poly))
        c = cols.get(g, cols.get("garment"))
        S = streaks(SRC_FINE, angle=np.radians(ang) * sgn, su=0.9, sv=1.1, seed=seed * 31 + k) * 0.6
        paint(M, c, c * 0.88, S=S, soft=0.5, wob=0.4, wob_scale=12, width=0.12, dry=0.03, dry_edge=0.35, mot=0.8, rim=0.03,
              seed=seed * 31 + k, valvar=0.06, cvar=0.5, gran=0.06, edge_tex=1.0)
        # form: a light glaze on the sun side of each colour group
        ys_, xs_ = np.nonzero(M > 0.5)
        if len(xs_):
            cx0, wpx = xs_.mean(), max(2.0, xs_.std() * 2)
            side = smooth(-0.2, 0.9, (xx * W - cx0) / wpx * lx).astype(f32)
            paint(M * side, c + (1 - c) * 0.22, c + (1 - c) * 0.16, soft=1.5, wob=0.3, wob_scale=12, width=0.3, dry=0.15, dry_edge=0.4, mot=0.4,
                  rim=0.0, seed=seed * 31 + k + 7, alpha=0.5, edge_tex=0.5)
    EDGE_TOOTH = keep

def wading(before, x, y, h_mm, ground, depth_m=0.12, foam=None, seed=0, refl=0.6, water=None):
    """A standing figure in shallow water. Call right after figure2(..., shadow=False), with before = canvas.copy() taken just
    before it. On water a figure shows a reflection, not a cast shadow (the surface hides it), so: the feet are seen through
    the water, the reflection hangs below the waterline broken by ripples, and ripple rings (ellipses from the scene camera,
    at the water surface) circle the legs. The half of each ring behind the legs is hidden by them.
    water: optional mask (1 = water); the reflection and rings stay on it, so neither crosses onto the foam or the sand."""
    global canvas
    r = np.random.default_rng(seed); hp = h_mm / 25.4 * DPI; fx, fy = X(x), Y(y)
    y0, y1 = int(max(0, fy - hp * 1.15)), int(min(H, fy + hp * 0.9)); x0, x1 = int(max(0, fx - hp * 0.7)), int(min(W, fx + hp * 0.7))
    reg = canvas[y0:y1, x0:x1].copy(); bef = before[y0:y1, x0:x1]; fig_only = reg.copy()
    M = smooth(0.015, 0.06, np.abs(reg - bef).sum(-1))
    yw = fy - depth_m * ground.m(y) * H                                  # waterline on the legs, px
    rows = np.arange(y0, y1, dtype=f32)[:, None]
    sub = (smooth(yw - 1, yw + 1, rows) * M)[..., None]                 # 1 feet seen through the water
    reg = reg * (1 - 0.65 * sub) + bef * (0.65 * sub)
    R = np.zeros_like(reg); RA = np.zeros(M.shape, f32)                 # 2 reflection: mirrored about the waterline, rows wobble sideways
    jit = {}; hp80 = h_mm / 25.4 * REF_DPI; fy80 = y * H_REF                # one phase per reflected row of the 80 dpi page (RULES 56):
    y080, y180 = int(max(0, fy80 - hp80 * 1.15)), int(min(H_REF, fy80 + hp80 * 0.9)); yw80 = fy80 - depth_m * ground.m(y) * H_REF
    for i in range(y180 - y080):                                         # drawn first, in the order the rows used to draw them
        if i + y080 <= yw80: continue
        if int(round(2 * (yw80 - y080) - i)) < 0: break
        jit[i + y080] = r.uniform(-0.6, 0.6)
    jk = sorted(jit) or [0]
    for i in range(y1 - y0):
        if i + y0 <= yw: continue
        sr = int(round(2 * (yw - y0) - i))
        if sr < 0: break
        ph = jit.get(min(max(int(round((i + y0) * H_REF / H)), jk[0]), jk[-1]), 0.0)
        sh = int(round(0.008 * hp * np.sin((i + y0 - yw) / (0.035 * hp) * 2 * np.pi + ph)))
        R[i] = np.roll(reg[sr], sh, axis=0); RA[i] = np.roll(M[sr] * (sr + y0 < yw), sh)
    dist = np.clip((rows - yw) / hp, 0, None)
    bands = smooth(-0.6, 0.4, np.sin((rows - yw) / (0.02 * hp) * 2 * np.pi + 3.0 * lowfreq(0.05 * hp, seed, 2)[y0:y1, x0:x1]))
    a = (RA * np.exp(-dist / 0.28) * (0.55 + 0.45 * bands) * refl)[..., None]
    reg = reg * (1 - a) + (bef * 0.45 + R * 0.55) * a
    canvas[y0:y1, x0:x1] = reg
    keep = reg.copy(); above = M * (rows < yw)
    if foam is None: foam = np.clip(bef.reshape(-1, 3).mean(0) * 1.15 + 0.12, 0, 1)
    Xf, Zf = ground.to_world(x, y); mm = DPI / 25.4
    G0 = Ground(ground.HZ, y, ground.mm(y, 1.0) * 1.0, ref_m=1.0, F=ground.F, vpx=x)        # same camera, centred on the figure: no wide-angle skew
    for k, (rad, wd, al) in enumerate([(0.16, 0.5, 0.75), (0.28, 0.42, 0.45), (0.42, 0.35, 0.22)]):   # ripple rings: irregular, broken, fading out
        t = np.linspace(0, 2 * np.pi, 120) + r.uniform(0, 6)
        rr = rad * (1 + 0.08 * np.sin(t * 3 + r.uniform(0, 6)) + 0.05 * np.sin(t * 5 + r.uniform(0, 6)))
        X0, Z0 = G0.to_world(x, y)
        pts = np.array([G0.from_world(X0 + q * np.cos(a_) * 1.2, Z0 + q * np.sin(a_), depth_m) for a_, q in zip(t, rr)])
        on = np.sin(t * r.uniform(2.0, 3.0) + r.uniform(0, 6)) + 0.5 * np.sin(t * 7 + r.uniform(0, 6)) > 0.1
        i = 0
        while i < len(t):
            if not on[i]: i += 1; continue
            j = i
            while j < len(t) and on[j]: j += 1
            if j - i > 3: ink_line(np.stack([pts[i:j, 0] * W, pts[i:j, 1] * H], 1), wd * mm, foam, al)
            i = j
    cols_ = np.nonzero(M[int(round(yw)) - y0] > 0.5)[0] if y0 <= yw < y1 else []          # a light line where each leg meets the water
    if len(cols_):
        runs = np.split(cols_, np.nonzero(np.diff(cols_) > 1)[0] + 1)
        for run in runs:
            a0, a1 = run[0] - 0.25 * len(run), run[-1] + 0.25 * len(run)
            ink_line([(x0 + a0, yw + 0.5), (x0 + (a0 + a1) / 2, yw + 1.0), (x0 + a1, yw + 0.5)], 0.5 * mm, foam, 0.9)
    reg = canvas[y0:y1, x0:x1]
    reg = reg * (1 - above[..., None]) + keep * above[..., None]
    if water is not None:                                                # off the water: back to the figure and what was behind it
        Wm = water[y0:y1, x0:x1][..., None]; reg = reg * Wm + fig_only * (1 - Wm)
    canvas[y0:y1, x0:x1] = reg
