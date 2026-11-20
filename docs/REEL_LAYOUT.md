# REEL_LAYOUT: "The Uncle Who Only Reads Letters", 9:16 version

This is the layout proposal for the Instagram Reel / YouTube Shorts cut of ep4. It is for review **before anything is painted**.

- Output: 1080 × 1920, 24 fps, 72.05 s. The voice, the mix and `ep4/timeline.py` stay exactly as they are; only the picture is recomposed.
- Blockouts: `out/ep4_reel/blockouts_1.jpg`, `_2.jpg`, `_3.jpg` (6 frames each). The individual frames are in `out/ep4_reel/blockouts/NN_*.png`.
- Generator: `scripts/reel_blockouts.py`. It draws flat shapes, real text at real size in `assets/fonts/`, and the overlays. It also writes `out/ep4_reel/layout.json` with every computed box and checks that every text and key-action box sits inside the safe box (current result: none outside). Every px number below comes from that script.

## 0. Frame rules

| zone | px | use |
|---|---|---|
| safe box | x 60–960, y 250–1470 (900 × 1220, centre (510, 860)) | all text and key action |
| top bar | y 0–250 | sky, paper, gulls only |
| caption / audio | y 1470–1920 | sea, body, paper; things may enter or leave through it |
| buttons | x 960–1080 | nothing that must be read; the s7 arrow stops at x 926 |
| 3:4 grid crop | y 240–1680 | the title frame (03) and every key frame read inside it |

- Type minimums on a phone: body text ≥ 40 px, labels ≥ 28 px. Every size below meets them.
  - The smallest are the s7 card labels at 28 px mono.
  - The far drifting words are also 28 px, but they are decoration at alpha ≤ 0.2.
- The landscape `F = 1.5` (1280-space) multiplier does not carry over. The portrait tables are written in output px.
- One idea per frame, as in landscape. The portrait version does not add any elements.

## 1. Beats seen in `ep4_v10.mp4` (frames every 0.5 s plus the spec §8 moments)

| # | time | beat | blockout |
|---|---|---|---|
| 1 | 0–0.6 | dusk sky at zoom 2, three gulls | 01 |
| 2 | 0.6–5.0 | tilt down with parallax; the cottage window lights at 4.2 | 02 |
| 3 | 5.6–10.6 | title tag folds in, holds, wipes out | 03 |
| 4 | 11.3–14.5 | slow 6 % push toward the window | (03/04) |
| 5 | 14.5–16.9 | letter flies out to the window with a dotted trail | 04 |
| 6 | 17.5–18.6 | w3: rush into the window, resolve out of the head hole | 05 |
| 7 | 18.2–19.4 | uncle, hole open, envelope lands in the hole | 06 |
| 8 | 19.4–24.1 | letter card slides in; read-nod | 07 |
| 9 | 24.1–24.7 | w4: yellow sheet from the right | 08 |
| 10 | 24.7–29.5 | prompt box; the reply types | 09 |
| 11 | 29.5–30.2 | w5: yellow sheet slides down | 10 |
| 12 | 30.2–37.4 | he forgets: icon shrinks, words drift out | 11 |
| 13 | 37.4–40.9 | words fade; hole closes on "Gone" | 12 |
| 14 | 40.9–41.5 | w6: pink sheet (landscape: from the bottom) | 13 |
| 15 | 41.5–49.4 | "Thanks! Can you make it without eggs?", "…", "Make what, dear?", "it" highlighted | 14 |
| 16 | 49.4–50.0 | w7: cream sheet from the right | 15 |
| 17 | 50.0–57.1 | three letters drop in and tape down | 16 |
| 18 | 57.1–61.2 | "it" sweep, ink arrow, "spinach omelette" sweep, reply types | 17 |
| 19 | 61.2–62.4 | f8: dip to black, night fades up | (18) |
| 20 | 62.4–72.05 | night: reply flies home, 4 % push, fade out | 18 |

## 2. Per beat: layout, what changes and why

### s1–s2 dusk (blockouts 01–04)

**Plate.** The plate is repainted at 1080 × 1920 (§4). The positions are:

