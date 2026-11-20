"""Per-format layout tables for ep4: every position, size, font size and path that differs between the landscape film
(1920 x 1080, approved) and the 9:16 reel (1080 x 1920, docs/REEL_LAYOUT.md).

    from ep4 import layout as L
    L.WIN_C, L.TITLE["px"], L.S4["reply_px"], ...        # values for the active EP4_FORMAT (ep4.common.FORMAT)
    L.LANDSCAPE["WIN_C"], L.REEL["WIN_C"]                 # either table explicitly

Rules:
- LANDSCAPE holds the values the modules hard-code today, verbatim (same expressions, so the floats are bit-identical):
  switching a module from its literal to `L.<name>` must leave the landscape render pixel-identical.
- REEL holds the numbers from docs/REEL_LAYOUT.md / out/ep4_reel/layout.json, in output px (no F multiplier).
- Both tables have exactly the same keys (checked at import). Where the two formats need a different *shape* of data
  (the s5 word cloud), both shapes are present and the unused one is None.
- Plate geometry (horizon, window) for the running video comes from the masks npz written by ep4.backdrops; the
  PLATE_* values here are what the backdrop recipe paints, kept for reference and for checks.
"""
from ep4.common import FORMAT, A, F, INK, TAG_LIGHT

# the landscape window centre, as painted (out/ep4/dusk_masks.npz "win" x 1920 x 1080); the video reads the npz
_WIN_LAND = (1501.44, 485.91)
_WIN_REEL = (680.0, 980.0)


def _U(x, y):
    """the reel figure map: landscape uncle px -> reel px (REEL_LAYOUT §2 s3/s5: x' = 60 + (x - 393) 1.25, ...)"""
    return (60 + (x - 393) * 1.25, 600 + (y - 172) * 1.25)


