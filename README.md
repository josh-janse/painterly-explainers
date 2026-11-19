# Painterly explainers

Python code that renders painterly explainer videos: frames painted with a procedural gouache, watercolour and dry-brush engine, cut to a voiceover with sound effects.

## Setup

```bash
pip install numpy scipy pillow     # ffmpeg is also needed for audio and video
cd engine && ./fetch_textures.sh   # CC0 paper and paint scans into engine/tex/
python3 smoke_engine.py 40 ../out/smoke_40.png
cd .. && python3 tools/fetch_sfx.py  # Freesound previews into assets/sfx/raw/
```

## Layout

- `engine/`: vendored snapshot of the painterly renderer (see `engine/README.md`). Modules are `exec`'d in a fixed order, and texture paths are relative to `engine/`.
- `assets/sfx/`: `manifest.json` maps short names to Freesound IDs, credits and files; `credits.md` holds the published credits; `raw/` holds the downloaded mp3s (fetch with `tools/fetch_sfx.py`).
- `assets/audio/`: `vo_sekou.mp3` (ElevenLabs voice) and `vo2.wav` (the same, decoded to 48 kHz mono). `ref_jamal.mp3` is a reference music track kept locally only: it is gitignored because its licence is unknown.
- `tools/`: helper scripts.
- `out/`, `renders/`: render outputs (gitignored).