- horizon `HZ = 0.599` (y 1150; landscape 0.58 / y 626);
- hill crest at x 680, 168 px above the horizon;
- concave left tail at a scale of 330 px, right fall at 215 px (landscape 384 / 250);
- cottage on the crest: body 44 × 40, roof 44, chimney right;
- lit window `WIN = (680, 980)`.

Why: the sky gets 60 % of the height for the opening tilt and the title. The window sits in the middle third (640–1280), 120 px below the safe-box centre, so both pushes keep it in the box. The cottage is about 1.2× its landscape px size because it is the hero of a narrow frame. Far land is on the right at x 760–1100. Add two more cloud wisps for the taller sky; the six positions are in `sea_plate()`.

**01, 0.0 s: camera on the sky.**

- `cam_box(2.0, 0.45 W, 0.25 H)` → box (216, 0, ×2), so you see source y 0–960.
- The near plane starts 90 px low (`PARALLAX = 90`, landscape 70), so the roof (y ≈ 935 + 90) is out of shot.
- Gulls `BIRDS` = (330, 0.12), (470, 0.15), (400, 0.10) (x0 source px, y fraction), same speeds and spans. On screen at t = 0: (228, 461), (508, 576), (368, 384), all in the box.

**02, tilt 0.6–5.0 s.**

- Scale `2.0 − 1.0·p`; centre `((0.45 + 0.05p)·W, (0.25 + 0.25p)·H)`; near plane `dy = 90·(1 − p)^1.5`. At 3.0 s: box (140, 82, ×1.43), dy 25.6.
- The landscape move panned sideways (0.32 → 0.50 W). Here the move is almost purely vertical, a real tilt. Vertical travel is what portrait is good at.

**03, title 5.6–10.6 s.**

- One tag (no EPISODE 4), set as two lines: `THE UNCLE WHO` / `ONLY READS LETTERS`.
- IBM Plex Mono 46 px, tracking 0.10 em, padding 22 × 16, line gap 10.
- Box at (96, 400)–(715, 557), top-left anchored, light tag (238, 238, 236) with INK text.
- Fold-in unchanged (0.42 s, stepped, ragged edge). The second line lags 0.12 s, which re-uses the old two-tag `delay`. The wipe-out is unchanged.

Why the changes:

- At 33 px on one 780 px line, the landscape title would be below the 40 px body size.
- Bottom-left over the sea (the landscape spot) would sit on the window's reflection column, and too close to where Reels captions stack.
- The empty upper sky is darker lilac, so the light tag still reads. This is also the frame that should be the grid thumbnail: tag and cottage both sit inside the 3:4 crop.

**s2 push 5.0–17.5 s.** `push_box(…, WIN, 0.06)`, unchanged.

**04, letter out 14.46–16.86 s.**

- `PATH_OUT = (−150, 1330) → (330, 1280) → (540, 1100) → WIN`.
- Envelope 280 → 16 px (landscape 260), rotation −14° → −2°, cream dotted trail as before.
- It enters from off the left edge just above the caption zone. At u = 0.30 it is fully inside the box at (77, 1199)–(300, 1342), then arcs up into the window.
- Landscape entered from the bottom-left corner, which in portrait is deep in the caption/audio zone.

### w3, window to window (blockout 05)

- Rush (17.50–17.885) into `WIN (680, 980)`. Resolve (17.885–18.60) out of the hole `WIN_C (240, 780)`.
- Same zoom, blur and glow curves.
- Both focus points sit in the box. The resolve now travels from the right-centre to the left-centre of the frame. That is a slight lateral move; it reads as a match cut, so it doesn't need compensating.

### s3, s5: uncle (blockouts 06, 07, 10–12)

**Figure.** The figure faces right, as in every plate; the hole and the drifting words depend on the profile.

- The landscape polygons are mapped by one similarity: `x' = 60 + (x − 393)·1.25`, `y' = 600 + (y − 172)·1.25`. Back of the skull at x 60, head top at y 600.
- Head box (60, 600)–(549, 1144). The body runs off the bottom and left: extend `BODY`'s bottom points from y 1090 to ≥ 1640 in landscape units.
- `WIN_C = (240.1, 779.8)`, `WIN_R = 116` (93·1.25). Envelope icon 140 px (112·1.25).
- Lens centre (470, 843). Pivot `U(604, 584)` = (324, 1115). Split y = 1123.
- Breathing ±2.8 / 1.5 px (head / body).

