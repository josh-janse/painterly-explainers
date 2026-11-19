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

