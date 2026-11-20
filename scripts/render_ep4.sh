#!/usr/bin/env bash
# Render episode 4 end to end: two halves in parallel, join, add the mix, encode.
# Usage: scripts/render_ep4.sh [OUT.mp4]   (backdrops must exist: scripts/build_backdrops.sh)
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-out/ep4/ep4.mp4}"; D=out/ep4/full; mkdir -p "$D"
[ -f out/ep4/mix.wav ] || STEMS=1 python3 -m ep4.audio out/ep4/mix.wav
python3 -m ep4.video "$D/a.mp4" 0 36 > "$D/a.log" 2>&1 &
python3 -m ep4.video "$D/b.mp4" 36 72.05 > "$D/b.log" 2>&1 &
wait
printf "file 'a.mp4'\nfile 'b.mp4'\n" > "$D/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$D/list.txt" -i out/ep4/mix.wav -map 0:v -map 1:a \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart "$OUT"
echo "wrote $OUT"