LANDSCAPE = dict(
    W=1920, H=1080, SAFE=(0, 0, 1920, 1080), GRID=None,
    OUT_DIR="out/ep4", DELIVER="deliver/ep4_vN.mp4",

    # ---- plates (ep4/backdrops.py) ----
    PLATE_HZ=0.58, PLATE_WIN=_WIN_LAND,
    UNCLE_MAP=dict(scale=1.0, ref=(0.0, 0.0), origin=(0.0, 0.0)),     # uncle polygons are already in frame px

    # ---- s1/s2 camera (ep4/video.py dusk_box) and gulls (ep4/seasky.py) ----
    DUSK_ZOOM0=2.0,                              # zoom at t = 0, eased to 1.0 over TILT
    DUSK_CX=(0.32, 0.18),                        # centre x = (a + b p) W
    DUSK_CY=(0.25, 0.25),                        # centre y = (a + b p) H
    PARALLAX=70,                                 # near-plane lead in source px (timeline.PARALLAX)
    PUSH_S2=0.06, PUSH_S8=0.04,
    BIRDS=[(380, 0.17, 40, 0.0, 17), (560, 0.21, 34, 1.3, 14), (470, 0.13, 46, 2.1, 19)],   # (x0 px, y frac, px/s, phase, half-span)

    # ---- envelope flights (ep4/seasky.py PATH_*, sizes/rotations at the video.py call sites) ----
    PATH_OUT=[(-182, 1154), (502, 728), (1097, 408)],      # + the plate window (KD_win) as the 4th point
    PATH_OUT_TRAIL=dict(spacing=(40, 24), radius=(1.7, 3.6)),
    PATH_HOME=[(1198, 508), (700, 765), (559, 859)],       # after the plate window (KN_win) as the 1st point
    PATH_HOME_TRAIL=dict(spacing=(20, 17), radius=(1.5, 3.4)),
    FLY_OUT_SIZE=(260, 16), FLY_OUT_ROT=(-14, -2),
    FLY_HOME_SIZE=(16, 300), FLY_HOME_ROT=(0, 8),

    # ---- title (ep4/cards.py title_reveal / tag) ----
    TITLE=dict(lines=["THE UNCLE WHO ONLY READS LETTERS"], px=22 * F, track_em=0.10, pad=(14 * F, 9 * F),
               line_gap=10 * F, pos=(64 * F, 1080 - 64 * F), anchor="bl", line_delay=0.0, fg=INK, bg=TAG_LIGHT),

    # ---- the uncle (ep4/uncle.py, ep4/transitions.py) ----
    WIN_C=(0.27975 * 1920, 0.2924 * 1080), WIN_R=62 * F,
    ICON_W=112, BREATH_HEAD=2.2, BREATH_BODY=1.2,
    LETTER=dict(w=420 * F, px=30 * F, size_arg=30, rot=-2, pad=None, lh_em=None, para_em=None),   # cards.card(LETTER_LINES, 420*F, -2)
    CARD_CENTRE=(1460.0, 541.0), CARD_OFF=912,
    WORDS=[("spinach", 26, 0, 90, .85), ("eggs", 24, 60, 160, .75), ("tonight", 22, 150, 40, .6),
           ("omelette", 22, 200, 220, .55), ("Dear Uncle", 20, 290, 120, .45), ("butter", 18, 380, 290, .35),
           ("Sam", 16, 470, 60, .25), ("fold", 15, 520, 190, .2), ("cook", 13, 610, 260, .12), ("love", 12, 660, 140, .08)],
    WORDS_PX=None,                               # reel only
    WORD_ORIGIN=(790, 145), WORD_EMERGE=(812, 360),

    # ---- s4 yellow (ep4/cards.py scene_reply, prompt_box, text_block) ----
    S4=dict(box_xy=(240 * F, 150 * F), box_w=800 * F, box_px=28 * F, box_lh_em=1.4, box_radius=18 * F,
            box_outline=int(2 * F), box_pad=(32 * F, 26 * F), box_trim_em=0.0,
            reply_px=34 * F, reply_dx=244 * F, reply_gap=40 * F, reply_measure=800 * F, reply_lh=48 * F,
            cursor=(6 * F, 9 * F), group_cy=None),
    # ---- s6 pink (scene_second) ----
    S6=dict(box_xy=(240 * F, 190 * F), box_w=800 * F, box_px=30 * F, box_lh_em=1.4, box_radius=18 * F,
            box_outline=int(2 * F), box_pad=(32 * F, 26 * F), box_trim_em=0.0,
            hl_pad=(5 * F, 5.5 * F), hl_h_em=1.28,
            ans_px=40 * F, ans_dx=244 * F, ans_gap=44 * F, ans_measure=800 * F, ans_lh=40 * F * 1.35, group_cy=None),
    # ---- s7 cream (scene_history) ----
    S7=dict(card_w=500 * F, text_px=22 * F, size_arg=22, label_px=13 * F, label_track_em=0.14, pad=42 * F,
            lh_em=1.48, para_em=0.62, rots=(3, -1.5, 1),
            card_pos=[(110 * F - 40, 140 * F - 40), (150 * F - 40, 300 * F - 40), (125 * F - 40, 470 * F - 40)],
            card_x=None, card_overlap=None, stack_cy=None,
            tape_wh=(138, 40), tape_spec=[(0.46, 4.5, 1), (0.55, -5.0, 2), (0.80, 3.5, 3)],
            arrow_width=3.6, arrow_head=17 * F, arrow_waypoints=None,
            ans2_px=34 * F, ans2_xy=(760 * F, 300 * F), ans2_gap=None, ans2_measure=420 * F, ans2_lh=34 * F * 1.35),

    # ---- wipes (ep4/sheets.py, ep4/video.py) and sound ----
    WIPES=dict(w4="left", w5="down", w6="up", w7="left"),
    W6_PAN=None,                                 # optional reel-only pan of the w6 slide (ep4/audio.py)
)