Why: on a phone the landscape video plays 1080 wide (×0.5625), so its head is about 240 px. Here it is 545 px, 2.3× larger. The whole head, hole and glasses stay inside the box. The top band (y 250–600) and the right column (x 560–960) are kept empty for the card and the words.

**06, envelope lands (18.90).** Unchanged timing; the icon grows in the hole.

**07, letter card (19.40 in, rests to 24.1).**

- Paper 430 wide × 404 tall, rotated −2°; top-left of the paper at rest (515, 1000) → rotated bbox (516, 1002)–(960, 1420).
- Source Serif 4 at 40 px (italic for "Dear Uncle," / "Love, Sam"), line height 1.42, paragraph gap 0.55 em, padding 44.
- Wraps to "Dear Uncle," / "What can I cook / tonight with eggs / and spinach?" / "Love, Sam".
- Slides in from the right (`CARD_OFF` ≈ 520 px), as in landscape.

Why: there is no room to the right of the face at head height. Below-right, in front of his chest, the read-nod (nose down 2°) now actually looks down at the letter. That improves on landscape, where he nodded at a card level with his face. The card's left edge clears the chin and mouth by about 15 px.

**10, w5.** The yellow sheet slides down with its content (unchanged), exiting through the caption zone. The uncle, with the icon, is revealed above.

**11, words 32.84–39.69.**

- Ten words in IBM Plex Mono.
- They emerge in front of the mouth at `EMERGE = (556, 935)` and ease out over 3 s to the rest positions below. Then they drift up and slightly right, not right as in landscape. They fade together over `FADE_WORDS`.
- They rise into the empty top band like steam leaving. Portrait has height to spare, not width. All words, including at the end of the fade (+3.7 s of drift), stay inside x ≤ 960 and y ≥ 271.

| word | px | alpha | rest top-left (36.0 s) | drift px/s (vx, vy) |
|---|---|---|---|---|
| spinach | 50 | .85 | (590, 820) | (6, −12) |
| eggs | 46 | .75 | (640, 905) | (8, −8) |
| tonight | 42 | .60 | (650, 640) | (10, −18) |
| omelette | 42 | .55 | (520, 520) | (8, −22) |
| Dear Uncle | 38 | .45 | (650, 455) | (8, −20) |
| butter | 34 | .35 | (760, 740) | (14, −16) |
| Sam | 30 | .25 | (330, 420) | (4, −26) |
| fold | 28 | .20 | (840, 590) | (14, −22) |
| cook | 28 | .12 | (480, 330) | (6, −18) |
| love | 28 | .08 | (800, 330) | (12, −14) |

Sizes are landscape px × 1.3 with a 28 px floor (landscape ran down to 18 px). The emergence order and gaps are unchanged.

**12, "Gone".** The hole closes from 39.49 (r 116 → 0, 0.45 s). Solid head to 40.9.

### Paper scenes (blockouts 08, 09, 13, 14)

**09, s4 yellow.**

- Prompt box x 84–936 (852 wide), y 565–755: radius 27, 3 px INK outline, padding 48 / 40.
  - Text: Manrope 44 px, line height 1.4, wrapping to "Dear Uncle, what can I cook tonight / with eggs and spinach? Love, Sam".
- Reply: Source Serif 4 Bold 56 px at (90, box bottom + 64) = (90, 819), measure 846, line height 76.
  - It wraps to 4 lines ("A spinach omelette. Wilt the / spinach in butter, pour in / three beaten eggs, fold it over / and serve.") and ends at y 1115.
  - Cursor 5 px; the "…" sits at the reply origin before typing. Timing is unchanged (98 chars at 24 cps).
- The group is centred at y 840 (just above the box centre).
- Landscape (42 / 51 px across 1200 px) would shrink to 24 / 29 px on a phone. These sizes are about 1.9× that.

