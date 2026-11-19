# SPEC — "The Uncle Who Only Reads Letters" (episode-4 pilot), rebuild of v9 "track"

This is the only surviving description of a 72.05 s painterly explainer whose source code was lost when the
workspace was wiped (October 2026 build, scripts `ep4_scenes.py`, `ep4_timeline.py`, `ep4_video.py`,
`ep4_audio2.py`). Implement from this document. Precision beats prose: every number here was either
**recovered verbatim** from the build transcript (marked *recovered fragment* / *recovered*), **measured** from the
approved reference video `ep4_v9_track.mp4` (marked *measured*), or **inferred** (marked *inferred* — use judgement).

Sources this spec was built from (all still on disk, read-only):

| Source | Path | What it gives |
|---|---|---|
| Old session transcript | `/root/.claude/projects/-home-claude/3a9316e9-5147-5c46-bb7f-64607975cb81.jsonl` | the build summary, the full `ep4_timeline.py`, most of `ep4_audio2.py`, large parts of `ep4_video.py` and `ep4_scenes.py`, every v7→v9 patch |
| Approved reference video | `/home/claude/ref/ep4_v9_track.mp4` (1920×1080, 24 fps, 1729 frames, 72.04 s) | layouts, timings, colours. **Contains the three things we are changing** (EPISODE 4 tag, music dip at "Gone", crunchy voice) |
| Reference frames | `/home/claude/ref/frames/f_0001.jpg … f_0144.jpg` | ⚠ these were extracted with an fps filter and are **offset by up to +0.2 s** from their nominal `(N−1)×0.5 s`; use exact frame numbers (§8) instead |
| Reference audio | `/home/claude/ref/v9_track_audio.wav` | the old mix (do not copy its voice chain) |
| Design canvas (published artifact) | `https://claude.ai/artifact/ATjbXZYhmshVobZ2WX1GBh` | the v1 storyboard: **font families and weights**, ink/tag colours, envelope colours, card styles, the drifting-words list, VO draft text per scene, and the painted backdrops (copied to `docs/ref/canvas_v6/`) |
| Canvas backdrops | `docs/ref/canvas_v6/{dusk,night,uncle,paper_yellow,paper_pink,paper_cream}.jpg` (1920×1080) | painted plates as of ~v6. Paper plates are believed final; dusk/night predate the v8 hill fix; uncle is the full figure with collar (no hole) |
| Attachments | `/mnt/user-data/attachments/3a9316e9-5147-5c46-bb7f-64607975cb81/` | `723b837b-credits.md` (Freesound IDs), voice mp3, music mp3, v7/v8 contact sheets, `177f39ea-attachment.txt` (= the ElevenLabs "best practices" doc, **not** the script) |
| Painterly engine | `engine/` (vendored from `/home/claude/painterly-posters/renderer/`) | `paint`, `brushwork`, `streaks`, `soft_strokes`, `apply_strokes`, `riso`, `ink_line`, `poly_mask`, … |

---

## 0. The three owner changes (apply on top of v9)

1. **Music** — the reference track (`assets/audio/ref_jamal.mp3`, "Jamal", 172.46 s) plays under the whole video,
   ducked under the voice exactly as the v9 "track" mix, **but with no dip / silence around "Gone"** (≈39.6 s). The
   music bed runs continuously from 0 to the master fade. (v9 gated the music to zero from `GONE−0.12` and faded it
   back over 0.9 s at the start of s6 — delete that gate, §5.6.)
2. **No "EPISODE 4" tag** — the opening title is a single tag `THE UNCLE WHO ONLY READS LETTERS`, same position,
   same stepped fold-in / fold-out (§4.4.4). The video must work standalone (no series branding anywhere).
3. **Clean voice master** — replace HPF 80 → 2:1 comp @ −20 → +2.5 dB @ 3.2 kHz → voiced RMS −16.5 dB → tanh soft
   ceiling at −1.5 dB (peaks hit ≈ +4.3 dBFS into the tanh; distortion only ≈25 dB below the voice = audible grit) with:
   gentle compression, no presence boost (or ≤ +1 dB), voiced RMS −18 dBFS, and a **look-ahead true-peak limiter**
   at −1.0 dBTP (no tanh anywhere); the master bus gets the same kind of limiter. Ambience ducking and music ducking
   stay. (§5.3, §5.8.)

Everything else = the final v9 state: eyebrow scene labels off, rough edges softened, arrow rising from the middle of
"it" and routed round the card, hill with long concave left tail (HFADE as paint alpha, `land_shape` mask), cloud
drift + warp, twinkling glints (no chevrons), smooth sky-fill inpaint for parallax, painted gulls, 2.5D parallax
tilt, window-to-window blur transition, yellow annotation highlights, etc.

---

## 1. Overview and global conventions

### 1.1 Output

- 1920×1080, 24 fps, duration `END = 72.05 s` (1729 frames; frame `n` is at `t = n/24`).
- Video: H.264 (libx264), `-crf 21 -preset slow -pix_fmt yuv420p` (v9 used `-preset medium` for the final mux).
  Audio: AAC 192 kb/s, 48 kHz stereo, `-shortest`. Delivery files had to stay **under 30 MB** (v9 track = 26.3 MB);
  re-encode at crf 21–22 if over.
- Render: `python3 ep4_video.py OUT.mp4 [t0 t1]` renders a time range; a `.png` OUT renders one frame at `t0`.
  Two halves were rendered in parallel (2 cores: `0 36` and `36 72.05`) and joined with the ffmpeg concat demuxer, then
  muxed with the WAV. Full render ≈ 9–15 min on 2 cores. Logged progress every 5.0 s of video.
- Audio: `python3 ep4_audio2.py OUT.wav`; env `STEMS=1` also writes `OUT_fx.wav`, `OUT_music.wav`, `OUT_amb.wav`;
  env `MUSIC=track|bed` picks the music mode (rebuild: `track` only, §5.6).

### 1.2 Layout scale and easing helpers (*recovered*)

The layouts were designed on a 1280×720 canvas and scaled up:

```python
# recovered fragment (ep4_video.py, lines 14-21)
F = 1.5                                    # layout scale from the 1280 x 720 canvas frames
def ease(p): p = min(max(p, 0.0), 1.0); return 1 - (1 - p) ** 3
def ease_io(p): p = min(max(p, 0.0), 1.0); return p * p * (3 - 2 * p)
def twos(t): return math.floor(t * 12) / 12          # overlays step at 12 fps (the house "on twos" stutter)
```

Every number written `NN*F` below is in 1280-space; multiply by 1.5 for pixels.

### 1.3 The frame-stepping rule ("on twos")

- **Painted plates and their continuous motion** (sea sway, cloud drift/warp, camera tilts/pushes, parallax) run on
  the true 24 fps clock `t`.
- **Overlays / graphic elements** step at 12 fps: every overlay animation samples time through `twos(t)` (or
  `twos(local_t)`): the envelope flights, the typing (character counts), cards dropping in, highlight sweeps, the ink
  arrow draw-on, the title fold-in (`lt = twos(lt)` inside `title_reveal`), the window flicker (`tt = twos(t)`), the
  glints (`glints(..., twos(t), ...)`), the drifting words, bird wing flaps (`sin(twos(t)*5.2)`).
- `scene_history(t)` starts with `lt = twos(t)`; `scene_night` uses `twos(lt)` for the flight progress; `scene_dusk`
  uses `twos(t)` for the flight.

### 1.4 Fonts (*recovered from the design canvas* + transcript)

The build had six TTFs in `SP/fonts/`, loaded through `font(name, px)` (`ImageFont.truetype(f"fonts/{name}.ttf", px)`):

| key | family / weight (from the canvas `<link>`: `IBM+Plex+Mono:wght@400;500`, `Manrope:wght@400;500;600`, `Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,700;1,8..60,400`) | used for |
|---|---|---|
| `mono` | IBM Plex Mono 400 | title tag, card labels, drifting words |
| `mono5` | IBM Plex Mono 500 | (spare; possibly labels) |
| `sans` | Manrope 500 (the canvas prompt box used weight 500) | prompt-box text (s4, s6) |
| `serif` | Source Serif 4 400 (default optical size) | letter card body, card text |
| `serif_i` | Source Serif 4 400 italic | "Dear Uncle," / "Love, Sam" |
| `serif_b` | Source Serif 4 700 | the uncle's typed replies, HIS REPLY card (bold) |

They were "converted from @fontsource packages": the npm packages ship only `.woff2`/`.woff`
(`@fontsource/ibm-plex-mono/files/ibm-plex-mono-latin-400-normal.woff2`, `@fontsource/manrope/files/manrope-latin-500-normal.woff2`,
`@fontsource/source-serif-4/files/source-serif-4-latin-{400,700}-normal.woff2`, `…-latin-400-italic.woff2`), which were
converted to TTF for Pillow (*inferred*: `fontTools.ttLib.TTFont(woff2); f.flavor = None; f.save(ttf)`). The latin
subset includes "…" (U+2026) and the curly apostrophe. Any route to the same static TTFs is fine (Google Fonts static
TTFs are identical in design).

### 1.5 Palette

| name | RGB | where / source |
|---|---|---|
| `INK` | (46, 44, 45) = `#2e2c2d` | text, prompt-box outline, arrow, tag dark bg (*canvas*; measured dark tag ≈ (45,43,44)) |
| tag light | (238, 238, 236) = `#eeeeec` | title tag background (*recovered*) |
| `HL` | (245, 212, 74) | the one accent: marker highlights on "it" and "spinach omelette" (*recovered*) |
| card paper | (242, 233, 217) `#f2e9d9` | letter cards (measured (241,234,218)); HIS REPLY card in the canvas was `#f8f4ec` |
| card label | (109, 106, 111) `#6d6a6f` | YOUR FIRST LETTER / HIS REPLY / YOUR NEW LETTER (*canvas*) |
| tape | (236, 224, 196) α 0.78 | tape strips (*canvas*) |
| envelope paper | (239, 230, 214) `#efe6d6`; flap line (168,151,127) `#a8977f`; lower folds (205,191,168) `#cdbfa8`; stamp (188,97,94) `#bc615e` α 0.85 | envelope (*canvas*) |
| out-flight trail | (243, 235, 224, α170) | dotted trail, dusk (*recovered*) |
| home-flight trail | (246, 207, 134, α150) | dotted trail, night (*recovered*) |
| paper yellow plate | ≈ (236, 212, 144) mean; canvas fill `#f6de96` | s4 background (*measured*) |
| paper pink plate | ≈ (233, 163, 178) mean; canvas fill `#f0aaba` | s6 background |
| paper cream plate | ≈ (218, 211, 199) mean; canvas fill `#e2dbce` | s7 background |
| uncle background | left (232,226,214), right (230,219,202), lamp-warm top-right (226,212,185) | s3/s5 |
| uncle head | (66, 56, 54) with light speckle (237,231,222); back-of-head highlight band (112,105,103); ear (93,73,67); warm rim light on face edge (182,149,114) | measured |
| cardigan | (90, 79, 61) olive-brown with diagonal brushwork | measured |
| collar | (213, 202, 184) | measured |
| glasses | (196, 169, 134) thin gold line | measured |
| hole in head | (228, 217, 201) ≈ uncle background colour | measured |
| dusk sky | TL (202,166,178), mid (161,153,190), TR (133,136,183), near horizon left (238,185,167) | measured @12.0 s |
| dusk hill | (121, 100, 119) | measured |
| dusk sea | near horizon (119,120,149), foreground (89,94,131) | measured |
| night sky | TL (91,80,113), TR (35,40,77); hill (54,48,63); sea (40,44,78) → (20,25,51) at bottom | measured @64.0 s |

Painted-plate colours are set by the scene recipes in §3 (those are the authority); the measured values above are
for checking.

### 1.6 Textures / paper

- Engine textures are the Poly Haven scans fetched by `engine/fetch_textures.sh` into `engine/tex/` (engine defaults:
  `tooth = white_stucco_Displacement.png (6, 0.6)`, `mottle = plaster_grey_04_Rough.png (60, 1.2)`,
  `grain2 = white_plaster_02_Rough.png (10, 0.8)`, `linen = rough_linen_Rough.png (8, 0.5)`). ambientCG was blocked in
  October, so **only Poly Haven** scans were used. The episode used these defaults (*inferred*: no TEX override was
  ever mentioned); the visible paper character of the plates (soft plaster mottle, faint stains) matches them.
- Owner direction: "lighter, varied texture — not the same texture as intensely over everything". Keep granulation light
  (sky `0.03`, mottle `0.012`, see §3.2).
