#!/usr/bin/env bash
# Builds Claude's beats for the "Claude animation skill" Short and a silent preview with placeholders.
# Needs: python3 with numpy, scipy, pillow, playwright (+ a Chromium), and ffmpeg.
#   SWATCH_HTML=/path/to/swatch-book.html   required for step 1 (the swatch book artifact, saved as HTML)
#   CHROMIUM=/path/to/chrome                optional, if Playwright can't find its own browser
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
mkdir -p "$HERE/out/beats" "$HERE/out/plates"

[ -d "$REPO/engine/tex" ] || (cd "$REPO/engine" && sh fetch_textures.sh)

cd "$HERE"
python3 prep.py paint                                                    # dusk plate + a snapshot per pass
(cd "$REPO" && EP4_FORMAT=reel python3 -m ep4.backdrops uncle --out "$HERE/out/plates")
(cd "$REPO" && python3 scripts/reel_blockouts.py)                        # flat 9:16 frames for step 3
python3 prep.py stems                                                    # voice, effects, sea (no music)

python3 beat_study.py      # step 1, 6 s
python3 beat_rough.py      # step 3, 5 s
python3 beat_paint.py      # step 4, 6 s
python3 beat_notes.py      # step 5, 8 s
python3 beat_sound.py      # step 6, 5 s (+ matching audio)
python3 assemble.py        # out/short_preview_v1.mp4