**14, s6 pink.**

- Prompt box x 84–936, y 654–864: Manrope 52 px, 2 lines "Thanks! Can you make it / without eggs?".
- "it" sweep: HL fill from 7 px before the word to 8 px after it, 1.28 em tall.
- "Make what, dear?": Source Serif 4 Bold 76 px at (90, 934), one line, ending at x 737.
- The group is centred at y 840. s6 is bigger than s4 because there is less text and this is the beat's punchline.

**Wipes (08, 10, 13, 15).** Same torn-edge sheet, timing and ease.

| wipe | direction | change |
|---|---|---|
| w4 | yellow revealed from the right | unchanged; travel is 1080 px instead of 1920, so it reads calmer |
| w5 | yellow slides down off the uncle | unchanged |
| w6 | **pink revealed from the left** (landscape: from the bottom) | **changed** |
| w7 | cream revealed from the right | unchanged |

Why w6 changes:

- In a vertical feed, an upward wipe looks like the platform's own swipe-to-next.
- Its edge would start behind the caption block.
- The sequence (right, down, left, right) still reads as a deck of sheets.

This needs a `"right"` direction in `sheet()`, the mirror of `"left"`. Optionally pan the w6 slide sound to −0.3 (`ep4/audio.py`, line 245). If you prefer the original, keeping w6 "up" works too; only that pan line would stay.

### s7 cream: the conversation stack (blockouts 16, 17)

**Cards.** The cards are 720 wide (landscape 750) with:

- Source Serif 4 40 px text, line height 1.42; card 2 bold;
- IBM Plex Mono 28 px labels (YOUR FIRST LETTER / HIS REPLY / YOUR NEW LETTER), tracking 0.12 em;
- padding 50;
- rotations +3 / −1.5 / +1, as in landscape.

Paper left edges are x 100 / 140 / 114, the same zig-zag as landscape. Each card tucks 14 / 16 px under the one above, so no text is covered. The stack plus the reply is centred on y 860, giving card 1 top = 339. Rotated bboxes:

| card | bbox | wraps to |
|---|---|---|
| 1 | (94, 320)–(826, 606) | "What can I cook tonight with / eggs and spinach?" |
| 2 | (136, 564)–(864, 909) | "A spinach omelette." / "Wilt the spinach in butter, pour / in three beaten eggs…" |
| 3 | (112, 878)–(836, 1138) | "Thanks! Can you make it / without eggs?" |

**Tapes.** 156 × 46 px (120 × 36 × 1.3), centred on each card's top edge at 43 / 50 / 57 % of the width.

**Drop-in.** Unchanged: 60 px fall, scale 1.08 → 1, starts at 52.67 / 53.87 / 55.07.

**Annotation.** "it" sits at the end of card 3's first line, which gives the arrow a clean start.

- The ink arrow (width 5, 26 px head) starts just above "it" at (616, 969). It rises into the clear strip above card 3 (y ≈ 862), runs right, and loops round card 2's right edge (outermost x 926: the 96 px gutter to the button column is why the cards are 720, not 820). It comes back left along the "A spinach omelette." line to (586, 697).
- Catmull-Rom waypoints: (616, 969), (624, 935), (686, 864), (824, 862), (894, 840), (926, 785), (908, 717), (870, 703), (656, 699), (586, 697).
- Timing is unchanged (`ANNOT`).

**Reply.**

- `ANS2` is set in Source Serif 4 Bold 60 px at (104, card 3 bottom + 70) = (104, 1208), measure 840, line height 81.
- It wraps to 2 lines "Without eggs? Try spinach / and cheese on toast." and ends at y 1361. Typing is unchanged (24 cps).
- In landscape the reply sat beside the cards. Here it goes **below** them, so the reading order is top to bottom: history, then the new answer.

### f8, s8 night (blockout 18)