- A "grain standard" (three noise plates rotated at 12 fps) existed in `ep4_video.py`
  (`GRAIN = [ndi.gaussian_filter(rng.standard_normal((H,W)),1.5)/std for i in range(3)]`, "house standard, applied
  lightly") but the owner said "we don't need the grain standard". *Inferred*: grain off or imperceptible in v9. Leave
  it out (optional flag, amplitude ≤ 0.006 if ever used).

---

## 2. Timeline

### 2.1 `ep4_timeline.py` (*recovered verbatim — the whole file*)

```python
# Episode 4 timeline, taken from the voice-over's pauses. Shared by the picture (ep4_video.py) and the sound (ep4_audio2.py).
# All times in seconds. Audio times are positions in the voice file; the video starts A_OFF seconds before the voice.
A_OFF = 1.5
P = [0.0, 9.76, 16.70, 23.20, 28.69, 40.00, 48.47, 60.87]     # where each of the 8 paragraphs starts in vo2.wav (ElevenLabs, Sekou)
VO_END = 67.55
VO_FILE = "vo2.wav"
def v(a): return a + A_OFF
END = round(v(VO_END) + 3.0, 2)     # a little longer tail for the final chord

T = dict(s1=(0, v(P[1])), s2=(v(P[1]), v(P[2]) - 0.7),
         w3=(v(P[2]) - 0.7, v(P[2])), s3=(v(P[2]), v(P[3]) - 0.6),
         w4=(v(P[3]) - 0.6, v(P[3])), s4=(v(P[3]), v(P[4]) - 0.7),
         w5=(v(P[4]) - 0.7, v(P[4])), s5=(v(P[4]), v(P[5]) - 0.6),
         w6=(v(P[5]) - 0.6, v(P[5])), s6=(v(P[5]), v(P[6]) - 0.6),
         w7=(v(P[6]) - 0.6, v(P[6])), s7=(v(P[6]), v(P[7]) - 1.2),
         f8=(v(P[7]) - 1.2, v(P[7])), s8=(v(P[7]), END))

# moments inside scenes, in seconds from the scene's start, each tied to a line of the voice-over
FLY_OUT = (3.2, 2.4)        # s2: the letter leaves on "All you can do…" and lands just after "…is write"
READ_TILT = 1.6             # s3: he tips his head down on "he reads it carefully"
REPLY_TYPE = (0.6, 24.0)    # s4: reply starts typing (start, characters per second)
FORGET = 2.6                # s5: "he forgets everything": the letter leaves his head, the words start to drift
FADE_WORDS = (7.2, 9.5)    # s5: the words fade out, gone by "Gone"
Q2_TYPE = (1.5, 16.0)       # s6: the quoted letter types as it's read aloud
ANS_DOTS, ANS_TYPE = 3.9, (4.3, 14.0)   # s6: "…", then "Make what, dear?" on "he has no idea"
IT_SWEEP = 6.0              # s6: highlight on "it" as he says it
CARD0, CARD_GAP = 2.7, 1.2  # s7: letters drop in from "Every time you write"
ANS2_DOTS, ANS2_TYPE = 8.9, (9.2, 24.0) # s7: the reply, from "He reads it all again"
FLY_HOME = (0.8, 4.2)       # s8: the reply heads home
TILT = (0.6, 5.0)           # s1: the camera tilts down from the sky to the house ("…who lives far away")
LIGHT_ON = 4.2              # s1: the window lights up as the house comes into view
TITLE = (5.6, 10.6)         # s1: the episode title, after the reveal
HOLE_CLOSE = 9.3           # s5: the hole in his head closes, shut by "Gone"
ANNOT = (7.1, 7.6, 8.3)     # s7, on "He reads it all again": sweep "it", draw the arrow back to the reply, sweep "spinach omelette"
PARALLAX = 70               # s1: how much further the near plane (hill and sea) travels than the sky during the tilt, in source px
VO_GAPS = [(8.44, 9.76), (15.03, 16.70), (22.20, 23.20), (27.07, 28.69), (38.55, 40.00), (46.73, 48.47), (59.43, 60.87)]   # pauses between paragraphs in vo2.wav
```

Notes: `TILT`, `LIGHT_ON` and `TITLE` are in s1 time, which equals absolute time (s1 starts at 0). `scene_dusk`
treats s1+s2 as one continuous shot on the absolute clock. Helpers used by the renderer (*inferred names, recovered
usage*): `in_(key, t)` → `T[key][0] <= t < T[key][1]`; `frac(key, t)` → `(t − a)/(b − a)`; `local(key, t)` → `t − a`.

### 2.2 Absolute schedule (computed from 2.1)

| key | start | end | dur | content |
|---|---|---|---|---|
| s1 | 0.000 | 11.260 | 11.26 | dusk sky → tilt down (parallax) → house; light on; title |
| s2 | 11.260 | 17.500 | 6.24 | same shot, slow push to the window; the letter flies out to the house |
| w3 | 17.500 | 18.200 | 0.70 | rush into the lit window (blur, warm light) → resolve out of the uncle's head window |
| s3 | 18.200 | 24.100 | 5.90 | uncle, hole open; envelope lands in head; letter card slides in; he nods to read |
| w4 | 24.100 | 24.700 | 0.60 | torn-paper sheet, yellow from the right |
| s4 | 24.700 | 29.490 | 4.79 | yellow: prompt box with Sam's letter, reply types |
| w5 | 29.490 | 30.190 | 0.70 | yellow sheet pulled down off the uncle |
| s5 | 30.190 | 40.900 | 10.71 | uncle forgets: letter leaves, words drift and fade, hole closes |
| w6 | 40.900 | 41.500 | 0.60 | pink sheet up from the bottom |
| s6 | 41.500 | 49.370 | 7.87 | pink: "Thanks! Can you make it without eggs?" → "Make what, dear?" → highlight "it" |
| w7 | 49.370 | 49.970 | 0.60 | cream sheet from the right |
| s7 | 49.970 | 61.170 | 11.20 | three letters taped down, annotate it→omelette, reply types |
| f8 | 61.170 | 62.370 | 1.20 | dip to black and up into night |
| s8 | 62.370 | 72.050 | 9.68 | night, reply flies home, slow push, fade out |

Key events in absolute time: tilt 0.60→5.00; light on 4.20 (0.5 s ramp); title 5.60→10.60; letter flight out
14.46→16.86; rush 17.50→17.885; resolve 17.885→18.60; envelope into head 18.90; letter card in 19.40; read-nod 19.80;
reply dots 24.70→25.30, reply typing 25.30→29.38 (98 chars @ 24 cps); FORGET 32.79; words fade 37.39→39.69;
hole close from 39.49; "Gone" (voice) 39.61; Q2 typing 43.00→45.31 (37 chars @ 16 cps); "…" 45.40; answer typing
45.80→46.94 (16 chars @ 14 cps); "it" sweep 47.50; cards 52.67 / 53.87 / 55.07; annotate 57.07 / 57.57 / 58.27;
ANS2 "…" 58.87, typing 59.17→61.09 (46 chars @ 24 cps); fade to black 61.17→61.71; night fades up 61.83→62.37;
home flight 63.17→67.37; picture fade-out ≈70.9→71.95 (*measured*), audio fade 70.85→72.05.

### 2.3 Voice-over script by paragraph

Voice file: ElevenLabs "Sekou – Friendly and Confident" (`assets/audio/vo_sekou.mp3`, 44.1 kHz 128 kb/s mp3,
67.55 s; decoded to `assets/audio/vo2.wav`, 48 kHz mono). Placed at `A_OFF = 1.5 s`. The exact final script was lost; the
text below is the storyboard VO from the design canvas, which every recovered cue phrase matches ("…who lives far
away", "All you can do… is write", "he reads it carefully", "But the moment his reply is posted", "he forgets
everything", "Gone", "he has no idea", "Every time you write", "He reads it all again"). The owner ruled out a "what's
next" line, and the voice file confirms paragraph 8 has only four phrases, so the canvas's last sentence ("Next: why
the letters can't get too long.") is **not** in the read.

| ¶ | starts (voice file / video) | text (storyboard draft) | phrase timings in the voice file (silencedetect −40 dB, ≥0.25 s) |
|---|---|---|---|
| 1 | 0.00 / 1.50 | Imagine an uncle who lives far away. He has read an enormous amount, and he answers every letter you send him. | 0–1.29, 1.64–2.96, 3.64–5.69, 6.06–8.44 |
| 2 | 9.76 / 11.26 | You can't phone him, and you can't visit. All you can do is write. | 9.76–10.71, 11.17–12.13, 13.02–13.92, 14.39–15.03 |
| 3 | 16.70 / 18.20 | When your letter arrives, he reads it carefully, from the first word to the last… | 16.70–18.08, 18.40–19.62, 20.06–21.13, 21.44–22.20 |
| 4 | 23.20 / 24.70 | …and writes straight back. Quickly, and usually rather well. | 23.20–24.61, 24.97–25.42, 25.77–27.07 |
| 5 | 28.69 / 30.19 | But the moment his reply is posted, he forgets everything. Your letter, his answer, all of it. Gone. | 28.69–30.74, 31.31–32.56, 33.21–33.87, 34.27–35.03, 35.57–36.13, 37.18–37.56, **38.11–38.55 ("Gone.")** |
| 6 | 40.00 / 41.50 | So if your next letter says "Thanks! Can you make it without eggs?", he has no idea what "it" is. | 40.00–41.58, 41.85–43.85, 44.27–46.73 |
| 7 | 48.47 / 49.97 | The answer is simple. Every time you write, you include the whole conversation so far. He reads it all again, fresh, every single time. | 48.47–49.02, 49.43–50.73, 51.21–55.06, 55.59–56.89, 57.18–57.76, 58.13–59.43 |
| 8 | 60.87 / 62.37 | That's how an AI chat works. It doesn't remember you. It rereads everything, every time. | 60.87–62.72, 63.13–64.24, 64.64–66.23, 66.60–67.55 |

`VO_GAPS` (the inter-paragraph pauses) in video time: (9.94, 11.26), (16.53, 18.20), (23.70, 24.70), (28.57, 30.19),
(40.05, 41.50), (48.23, 49.97), (60.93, 62.37). `GONE = v(38.11) = 39.61`. `v(VO_END) = 69.05`.

</content>
---

## 3. Backdrops — `ep4_scenes.py`

### 3.1 Invocation, header and outputs

- Run from the engine directory (texture paths `tex/...` are relative): `SCENE=<name> python3 ep4_scenes.py 144 OUT.jpg`
  → prints `canvas 1920 1080`, saves `OUT.jpg`. At 144 dpi the page must be 1920×1080, so the header sets
  `PAGE_MM = (1920/144*25.4, 1080/144*25.4) = (338.667, 190.5)` **before** exec'ing the engine (*inferred*; the engine
  computes `W,H` from `PAGE_MM` and `sys.argv[1]` = DPI). `K = 144/300 = 0.48`; stroke widths are written
  `n * DPI / 100` (= `n*1.44` px).
- Header (lines 1–35 were never shown; *inferred* from usage): imports (`os, sys, numpy as np, PIL.Image/ImageDraw`,
  `scipy.ndimage`), `SCENE = os.environ["SCENE"]`, `NIGHT = SCENE == "night"`, `WOFF = bool(os.environ.get("WINDOW_OFF"))`,
  `f32 = np.float32`, config globals (`SEED`, `EDGE_TOOTH = 0.6`, `PAGE_MM`, optional `PAPER_RGB`), then
  `exec` of `engine.py`, `marks.py`, `figures.py` (for `ink_line`, `fill`) in the CLAUDE.md order. Helpers:
  `PX = lambda pts: [(X(x), Y(y)) for x, y in pts]`; `save()` writes `canvas` (0–1 float) to `OUT` as JPEG (quality ≈92)
  and prints `saved OUT`; `paper_ground()` = the plain paper-plate recipe (§3.5).
- A current engine note: since October the posters engine gained RULES-56 machinery (`ref_canvas`, `W_REF`…). It is
  irrelevant here (no DPI changes; 144 dpi only) — just keep the seeds fixed.
- Scenes and their outputs (all 1920×1080):

| SCENE | env | file(s) | masks |
|---|---|---|---|
| `dusk` | — | `dusk.jpg` | `dusk_masks.npz`: `land` (uint8 0–255, faded hill + far land), `land_shape` (uint8, **unfaded** hill outline + far land), `hz` (float32, = 0.58), `win` (float32 [wx, wy] normalised) |
| `dusk` | `NOCLOUDS=1` | `dusk_nc.jpg` | (same masks; rng state restored so everything but clouds is identical) |
| `dusk` | `WINDOW_OFF=1` | `dusk_off.jpg` | dark window, no glow, no reflection dashes |
| `night` | — | `night.jpg` | `night_masks.npz` (same keys) |
| `night` | `NOCLOUDS=1` | `night_nc.jpg` | |
| `uncle` | — | `uncle.jpg` (whole), `uncle_bg.jpg`, `uncle_fig.png` (RGBA), `uncle_collar.png` (RGBA), `uncle_geo.npz` (`pivot`, `split`, `lens`) | |
| `paper_yellow`, `paper_pink`, `paper_cream` | — | `paper_*.jpg` | |

The three backdrop renders of dusk (full / NOCLOUDS / WINDOW_OFF) and two of night ran in parallel in the background
(≈1 m 13 s each). **Important:** the `_nc` and `_off` variants must be pixel-identical to the full render except for
the clouds / the window light, because the video builds layers by subtraction (`cloud = DUSK − dusk_nc`,
`LIGHT_D = DUSK − dusk_off`).

### 3.2 Dusk and night (`SCENE in ("dusk","night")`) — final v9 code

*Recovered fragment* (ep4_scenes.py lines 39–175 as read in the transcript) **with the v8 patches applied** (hill
profile, HFADE as paint alpha, HL_SHAPE / `land_shape`). Engine calls: `lowfreq`, `smooth`, `poly_mask`, `paint`,
`stroke_layer`, `draw_stroke`, `bez` (engine's quadratic: `bez(p0, p1, p2, n)`), `soft_strokes`, `riso`, `brushwork`,
`streaks`, `apply_strokes`, `rgb`, `X`, `Y`, `xx`, `yy`, `rng`, `mottle`, `tooth`, `SRC_BROAD`, `SRC_FINE`.

```python
if SCENE in ("dusk", "night"):
    HZ = 0.58
    # ---------------- SKY: one graded wash, the sun just set off-frame left ----------------
    gx, gy = -0.15, HZ + 0.04
    d = np.sqrt((xx - gx) ** 2 + ((yy - gy) * H / W) ** 2) + 0.03 * lowfreq(900 * K, 11, 2)
    if NIGHT:
        stops_d = [0.0, 0.35, 0.60, 0.95, 1.5]
        stops_c = [(150, 112, 120), (98, 86, 118), (62, 64, 104), (40, 44, 82), (30, 33, 66)]
    else:
        stops_d = [0.0, 0.22, 0.48, 0.85, 1.5]
        stops_c = [(250, 214, 168), (238, 186, 168), (196, 168, 190), (150, 150, 192), (118, 126, 178)]
    canvas = np.stack([np.interp(d, stops_d, [c[i] for c in stops_c]) for i in range(3)], -1).astype(f32) / 255
    canvas *= (1 - 0.012 * mottle)[..., None]
    canvas *= (1 - 0.03 * smooth(0.3, 2.0, -tooth))[..., None]           # granulation, kept light
    del d
    # cloud wisps: long soft horizontal strokes, lit underneath. The random state is restored afterwards so a
    # NOCLOUDS=1 render matches the full render everywhere except the clouds (the video drifts them as a layer).
    _rng_state = rng.bit_generator.state
    for i, (cy, cx0, ln, col, a) in ([] if os.environ.get("NOCLOUDS") else enumerate([
            (0.20, 0.08, 0.34, (226, 170, 172), 0.45), (0.24, 0.18, 0.26, (244, 196, 176), 0.4),
            (0.31, 0.02, 0.22, (214, 160, 176), 0.35), (0.14, 0.52, 0.30, (186, 160, 196), 0.35),
            (0.36, 0.30, 0.18, (246, 206, 178), 0.3), (0.40, 0.60, 0.20, (212, 172, 186), 0.25)])):
        if NIGHT: col = tuple(int(c * 0.55) for c in col); a *= 0.8
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        for j in range(5):
            y = cy + rng.normal(0, 0.012); x0 = cx0 + rng.uniform(-0.03, 0.05); l = ln * rng.uniform(0.5, 1.0)
            draw_stroke(dr, bez((X(x0), Y(y)), (X(x0 + l / 2), Y(y - 0.008)), (X(x0 + l), Y(y + 0.003)), 30),
                        rng.uniform(10, 22) * DPI / 100, 2 * DPI / 100, 0.9, 0.3)
        soft_strokes(lay, rgb(*col), a, 7)
    rng.bit_generator.state = _rng_state
    if NIGHT:   # stars: sparse, uneven, mostly high
        riso(np.ones((H, W), f32) * smooth(0.45, 0.05, yy), rgb(240, 232, 214), 0.0012 * smooth(0.5, 0.0, yy), 501, size=0.6)
    haze = np.exp(-((yy - HZ + 0.006) / 0.02) ** 2) * (0.5 if not NIGHT else 0.25)
    canvas += (rgb(250, 222, 196) * (0.5 if NIGHT else 1) - canvas) * haze[..., None] * 0.5

    # ---------------- DISTANT LAND: two flat chalky bands on the right, the far one fading into haze ----------------
    far = lambda x: HZ - 0.035 * np.exp(-((np.asarray(x, f32) - 0.93) / 0.12) ** 2) - 0.004
    xs = np.linspace(0.6, 1.05, 160)
    FAR = poly_mask(PX([(0.6, HZ + 0.002)]) + [(X(x), Y(far(x))) for x in xs] + PX([(1.05, HZ + 0.002)]))
    paint(FAR, rgb(170, 146, 170) if not NIGHT else rgb(70, 64, 92), rgb(178, 156, 176) if not NIGHT else rgb(76, 70, 96),
          soft=2, wob=1, wob_scale=80, width=0.06, dry=0.05, dry_edge=0.3, mot=0.4, rim=0.0, seed=21, alpha=0.75)
    # main headland with the cottage on top
    def top(x):
        x = np.asarray(x, f32); dx = x - 0.78
        # a broad, low hill: rounded at the top, and on the left a long concave tail that runs out along the horizon
        # (exp(-a^2 / (1 + 0.6a)) is Gaussian near the top and exponential far out, so the slope keeps easing off
        # instead of steepening into a drop); the right side keeps its shorter fall
        aL = np.abs(dx) / 0.20
        bump = np.where(dx < 0, np.exp(-aL ** 2 / (1 + 0.6 * aL)), np.exp(-np.abs(dx / 0.13) ** 1.9))
        return HZ - 0.125 * bump - (0.0025 * np.sin(x * 41) + 0.0015 * np.sin(x * 97)) * smooth(0.02, 0.2, bump)
    xs = np.linspace(-0.05, 1.05, 440)
    HL = poly_mask(PX([(-0.05, HZ + 0.003)]) + [(X(x), Y(top(x))) for x in xs] + PX([(1.05, HZ + 0.003)]))
    # The fades go in as paint's alpha, not into the mask: paint() thresholds its mask at 0.5, so a faded mask gets
    # cut off with a hard edge wherever the fade crosses one half (that was the blunt end on the left toe).
    HFADE = smooth(0.0, 0.04, (HZ - top(xx))) ** 0.8              # the long thin toe thins out into the horizon haze
    HFADE = HFADE * (0.12 + 0.88 * smooth(0.24, 0.58, xx))       # and its far-left run dissolves into the sky rather than stopping
    Shl = brushwork(SRC_BROAD, su=1.0, sv=1.0, wob=8, seed=31, spread=0.6, patch=120, n=6, cover=0.5, base=-0.3)[0] * 0.6
    c1, c2 = (rgb(112, 96, 118), rgb(128, 106, 120)) if not NIGHT else (rgb(44, 42, 62), rgb(52, 48, 66))
    paint(HL, c1, c2, S=Shl, soft=1.5, wob=1.5, wob_scale=60, width=0.06, dry=0.04, dry_edge=0.5, mot=0.7, rim=0.03, seed=32, valvar=0.03, alpha=HFADE)
    HL_SHAPE = HL.copy()                                          # the unfaded outline, for the video's parallax planes
    HL = HL * HFADE                                               # (the glazes, haze and saved mask use the faded hill)
    # translucent glazes on the lit (left, sunset) flank
    for i in range(3):
        y0 = HZ - 0.10 + i * 0.03
        band = [(x, y0 + 0.35 * (0.8 - x) * 0 + 0.004 * np.sin(x * 19 + i)) for x in np.linspace(0.55, 0.82, 30)]
        pts = PX(band) + [(X(x), Y(y + 0.012)) for x, y in band[::-1]]
        col = [rgb(196, 146, 150), rgb(170, 128, 146), rgb(214, 168, 160)][i % 3]
        if NIGHT: col = col * 0.45
        paint(poly_mask(pts) * HL, col, col * 0.95, S=streaks(SRC_BROAD, angle=0.08, su=1.4, sv=0.5, seed=40 + i), soft=1.0, wob=1, wob_scale=40,
              width=0.1, dry=0.4, dry_edge=0.6, mot=0.4, rim=0.0, seed=40 + i, alpha=0.16)
    # horizon haze laid back over the foot of the hill so it sinks into the distance
    hz2 = np.exp(-((yy - HZ + 0.004) / 0.022) ** 2) * HL * (0.55 if not NIGHT else 0.35)
    canvas += (rgb(236, 210, 196) * (0.45 if NIGHT else 1) - canvas) * hz2[..., None]
    # cottage: clean built shapes, a lit sliver on the sunset side
    cx = 0.78; base_y = float(top(cx)) + 0.006; bw, bh = 0.019, 0.018
    body = [(cx - bw / 2, base_y), (cx - bw / 2, base_y - bh), (cx + bw / 2, base_y - bh), (cx + bw / 2, base_y)]
    roof = [(cx - bw / 2 - 0.004, base_y - bh + 0.001), (cx - 0.002, base_y - bh - 0.019), (cx + bw / 2 + 0.004, base_y - bh + 0.001)]
    chim = [(cx + 0.004, base_y - bh - 0.010), (cx + 0.004, base_y - bh - 0.020), (cx + 0.008, base_y - bh - 0.020), (cx + 0.008, base_y - bh - 0.006)]
    wall = (rgb(206, 186, 176), rgb(196, 176, 170)) if not NIGHT else (rgb(78, 72, 92), rgb(72, 66, 86))
    roofc = (rgb(96, 70, 80), rgb(90, 66, 76)) if not NIGHT else (rgb(34, 30, 44), rgb(30, 28, 40))
    EDGE_TOOTH = 0.3
    paint(poly_mask(PX(chim)), *roofc, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.0, seed=51)
    paint(poly_mask(PX(body)), *wall, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.02, seed=52)
    paint(poly_mask(PX(roof)), *roofc, soft=0.6, wob=0.2, width=0.05, dry=0.02, dry_edge=0.2, rim=0.0, seed=53)
    lit = [(cx - bw / 2, base_y), (cx - bw / 2, base_y - bh), (cx - bw / 2 + 0.003, base_y - bh), (cx - bw / 2 + 0.003, base_y)]
    paint(poly_mask(PX(lit)), rgb(246, 210, 180) * (0.5 if NIGHT else 1), rgb(240, 200, 176) * (0.5 if NIGHT else 1), soft=0.5, wob=0.1, width=0.05, dry=0.0,
          dry_edge=0.1, rim=0.0, seed=54, alpha=0.8)
    EDGE_TOOTH = 0.6
    # the lit window and its glow
    wx, wy = cx + 0.002, base_y - bh * 0.52
    gd = np.sqrt(((xx - wx) * W / H) ** 2 + (yy - wy) ** 2)
    glow = np.exp(-(gd / (0.022 if not NIGHT else 0.04)) ** 2) * (0.3 if not NIGHT else 0.55)
    if not WOFF: canvas += (rgb(255, 214, 140) - canvas) * glow[..., None]
    win = [(wx - 0.0032, wy - 0.0048), (wx + 0.0032, wy - 0.0048), (wx + 0.0032, wy + 0.0048), (wx - 0.0032, wy + 0.0048)]
    EDGE_TOOTH = 0.2
    paint(poly_mask(PX(win)), *((rgb(92, 78, 86), rgb(86, 72, 80)) if WOFF else (rgb(255, 222, 150), rgb(250, 204, 120))), soft=0.4, wob=0.1, width=0.05, dry=0.0, dry_edge=0.0, rim=0.0, seed=55)
    EDGE_TOOTH = 0.6
    if not NIGHT:   # a thin wisp from the chimney
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        sx, sy = X(cx + 0.006), Y(base_y - bh - 0.021)
        draw_stroke(dr, bez((sx, sy), (sx - X(0.012), sy - Y(0.03)), (sx - X(0.045), sy - Y(0.045)), 40), 4 * DPI / 100, 9 * DPI / 100, 0.7, 0.1)
        soft_strokes(lay, rgb(236, 220, 214), 0.35, 4)

    # ---------------- SEA: horizontal brushwork in two close hues, sunset glow reflected on the left ----------------
    SEA = poly_mask(PX([(-0.05, HZ), (1.05, HZ), (1.05, 1.05), (-0.05, 1.05)]))
    Ssea, Csea = brushwork(SRC_BROAD, su=2.6, sv=1.6, wob=6, seed=61, spread=0.02, patch=300, n=6, cover=0.6)
    s1, s2 = (rgb(120, 128, 160), rgb(136, 136, 166)) if not NIGHT else (rgb(36, 42, 74), rgb(42, 46, 78))
    paint(SEA, s1, s2, S=Ssea, C=Csea, soft=1.0, wob=0.3, wob_scale=200, width=0.03, dry=0.05, dry_edge=0.1,
          mot=0.5, rim=0.0, seed=62, valvar=0.06, cvar=0.4, edge_tex=0.2)
    deep = (rgb(84, 92, 134), rgb(92, 96, 136)) if not NIGHT else (rgb(22, 26, 52), rgb(26, 30, 56))
    paint(SEA * smooth(0.70, 1.0, yy), *deep, S=Ssea, C=Csea, soft=8, wob=1, wob_scale=150, width=0.3, dry=0.15, dry_edge=0.4, mot=0.5, rim=0.0,
          seed=63, alpha=0.7)
    glowc = (rgb(240, 196, 176), rgb(232, 182, 180)) if not NIGHT else (rgb(110, 90, 112), rgb(100, 84, 108))
    paint(SEA * smooth(0.50, 0.0, xx) * smooth(HZ + 0.16, HZ, yy), *glowc, S=Ssea, C=Csea, soft=8, wob=1, wob_scale=150,
          width=0.2, dry=0.25, dry_edge=0.6, mot=0.5, rim=0.0, seed=64, valvar=0.08, alpha=0.4)
    del Ssea, Csea
    Sw = streaks(SRC_FINE, su=1.4, sv=1.0, seed=65)
    # crests: short tapered horizontal strokes, longer and wider toward the viewer
    lay = stroke_layer(); dr = ImageDraw.Draw(lay)
    for _ in range(34 if not NIGHT else 22):
        y = HZ + 0.02 + (1 - HZ) * rng.uniform(0.08, 1) ** 1.1; depth = (y - HZ) / (1 - HZ)
        x = rng.uniform(-0.05, 1.0); ln = (0.015 + 0.10 * depth) * rng.uniform(0.5, 1.3)
        draw_stroke(dr, bez((X(x), Y(y)), (X(x + ln / 2), Y(y - 0.002)), (X(x + ln), Y(y)), 16),
                    (0.6 + 4.5 * depth) * DPI / 100, 0.6 * DPI / 100, 0.8, 0.3)
    cr = (rgb(232, 214, 210), rgb(240, 222, 206)) if not NIGHT else (rgb(120, 122, 156), rgb(130, 128, 160))
    apply_strokes(lay, *cr, Sw, dry=0.6, seed=66, rim=0)
    lay = stroke_layer(); dr = ImageDraw.Draw(lay)
    for _ in range(14):
        y = HZ + 0.01 + (1 - HZ) * rng.uniform(0.05, 1) ** 1.3; depth = (y - HZ) / (1 - HZ)
        x = rng.uniform(-0.05, 1.0); ln = (0.03 + 0.14 * depth) * rng.uniform(0.6, 1.2)
        draw_stroke(dr, bez((X(x), Y(y)), (X(x + ln / 2), Y(y + 0.002)), (X(x + ln), Y(y)), 16), (1 + 5 * depth) * DPI / 100, 0.8 * DPI / 100, 0.8, 0.3)
    tr = (rgb(92, 98, 140), rgb(100, 104, 146)) if not NIGHT else (rgb(18, 22, 46), rgb(22, 26, 50))
    apply_strokes(lay, *tr, Sw, dry=0.55, seed=67, rim=0)
    if not WOFF:
        # window reflection: broken gold dashes straight down from the cottage
        lay = stroke_layer(); dr = ImageDraw.Draw(lay)
        for _ in range(26 if NIGHT else 12):
            y = HZ + 0.006 + rng.uniform(0, 0.30) ** 1.2; depth = (y - HZ) / (1 - HZ)
            w = (0.004 + 0.02 * depth) * rng.uniform(0.6, 1.4); x = wx + rng.normal(0, 0.002 + 0.01 * depth)
            draw_stroke(dr, [(X(x - w), Y(y)), (X(x), Y(y)), (X(x + w), Y(y))], (1 + 2.5 * depth) * DPI / 100, 0.8 * DPI / 100, 0.9, 0.5)
        apply_strokes(lay, rgb(250, 214, 150), rgb(244, 196, 130), Sw, dry=0.3, seed=68, rim=0)
    LAND = np.clip(HL + FAR, 0, 1)
    np.savez_compressed(OUT.rsplit(".", 1)[0] + "_masks.npz", land=(LAND * 255).astype(np.uint8),
                        land_shape=(np.clip(HL_SHAPE + FAR, 0, 1) * 255).astype(np.uint8),
                        hz=np.float32(HZ), win=np.array([wx, wy], f32))
    save(); sys.exit()
```

Caveats for implementers:

- `paint(..., alpha=HFADE)` passes an **array** as alpha; the engine multiplies `A * alpha` so a per-pixel map works.
  Do not fold the fade into the mask (paint thresholds the mask at 0.5 — that caused the blunt toe in v7).
- The WINDOW_OFF render draws the window dark (`rgb(92,78,86)/(86,72,80)`) and skips the glow and the reflection
  dashes. Because the reflection loop consumes `rng` draws only when `not WOFF`, and it comes **after** everything
  else, the off-render is still identical elsewhere. Keep that ordering.
- With the concave tail the hill height above the horizon at x = 0.0/0.15/0.25/0.35/0.45/0.55/0.65/0.78 is
  1.4/4.4/9.0/17.9/34.4/61.7/99.6/135.0 px (*recovered printout*; the v7 profile was 0/0.3/1.5/6.5/21.6/53.7/98.8/135.0).
- Derived geometry: horizon `HZ·H = 626.4 px`; hill top at x=0.78 is 135 px above the horizon (y ≈ 491); cottage
  `base_y = 0.461` (≈ 498 px), window centre `win = (0.782, 0.4516)` → **(1501.4, 487.7) px**; cottage body 36×19 px.
- The night plate is the same geometry: stars by `riso`, stronger glow (σ 0.04, 0.55), 26 reflection dashes, no smoke.
- Reference images of these plates (pre-v8 hill) are in `docs/ref/canvas_v6/dusk.jpg` / `night.jpg`; the final hill is
  visible in reference frames (§8).

### 3.3 The uncle (`SCENE == "uncle"`)

The code for this scene was **not** shown in the surviving transcript except three polygon fragments. Rebuild from the
description, the fragments, the reference frames and `docs/ref/canvas_v6/uncle.jpg` (the whole figure, ≈v6, with
collar; the v9 figure is the same drawing).

What it is: a sharp-cornered cut-paper silhouette of a bald older man in right-facing profile, head and shoulders,
left third of the frame, on a pale warm paper ground with a lamp-lit glow from the upper right. Owner notes: "sharp
corners" (polygon outlines via `P(...)` **without spline smoothing**), "a bit of a collar where the neck goes in",
bald with a grey fringe, glasses drawn with `ink_line`, cardigan, shirt collar band with cardigan fill under it.

*Recovered polygon fragments* (head-units; origin and scale unrecovered — see the fit below):

```python
# head outline (tail end of the list only — the front of the face/nose was not shown)
    ... (0.33, 0.98), (0.24, 1.01), (0.19, 1.06), (0.19, 1.18), (-0.20, 1.20), (-0.25, 1.02), (-0.33, 0.86), (-0.44, 0.66),
        (-0.47, 0.46), (-0.42, 0.24)]
body = [(-0.24, 1.05), (0.20, 1.10), (0.30, 1.22), (0.37, 1.45), (0.40, 1.85), (0.42, 2.6), (-1.3, 2.6), (-1.2, 1.85),
        ...]                                               # (the rest of the shoulder line was cut off)
collar = [(0.17, 1.10), (0.27, 1.15), (0.38, 1.27), (0.29, 1.33), (0.17, 1.24), (0.13, 1.16)]
```

Approximate pixel mapping (*inferred* fit to the reference): `x_px ≈ 572 + 350·u`, `y_px ≈ 180 + 342·v` (head top
v≈0 at y≈170–180, neck v≈1.2 at y≈590, frame bottom v=2.6 at y≈1069). Treat it as a guide; match the measured
silhouette below.

*Measured silhouette* (frame 744 = t 31.0, head upright): head-mask row extents (x_min, x_max): y=190 (520, 655);
210 (487, 686); 230 (466, 703); 250 (444, 720); 270 (424, 727); 290 (419, 735); 310 (413, 733); 330 (408, 734);
350 (403, 739); 370 (404, 740); 410 (408, 749 brow/glasses); 430 (411, 767); 450 (420, 777 = nose tip); 470 (430, 735
mouth notch); 490 (440, 740); 510 (450, 739); 530 (459, 733); 550 (469, 717 chin); 570 (489, 682); 590 (577, 645 neck).
Head top y ≈ 170. Cardigan/shoulder row extents: y=600 (457, 648); 640 (354, 627); 680 (273, 662); 720 (219, 711);
760 (175, 719); 800 (156, 723); 840 (138, 726); 880 (120, 729); 920 (107, 731); 960 (102, 732); 1000 (97, 733);
1040 (91, 734); runs off the bottom edge. Collar band: bbox ≈ (480, 585)–(735, 715), a pale band sloping down to the
right with a pointed tip at about (700, 700) over the chest.

Painting (from the frames): head fill (66,56,54) near-black brown, `riso` light speckle (237,231,222) sparse;
a pale grey highlight band (112,105,103) on the back of the skull (x≈410–445, y≈260–440, a curved strip); a brown ear
(93,73,67) as a small slanted quadrilateral at about (590–620, 380–440); a thin warm rim light (182,149,114, ≈4–6 px)
along the face edge from forehead to chin (lamp from the right); mouth/nose notches are sharp polygon corners;
glasses = a gold `ink_line` (196,169,134), ≈3 px, an oval lens ≈ 40×36 px around (712, 352) and an arm back to the
temple at ≈(600, 362). Cardigan (90,79,61) with diagonal dry brushwork (`brushwork` strokes at ≈ −35°) and pale
speckle; collar (213,202,184) with a slight shadow under it. Background: paper (232,226,214) on the left warming to
(226,212,185) at the top right (soft radial lamp glow centred off-frame top right).

Layers (*recovered from the summary*): the scene saves
- `uncle_bg.jpg` — the background only;
- `uncle_fig.png` — RGBA, head + body (full frame size);
- `uncle_collar.png` — RGBA collar band, composited **above** head and body (it hides the neck seam);
- `uncle_geo.npz` — `pivot` (head rotation pivot at the neck, px; *inferred* ≈ (600, 575)), `split` (the y where the
  figure is split into head/body, ≈ the neck line y ≈ 575–590), `lens` (glasses lens centre for the glint, ≈ (712, 352)).

The video (`ep4_video.py`) loads `UBG = load("uncle_bg.jpg")`, `_fig = Image.open(A/"uncle_fig.png").convert("RGBA").resize((W, H), LANCZOS)`,
splits `_fig` at `split` into head (above) and body (below; the body keeps an alpha mask so the head can rotate over
it without a seam), and composites body → head (rotated about `pivot`) → collar.

The hole in the head (`WIN_C`, `WIN_R`) is **not** painted into the plate; it is cut live by the video (§4.6.2).

### 3.4 Paper plates (`paper_yellow`, `paper_pink`, `paper_cream`)

Code not recovered: lines ≈20–37 of `ep4_scenes.py` were a branch for the three paper scenes ending
`paper_ground(); save(); sys.exit()`. They are flat, softly mottled coloured papers (no marks). The canvas images
`docs/ref/canvas_v6/paper_{yellow,pink,cream}.jpg` are believed to be the exact final plates (their blob ids were
listed as "current" in the build summary) — **use them directly** unless a re-paint is wanted. To re-paint: fill the
canvas with the base colour, then `canvas *= (1 − 0.03·mottle)` and light `tooth` granulation, plus a few large very
faint darker stains (plaster-like blotches visible in the plates). Base colours: yellow `#f6de96` (246,222,150),
pink `#f0aaba` (240,170,186), cream `#e2dbce` (226,219,206) (canvas fills); final plate means measured in the video:
yellow (236–238, 211–214, 143–145), pink (229–237, 160–166, 176–181), cream (215–221, 209–213, 197–201).

---

## 4. Video — `ep4_video.py`

### 4.1 Structure

- Module top: `import math, os, sys, subprocess, numpy as np, scipy.ndimage as ndi, PIL (Image, ImageDraw, ImageFont, ImageFilter)`;
  `from ep4_timeline import *`; `W, H = 1920, 1080`; `FPS = 24`; `A` = folder holding the backdrop outputs
  (`out/`); `rng = np.random.default_rng(<seed>)`; `F = 1.5`; easing helpers (§1.2).
- `load(name)` → float32 RGB 0–1 array of `A/name` (resized to W×H if needed).
- `font(key, px)` → cached `ImageFont.truetype("fonts/<key>.ttf", int(px))`.
- `comp(base, lay)` → `Image.fromarray(uint8(base*255)).convert("RGBA")` alpha-composited with the RGBA overlay `lay`
  (W×H); returns a PIL RGBA image. Scenes return float32 RGB arrays (`np.asarray(im.convert("RGB"), np.float32)/255`).
- `frame(t)` dispatches on the timeline (§4.10) and returns float32 RGB; the main loop renders `n = round(t0*24) …`,
  converts to uint8 and pipes raw RGB to one `ffmpeg -f rawvideo -pix_fmt rgb24 -s 1920x1080 -r 24 -i - -c:v libx264 …`
  process (*inferred*), printing progress every 5 s.
- Global load (*recovered fragment*, lines 25–43, plus the land-mask edit):

```python
DUSK, NIGHT, UNCLE = load("dusk.jpg"), load("night.jpg"), load("uncle.jpg")
YEL, PINK, CREAM = load("paper_yellow.jpg"), load("paper_pink.jpg"), load("paper_cream.jpg")
MD = np.load(os.path.join(A, "dusk_masks.npz")); MN = np.load(os.path.join(A, "night_masks.npz"))

def prep_masks(m):
    land = np.asarray(Image.fromarray(m["land"]).resize((W, H), Image.BILINEAR), np.float32) / 255
    land = ndi.gaussian_filter(land, 2)
    hz = float(m["hz"]); wx, wy = m["win"] * np.array([W, H])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    glow = np.exp(-(((xx - wx) ** 2 + (yy - wy) ** 2) / (2 * 40.0 ** 2)))
    # the cottage, chimney and smoke stand above the hill line: pin them to the land so the sky can't drag them
    house = ((np.abs(xx - wx) < 60) & (yy > wy - 110) & (yy < wy + 30)).astype(np.float32)
    # (no box around the house any more: only the cloud layer drifts, and the house and smoke sit in the still layer)
    return dict(land=land, hz=hz, win=(wx, wy), glow=glow)
KD, KN = prep_masks(MD), prep_masks(MN)
# clouds as their own layer: full render minus the cloudless render, so they can drift over a still sky
KD["nc"], KN["nc"] = load("dusk_nc.jpg"), load("night_nc.jpg")
KD["cloud"], KN["cloud"] = DUSK - KD["nc"], NIGHT - KN["nc"]
LIGHT_D = DUSK - load("dusk_off.jpg")     # the lit window, its glow and reflection, so the light can come on
```

  `KD_win`, `KN_win` = `KD["win"]`, `KN["win"]` (px; dusk ≈ (1501, 488)). The `house` array is computed but unused (left over).

### 4.2 Sea and sky motion (dusk s1–s2 and night s8)

#### 4.2.1 Row shifters (*recovered*)

```python
COLS = np.arange(W)
def shift_rows(img, rows, dx):
    """shift each listed row horizontally by dx (float, px), linear-interpolated, edges clamped"""
    src = COLS[None, :] - dx[:, None]
    i0 = np.floor(src).astype(np.int32); f = (src - i0)[..., None]
    i0c = np.clip(i0, 0, W - 1); i1c = np.clip(i0 + 1, 0, W - 1)
    r = rows[:, None]
    return img[r, i0c] * (1 - f) + img[r, i1c] * f

def shift_rows_zero(img, rows, dx):
    """like shift_rows, but what slides in from outside the frame is empty (for the cloud layer)"""
    src = COLS[None, :] - dx[:, None]
    i0 = np.floor(src).astype(np.int32); f = (src - i0)[..., None]
    v0 = ((i0 >= 0) & (i0 < W))[..., None]; v1 = ((i0 + 1 >= 0) & (i0 + 1 < W))[..., None]
    r = rows[:, None]
    return img[r, np.clip(i0, 0, W - 1)] * (1 - f) * v0 + img[r, np.clip(i0 + 1, 0, W - 1)] * f * v1
```

(`shift_rows_zero` was the v7 cloud drift; v8+ uses `cloud_layer`.)

#### 4.2.2 `cloud_layer` — drifting and slowly reshaping clouds (*recovered fragment, v8*)

```python
_CW = {}
def cloud_layer(K, rows, t, hzp):
    """the cloud wisps drift left (faster high up) and slowly change shape: two smooth displacement fields swap in
    and out, so the strokes stretch and thin a little as they travel, the way cloud does at dusk"""
    key = (id(K), len(rows))
    if key not in _CW:
        r = np.random.default_rng(77)
        f = [ndi.gaussian_filter(r.standard_normal((len(rows), W)).astype(np.float32), (40, 90)) for _ in range(4)]
        f = [x / (x.std() + 1e-6) for x in f]
        _CW[key] = (f, np.arange(len(rows), dtype=np.float32)[:, None], COLS[None, :].astype(np.float32))
    f, ys, xs = _CW[key]
    drift = -(t * 12.0) * (1.3 - 0.6 * ys / hzp)                       # px: about 12 px/s, a little faster high up
    a1, a2 = math.sin(t * 0.55), math.cos(t * 0.41 + 0.7)
    wx = 7.0 * (a1 * f[0] + a2 * f[1]); wy = 2.2 * (a1 * f[2] + a2 * f[3])
    sy, sx = ys - wy, xs - drift - wx
    return np.stack([ndi.map_coordinates(K["cloud"][rows][..., c], [np.broadcast_to(sy, sx.shape), sx], order=1, mode="constant", cval=0.0)
                     for c in range(3)], -1)
```

The cloud layer is a signed difference image (full − cloudless); `cval=0` means empty sky slides in from the right.

#### 4.2.3 `glints` — twinkling flecks in the window's reflection (*recovered fragment, v9*; replaced the "chevron" sparkle the owner saw as downward arrows)

```python
_GL = {}
def glints(K, hzp, y0, t, night):
    key = (id(K), night)
    if key not in _GL:
        r = np.random.default_rng(91 if night else 90); n = 34 if night else 22; G = []
        for _ in range(n):
            d = r.uniform(0, 1) ** 1.6 * 0.5                            # depth: most near the horizon
            y = hzp + 3 + d * (H - hzp); x = K["win"][0] + r.normal(0, 3 + 30 * d)
            G.append((x, y, (3 + 16 * d) * r.uniform(0.6, 1.3), 0.7 + 1.6 * d, r.uniform(0, 6.28), r.uniform(1.2, 2.6), math.exp(-d / 0.45)))
        _GL[key] = G
    acc = np.zeros((H - y0, W), np.float32)
    for x, y, hl, hh, ph, rate, k in _GL[key]:
        b_ = max(0.0, math.sin(ph + t * rate)) ** 3 * k
        if b_ < 0.02: continue
        xa, xb = int(x - hl - 3), int(x + hl + 4); ya, yb = int(y - hh - 3) - y0, int(y + hh + 4) - y0
        if ya < 0 or yb > acc.shape[0] or xa < 0 or xb > W: continue
        gx = np.arange(xa, xb, dtype=np.float32)[None, :]; gy = np.arange(ya + y0, yb + y0, dtype=np.float32)[:, None]
        acc[ya:yb, xa:xb] += b_ * np.exp(-((gx - x) / hl) ** 4) * np.exp(-((gy - y) / hh) ** 2)
    return np.clip(acc, 0, 1.2)[..., None]
```

#### 4.2.4 `living_sea` — final v9 (*recovered, with the v8/v9 patches applied*)

```python
def living_sea(img, K, t, night=False, on=1.0):
    """small movements for the painted sea scenes: drifting sky, swaying water, a flickering window"""
    out = img.copy()
    hzp = int(K["hz"] * H)
    # sky: the cloud layer drifts and reshapes over the still cloudless sky; the land stays put
    rows = np.arange(0, hzp + 2)
    sky = K["nc"][rows] + cloud_layer(K, rows, t, hzp)
    keep = K["land"][rows][..., None]
    out[rows] = sky * (1 - keep) + img[rows] * keep
    # water: rows sway sideways, more strongly toward the viewer, so strokes and reflections ripple
    y0 = hzp + 2
    ys = np.arange(y0, H, dtype=np.float32)[:, None]; xs = COLS[None, :].astype(np.float32)
    depth = (ys - hzp) / (H - hzp)
    dx = (1.0 + 6.5 * depth) * np.sin(ys * 0.06 + t * 1.5) + (0.6 + 3.0 * depth) * np.sin(ys * 0.019 - t * 0.9 + 1.3)
    dy = (0.3 + 2.6 * depth) * np.sin(xs * 0.011 + ys * 0.045 + t * 1.25)       # a gentle swell, stronger near the viewer
    sy = np.clip(ys + dy, y0, H - 1); sx = np.clip(xs - dx, 0, W - 1)
    for c in range(3): out[y0:, :, c] = ndi.map_coordinates(img[..., c], [sy, sx], order=1)
    # glints in the window's reflection: short horizontal flecks that wink on and off in place (stepped on twos).
    # (The old version was a sine band bent by x, which read as chevrons sliding down the water.)
    out[y0:] += glints(K, hzp, y0, twos(t), night) * np.array([0.30, 0.22, 0.09], np.float32)
    # window: a soft flicker, stepped on twos
    tt = twos(t)
    fl = 0.05 * math.sin(tt * 7.3) + 0.03 * math.sin(tt * 17.1 + 1) + (0.04 if night else 0.0)
    out = out * (1 + on * fl * K["glow"])[..., None] + on * K["glow"][..., None] * np.array([0.10, 0.07, 0.02], np.float32) * (0.5 + fl * 5) * (0.6 if not night else 1.0)
    return np.clip(out, 0, 1)
```

Notes: `t` is the **scene clock** (s1/s2 use absolute t; s8 uses `lt = t − T["s8"][0]`) — never mix a global clock
into the drift, or the house slides off its glow (a bug fixed in v6). Glints are additive light (gold) in the sea
rows only. The window glow `K["glow"]` is a σ = 40 px Gaussian at the window.

#### 4.2.5 Camera helpers

```python
# recovered fragment: push()
def push(img_pil, t, dur, focus, amount=0.045):
    """slow push-in toward a focus point (2.5D camera move on a still)"""
    s = 1 + amount * ease_io(t / dur)
    fx, fy = focus
    w, h = W / s, H / s
    x0 = min(max(fx - w * fx / W, 0), W - w); y0 = min(max(fy - h * fy / H, 0), H - h)
    return img_pil.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + w, y0 + h))
```

Not recovered verbatim, behaviour fixed by usage (`def cam(im, s, cx, cy): return apply_box(im, cam_box(s, cx, cy))` is recovered):

- `cam_box(s, cx, cy)` → `(x0, y0, s)`: a view `W/s × H/s` centred on source point `(cx, cy)`, clamped inside the
  frame (`x0 ∈ [0, W − W/s]`, `y0 ∈ [0, H − H/s]`).
- `push_box(t, dur, focus, amount)` → the same box `push()` uses: `s = 1 + amount·ease_io(t/dur)`, `w = W/s`,
  `x0 = clamp(fx − w·fx/W)`, `y0 = clamp(fy − h·fy/H)`; returns `(x0, y0, s)`.
- `apply_box(im, box)` → `im.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + W/s, y0 + H/s))`.
- Screen mapping for overlays drawn after the camera: `to_screen(x, y) = ((x − x0)·s, (y − y0)·s)`.

### 4.3 2.5D parallax (s1 tilt)

The dusk plate is split into two planes. Far: the cloudless sky with the hill painted out (SKYFILL) and extended below
the horizon. Near: hill + house + sea. During the tilt the near plane is shifted **down** by `dy = PARALLAX·(1−p)^1.5`
source px (70 px at p=0 → 0 at p=1), so it rises faster than the sky as the camera tilts down.

*Recovered fragment* (v9 final, including the `land_shape` change and the smooth inpaint that replaced the
column-copy fill):

```python
# 2.5D: the dusk painting as two planes. Far: sky (hill painted out, extended below the horizon). Near: hill, house and sea.
_hzp = int(KD["hz"] * H)
_nc = KD["nc"]
_land = ndi.gaussian_filter(np.asarray(Image.fromarray(MD["land_shape"] if "land_shape" in MD else MD["land"]).resize((W, H), Image.BILINEAR), np.float32) / 255, 2)   # hill only (its full outline, so the faded toe moves as one piece)
_wx, _wy = KD["win"]; _yy0, _xx0 = np.mgrid[0:H, 0:W].astype(np.float32)
_land = np.maximum(_land, ndi.gaussian_filter(((np.abs(_xx0 - _wx) < 30) & (_yy0 > _wy - 38) & (_yy0 < _wy + 14)).astype(np.float32), 1.2))   # + a tight house
del _yy0, _xx0
_landD = ndi.gaussian_filter(ndi.grey_dilation((_land > 0.02).astype(np.float32), size=(11, 11)), 1.5)
# sky behind the hill: a smooth fill grown in from the surrounding sky (normalised convolution at a few scales), plus
# paper/wash texture borrowed from the sky 150 px higher up. (The old column-copy fill left vertical streaks.)
_hole = (_landD > 0.05).astype(np.float32); _hole[_hzp:] = 1.0
_known = 1 - _hole
SKYFILL = _nc * _known[..., None]; _filled = _known.copy()
for _sg in (6, 16, 40, 100):
    _num = ndi.gaussian_filter(_nc * _known[..., None], (_sg, _sg, 0)); _den = ndi.gaussian_filter(_known, _sg)[..., None]
    _est = _num / np.maximum(_den, 1e-4); _w = np.clip(_den * 6, 0, 1) * (1 - _filled)[..., None]
    SKYFILL = SKYFILL + _est * _w; _filled = np.clip(_filled + _w[..., 0], 0, 1)
_detail = _nc - ndi.gaussian_filter(_nc, (5, 5, 0)); _src = np.roll(_detail, 150, axis=0)
SKYFILL = SKYFILL + _src * (_hole * (np.arange(H)[:, None] < _hzp))[..., None]
SKYFILL[_hzp:] = SKYFILL[_hzp - 2:_hzp - 1]
SKYFILL = SKYFILL * (1 - _known[..., None]) + _nc * _known[..., None]
del _num, _den, _est, _w, _detail, _src
_rowsf = np.arange(H, dtype=np.float32)[:, None]
NEAR_A = np.maximum(_land, np.clip(_rowsf - _hzp + 1, 0, 1))[..., None]          # hill + house + sea
SKY_KEEP = ((1 - _landD) * (_rowsf < _hzp))[..., None]                             # live sky (moving clouds) where it is really sky
def shift_down(a, dy):
    """shift an image down by a fractional number of pixels (top filled with zeros)"""
    i = int(math.floor(dy)); f = dy - i
    def sh(n):
        if n <= 0: return a
        o = np.zeros_like(a); o[n:] = a[:-n]; return o
    return sh(i) * (1 - f) + sh(i + 1) * f if f > 1e-3 else sh(i)
def parallax(base, dy):
    sky = base * SKY_KEEP + SKYFILL * (1 - SKY_KEEP)
    if dy < 0.05: return base
    na = shift_down(NEAR_A, dy); nb = shift_down(base, dy)
    return sky * (1 - na) + nb * na
```

Known artefact: a faint vertical streak at the house is paint texture (it shows at the same level with parallax off) —
acceptable.

### 4.4 Scenes 1–2: `scene_dusk(t)` (one continuous shot, 0 → 17.50)

#### 4.4.1 Recovered body (v7 form; the two tag lines changed later, see below)

```python
def scene_dusk(t, t_scene0=0):
    """scenes 1 and 2 are one shot: high on the sky with gulls, tilt down to the sea and the house (the near plane rising
    faster than the sky), the window lights, then a slow push in"""
    on = ease_io((t - LIGHT_ON) / 0.5)
    base = living_sea(DUSK - (1 - on) * LIGHT_D, KD, t, on=on)
    if t < TILT[1]:
        p = ease_io((t - TILT[0]) / (TILT[1] - TILT[0]))
        base = parallax(base, PARALLAX * (1 - p) ** 1.5)
        box = cam_box(2.0 - 1.0 * p, (0.32 + 0.18 * p) * W, (0.25 + 0.25 * p) * H)     # starts on sky only: hill, horizon and house out of shot
    else:
        box = push_box(t - TILT[1], T["s2"][1] - TILT[1], KD_win, 0.06)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t >= T["s2"][0] + FLY_OUT[0]:
        u = ease_io(min(1, (twos(t) - T["s2"][0] - FLY_OUT[0]) / FLY_OUT[1]))
        fly(lay, PATH_OUT, u, 260, 16, -14, -2, t, (243, 235, 224, 170))
    im = apply_box(comp(base, lay), box)
    x0, y0, sc = box
    birds(im, t, lambda x, y: ((x - x0) * sc, (y - y0) * sc), sc)
    if TITLE[0] <= t < TITLE[1]:
        im.alpha_composite(title_reveal(t - TITLE[0], TITLE[1] - TITLE[0]))      # v8: was a static tag()
    # v8: the "YOUR LETTER" tag became eyebrow(...), which returns an empty layer (EYEBROWS = False) — omit it entirely
    return np.asarray(im.convert("RGB"), np.float32) / 255
```

Camera, worked out: at t ≤ 0.6 the box is zoom 2.0 centred (614.4, 270) → source rect x 134.4–1094.4, y 0–540
(sky only; birds large). At t = 5.0 zoom 1.0 = full frame (horizon at y = 626, house at (1501, 488)). Then
`push_box` from 5.0 to 17.50 pushes 6 % toward the window (house ends ≈ (1490, 476) on screen at 12 s, measured).

Light-on: the window, its glow and its sea reflection fade in over 4.20–4.70 (`ease_io`), and the flicker scales with `on`.

#### 4.4.2 Birds (painted gulls, screen space, after the camera)

*Recovered*: `bird_sprite(span, wy)` draws two tapered brush-stroke wings plus a small body at 4× supersampling,
cached; `birds(im, t, to_screen, scale)` draws them on the camera-applied PIL image.
`BIRDS = [(380, 0.17, 40, 0.0, 17), (560, 0.21, 34, 1.3, 14), (470, 0.13, 46, 2.1, 19)]`; flap = `sin(twos(t)*5.2)`
modulated by a glide factor (slower periods where the bird glides).

Tuple meaning (*measured* against the reference): `(x0_src, y_frac, speed_px_per_s, phase, half_span_px)`:
source position `x = x0 + speed·t` (rightward), `y = y_frac·H` (+ a small bob); drawn at
`to_screen(x, y)` with size `half_span·scale`. Check: at t=0 the gulls are on screen at ≈ (488,361), (669,287),
(850,464) (= source (378,180), (468,143), (559,232)); at t=3.0 source ≈ (497,182), (607,131), (661,220) →
speeds 40, 46, 34 px/s. Colour: dark slate (≈ (70,62,80), soft, alpha ~0.85), wings as two curved tapered strokes
(gull "m" shape), wingspan on screen at t=0 ≈ 70 px. Flap: wing tips move ±(0.35·half_span) vertically with
`sin(twos(t)*5.2 + phase)`, times a glide factor `g = 0.35 + 0.65·smoothstep(sin(t*0.7+phase))` (*inferred* — any
slow modulation that makes them alternate flapping and gliding). Birds remain throughout s1–s2 (visible near the top
of frame at 16.5 s).

#### 4.4.3 The letter flight out (s2) and `fly()`

`fly(lay, path, u, size0, size1, rot0, rot1, t, dot_col)` (*name and call recovered; body inferred*):
- `path(u)` is a cubic Bézier in source px; the envelope sprite `ENV` (§4.8.3) is scaled to width
  `size0 + (size1 − size0)·u` px, rotated `rot0 + (rot1 − rot0)·u` degrees, centred on `path(u)`.
- A dotted trail of small round dots (radius ≈ 2.5–3 px, spacing ≈ 18–22 px along the arc) in `dot_col` is drawn along
  the path from `u = 0` to the current `u` behind the envelope; the whole travelled trail stays visible. Dots taper
  smaller toward the far end (the house).
- Hidden when `u ≤ 0`; at `u = 1` the envelope is 16 px and sits at the window.

`PATH_OUT` (*inferred* from the canvas storyboard, ×1.5): P0 (180, 960), P1 (540, 675), P2 (1080, 495),
P3 = window (1501, 488) — from off the bottom-left, over the sea, arcing up and slightly over to the cottage window.
Call: `fly(lay, PATH_OUT, u, 260, 16, -14, -2, t, (243, 235, 224, 170))` with
`u = ease_io(min(1, (twos(t) − 14.46)/2.4))` (14.46 → 16.86). The envelope enters large (≈260 px), tilted −14°, at the
bottom-left (frame at 15.0: lower-left corner), and shrinks into the window by 16.86.

#### 4.4.4 Title fold-in — `title_reveal` (*recovered fragment, v8*, then **modified for the standalone title**)

v8/v9 code (two tags: "EPISODE 4" dark + title light):

```python
TITLE_LAY = None
def title_reveal(lt, dur):
    """the episode title folds in: each tag grows from its left edge in stepped, ragged jumps (on twos), the lower line a beat
    behind; on the way out it is wiped away left to right the same way"""
    global TITLE_LAY
    if TITLE_LAY is None:
        TITLE_LAY = tag([("EPISODE 4", 16, (238, 238, 236), INK), ("THE UNCLE WHO ONLY READS LETTERS", 22, INK, (238, 238, 236))], (64 * F, H - 64 * F), "bl")
    a = np.asarray(TITLE_LAY.getchannel("A"), np.float32)
    ys, xs = np.nonzero(a > 0); x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    lt = twos(lt); span = x1 - x0 + 24
    split = H - 64 * F - (22 * F * 1.25 + 18 * F) - 5 * F                   # between the two tags
    rows = np.arange(y0, y1)
    r = np.random.default_rng(int(lt * 12) + 3)
    band = np.repeat(r.uniform(-1, 1, (y1 - y0) // 5 + 2), 5)[: y1 - y0] * 5 * F   # ragged leading edge, re-cut every frame
    delay = np.where(rows > split, 0.12, 0.0)
    p_in = np.array([ease((lt - d) / 0.42) for d in delay]); p_out = np.array([ease((lt - (dur - 0.42) - d * 0.5) / 0.36) for d in delay])
    edge_in = x0 - 12 + p_in * (span + 12) + band * (p_in < 1)
    edge_out = x0 - 12 + p_out * (span + 12) + band * ((p_out > 0) & (p_out < 1))
    cols = np.arange(x0, x1)[None, :]
    m = ((cols < edge_in[:, None]) & (cols >= edge_out[:, None])).astype(np.float32)
    out = np.array(TITLE_LAY); out[y0:y1, x0:x1, 3] = (out[y0:y1, x0:x1, 3] * m).astype(np.uint8)
    return Image.fromarray(out, "RGBA")
```

**Rebuild (owner change 2)**: one tag only, no delay:

```python
TITLE_LAY = tag([("THE UNCLE WHO ONLY READS LETTERS", 22, INK, (238, 238, 236))], (64 * F, H - 64 * F), "bl")
delay = np.zeros(len(rows))          # no second line to lag
```

Everything else identical: fold-in 0.42 s from 5.60 (cubic ease-out, stepped at 12 fps, ragged leading edge re-cut
each step with 5-row bands of ±5F px), held, wiped out left→right over 0.36 s starting at `dur − 0.42` (10.18 → 10.54).
Geometry: the light tag box is x 96 → ≈ 96 + (text width + 42) px, y ≈ 915.75 → 984 (bottom-left anchored at
(96, 984)); text IBM Plex Mono 33 px, INK on (238,238,236), tracking 0.10·33 px; box roughened (§4.8.1).
In the reference (which still has EPISODE 4) the dark tag sits at y ≈ 850–901 above it — delete that.

#### 4.4.5 `tag()` and `eyebrow()` (*recovered*, v9 values)

```python
EYEBROWS = False      # the black scene labels; off since v8 (the title tag stays)
def eyebrow(*a, **k): return tag(*a, **k) if EYEBROWS else Image.new("RGBA", (8, 8), (0, 0, 0, 0))
TAGC = {}
def tag(lines, pos, anchor="tl"):
    """mono boxed tags; lines = [(text, size, fg, bg)]"""
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(lay)
    x, y = pos; boxes = []
    for text, size, fg, bg in lines:
        fnt = font("mono", size * F); tr = size * F * (0.14 if size < 20 else 0.10)
        tw = sum(dr.textlength(c, font=fnt) + tr for c in text) - tr
        padx, pady = 12 * F if size < 20 else 14 * F, 7 * F if size < 20 else 9 * F
        bw, bh = tw + 2 * padx, size * F * 1.25 + 2 * pady
        boxes.append((text, fnt, tr, fg, bg, bw, bh, padx, pady))
    if anchor == "bl":
        y = y - sum(b[6] for b in boxes) - 10 * F * (len(boxes) - 1)
    for text, fnt, tr, fg, bg, bw, bh, padx, pady in boxes:
        bx = x if anchor in ("tl", "bl") else x - bw
        key = (int(bw), int(bh), tuple(bg))
        if key not in TAGC:
            m = 8; bi = Image.new("RGBA", (int(bw) + 2 * m, int(bh) + 2 * m), (0, 0, 0, 0))
            ImageDraw.Draw(bi).rectangle([m, m, m + bw, m + bh], fill=tuple(bg))
            TAGC[key] = rough(bi, 0.6, 10, seed=31 + len(TAGC), fine=0.1)        # v8 softened (v7: 1.1, fine 0.22)
        lay.alpha_composite(TAGC[key], (int(bx) - 8, int(y) - 8))
        tracked(dr, (bx + padx, y + pady + 1), text, fnt, fg, tr)
        y += bh + 10 * F
    return lay

def tracked(dr, xy, text, fnt, fill, track):
    x, y = xy
    for ch in text:
        dr.text((x, y), ch, font=fnt, fill=fill)
        x += dr.textlength(ch, font=fnt) + track
    return x
```

With eyebrows off, **no** scene labels appear anywhere (the old ones were YOUR LETTER, HE READS EVERY WORD, HIS
REPLY, AND THEN IT'S GONE, YOUR NEXT LETTER, EVERY LETTER CARRIES THE WHOLE CONVERSATION). The rebuild can drop
`eyebrow` entirely.

### 4.5 Transition w3: window-to-window blur (17.50 → 18.60)

*Recovered names/params*: `light_rush(img_f, s, focus, blur, glow, radius, col)` using `zoom_at`; in the first 55 % of
w3 the dusk shot rushes into `KD_win` (scale up to 3.6, blur up to 18 px, warm glow); then `resolve()` comes out of the
uncle's head window `WIN_C` over `_RD`, which runs into the first 0.4 s of s3. In s3 the head window is open from the
start (`window(lay, 1.0, …)`). Bodies not recovered — implement:

- `zoom_at(img, s, focus)` — scale the image by `s` about the fixed point `focus` (focus stays put on screen; bicubic).
- **Rush** (17.50 → 17.885, `q = (t − 17.50)/0.385`): take the frame `scene_dusk(t)` would give at this time (its push
  box applies; the house window is at its screen position), then `s = 1 + 2.6·ease_in(q)` (→ 3.6; use `q²` or
  `1 − ease_io` mirror), Gaussian blur σ = 18·q px, and add a warm radial glow at the window: colour `col` ≈
  (255, 214, 140), radius growing from ≈ 60 px to > 1000 px, mixing amount → ≈ 0.85 at q=1 (frame 17.85 is a warm
  yellow wash with the blurred hill still faintly visible bottom-left).
- **Resolve** (17.885 → 18.60, `r = (t − 17.885)/0.715`): render `scene_reads(t − T["s3"][0])` (clamped ≥ 0) with the
  window open, `zoom_at(img, s, WIN_C)` with `s = 1 + 1.2·(1 − ease(r))` (≈2.2 → 1.0), blur σ = 18·(1 − ease(r)),
  warm glow at `WIN_C` fading from ≈0.85 to 0. *Measured* zoom about the hole: ≈1.67 at 18.00, ≈1.37 at 18.15,
  ≈1.0–1.15 by 18.40; sharp by ≈18.40; settled at 18.60. Frame 18.00 shows the uncle blurred, greyed by the warm wash,
  enlarged about the hole (hole stays at (537, 316)).
- Sound: a whoosh panned 0.45 → −0.1 starting 0.35 s before w3 (§5.4).

### 4.6 The uncle scenes (s3, s5; also the outgoing frame of w4 and the incoming frame of w6)

#### 4.6.1 Layers and motion

- `WIN_C = (0.27975 * W, 0.2924 * H)` = **(537.1, 315.8)**, `WIN_R = 62 * F` = **93 px** (*recovered*).
- Composition per frame: `UBG` → body layer → head layer rotated by `θ` about `pivot` (bicubic, expand=False) →
  collar layer → hole/window + icon (in head space, so they rotate with the head) → glint on the glasses lens →
  overlays (letter card, drifting words).
- Breathing loop (*recovered: "a breathing loop"*; measured): the whole figure (or head + shoulders) rises and falls
  ≈ ±3 px with a period of ≈ 4–5 s (head top measured 165–173 px during s3/s5).
- Read-nod (s3, `READ_TILT = 1.6` → 19.80): head rotates forward (nose down) by ≈ 1.5–2° about `pivot`, eased over
  ≈ 0.7 s, held to the end of s3 (measured: nose tip (775,438) → (781–783, 446–449); back of skull x 406 → 412).
- s5 starts in the nodded pose and lifts back upright around FORGET (back of skull 417 at 30.0 s → 403 by 34.0 s, *measured*)
  — i.e. ease the tilt from 1 → 0 over ≈1 s starting at FORGET (32.79).
- Dry glint (*recovered*): a thin short diagonal highlight line across the glasses lens, alpha `150·g`, Gaussian blur
  0.8, where `g` is a brief pulse (*inferred*: one pulse when the letter lands in s3 and occasionally after; keep it
  subtle — owner: "the blink should feel less glowy"; the halo around the hole was removed in v6/v7).

#### 4.6.2 The hole — `window()` (*recovered: "the crisp supersampled hole (`window()`), with the icon threshold at > 0.02"*)

`window(lay, open_frac, icon=0.0, …)` draws, at 4× supersampling then LANCZOS down, a filled circle of radius
`WIN_R·open_frac` at `WIN_C` in the uncle-background colour (≈ (228, 217, 201) — sample `UBG` at the centre so it
reads as a hole through the head), crisp edge, no halo. If `icon > 0.02` it draws the envelope sprite `ENV` inside,
centred, at width `≈ 1.1·WIN_R·icon` (full icon ≈ 100 px wide, measured), with a faint drop shadow. (The `> 0.02`
threshold avoids a zero-size resize crash.)

- s3: `open_frac = 1` from the first frame of s3 (also during the resolve). Icon: 0 until s3 + 0.70 (18.90), then grows
  `icon = ease((lt − 0.70)/0.30)` (tiny at 18.95, full by ≈19.20); stays 1.
- s5: icon 1 until FORGET (32.79), then shrinks `icon = 1 − ease((lt − FORGET)/0.35)` (gone ≈33.15). Hole stays open
  until `HOLE_CLOSE = 9.3` (39.49), then `open_frac = 1 − ease_io((lt − 9.3)/0.45)` (measured ≈0.85 at 39.65, ≈0.55 at
  39.8, closed by ≈40.0) and the head is solid for the rest of s5 and in w6.

#### 4.6.3 Scene 3 — `scene_reads(lt)` (18.20 → 24.10)

- Uncle layers, window open, envelope icon arriving at 0.70 s (with the `settle` sound at s3+0.75).
- The letter card `LETTER = card([("i", "Dear Uncle,"), ("r", "What can I cook tonight with eggs and spinach?"), ("i", "Love, Sam")], 420 * F, -2)`
  (*recovered*; default `size=30` → 45 px Source Serif; italic lines in `serif_i`) slides in from the right at
  s3 + 1.2 (19.40; `slide_b` sound): from off-screen right to its rest position in ≈0.5 s with `ease`, on twos.
  Rest position (*measured*): paper rect ≈ x 1134–1775, y 271–806 (rotated −2°, i.e. clockwise, right side lower);
  first text line ("Dear Uncle,") cap top at y ≈ 353, x ≈ 1203. At 19.6 it is still entering (left edge ≈ x 1545).
- Read-nod at 1.6 s, breathing throughout. Card stays until the w4 wipe.

#### 4.6.4 Scene 5 — `scene_forget(lt)` (30.19 → 40.90)

- Uncle layers; envelope icon in the hole at the start; head lifts upright after FORGET.
- At FORGET (32.79) the icon shrinks away (`air` sound, §5.4) and the **words drift out** of his face:
  `WORDS = [("spinach", 26, 0, 90, .85), ("eggs", 24, 60, 160, .75), ("tonight", 22, 150, 40, .6), ("omelette", 22, 200, 220, .55), …]`
  (*recovered* first four; the full storyboard list from the canvas is
  `("Dear Uncle", 20, 290, 120, .45), ("butter", 18, 380, 290, .35), ("Sam", 16, 470, 60, .25), ("fold", 15, 520, 190, .2), ("cook", 13, 610, 260, .12), ("love", 12, 660, 140, .08)`
  — all ten are visible in the reference). Tuple = `(text, size_1280, x_1280, y_1280, alpha)`; the storyboard placed
  them relative to an origin (440, 110) in 1280-space → (660, 165) px; font `mono` at `size·F` px; colour INK at `alpha`.
- Motion (*measured*, behaviour to reproduce): words appear one after another from FORGET + 0.1 s (spinach first,
  then eggs, tonight, …, ≈0.12–0.2 s apart), each emerging at the front of the face (≈ (810, 350)) and easing out over
  ≈1–1.5 s to its layout spot `(660 + x·F, 165 + y·F)`, then drifting slowly right (≈ +10 px/s for the near words up to
  ≈ +45 px/s for the far ones) and slightly up, so the cloud of words spreads. Positions measured (top-left of text):
  spinach (815,343) @32.9 → (782,303) @34.2 → (799,293) @36.0 → (813,270) @37.0 → (838,272) @38.6; eggs (≈850,385) @34–37;
  tonight (1028,195) @37.0; Dear Uncle (1146,343) @36.0 → (1230,345) @37.0; Sam (1368,269) @36 → (1484,248) @37;
  omelette (1080,490) @36.0; butter (1299,574) @36; fold (1352,420) @36; cook (1320,464) @36; love (1635,365) @37.
  Opacity: fade in over ≈0.4 s each; all fade out together over `FADE_WORDS = (7.2, 9.5)` → 37.39 → 39.69 (gone by
  "Gone" at 39.61). Drawn on twos.
- Hole closes from 39.49 (above). The last second (40.0–40.9) is the uncle with a solid head.

### 4.7 Paper scenes with the prompt box (s4 yellow, s6 pink)

#### 4.7.1 Helpers (*recovered*, v9 values)

```python
def wrap(dr, text, fnt, width):
    words, lines, cur = text.split(" "), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if dr.textlength(trial, font=fnt) <= width: cur = trial
        else: lines.append(cur); cur = w_
    lines.append(cur); return lines

def text_block(lay, xy, text, fnt, width, lh, fill=INK, nchars=None, cursor=False):
    dr = ImageDraw.Draw(lay)
    lines = wrap(dr, text, fnt, width)
    shown = len(text) if nchars is None else nchars
    x, y = xy; used = 0
    last = (x, y)
    for ln in lines:
        take = max(0, min(len(ln), shown - used))
        dr.text((x, y), ln[:take], font=fnt, fill=fill)
        last = (x + dr.textlength(ln[:take], font=fnt), y)
        used += len(ln) + 1
        if take < len(ln): break
        y += lh
    if cursor:
        cx, cy = last
        dr.rectangle([cx + 6 * F, cy + 0.12 * lh, cx + 9 * F, cy + 0.88 * lh], fill=fill)
    return lines

PBC = {}
def prompt_box(lay, xy, w, text, size, highlight=None, nchars=None):
    dr = ImageDraw.Draw(lay); fnt = font("sans", size * F)
    lines = wrap(dr, text, fnt, w - 64 * F)
    lh = size * F * 1.4
    hgt = len(lines) * lh + 52 * F
    x, y = xy
    # --- (rest not recovered) ---
```

Rest of `prompt_box` (*inferred*, consistent with the frames): the outline is a rounded rectangle at
`(x, y, x + w, y + hgt)`, radius 18F, stroke ≈ 2F (3 px) INK, drawn into a cached RGBA image (`PBC`, keyed by size) and
roughened with `rough(bi, 0.55, 14, seed=61 + len(PBC), fine=0.05)` (v8; v7 was 0.9/0.1) — the outline reads hand-drawn
and slightly wavy. Text in `sans` at `size·F`, INK, starting at `(x + 32F, y + 26F)`, line height `1.4·size·F`, wrapped
at `w − 64F`, showing `nchars` characters (typing; no cursor in the box). `highlight = (word, p)`: before drawing the text,
fill a rectangle behind the regex-matched word (`\bword\b`) in `HL` from the word's left edge to `left + p·width`
(full height of the line box ≈ x-height + ascenders, padding ≈ 2–4 px), so the sweep runs left→right. The box height
is computed from the **full** text so it doesn't grow while typing. Returns the box rect (the recovered call stores
it: `hb = prompt_box(...)`).

#### 4.7.2 Scene 4 — `scene_reply(lt)` on `YEL` (24.70 → 29.49)

- `hb = prompt_box(lay, (240 * F, 150 * F), 800 * F, "Dear Uncle, what can I cook tonight with eggs and spinach? Love, Sam", 28)`
  (*recovered*) → box x 360–1560, y 225–≈421 (2 lines of Manrope 42 px; *measured* outline bbox (359,223)–(1562,424);
  text starts (411, 279)).
- Reply (*inferred from frames + canvas*): `text_block(lay, (244F, hb_bottom + 40F), REPLY, font("serif_b", 34F), 800F, 34F*1.35, nchars=m, cursor=True)`
  with `REPLY = "A spinach omelette. Wilt the spinach in butter, pour in three beaten eggs, fold it over and serve."`
  (98 chars) and `m = int((twos(lt) − 0.6)·24)`. Measured: first line cap top y = 497, x = 367; line height ≈ 69 px;
  wraps after "butter," (line 1 ends x ≈ 1511). Before typing starts (lt < 0.6) a bold "…" sits at the text origin
  (visible at 25.0). The cursor (a 3F-wide bar) shows while typing and remains after the last character.
- Sound: typewriter keystrokes, one per character (§5.5).

#### 4.7.3 Scene 6 — `scene_second(lt, static=False)` on `PINK` (41.50 → 49.37)

- Prompt box at `(240 * F, 190 * F)`, width `800 * F`, size **30** (45 px): measured outline (360, 283)–(1561, 429).
  Text "Thanks! Can you make it without eggs?" types into it from `Q2_TYPE = (1.5, 16.0)` → 43.00 at 16 cps
  (`nchars = int((twos(lt) − 1.5)·16)`; empty box before 43.0).
- At `ANS_DOTS = 3.9` (45.40) a bold "…" appears at the answer origin; from `ANS_TYPE = (4.3, 14.0)` (45.80) "Make what,
  dear?" types at 14 cps in `serif_b` **40F (60 px)**, at `(244F, box_bottom + 44F)` ≈ (366, 495); measured cap top
  y = 515, x = 368, extent to x ≈ 872.
- At `IT_SWEEP = 6.0` (47.50) the word "it" in the prompt box gets a yellow sweep (`highlight=("it", ease((lt − 6.0)/0.4))`;
  partial at 47.6, full by ≈47.9). Sound: `slide_b` swipe at −30 dB.
- `static=True` (used as the outgoing frame of w7) = everything complete.

### 4.8 Cards, tape, envelope, edge roughness

#### 4.8.1 `rough()` — static edge roughness (*recovered*)

```python
HL = (245, 212, 74)                      # the one accent: Vox-ish marker yellow
def rough(im, amp=1.5, size=12, seed=0, fine=0.3):
    """static turbulent displacement on an RGBA image, so flat shapes read as cut or printed rather than vector-perfect"""
    a = np.asarray(im, np.float32); h, w = a.shape[:2]
    r = np.random.default_rng(seed)
    def field():
        f = ndi.gaussian_filter(r.standard_normal((h, w)).astype(np.float32), size / 3)
        g = ndi.gaussian_filter(r.standard_normal((h, w)).astype(np.float32), 1.0)
        return f / (f.std() + 1e-6) * amp + g / (g.std() + 1e-6) * amp * fine
    dx, dy = field(), field()
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    out = np.stack([ndi.map_coordinates(a[..., c], [yy + dy, xx + dx], order=1, mode="nearest") for c in range(4)], -1)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
```

v9 settings (the owner said v7's were "slightly too rough"; v8 roughly halved them):

| element | v9 call | (v7) |
|---|---|---|
| tag boxes | `rough(bi, 0.6, 10, seed=31 + len(TAGC), fine=0.1)` | (1.1, 10, fine 0.22) |
| prompt-box outline | `rough(bi, 0.55, 14, seed=61 + len(PBC), fine=0.05)` | (0.9, 14, fine 0.1) |
| envelope | `ENV = rough(envelope(320), 0.6, 10, seed=7, fine=0.15)` | (1.0, 10) |
| card paper | `im = rough(im, 0.8, 12, seed=101 + seed, fine=0.15)` | (1.4, 12) |

Roughness is static (no boil). Text is always drawn **after** roughening so it stays crisp.

#### 4.8.2 `card()` (*signature, docstring fragment and anchor code recovered; layout inferred*)

`card(text_lines, w, rot, label=None, bold=False, size=30, marks=None, seed=0, anchors=None)`:
"lays out first, draws marker sweeps `{word: progress}` via regex `\b…\b`, roughens, draws text, rotates, and
optionally returns word anchors (left, right, top, bottom) mapped through the rotation"; docstring: "anchors: list of
words whose (left, right, mid-y) positions in the rotated image are returned as well."

- `text_lines`: list of `(style, text)` with style `"i"` (serif_i), `"r"` (serif, or serif_b if `bold`), (or plain
  strings when `bold=True`, as `C2_ARGS` passes). Font size `size·F` px; line height ≈ 1.4–1.45 × size·F; paragraph
  gap ≈ 0.5–0.65 × size·F; padding ≈ 26F top/bottom, 30F sides for the small history cards (canvas), 40F/44F for the
  big letter (measured text inset ≈ 68 px).
- `label`: small caps line above the text in `mono` ≈ 13F (≈ 20 px), tracking 0.14 em, colour (109,106,111), gap 10F.
- Paper (242,233,217) rectangle `w` wide × content height, on a transparent canvas with a margin (≈ 40 px each side,
  hence `CARD_POS = (x·F − 40, y·F − 40)`), soft drop shadow (offset ≈ (0, 14F·0.7), blur ≈ 20–30 px, INK at α ≈ 0.16).
- `marks`: highlights drawn on the paper before roughening: for each `{phrase: p}` find the phrase (word-boundary
  regex) in the laid-out lines and fill `HL` from its left to `left + p·width`, height ≈ 0.95·size·F, with a slightly
  irregular marker edge (it then gets roughened with the paper).
- Then `rough(im, 0.8, 12, seed=101+seed, fine=0.15)`, then the text (crisp), then `im.rotate(rot, expand=True, resample=BICUBIC)`
  (PIL: positive = counter-clockwise).
- Anchors (*recovered*):

```python
    if anchors is None: return out
    W1, H1 = out.size; ar = math.radians(rot)
    def rp(px, py):
        dx, dy = px - W0 / 2, py - H0 / 2
        return (W1 / 2 + dx * math.cos(ar) + dy * math.sin(ar), H1 / 2 - dx * math.sin(ar) + dy * math.cos(ar))
    res = {}
    for word in anchors:
        f_ = find(word)
        if f_:
            x0, x1, yy_ = f_; ym = yy_ + 0.62 * fs
            res[word] = dict(left=rp(x0, ym), right=rp(x1, ym), top=rp((x0 + x1) / 2, yy_ + 0.05 * fs), bottom=rp((x0 + x1) / 2, yy_ + 1.25 * fs))
    return out, res
```

  (`W0, H0` = unrotated size; `fs` = font px; `find(word)` returns `(x0, x1, line_top_y)` of the first `\bword\b` match.)

#### 4.8.3 `tape()` and `envelope()`

- `tape(w, h, rot, seed)` — "a strip of paper tape: translucent, torn ends" (*recovered docstring*): a `w×h` px strip
  (120×36 here, **not** ×F) of (236,224,196) at α ≈ 0.78 with ragged short ends (seeded), faint fibre texture,
  rotated `rot` degrees.
- `envelope(w)` — `w = 320` px wide sprite, aspect ≈ 1.55 (≈ 320×206): paper (239,230,214) with a thin border
  (205,191,168), flap V lines (168,151,127) from the top corners to ≈ 60 % height at the centre, two lower fold lines
  from the bottom corners toward the centre (205,191,168), a red stamp (188,97,94, α 0.85) top-right (≈ 13 %×25 % of
  the size, inset ≈ 7 %), and a soft shadow. `ENV = rough(envelope(320), 0.6, 10, seed=7, fine=0.15)`.

#### 4.8.4 Scene 7 — `scene_history(t, static=False)` on `CREAM` (49.97 → 61.17)

*Recovered* (v9 final; arrow waypoints from the last patch):

```python
CARDS = [card([("r", "What can I cook tonight with eggs and spinach?")], 500 * F, 3, "YOUR FIRST LETTER", size=22, seed=1),
         card(*C2_ARGS, size=22, seed=2),
         card(*C3_ARGS, size=22, seed=3)]
_, ANC2 = card(*C2_ARGS, size=22, seed=2, anchors=["omelette", "spinach"])
_, ANC3 = card(*C3_ARGS, size=22, seed=3, anchors=["it"])
CARD_HL = {}
def card_marked(i, p_it, p_om):
    key = (i, round(p_it, 2), round(p_om, 2))
    if key not in CARD_HL:
        CARD_HL[key] = card(*C2_ARGS, size=22, seed=2, marks={"spinach omelette": p_om}) if i == 1 else card(*C3_ARGS, size=22, seed=3, marks={"it": p_it})
    return CARD_HL[key]

CARD_POS = [(110 * F - 40, 140 * F - 40), (150 * F - 40, 300 * F - 40), (125 * F - 40, 470 * F - 40)]
TAPES = [(tape(120, 36, 6, 1), (110 * F + 300, 140 * F - 26)), (tape(120, 36, -8, 2), (150 * F + 360, 300 * F - 26)), (tape(120, 36, 4, 3), (125 * F + 320, 470 * F - 26))]
ANS2 = "Without eggs? Try spinach and cheese on toast."
def scene_history(t, static=False):
    lt = twos(t)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p_it = 1 if static else ease((lt - ANNOT[0]) / 0.45)
    p_ar = 1 if static else (lt - ANNOT[1]) / 0.65
    p_om = 1 if static else ease((lt - ANNOT[2]) / 0.5)
    for i, (c, pos) in enumerate(zip(CARDS, CARD_POS)):
        if i == 1 and p_om > 0: c = card_marked(1, 0, p_om)
        if i == 2 and p_it > 0: c = card_marked(2, p_it, 0)
        p = 1 if static else ease((lt - CARD0 - CARD_GAP * i) / 0.45)
        if p <= 0: continue
        cc = c if p >= 1 else c.resize((int(c.width * (1.08 - 0.08 * p)), int(c.height * (1.08 - 0.08 * p))), Image.LANCZOS)
        x = pos[0] - (cc.width - c.width) / 2; y = pos[1] - (cc.height - c.height) / 2 - 60 * (1 - p)
        a = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a.alpha_composite(cc, (int(x), int(y)))
        if p < 1: a.putalpha(a.getchannel("A").point(lambda v: int(v * min(1, p * 2))))
        lay.alpha_composite(a)
        tp, tpos = TAPES[i]
        if static or lt > CARD0 + CARD_GAP * i + 0.5: lay.alpha_composite(tp, (int(tpos[0]), int(tpos[1])))
    if p_ar > 0:      # from "it" in the new letter, round to the end of "spinach omelette" in his reply
        it = ANC3["it"]["top"]; om = ANC2["omelette"]["right"]
        a0 = (CARD_POS[2][0] + it[0], CARD_POS[2][1] + it[1] - 10)      # rises straight out of the middle of "it"
        a3 = (CARD_POS[1][0] + om[0] + 16, CARD_POS[1][1] + om[1])
        R = CARD_POS[1][0] + CARDS[1].width - 20
        # up out of the middle of "it", right through the clear band under his reply, round the card's edge and back in
        ym = (a0[1] - 100 + a3[1]) / 2
        ink_arrow(lay, (a0, (a0[0] + 10, a0[1] - 40), (a0[0] + 100, a0[1] - 68), (R - 30, a0[1] - 76), (R + 30, a0[1] - 90), (R + 62, a0[1] - 116),
                        (R + 74, ym), (R + 60, a3[1] + 24), (R + 22, a3[1] + 9), (a3[0] + 90, a3[1] + 3), a3), ease_io(p_ar))
    if static or lt > ANS2_DOTS:
        m = len(ANS2) if static else int((lt - ANS2_TYPE[0]) * ANS2_TYPE[1])
        if not static and lt < ANS2_TYPE[0]: text_block(lay, (760 * F, 300 * F), "…", font("serif_b", 34 * F), 420 * F, 34 * F * 1.35)
        elif m > 0: text_block(lay, (760 * F, 300 * F), ANS2, font("serif_b", 34 * F), 420 * F, 34 * F * 1.35, nchars=m)
    # (the eyebrow "EVERY LETTER CARRIES THE WHOLE CONVERSATION" was here; EYEBROWS = False → nothing)
    return np.asarray(comp(CREAM, lay).convert("RGB"), np.float32) / 255
```

`C2_ARGS` / `C3_ARGS` (*summary + frames; exact tuples not recovered*):
- `C2_ARGS = (["A spinach omelette.", "Wilt the spinach in butter, pour in three beaten eggs…"], 500 * F, ≈ -1.5, "HIS REPLY", True)`
  — two paragraphs, **bold** serif 33 px, label HIS REPLY (measured card 2 top edge falls to the right ≈1–1.5°).
  The reply text is deliberately cut with "…" (the tape of card 3 covers "eggs…").
- `C3_ARGS = ([("r", "Thanks! Can you make it without eggs?")], 500 * F, ≈ 1, "YOUR NEW LETTER")`.
- (canvas storyboard rotations were −3 / +1.5 / −1; the video uses +3 / ≈−1.5 / ≈+1 — match the reference.)

Measured rest positions (paper corners, full res): card 1 ≈ x 171–930, y 211–502 (rot +3°, counter-clockwise);
card 2 ≈ x 231–984, y 454–795; card 3 ≈ x 191–944, y 705–922; tapes centred near the top edge of each card at
x ≈ 465–585 (tape 1 at (465, 184), tape 2 at (585, 424), tape 3 at (507, 679) top-left).

Drop-in: each card scales from 1.08 → 1.0 and falls 60 px → 0 with `ease` over 0.45 s, opacity `min(1, 2p)`, starting
52.67 / 53.87 / 55.07; tape appears 0.5 s after each start (with `slide_a` + `settle` + `tape` sounds).

Annotation (`ANNOT = (7.1, 7.6, 8.3)`): "it" on card 3 swept yellow 57.07→57.52; the ink arrow draws on 57.57→58.22
(`ease_io`), head appears at the end; "spinach omelette" on card 2 swept 58.27→58.77. In the reference (frame 1464,
t = 61.0) the arrow rises from just above the middle of "it" ("it" sits at ≈ (627, 825)), curves up-right into the clear
band between card 2's last text line ("three beaten eggs…", y ≈ 690) and card 3's top edge, runs right at y ≈ 715,
loops round outside card 2's right edge (outermost x ≈ 1065), climbs to the "A spinach omelette." line (y ≈ 578) and
comes back left, arrowhead pointing left, ending ≈ 16 px right of "omelette." (≈ (630, 578)).

ANS2: "…" at 58.87; types 59.17 → 61.09 at 24 cps; bold serif 51 px at (1140, 450), width 630 px, line height 68.85 px →
three lines "Without eggs? Try / spinach and cheese on / toast." (measured line tops 466 / 535 / 609, x = 1141).

#### 4.8.5 `ink_arrow` (*recovered, final v9 form assembled from the patches*)

```python
def bez(p0, p1, p2, p3, u):          # cubic Bézier point (ep4_video's own helper; NOT the engine's quadratic bez)
    a = 1 - u
    return (a**3 * p0[0] + 3*a*a*u * p1[0] + 3*a*u*u * p2[0] + u**3 * p3[0],
            a**3 * p0[1] + 3*a*a*u * p1[1] + 3*a*u*u * p2[1] + u**3 * p3[1])

def ink_arrow(lay, pts, prog, seed=5, width=3.6):
    """a hand-drawn ink arrow along a curve, drawn on progressively; head appears when the line arrives"""
    if prog <= 0: return
    r = np.random.default_rng(seed); n = 90
    us = np.linspace(0, 1, n)
    if len(pts) == 4: P = np.array([bez(*pts, u) for u in us])
    else:             # a smooth Catmull-Rom curve through the waypoints, resampled evenly along its length
        Q = np.array(pts, np.float64); Q = np.vstack([2 * Q[0] - Q[1], Q, 2 * Q[-1] - Q[-2]]); fine_ = []
        for i in range(1, len(Q) - 2):
            p0, p1_, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
            for u in np.linspace(0, 1, 40, endpoint=False):
                fine_.append(0.5 * (2 * p1_ + (-p0 + p2) * u + (2 * p0 - 5 * p1_ + 4 * p2 - p3) * u * u + (-p0 + 3 * p1_ - 3 * p2 + p3) * u ** 3))
        fine_.append(Q[-2]); fine_ = np.array(fine_)
        L = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(fine_, axis=0), axis=1))])
        P = np.stack([np.interp(us * L[-1], L, fine_[:, c]) for c in range(2)], 1)
        ends = P[[0, -1]].copy(); P = ndi.gaussian_filter1d(P, 3.0, axis=0, mode="nearest")    # round the corners like a hand would
        w_ = np.clip(np.minimum(np.arange(n), n - 1 - np.arange(n)) / 6, 0, 1)[:, None]
        P[:n // 2] = P[:n // 2] * w_[:n // 2] + ends[0] * (1 - w_[:n // 2]); P[n // 2:] = P[n // 2:] * w_[n // 2:] + ends[1] * (1 - w_[n // 2:])
    d = np.gradient(P, axis=0); nrm = np.stack([-d[:, 1], d[:, 0]], 1); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-6
    P = P + nrm * (ndi.gaussian_filter(r.standard_normal(n), 4) * 1.6)[:, None]       # a slightly wavering hand
    m = max(2, int(n * min(1, prog)))
    x0, y0 = P.min(0) - 40; x1, y1 = P.max(0) + 40; k = 3
    im = Image.new("RGBA", (int((x1 - x0) * k), int((y1 - y0) * k)), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    Q = [((x - x0) * k, (y - y0) * k) for x, y in P[:m]]
    for j in range(len(Q) - 1):
        wj = width * k * (0.75 + 0.35 * math.sin(j / n * math.pi))
        dr.line([Q[j], Q[j + 1]], fill=INK + (235,), width=int(wj))
        dr.ellipse([Q[j + 1][0] - wj / 2, Q[j + 1][1] - wj / 2, Q[j + 1][0] + wj / 2, Q[j + 1][1] + wj / 2], fill=INK + (235,))
    if prog >= 1:
        tip = np.array(Q[-1]); back = np.array(Q[-6]); v = (tip - back) / (np.linalg.norm(tip - back) + 1e-6)
        for ang in (0.5, -0.5):
            c_, s_ = math.cos(ang), math.sin(ang); wv = np.array([v[0] * c_ - v[1] * s_, v[0] * s_ + v[1] * c_])
            dr.line([tuple(tip), tuple(tip - wv * 17 * F * k)], fill=INK + (235,), width=int(width * k))
    lay.alpha_composite(im.resize((int(x1 - x0), int(y1 - y0)), Image.LANCZOS), (int(x0), int(y0)))
```

(The cubic `bez(p0,p1,p2,p3,u)` body is *inferred*; it is the standard cubic. `INK` is an RGB tuple.)

### 4.9 Paper-sheet transitions w4–w7 — `sheet()`

*Recovered calls*:
```python
elif in_("w4", t): img = sheet(scene_reads(local("s3", t)), scene_reply(0), frac("w4", t), "left", 12)
elif in_("w7", t): img = sheet(scene_second(0, static=True), scene_history(0), frac("w7", t), "left", 15)
```
w5 and w6 calls were not shown; *inferred*: `sheet(scene_reply(<end>), scene_forget(0), frac("w5", t), "down", 13)` and
`sheet(scene_forget(<end>), scene_second(0), frac("w6", t), "up", 14)`.

Behaviour (*measured*): a sheet boundary with a **torn paper edge** sweeps across the frame; position = `ease(p)`
(cubic ease-out — 70 % covered at p = 0.33, 43 % at p = 0.17).
- **w4 "left"** (24.10–24.70): the yellow s4 frame is revealed from the right; the torn edge (a vertical ragged line)
  moves from x = W to x = 0: `edge_x = W·(1 − ease(p))`. Both images static (the incoming yellow content is already
  in its final place — the prompt box's right end is at its final x while the edge is at x ≈ 600).
- **w5 "down"** (29.49–30.19): the **outgoing yellow sheet slides down** off the frame (its content translates down
  with it), revealing the uncle (static) underneath: yellow top edge `y = H·ease(p)`, yellow content offset `+H·ease(p)`.
  The yellow sheet casts a dark soft shadow upward onto the uncle (dark ragged fringe above its torn top edge).
- **w6 "up"** (40.90–41.50): pink revealed from the bottom; torn horizontal edge rising `y = H·(1 − ease(p))`; contents
  static. A light-grey soft shadow band (≈20–30 px) falls on the uncle just above the pink edge.
- **w7 "left"** (49.37–49.97): cream revealed from the right as w4.
- Torn edge: a ragged line (amplitude ≈ ±4–6 px, fine fibrous jaggies at ≈3–8 px wavelength plus a slow wobble),
  seeded by the last argument (12–15), with a thin brighter paper lip (a 2–4 px lighter fringe, fibres) on the incoming
  sheet's edge and a soft shadow (σ ≈ 8–12 px, α ≈ 0.25) cast by the top sheet onto the one beneath.
- Sound per wipe: a paper slide starting 0.05 s before the wipe and a "settle" thud at its end (§5.4).

### 4.10 f8 dip to night, s8 night, end fade, and the frame dispatcher

*Recovered*:
```python
    elif in_("f8", t):
        p = frac("f8", t)
        img = scene_history(0, static=True) * (1 - ease_io(p / 0.45)) if p < 0.45 else (scene_night(T["s8"][0]) * ease_io((p - 0.55) / 0.45) if p > 0.55 else np.zeros((H, W, 3), np.float32))
    else: img = scene_night(t)

def scene_night(t):
    lt = t - T["s8"][0]
    base = living_sea(NIGHT, KN, lt, night=True)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    u = ease_io(min(1, max(0, (twos(lt) - FLY_HOME[0]) / FLY_HOME[1])))
    if u > 0: fly(lay, PATH_HOME, u, 16, 300, 0, 8, t, (246, 207, 134, 150))
    im = push(comp(base, lay), lt, END - T["s8"][0], KN_win, 0.04)
    return np.asarray(im.convert("RGB"), np.float32) / 255
```

- f8: s7's final state fades to black 61.17 → 61.71 (`ease_io`), black 61.71 → 61.83, night fades up 61.83 → 62.37
  (measured mean luma 211 → 0 → 61).
- s8: night sea with clouds drifting (on the s8 clock), glints, flicker (`night=True` → +0.04 base flicker, full glow);
  the reply envelope leaves the window at 63.17 tiny (16 px) and flies toward the viewer, growing to 300 px and
  rotating 0 → +8° (PIL CCW) by 67.37 along `PATH_HOME`, leaving a gold dotted trail; whole frame pushes 4 % toward the
  window over the scene. `PATH_HOME` (*inferred* from the storyboard ×1.5): window (1501, 488) → (1230, 540) →
  (840, 660) → (510, 840) (ends lower-left of centre over the sea; measured envelope centre ≈ (527, 872) on screen at 70 s,
  with a red stamp at its top-right).
- **End fade (picture)**: *measured* — the picture fades to black from ≈70.90 to ≈71.95 (mean luma 65.8 → 0, roughly
  linear). Not in the recovered code; implement `img *= clip((END − 0.10 − t)/1.05, 0, 1)` (or ease) so it reaches
  black at ≈71.95 and matches the audio fade (§5.8).
- Dispatcher order (*inferred*, consistent with recovered branches): s1/s2 → `scene_dusk(t)`; w3 → rush/resolve;
  s3 → `scene_reads(local("s3", t))`; w4 → sheet; s4 → `scene_reply(local("s4", t))`; w5; s5 → `scene_forget(...)`;
  w6; s6 → `scene_second(...)`; w7; s7 → `scene_history(local("s7", t))`; f8; else `scene_night(t)`.
  (Note `scene_history` takes the **local** time; `scene_night` takes absolute `t`.)

---

## 5. Audio — `ep4_audio2.py`

48 kHz stereo float32 buses: `mix` (effects), `amb` (ambience, ducked separately), `music`, `VO` (mono voice).
`N = int(END * SR)` = 3,458,400 samples. All placement times are **video** time.

### 5.1 Sounds (Freesound, CC0, HQ preview mp3s)

| key | Freesound ID | title / author (credits.md) | used for |
|---|---|---|---|
| `sea` | 578524 | Calm ocean waves — SamsterBirdies | dusk and night sea beds |
| `gulls` | 537854 | Seagulls distant.wav — Ambientsoundapp | before the first word, and in gap 1 |
| `room` | 641306 | House Room Tone — aleclubin | the uncle's room, w3 end → f8 |
| `clock` | 434841 | Kitchen Wall Clock Ticking 2 — giddster | under s3 and s5 |
| `slide_a` | 464302 (cat `paper_slide`) | PaperSlide.wav — eyesonlegs | wipes w4/w6, cards, pen arrow |
| `slide_b` | 154403 (cat `paper_slide`) | paper slide.wav — semccab | wipes w5/w7, letter slide-in, highlighter swipes |
| `settle` | 406586 (cat `paper_settle`) | Picture Drop_Heavy Paper_Near_Mono — _stubb | end of wipes, envelope lands, cards land |
| `flutter` | 468113 | Flutter.wav — Aquafeniz | envelope launch / arrival |
| `whoosh` | 701104 | Whoosh stereo light (transition) — xkeril | w3 rush, envelope flights |
| `tape` | 467721 | Free Tape Ripping Sound — MilkyGacha | cards taped down |
| `air` | 182868 | Sandy Breeze (foley) — FableVision_Studios | words leave his head |
| `typewriter` | 406241 | (not in the attached credits.md; look up on the page) | per-character keystrokes |
| (`shaker` 375639, `kalimba` 331047, `bass` 383711, `kick` 371192, `snap` 332604 as `snap2_332604`, `rim` 82280) | | | **not used** in the track version (they belonged to the piano/kalimba "bed" modes) |

Fetching (*recovered approach*, `sfx_fetch.py`): only `freesound.org` and `cdn.freesound.org` were reachable. Search /
sound pages are HTML; each player is an element with `class="bw-player"` carrying `data-sound-id`, `data-username`,
`data-mp3`, `data-title`, `data-duration`, `data-num-downloads`; the `data-mp3` URL ends `-lq.mp3`; replace with
`-hq.mp3` and download (`curl -s -m 60`). Files were stored as `sfx/raw/<cat>_<id>.mp3` and decoded with
`ffmpeg -v error -i FILE -f f32le -ac 2 -ar 48000 -`. The rebuild kit stores them as `assets/sfx/raw/<id>.mp3` with
`assets/sfx/manifest.json` (map the keys above to ids). `credits.md` is regenerated from the manifest for the ids in
`USE` (header "All from Freesound under CC0 (public domain). Voice: ElevenLabs (Sekou)." — the attached old copy
still says MiniMax and lacks the typewriter line; music: add a line for the reference track, licence unknown).

### 5.2 Core helpers (*recovered*, with the v9 `place()` fix)

```python
SR = 48000; N = int(END * SR)
mix = np.zeros((N, 2), np.float32); amb = np.zeros((N, 2), np.float32)    # ambience is kept apart so it can duck under the voice
def db(x): return 10 ** (x / 20)

USE = {"sea": "578524", "gulls": "537854", "room": "641306", "clock": "434841", "slide_a": ("paper_slide", "464302"),
       "slide_b": ("paper_slide", "154403"), "settle": ("paper_settle", "406586"), "flutter": "468113", "whoosh": "701104",
       "tape": "467721", "air": "182868", "typewriter": "406241"}
CACHE = {}
def load(key):
    cat, sid = USE[key] if isinstance(USE[key], tuple) else (key, USE[key])
    if key not in CACHE:
        fn = os.path.join(S, "sfx", "raw", f"{cat}_{sid}.mp3")          # rebuild: assets/sfx/raw/<sid>.mp3
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", fn, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
        CACHE[key] = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    return CACHE[key]

def seg(x, t0, dur, fi=0.02, fo=0.08):
    y = x[int(t0 * SR): int((t0 + dur) * SR)].copy(); n = len(y); t = np.arange(n) / SR
    y *= (np.clip(t / max(fi, 1e-3), 0, 1) * np.clip((n / SR - t) / max(fo, 1e-3), 0, 1))[:, None]
    return y
def rms_to(x, d): return x * db(d) / (np.sqrt((x ** 2).mean()) + 1e-9)
def peak_to(x, d): return x * db(d) / (np.abs(x).max() + 1e-9)

def place(x, t0, pan=None, bus=None):
    """add a stereo clip at t0; with pan (-1..1, scalar or per-sample) it is folded to mono and panned"""
    bus = mix if bus is None else bus
    i0 = int(t0 * SR)
    if i0 >= N: return
    if i0 < 0: x = x[-i0:]; i0 = 0
    x = x[: N - i0]
    if pan is not None:
        m = x.mean(1); pan = np.asarray(pan, np.float32); pan = pan[-len(m):] if pan.ndim else pan
        p = np.broadcast_to(pan, m.shape)
        x = np.stack([m * np.cos((p + 1) * np.pi / 4), m * np.sin((p + 1) * np.pi / 4)], 1) * 1.414
    bus[i0:i0 + len(x)] += x
```

(A per-sample `pan` array longer than the clip after truncation would mis-broadcast; slice it to the clip length.)
If a source recording is shorter than `t0 + dur` for `seg`, loop it with a short crossfade rather than returning a
short clip (the sea bed uses offsets 20 s and 110 s).

### 5.3 The voice — NEW clean chain (owner change 3)

Old chain (*recovered*, for reference only — do not reuse):
```python
vo = signal.sosfilt(signal.butter(2, 80, "highpass", fs=SR, output="sos"), vo)
vo = vo / (np.abs(vo).max() + 1e-9) * db(-3)
vo = peaking(compress(vo, thr_db=-20.0, ratio=2.0), 3200, 2.5, 0.9)
_e = np.sqrt(signal.sosfilt(signal.butter(1, 6.0, "lowpass", fs=SR, output="sos"), vo ** 2).clip(0))
_voiced = _e > _e.max() * 0.15
vo = vo * db(-16.5) / (np.sqrt((vo[_voiced] ** 2).mean()) + 1e-9)
vo = (np.tanh(vo / db(-1.5)) * db(-1.5)).astype(np.float32)                  # ← the crunch: peaks ≈ +4.3 dBFS go in here
```
Measured on the source: peak −1.0 dBFS, voiced RMS −18.1 dBFS, crest 17.2 dB, no clipped samples — the file is clean;
the old chain alone caused the grit (tanh error ≈ −41 dB RMS, ≈25 dB under the voice).

New chain (spec; the code is new, not recovered):

1. Decode `assets/audio/vo2.wav` (48 kHz mono; if decoding the mp3, `ffmpeg -ac 1 -ar 48000`); float64 for processing.
2. High-pass: 2nd-order Butterworth at **80 Hz** (`sosfilt`) — keep.
3. Peak-normalise to −3 dBFS (as before), then **gentle compression**: the recovered `compress()` (feed-forward, 40 Hz
   RMS detector on a 1 kHz control signal) with `thr_db = −26, ratio = 1.5, att = 0.010, rel = 0.150`, plus a 6 dB soft
   knee if implemented. Target ≤ 3 dB of gain reduction on the loudest syllables.
4. Presence EQ: **none** by default (`PRESENCE_DB = 0.0`); allow at most +1.0 dB peaking at 3.2 kHz, Q 0.9, if the voice
   sinks under the sea in the opening.
5. Level: scale so the RMS over voiced samples (`_e` > 0.15·max with the 6 Hz envelope, as before) is **−18.0 dBFS**.
6. **Look-ahead true-peak limiter**, ceiling **−1.0 dBTP**, 5 ms look-ahead, 80 ms release, 4× oversampled peak
   detection (`tp_limit` below). With the numbers above it should touch only a handful of peaks (report the count and
   max gain reduction; > 2 dB means the level/compression is wrong).
7. Place at `A_OFF`: `VO = np.zeros(N); VO[i0:i0+len(vo)] = vo[:N-i0]` with `i0 = int(1.5*SR)`; added to both channels
   (centre).

Recovered `compress` (reuse with the new settings) and `peaking`:

```python
def peaking(x, f0, gain_db, q):
    A = 10 ** (gain_db / 40); w0 = 2 * np.pi * f0 / SR; al = np.sin(w0) / (2 * q); c = np.cos(w0)
    b = np.array([1 + al * A, -2 * c, 1 - al * A]); a = np.array([1 + al / A, -2 * c, 1 - al / A])
    return signal.lfilter(b / a[0], a / a[0], x)
def compress(x, thr_db=-24.0, ratio=2.5, att=0.005, rel=0.12):
    """feed-forward compressor on a 1 kHz control signal"""
    dec = SR // 1000
    lev = np.sqrt(np.maximum(signal.sosfilt(signal.butter(1, 40, "lowpass", fs=SR, output="sos"), x ** 2), 1e-12))[::dec]
    over = np.maximum(0, 20 * np.log10(lev) - thr_db) * (1 - 1 / ratio)
    g = np.zeros_like(over); ka, kr = np.exp(-1 / (att * 1000)), np.exp(-1 / (rel * 1000)); cur = 0.0
    for i, o in enumerate(over):
        k = ka if o > cur else kr; cur = k * cur + (1 - k) * o; g[i] = cur
    return x * db(-np.interp(np.arange(len(x)) / dec, np.arange(len(g)), g))
```

Reference limiter (new; offline, so the look-ahead needs no output delay):

```python
from scipy import ndimage as ndi
def tp_limit(x, ceiling_db=-1.0, look_ms=5.0, rel_ms=80.0, os_=4, block=48):
    """look-ahead true-peak limiter for mono (N,) or linked multichannel (N, C) float arrays"""
    x2 = x[:, None] if x.ndim == 1 else x
    n = len(x2); c = db(ceiling_db)
    up = signal.resample_poly(x2, os_, 1, axis=0)                           # 4x oversampled for inter-sample peaks
    pk = np.abs(up).max(1)[: n * os_].reshape(n, os_).max(1)                 # per-sample true-peak estimate
    g_req = np.minimum(1.0, c / np.maximum(pk, 1e-12))                       # gain each sample needs
    L = max(1, int(look_ms * SR / 1000))
    g_hold = ndi.minimum_filter1d(g_req, size=L + 1, origin=-(L // 2))      # min over [n, n+L]: reduce before the peak
    g_att = np.convolve(g_hold, np.hanning(L + 2)[1:-1] / np.hanning(L + 2)[1:-1].sum(), mode="full")[:n]   # smooth ramp over [n-L, n]
    g_att = np.minimum(g_att, g_hold)                                        # never above the held requirement
    # release at block rate (1 ms), then back to samples; take the min with the attack curve so peaks stay covered
    nb = (n + block - 1) // block
    gb = np.pad(g_att, (0, nb * block - n), constant_values=1.0).reshape(nb, block).min(1)
    kr = np.exp(-block / (rel_ms * SR / 1000)); out = np.empty(nb); cur = 1.0
    for i, v in enumerate(gb):
        cur = v if v < cur else cur * kr + v * (1 - kr); out[i] = cur
    g = np.minimum(np.interp(np.arange(n), np.arange(nb) * block + block / 2, out), g_att)
    y = x2 * g[:, None]
    y = np.clip(y, -c, c)                                                    # safety; should be a no-op
    return (y[:, 0] if x.ndim == 1 else y).astype(np.float32), g
```

Verification to print: voiced RMS of the processed voice; number of samples with gain < 0.999 and the minimum gain
(dB); true peak of the result (4× oversampled) ≤ −1.0 dBTP.

### 5.4 Speech envelope, ducking, ambience and effects (*recovered*, unchanged)

```python
venv = np.sqrt(signal.sosfilt(signal.butter(1, 6.0, "lowpass", fs=SR, output="sos"), VO ** 2).clip(0))
speech = np.clip(venv / (venv.max() * 0.35 + 1e-9), 0, 1)
duck = 1 - 0.62 * speech                                         # about -8 dB under the voice

# ------------------------------------------------------------ ambience
sea = load("sea")
place(rms_to(seg(sea, 20.0, T["w3"][1] + 0.3, 1.5, 1.0), -37), 0.0, bus=amb)                      # dusk, until the first paper wipe
t_n = T["f8"][0] + 0.5
place(rms_to(seg(sea, 110.0, END - t_n, 1.6, 1.4), -38), t_n, bus=amb)                             # night
GAPS = [(v(a), v(b)) for a, b in VO_GAPS]                                                         # the pauses between paragraphs, in video time
place(rms_to(seg(load("gulls"), 2.0, A_OFF + 0.6, 0.4, 0.5), -37), 0.0, bus=amb)                     # distant gulls before his first word
place(rms_to(seg(load("gulls"), 9.0, GAPS[0][1] - GAPS[0][0] + 0.8, 0.3, 0.6), -38), GAPS[0][0] - 0.1, bus=amb)   # and in the first pause
place(rms_to(seg(load("room"), 10.0, T["f8"][0] + 0.4 - T["w3"][1], 0.6, 0.8), -52), T["w3"][1], bus=amb)
for k in ("s3", "s5"):
    a, b = T[k]; place(rms_to(seg(load("clock"), 5.0 + a % 20, b - a, 0.5, 0.6), -47), a, pan=0.35, bus=amb)

# ------------------------------------------------------------ effects
wh = load("whoosh")
place(peak_to(seg(wh, 0.0, min(1.4, len(wh) / SR), 0.15, 0.5), -25), T["w3"][0] - 0.35, pan=np.linspace(0.45, -0.1, int(min(1.4, len(wh) / SR) * SR)))
for i, k in enumerate(("w4", "w5", "w6", "w7")):
    a, b = T[k]
    sl = load("slide_a" if i % 2 == 0 else "slide_b")
    place(peak_to(seg(sl, 0.0, min(len(sl) / SR, b - a + 0.5), 0.01, 0.2), -21), a - 0.05, pan=0.3 if k in ("w4", "w7") else 0.0)
    place(peak_to(seg(load("settle"), 0.0, 0.55), -25), b - 0.03)

place(peak_to(seg(load("slide_b"), 0.0, 1.0, 0.01, 0.25), -27), T["s3"][0] + 1.2, pan=0.55)        # the letter slides in from the right
place(peak_to(seg(load("settle"), 0.0, 0.4), -33), T["s3"][0] + 0.75, pan=-0.35)                    # the envelope lands in his head

def flight(t0, dur, pan0, pan1, launch_gain, whoosh_gain):
    fl = load("flutter"); wh = load("whoosh")
    place(peak_to(seg(fl, 0.0, min(1.2, len(fl) / SR), 0.01, 0.4), launch_gain), t0, pan=pan0)
    w = seg(wh, 0.0, len(wh) / SR, 0.05, 0.4); n = len(w)
    place(peak_to(w, whoosh_gain), t0 + max(0.0, (dur - n / SR) / 2), pan=np.linspace(pan0, pan1, n))
flight(T["s2"][0] + FLY_OUT[0], FLY_OUT[1], -0.7, 0.55, -24, -25)
flight(T["s8"][0] + FLY_HOME[0], FLY_HOME[1], 0.5, -0.5, -30, -23)
place(peak_to(seg(load("flutter"), 0.2, 0.9, 0.02, 0.4), -24), T["s8"][0] + FLY_HOME[0] + FLY_HOME[1] - 0.3, pan=-0.5)   # it arrives, close

place(peak_to(seg(load("slide_b"), 0.0, 0.45, 0.01, 0.15), -30), T["s6"][0] + IT_SWEEP, pan=-0.15)  # highlighter swipe on "it"
place(peak_to(seg(load("slide_b"), 0.0, 0.45, 0.01, 0.15), -31), T["s7"][0] + ANNOT[0], pan=-0.3)   # scene 7: the swipe on "it",
place(peak_to(seg(load("slide_a"), 0.1, 0.7, 0.05, 0.2), -35), T["s7"][0] + ANNOT[1], pan=np.linspace(-0.2, 0.2, int(0.7 * SR)))   # the pen arrow,
place(peak_to(seg(load("slide_b"), 0.0, 0.5, 0.01, 0.15), -31), T["s7"][0] + ANNOT[2], pan=-0.35)   # and the swipe on "spinach omelette"

for i in range(3):                                                                                  # letters land and are taped down
    t0 = T["s7"][0] + CARD0 + CARD_GAP * i
    place(peak_to(seg(load("slide_a"), 0.0, 0.5, 0.01, 0.15), -27), t0, pan=-0.4)
    place(peak_to(seg(load("settle"), 0.0, 0.45), -25), t0 + 0.42, pan=-0.4)
    place(peak_to(seg(load("tape"), 0.0, 0.7, 0.01, 0.2), -25), t0 + 0.48, pan=-0.3)

place(rms_to(seg(load("air"), 0.0, 6.0, 1.0, 2.2), -40), T["s5"][0] + FORGET, pan=0.35)            # the words leave his head
```

Event table in absolute time (from the code above):

| t (s) | sound | gain | pan |
|---|---|---|---|
| 0.00–18.50 | sea bed (src 20 s→), fade in 1.5 / out 1.0 | RMS −37 | — |
| 0.00–2.10 | gulls (src 2 s), fades 0.4/0.5 | RMS −37 | — |
| 9.84–11.96 | gulls (src 9 s), fades 0.3/0.6 | RMS −38 | — |
| 14.46 | flutter launch (≤1.2 s) | peak −24 | −0.7 |
| 14.46 + (2.4 − len)/2 | whoosh, panned −0.7 → +0.55 | peak −25 | sweep |
| 17.15 | w3 whoosh (≤1.4 s), fades 0.15/0.5 | peak −25 | +0.45 → −0.1 |
| 18.20–61.57 | room tone (src 10 s), fades 0.6/0.8 | RMS −52 | — |
| 18.20–24.10 | clock (src 5 + 18.2 % 20 = 23.2 s), fades 0.5/0.6 | RMS −47 | +0.35 |
| 18.95 | settle (0.4 s) — envelope lands in his head | peak −33 | −0.35 |
| 19.40 | slide_b (1.0 s) — letter slides in | peak −27 | +0.55 |
| 24.05 | slide_a (w4) | peak −21 | +0.3 |
| 24.67 | settle (0.55 s) | peak −25 | — |
| 25.30→29.38 | typewriter, reply, 24 cps | −26 ±1.5 (spaces −5) | +0.05 ± 0.08 |
| 29.44 | slide_b (w5) | peak −21 | 0 |
| 30.16 | settle | peak −25 | — |
| 30.19–40.90 | clock (src 5 + 30.19 % 20 = 15.19 s) | RMS −47 | +0.35 |
| 32.79–38.79 | air (6 s), fades 1.0/2.2 | RMS −40 | +0.35 |
| 40.85 | slide_a (w6) | peak −21 | 0 |
| 41.47 | settle | peak −25 | — |
| 43.00→45.31 | typewriter, Q2, 16 cps | −27 | −0.05 |
| 45.80→46.94 | typewriter, "Make what, dear?", 14 cps | −26 | +0.05 |
| 47.50 | slide_b swipe on "it" (0.45 s) | peak −30 | −0.15 |
| 49.32 | slide_b (w7) | peak −21 | +0.3 |
| 49.94 | settle | peak −25 | — |
| 52.67 / 53.87 / 55.07 | slide_a (0.5 s) | peak −27 | −0.4 |
| +0.42 | settle (0.45 s) | peak −25 | −0.4 |
| +0.48 | tape (0.7 s) | peak −25 | −0.3 |
| 57.07 | slide_b swipe on "it" | peak −31 | −0.3 |
| 57.57 | slide_a from 0.1 s, 0.7 s, pen arrow | peak −35 | −0.2 → +0.2 |
| 58.27 | slide_b swipe on "spinach omelette" (0.5 s) | peak −31 | −0.35 |
| 59.17→61.09 | typewriter, ANS2, 24 cps | −26 | +0.3 |
| 61.67–72.05 | night sea (src 110 s), fades 1.6/1.4 | RMS −38 | — |
| 63.17 | flutter launch | peak −30 | +0.5 |
| centred in 63.17–67.37 | whoosh +0.5 → −0.5 | peak −23 | sweep |
| 67.07 | flutter (src 0.2 s, 0.9 s) — arrives close | peak −24 | −0.5 |

### 5.5 Typewriter (*recovered*)

```python
tw = load("typewriter"); twm = tw.mean(1)
env = np.convolve(np.abs(twm), np.ones(96) / 96, "same"); de = np.diff(env, prepend=0); thr = env.max() * 0.25
onsets, last = [], -SR
for i in np.where((env > thr) & (de > 0))[0]:
    if i - last > int(0.12 * SR): onsets.append(i)
    last = i
KEYS = []
for o in onsets:
    k = tw[max(0, o - int(0.004 * SR)): o + int(0.11 * SR)].copy(); n = len(k)
    k *= np.clip(np.arange(n) / (0.002 * SR), 0, 1)[:, None] * np.clip((n - np.arange(n)) / (0.03 * SR), 0, 1)[:, None]
    KEYS.append(peak_to(k, 0))
rk = np.random.default_rng(31)
def typing(text, t0, cps, gain=-26, pan=0.0):
    prev = -1
    for i, ch in enumerate(text):
        j = int(rk.integers(len(KEYS)))
        if j == prev: j = (j + 1) % len(KEYS)
        prev = j
        g = gain - (5 if ch == " " else 0) + rk.uniform(-1.5, 1.5)
        place(KEYS[j] * db(g), t0 + i / cps + rk.uniform(-0.008, 0.008), pan=pan + rk.uniform(-0.08, 0.08))
REPLY = "A spinach omelette. Wilt the spinach in butter, pour in three beaten eggs, fold it over and serve."
typing(REPLY, T["s4"][0] + REPLY_TYPE[0], REPLY_TYPE[1], pan=0.05)
typing("Thanks! Can you make it without eggs?", T["s6"][0] + Q2_TYPE[0], Q2_TYPE[1], gain=-27, pan=-0.05)
typing("Make what, dear?", T["s6"][0] + ANS_TYPE[0], ANS_TYPE[1], pan=0.05)
typing("Without eggs? Try spinach and cheese on toast.", T["s7"][0] + ANS2_TYPE[0], ANS2_TYPE[1], pan=0.3)
```

(About 18 distinct keystrokes were found in recording 406241. The picture's character counts use `twos()`, so sound
leads picture by ≤ 1/12 s — accepted.)

### 5.6 Music — track mode, **without the "Gone" gate** (owner change 1)

v9 track-mode code (*recovered*), shown with the gate that must go:

```python
music = np.zeros((N, 2), np.float32)
tt_ = np.arange(N) / SR
# Josh's reference track as the bed. Its sparse opening sits under the sky; its groove arrives around the uncle.
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(S, "sfx", "ref_jamal.mp3"), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"], capture_output=True).stdout
trk = np.frombuffer(raw, np.float32).reshape(-1, 2).copy()[:N]
music[: len(trk)] = trk
music *= (db(-16.5) * (1 + (db(6.0) - 1) * np.clip((18.0 - tt_) / 3.0, 0, 1)))[:, None]   # its quiet intro lifted a little
back = T["s6"][0]
music *= (1 - 0.55 * speech)[:, None]
lift = np.clip((tt_ - (v(VO_END) - 0.3)) / 0.8, 0, 1)                         # up a little for the ending
music *= (1 + 0.6 * lift)[:, None]
# under the voice, keep the band the words live in a little clearer
_bs = np.stack([signal.sosfilt(signal.butter(2, [700, 4000], "bandstop", fs=SR, output="sos"), music[:, c]) for c in range(2)], 1)
music = (music * (1 - 0.5 * speech)[:, None] + _bs * (0.5 * speech)[:, None]).astype(np.float32)
# "Gone": the music stops with the room, and comes back with the fix          <-- DELETE these two lines in the rebuild
mq = 1 - np.clip((tt_ - (GONE - 0.12)) / 0.12, 0, 1) * np.clip((back + 0.02 - tt_) / 0.9, 0, 1)
music *= mq[:, None]
# (track mode had no reverb: the fftconvolve reverb was multiplied by 0.0)
```

Rebuild settings, explicitly:
- Track from its own t = 0, aligned to video t = 0, stereo, 48 kHz; truncated at `END` (the track is 172.46 s).
- Gain: −16.5 dB, plus a lift of +6 dB (×1.995) for t < 15 s that ramps linearly to 0 dB between 15 and 18 s
  (the track's first ≈16 s are nearly silent: its RMS is −27/−28 dB for 0–16 s, then ≈ −15 dB).
- Duck: `× (1 − 0.55·speech)` (≈ −7 dB at full speech).
- Speech-band clearing: blend in a 2nd-order Butterworth 700–4000 Hz band-stopped copy by `0.5·speech`.
- End lift: `× (1 + 0.6·lift)` with `lift` ramping 0 → 1 over 68.75 → 69.55 s (+4.1 dB at the end).
- **No `mq` gate** — the music is continuous through "Gone" (39.61) and s6.
- No reverb.
- Old v9 music-stem levels for orientation (RMS dBFS): pre-roll 0–1.5 s −31.1; gaps −36.5, −32.2, −32.0, −29.0,
  [gap 5 was −39.7 because of the gate; expect ≈ −30 now], −28.3, −33.7; under the voice v(2)–v(8) −36.5, v(30)–v(37) −31.3;
  tail −29.4.
- Track facts (analysed in October): ≈ 89 BPM, warm deep bass, rolled-off top, minor colour (chroma D, A strongest),
  ≈ 3.4 onsets/s. Licence unknown — keep `ref_jamal.mp3` out of git; warn before public posting.

### 5.7 Ambience around "Gone"

v9 also dropped the room and clock out around "Gone" (*recovered*):

```python
GONE = v(38.11)
quiet = 1 - np.clip((np.arange(N) / SR - (GONE - 0.15)) / 0.15, 0, 1) * np.clip((T["s6"][0] + 0.6 - np.arange(N) / SR) / 0.6, 0, 1)
amb *= quiet[:, None]
```

The owner asked for no pause at "Gone". With the music now continuous this ambience dip is barely audible, but to honour
the request **default it off** (`AMB_GONE_DIP = False`); keep the code behind the flag. (Judgement call — see §6.)

### 5.8 Mix and master — NEW limiter (owner change 3)

Recovered v9 mix, then the change:

```python
amb_bs = np.stack([signal.sosfilt(signal.butter(2, [900, 4500], "bandstop", fs=SR, output="sos"), amb[:, c]) for c in range(2)], 1)
amb = amb * (1 - speech)[:, None] + amb_bs * speech[:, None]                  # the sea loses its hiss under the voice
out = mix + music + amb * duck[:, None] + VO[:, None]
if os.environ.get("STEMS"):
    for nm, x in (("fx", mix), ("music", music), ("amb", amb * duck[:, None])):
        wavfile.write(sys.argv[1].replace(".wav", f"_{nm}.wav"), SR, (np.clip(x, -1, 1) * 32767).astype(np.int16))
t = np.arange(N) / SR
out *= np.clip((END - t) / 1.2, 0, 1)[:, None]                                 # master fade over the last 1.2 s (70.85 → 72.05)
peak = np.abs(out).max()
out = np.tanh(out / db(-1.0)) * db(-1.0)                                       # <-- REPLACE
wavfile.write(sys.argv[1], SR, (np.clip(out, -1, 1) * 32767).astype(np.int16))
print(f"saved {sys.argv[1]}: {N / SR:.2f}s, pre-limiter peak {20 * np.log10(peak):.1f} dBFS")
```

Rebuild master:
- Replace the tanh with `out, g = tp_limit(out, ceiling_db=-1.0, look_ms=5.0, rel_ms=80.0)` (stereo-linked gain).
  v9's pre-limiter mix peak was ≈ −1.8 to −2.1 dBFS **with** the hot voice; with the −18 dB voice the limiter should
  rarely engage.
- Write 24-bit PCM (or 32-bit float) WAV; if 16-bit is required, add TPDF dither (±1 LSB).
- Add a `VO_STEM` export (the processed voice alone) to the `STEMS=1` outputs so the voice can be checked in isolation.
- Print: voice RMS in the window v(2)–v(2.8) (old v9: −20.4 dB before the +1.5 dB nudge; target ≈ −18 ± 0.5 in the voice
  stem), mix true peak (≤ −1.0 dBTP), limiter gain-reduction stats, music and ambience levels per gap, and an approximate
  integrated loudness (BS.1770 K-weighting; expected ≈ −18 to −16 LUFS — report, do not normalise to it).
- The mux re-encodes to AAC 192 k; −1.0 dBTP leaves headroom for codec overshoot.

---

## 6. Known differences and uncertainties (use judgement here)

Lost outright (rebuild from description + reference frames):
1. **Uncle scene code**: full head/body polygons (only the tail of the head list, the start of the body list and the
   collar survive), unit→pixel mapping, brushwork/speckle parameters, the exact `pivot`/`split`/`lens` values, the
   background lamp glow, and the breathing loop formula. Match the measured silhouette (§3.3) and
   `docs/ref/canvas_v6/uncle.jpg`.
2. **Paper plates' recipe** (use the canvas plates, believed final).
3. **`ep4_scenes.py` header** (lines 1–35): seeds, `PAPER_RGB`, `EDGE_TOOTH` default, `TEX` override (if any), `save()` quality.
4. **`fly()`** body, **`PATH_OUT` / `PATH_HOME`** control points (canvas storyboard curves used here), dot size/spacing.
5. **`envelope()`**, **`tape()`**, the full **`card()`** layout (padding, paragraph gap, label size, shadow) and
   `C2_ARGS`/`C3_ARGS` widths and rotations.
6. **`prompt_box()`** after the height computation (outline radius/stroke, highlight padding).
7. **`sheet()`** (torn edge generator, lip, shadow), and the w5/w6 call arguments. Note the measured asymmetry: w5 moves
   the outgoing sheet; w4/w6/w7 reveal the incoming sheet with static content.
8. **`light_rush()` / `resolve()` / `zoom_at()`** bodies and `_RD` (≈0.715 s inferred), the glow colour/radius curve.
9. **Bird sprite** drawing and the exact glide modulation.
10. **The drifting-words motion** (emergence, per-word drift speeds); only the word list and final layout offsets are exact.
11. **Head tilt amplitude / timing** (≈1.5–2°, measured indirectly), the dry glint timing.
12. **Picture end fade** — measured (≈70.90 → 71.95), not recovered.
13. **Main render loop / ffmpeg pipe**, `frame()` order beyond the recovered branches.
14. **Exact final VO script** — the canvas storyboard text is a draft; the voice file is the authority (timings in §2.3).

Recovered but with caveats:
- `bez(p0,p1,p2,p3,u)` in the video module is a cubic with a parameter (different from the engine's quadratic list
  version); its body is the standard formula (not seen).
- The engine has changed since October (RULES-56 `ref_canvas` etc.). The dusk/night recipe only uses functions whose
  signatures are unchanged; results will not be pixel-identical to v9 plates (texture offsets / rng draws may differ).
  That is acceptable — compare by eye against §8.
- Fonts: families/weights are certain (canvas `<link>`), the exact conversion route is not.
- Grain plates: present in code, probably not applied (owner declined the "grain standard"). Leave off.
- Ambience dip at "Gone": spec defaults it **off** (owner disliked the pause); if the owner meant music only, set
  `AMB_GONE_DIP = True` (restores v9's room/clock drop-out).
- The reference video still shows the "EPISODE 4" tag, the music gate and the old voice chain — do **not** match
  those three.
- The old summary said the voice sat at "−18 dB RMS" then "−16.5" (the +1.5 dB nudge was in v7+). The rebuild target is
  −18 dBFS voiced RMS on the voice stem.

---

## 7. Suggested module split for the rebuild

```
painterly-explainers/
  engine/                  vendored painterly engine (+ tex/ via fetch_textures.sh)
  assets/fonts/            mono.ttf mono5.ttf sans.ttf serif.ttf serif_i.ttf serif_b.ttf
  assets/sfx/raw/<id>.mp3  + manifest.json, credits.md
  assets/audio/            vo2.wav (48 k mono), vo_sekou.mp3, ref_jamal.mp3 (git-ignored)
  ep4/
    timeline.py            = §2.1 verbatim (+ in_, frac, local helpers)
    backdrops.py           = ep4_scenes.py: SCENE dusk/night/uncle/paper_*; NOCLOUDS, WINDOW_OFF; writes out/ep4/*.jpg|png|npz
    common.py              W,H,F, ease/ease_io/twos, load(), font(), comp(), INK, HL, rough(), tracked(), cubic bez()
    seasky.py              prep_masks, shift_rows*, cloud_layer, glints, living_sea, push/cam_box/push_box/apply_box,
                           SKYFILL + parallax, birds, fly()/PATH_OUT/PATH_HOME/envelope trail
    uncle.py               uncle layers (bg/body/head/collar), breathing, tilt, window()/hole + icon, glint,
                           drifting words, scene_reads(lt), scene_forget(lt)
    cards.py               tag/title_reveal, wrap/text_block/prompt_box, card()/anchors/card_marked, tape(), envelope(),
                           ink_arrow, scene_reply(lt), scene_second(lt, static), scene_history(t, static)
    transitions.py         light_rush/resolve (w3), sheet() (w4–w7), f8 dip, end fade
    video.py               scene_dusk, scene_night, frame(t) dispatcher, render loop (ffmpeg pipe), CLI OUT [t0 t1]
    audio.py               = ep4_audio2.py track mode: voice chain + tp_limit, ambience, sfx, typewriter, music, master, stems, credits
```

Interfaces:
- **backdrops → everything**: files in `out/ep4/` (names in §3.1). `*_masks.npz` keys `land`, `land_shape`, `hz`, `win`.
  `uncle_geo.npz` keys `pivot` (x,y px), `split` (y px), `lens` (x,y px).
- **common**: `ease(p)`, `ease_io(p)`, `twos(t)`; `load(name) -> float32 HxWx3`; `font(key, px) -> FreeTypeFont`;
  `comp(base_f32, lay_rgba) -> PIL RGBA`; `rough(im_rgba, amp, size, seed, fine) -> PIL RGBA`; constants `W=1920, H=1080, F=1.5,
  INK=(46,44,45), HL=(245,212,74)`.
- **seasky**: `living_sea(img, K, t, night=False, on=1.0) -> f32`; `parallax(base, dy) -> f32`;
  `cam_box(s, cx, cy) -> (x0, y0, s)`, `push_box(t, dur, focus, amount) -> (x0, y0, s)`, `apply_box(pil, box) -> pil`,
  `push(pil, t, dur, focus, amount) -> pil`; `birds(pil, t, to_screen, scale)` (in place);
  `fly(lay, path, u, size0, size1, rot0, rot1, t, dot_rgba)` (in place); `KD, KN, KD_win, KN_win, LIGHT_D, DUSK, NIGHT`.
- **uncle**: `scene_reads(lt) -> f32`, `scene_forget(lt) -> f32`; also `uncle_frame(lt, tilt, open_frac, icon, extra_lay=None) -> f32`
  for the transitions; constants `WIN_C=(537.1, 315.8)`, `WIN_R=93`.
- **cards**: `title_reveal(lt, dur) -> RGBA layer`; `scene_reply(lt)`, `scene_second(lt, static=False)`,
  `scene_history(t_local, static=False) -> f32`.
- **transitions**: `rush_resolve(t) -> f32` (covers 17.50–18.60, calls `scene_dusk` and `scene_reads`);
  `sheet(a_f32, b_f32, p, direction, seed) -> f32`; `dip(t) -> f32` for f8; `end_fade(img, t)`.
- **video**: `frame(t) -> f32`; CLI `python3 -m ep4.video OUT.mp4 [t0 t1]` / `OUT.png t`.
- **audio**: CLI `python3 -m ep4.audio OUT.wav` (env `STEMS=1`, `AMB_GONE_DIP=0|1`, `PRESENCE_DB`); reads only
  `timeline.py` and assets; writes the WAV, stems (`_fx`, `_music`, `_amb`, `_vo`) and `credits.md`.
- **mux**: `ffmpeg -i video.mp4 -i mix.wav -map 0:v -map 1:a -c:v libx264 -crf 21 -preset slow -pix_fmt yuv420p -c:a aac -b:a 192k -shortest ep4_v10.mp4`
  (or `-c:v copy` if the video is already final-encoded).

Build order suggestion: timeline+common → backdrops (dusk/night first; check masks) → seasky (s1/s2/s8 stills at
3.0, 6.5, 12.0, 16.5, 66.0) → uncle → cards → transitions → audio (independent; can run in parallel from the start).

---

## 8. Reference timestamps per scene (compare against `/home/claude/ref/ep4_v9_track.mp4`)

Extract with `ffmpeg -i ep4_v9_track.mp4 -vf "select=eq(n\,FRAME)" -frames:v 1 ref.png` (frame = round(t·24)). Do not
use `ref/frames/f_*.jpg` for timing (offset up to +0.2 s). Remember: the reference has the EPISODE 4 tag (5.6–10.6 s).

| scene | frame (t) | what to compare |
|---|---|---|
| s1 | 0 (0.000) | zoom-2 view of the dusk sky only; three gulls at ≈ (488,361), (669,287), (850,464); pink-left / lilac-right gradient, faint cloud wisps |
| s1 | 72 (3.000) | mid-tilt: horizon at y ≈ 850 of the frame, hill entering bottom-right, house at the right edge; parallax visible (hill/sea offset vs sky) |
| s1 | 120 (5.000) | tilt complete, full frame: horizon y 626, hill top + cottage at ≈ (1500, 480), window lit, glints under it |
| s1 | 156 (6.500) | title tag fully in (rebuild: only the light tag "THE UNCLE WHO ONLY READS LETTERS", bottom-left at (96, 916–984)) |
| s2 | 288 (12.000) | push-in ≈3 % toward the window; gulls top centre; cloud drift vs 5.0 s |
| s2 | 360 (15.000) | envelope entering large at the bottom-left corner, −14° |
| s2 | 396 (16.500) | envelope small near the house, dotted trail arcing from bottom-left |
| w3 | 425 (17.708), 428 (17.833) | rush: zoom into the window, blur, warm wash |
| w3 | 432 (18.000), 436 (18.167) | resolve: uncle enlarged about the hole (≈1.67×, ≈1.37×), blurred, warm wash |
| s3 | 446 (18.583) | settled uncle, empty hole at (537,316) r 93 |
| s3 | 461 (19.208) | envelope icon full in the hole (≈100 px) |
| s3 | 470 (19.583) | letter card sliding in from the right |
| s3 | 552 (23.000) | head nodded; letter card at rest x 1134–1775, y 271–806 |
| w4 | 583 (24.292) | yellow torn edge at x ≈ 600 moving left; prompt box text behind it at its final place |
| s4 | 600 (25.000) | prompt box + "…" |
| s4 | 696 (29.000) | reply typed to "fold it over" + cursor |
| w5 | 710 (29.583) | yellow sheet slid down to y ≈ 372 with its content; uncle (with icon) static above |
| s5 | 790 (32.917) | icon shrinking, "spinach" emerging at the face |
| s5 | 864 (36.000) | full word cloud (spinach, eggs, tonight, Dear Uncle, Sam, omelette, butter, fold, cook) |
| s5 | 950 (39.583) | words almost gone; hole starting to close |
| s5 | 972 (40.500) | head solid, no hole |
| w6 | 984 (41.000) | pink torn edge rising (≈ y 622), light shadow band on the uncle |
| s6 | 1008 (42.000) | empty prompt box at (360,285)–(1560,430) on pink |
| s6 | 1104 (46.000) | "Make what" typing |
| s6 | 1164 (48.500) | complete: "it" highlighted yellow in the box, "Make what, dear?" |
| w7 | 1187 (49.458) | cream torn edge at x ≈ 1186 moving left |
| s7 | 1272 (53.000) | card 1 dropping (scaled, slightly high) |
| s7 | 1344 (56.000) | three cards + tapes |
| s7 | 1380 (57.500) | "it" highlighted, arrow starting |
| s7 | 1416 (59.000) | arrow complete, "spinach omelette" highlighted, "…" at (1140,450) |
| s7 | 1464 (61.000) | ANS2 typed to "toa" |
| f8 | 1476 (61.500) | half-dark s7; 1488 (62.000) dark night fading up |
| s8 | 1512 (63.000) | night, glowing window, gold reflection, no envelope yet |
| s8 | 1584 (66.000) | envelope mid-flight (≈ 240 px wide, centre ≈ (720, 840)) with gold dotted trail |
| s8 | 1680 (70.000) | envelope ≈300 px at ≈ (527, 872), trail back to the window |
| s8 | 1716 (71.500) | fading to black (≈ 40 % luma) |

Audio checkpoints (rebuild vs reference audio `ref/v9_track_audio.wav`): music audible and continuous across 38–42 s
(the reference has silence there — intended difference); voice clean on sibilants and plosives at 2.0–8.4 s and on
"Gone" (39.61); typing audible under the voice at 25–29 s; whoosh at 17.15; paper slides at each wipe; tape thuds at
53.1 / 54.4 / 55.6.