REEL = dict(
    W=1080, H=1920, SAFE=(60, 250, 960, 1470), GRID=(0, 240, 1080, 1680),
    OUT_DIR="out/ep4_reel", DELIVER="deliver/ep4_reel_vN.mp4",

    PLATE_HZ=1150 / 1920, PLATE_WIN=_WIN_REEL,
    UNCLE_MAP=dict(scale=1.25, ref=(393.0, 172.0), origin=(60.0, 600.0)),   # x' = origin + (x - ref) * scale

    DUSK_ZOOM0=2.0,
    DUSK_CX=(0.45, 0.05),                        # almost purely vertical: a real tilt
    DUSK_CY=(0.25, 0.25),
    PARALLAX=90,
    PUSH_S2=0.06, PUSH_S8=0.04,
    BIRDS=[(330, 0.12, 40, 0.0, 17), (470, 0.15, 34, 1.3, 14), (400, 0.10, 46, 2.1, 19)],

    PATH_OUT=[(-150, 1330), (330, 1280), (540, 1100)],     # + WIN (680, 980)
    PATH_OUT_TRAIL=dict(spacing=(40, 24), radius=(1.7, 3.6)),
    PATH_HOME=[(480, 900), (300, 1140), (430, 1290)],      # after WIN
    PATH_HOME_TRAIL=dict(spacing=(20, 17), radius=(1.5, 3.4)),
    FLY_OUT_SIZE=(280, 16), FLY_OUT_ROT=(-14, -2),
    FLY_HOME_SIZE=(16, 340), FLY_HOME_ROT=(0, 8),

    TITLE=dict(lines=["THE UNCLE WHO", "ONLY READS LETTERS"], px=46, track_em=0.10, pad=(22, 16),
               line_gap=10, pos=(96, 400), anchor="tl", line_delay=0.12, fg=INK, bg=TAG_LIGHT),
    # (both lines in ONE box: (96, 400)-(715, 557); line height 1.25 em)

    WIN_C=_U(537.1, 315.8), WIN_R=93 * 1.25,     # (240.1, 779.8), 116.25
    ICON_W=140, BREATH_HEAD=2.8, BREATH_BODY=1.5,
    LETTER=dict(w=430, px=40, size_arg=None, rot=-2, pad=44, lh_em=1.42, para_em=0.55),    # paper 430 x 404
    CARD_CENTRE=(730.0, 1202.0), CARD_OFF=520,  # paper top-left at rest (515, 1000); rotated bbox (516,1002)-(960,1420)
    WORDS=None,                                  # landscape only
    # (text, px, alpha, rest top-left x, y at 36.0 s, drift vx, vy px/s) -- rise up and slightly right
    WORDS_PX=[("spinach", 50, .85, 590, 820, 6, -12), ("eggs", 46, .75, 640, 905, 8, -8),
              ("tonight", 42, .60, 650, 640, 10, -18), ("omelette", 42, .55, 520, 520, 8, -22),
              ("Dear Uncle", 38, .45, 650, 455, 8, -20), ("butter", 34, .35, 760, 740, 14, -16),
              ("Sam", 30, .25, 330, 420, 4, -26), ("fold", 28, .20, 840, 590, 14, -22),
              ("cook", 28, .12, 480, 330, 6, -18), ("love", 28, .08, 800, 330, 12, -14)],
    WORD_ORIGIN=None, WORD_EMERGE=(556, 935),

    S4=dict(box_xy=(84, 565), box_w=852, box_px=44, box_lh_em=1.4, box_radius=27,
            box_outline=3, box_pad=(48, 40), box_trim_em=0.3,       # box h = lines*lh + 2*pad_y - 0.3 em
            reply_px=56, reply_dx=90, reply_gap=64, reply_measure=846, reply_lh=76,
            cursor=(9, 14), group_cy=840),                          # cursor 5 px wide; ends y 1115
    S6=dict(box_xy=(84, 654), box_w=852, box_px=52, box_lh_em=1.4, box_radius=27,
            box_outline=3, box_pad=(48, 40), box_trim_em=0.3,
            hl_pad=(7, 8), hl_h_em=1.28,
            ans_px=76, ans_dx=90, ans_gap=70, ans_measure=846, ans_lh=76 * 1.35, group_cy=840),  # "Make what, dear?" at (90, 934)
    S7=dict(card_w=720, text_px=40, size_arg=None, label_px=28, label_track_em=0.12, pad=50,
            lh_em=1.42, para_em=0.55, rots=(3, -1.5, 1),
            card_pos=None,                       # computed: stack + reply centred on y 860 -> card 1 top 339
            card_x=(100, 140, 114), card_overlap=(0, 14, 16), stack_cy=860,
            tape_wh=(156, 46), tape_spec=[(0.43, 6.0, 1), (0.50, -8.0, 2), (0.57, 4.0, 3)],
            arrow_width=5, arrow_head=26,
            arrow_waypoints=[(616, 969), (624, 935), (686, 864), (824, 862), (894, 840), (926, 785), (908, 717),
                             (870, 703), (656, 699), (586, 697)],          # outermost x 926; rebuild from anchors
            ans2_px=60, ans2_xy=None, ans2_gap=70, ans2_measure=840, ans2_lh=81),   # at (104, card3 bottom + 70) = (104, 1208)

    WIPES=dict(w4="left", w5="down", w6="right", w7="left"),        # w6: pink revealed from the LEFT (needs sheets "right")
    W6_PAN=-0.3,
)


def _check():
    a, b = set(LANDSCAPE), set(REEL)
    assert a == b, f"layout tables differ: only landscape {sorted(a - b)}, only reel {sorted(b - a)}"
    for k in ("TITLE", "LETTER", "S4", "S6", "S7"):
        assert set(LANDSCAPE[k]) == set(REEL[k]), f"layout {k}: keys differ"


_check()
TABLE = REEL if FORMAT == "reel" else LANDSCAPE
globals().update(TABLE)
PLATES = A                                       # directory of the active plates (dusk.jpg, uncle_*.png, paper_*.jpg ...)


def U(x, y):
    """map a landscape uncle-polygon point (1920-frame px) to the active frame (identity in landscape)"""
    m = UNCLE_MAP
    return (m["origin"][0] + (x - m["ref"][0]) * m["scale"], m["origin"][1] + (y - m["ref"][1]) * m["scale"])