- f8 is unchanged: fade to black, then the night plate fades up.
- The night plate is the same portrait geometry as dusk: horizon 1150, window (680, 980), plus stars in the top 700 px.
- `PATH_HOME = WIN → (480, 900) → (300, 1140) → (430, 1290)`. Envelope 16 → 340 px (landscape 300), rotation 0 → +8°, gold trail.
  - It ends low-centre at (253, 1189)–(593, 1408), inside the box and the 3:4 crop.
  - It swoops left and then toward the viewer. A straight line from the window would be too short in a frame only 1080 wide.
- The 4 % push toward `WIN` and the end fade (70.9 → 71.95) are unchanged.

## 3. What changes from landscape, in short

1. Every beat is recomposed for the frame, not cropped.
2. The title becomes two lines at 46 px and moves to the upper sky.
3. The letter enters lower-left above the caption zone.
4. The uncle is 1.25× larger. The letter card moves below-right, so the nod looks at it.
5. The words rise instead of drifting right.
6. Text on paper is about 1.3–1.5× its landscape px size, on an 852 px measure.
7. In s7 the stack is vertical and the reply goes below it. The arrow loops on the right inside x 926.
8. w6 comes from the left.
9. The reply flies home low-centre.

Timing, voice and sound are unchanged; the only optional change is the w6 pan.

## 4. Implementation notes

### FORMAT switch in `ep4/common.py`

```python
FORMAT = os.environ.get("EP4_FORMAT", "landscape")          # "landscape" | "reel"
W, H = (1080, 1920) if FORMAT == "reel" else (1920, 1080)
A = os.path.join(ROOT, "out", "ep4_reel" if FORMAT == "reel" else "ep4")   # portrait plates never overwrite the approved ones
```

- Keep `F = 1.5` for the landscape tables only.
- Each module gets a `LAYOUT = {"landscape": {...}, "reel": {...}}[FORMAT]` table. The landscape values move into it verbatim, so the landscape render stays pixel-identical; check with a frame diff against `ep4_v10.mp4` at the §8 times.
- `video.py`'s ffmpeg `-s {W}x{H}` already follows W/H. Use `out/ep4_reel/` for intermediates and `deliver/ep4_reel_vN.mp4` for the output.
- `scripts/render_ep4.sh` and `build_backdrops.sh` need the env var passed through.

### Backdrops to repaint at portrait size (engine page size)

The engine computes `W = round(PAGE_MM[0] / 25.4 · DPI)` and `H = round(PAGE_MM[1] / 25.4 · DPI)` at exec time, from `PAGE_MM` set before the exec (`engine/engine.py`, lines 7–8). `ep4/backdrops.py` sets `PAGE_MM = (338.667, 190.5)` for 1920 × 1080 at 144 dpi. For the reel, set `PAGE_MM = (190.5, 338.667)` at 144 dpi, which gives exactly 1080 × 1920. K stays 0.48, so stroke widths and texture scales are unchanged. The RULES-56 machinery derives `W_REF`/`H_REF` from the same `PAGE_MM` and needs nothing, because DPI is fixed. Seeds stay per scene.

| plate | repaint? | what has to change in the recipe |
|---|---|---|
| `dusk`, `dusk_nc`, `dusk_off`, `night`, `night_nc` + `*_masks.npz` | **yes** | <ul><li>`HZ` 0.58 → 0.599.</li><li>`top()` widths are normalised to W: rewrite in px (crest x 680, h 168, tail 330, fall 215).</li><li>Cottage `bw, bh` and the roof/chimney offsets mix W- and H-normalised units: convert to px (44 × 40, roof 44).</li><li>The haze and horizon bands are in H units (`/0.02`, `/0.022`): scale to keep about 22 px (`/0.0113`, `/0.0124`).</li><li>Cloud wisp table re-laid for the tall sky.</li><li>Far-land Gaussian re-centred (x 1010, σ 110 px).</li><li>Star band: keep in the top 0.36 H.</li><li>The `win` mask key then reads (0.630, 0.510).</li><li>The `_nc`/`_off` variants must still match pixel for pixel except the clouds or the light.</li></ul> |
| `uncle` (+ `uncle_bg.jpg`, `uncle_fig.png`, `uncle_collar.png`, `uncle_geo.npz`) | **yes** | <ul><li>The polygons are in 1920-frame px, scaled by `PXA` (`S144 = W/1920`, which would wrongly give 0.5625 here). Replace `PXA` with the portrait map `U(x, y) = (60 + (x − 393)·1.25, 600 + (y − 172)·1.25)`, applied to HEAD, BODY, COLLAR, COLLAR_FOLD, SKULL_HI, EAR, MOUTH, LENS, ARM, PIVOT, SPLIT.</li><li>Extend BODY's bottom to ≥ 1640 landscape units.</li><li>Scale brush and riso sizes by 1.25.</li><li>The lamp glow uses `(xx − 0.80)·W/H`: re-centre it upper-right for the tall frame.</li><li>Repainting beats upscaling the 1920 plate by 1.25: the cut-paper edges and the speckle stay crisp.</li></ul> |
| `paper_yellow`, `paper_pink`, `paper_cream` | cheap either way | <ul><li>Rotate the approved 1920 × 1080 plates by 90°: the same paper, exact size, no marks with a direction.</li><li>Or run `paper_ground()` at the portrait page.</li><li>Rotation is the safer match to the approved look.</li></ul> |

### Modules that need layout tables

- **`ep4/seasky.py`.**
  - `BIRDS` (portrait values above) and `PATH_OUT` / `PATH_HOME` (above).
  - `fly()` sizes: 280 → 16 out, 16 → 340 home (the call sites in `video.py`).
  - `prep_masks`, `cloud_layer`, `glints`, `living_sea` and the parallax inpaint already work from W, H and the masks. Check that the 150 px texture roll in the sky fill stays above the horizon, and that the glint spread (`3 + 30·d`) suits a 1080-wide sea.
- **`ep4/video.py`.**
  - `dusk_box`: zoom 2.0 → 1.0, centre x 0.45 → 0.50 W, centre y 0.25 → 0.50 H.
  - `PARALLAX` 90 (a reel override; leave `timeline.py` alone).
  - Envelope sizes.
- **`ep4/uncle.py`.**
  - `WIN_C` is written as fractions of W, H, which would land wrongly at (302, 561) in portrait. Make it a table value (240.1, 779.8), with `WIN_R` 116.25.
  - `ICON_W` 140; `BREATH_HEAD`/`BREATH_BODY` 2.8 / 1.5.
  - `CARD_CENTRE`: rest centre of the 430 px card ≈ (730, 1202); `CARD_OFF` ≈ 520.
  - `LETTER` card width 430 at size 40 px (not `420·F` at 30·F).
  - `WORDS` as absolute px tuples with per-word drift (the table above), and `WORD_EMERGE` (556, 935).
  - `uncle_geo.npz` supplies the pivot, split and lens.
- **`ep4/cards.py`.**
  - Title: lines, 46 px, top-left (96, 400), `tag()` called with two lines in one box, `delay` 0.12 on the second line.
  - `prompt_box` origins and sizes (s4: x 84, w 852, 44 px, group-centred; s6: 52 px); reply / answer fonts and origins.
  - `card()` takes px sizes (40 px text, 28 px label, padding 50) instead of `size·F`.
  - `CARD_POS` from the stacked layout; tape size 156 × 46 and positions.
  - `arrow_points()` replaced by the portrait waypoints (built from the anchors exactly as the generator does).
  - `ANS2` origin below the stack, 60 px, measure 840.
  - The whole s7 stack is centred from measured heights, so no hard-coded y.
- **`ep4/transitions.py`.** `WIN_C`/`WIN_R` duplicate the uncle values; take them from `uncle.py`, or from the table. The rush focus is `KD_win`, which comes from the masks.
- **`ep4/sheets.py`.** Add `"right"` (the mirror of `"left"`) for w6. `torn_profile` is already sized from W/H by direction.
- **`ep4/audio.py`.** Nothing is required. The optional w6 pan is `pan=-0.3` for w6 on line 245.

### Checks once it renders

- Run a frame grab at the §8 times through the overlay code in `scripts/reel_blockouts.py` (`overlays()`), so the real frames get the same safe-box and 3:4 lines.
- Preview the export inside the Instagram and YouTube apps before posting, because the safe zones are not officially published.
