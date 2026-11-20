#!/usr/bin/env bash
# Render episode 4 end to end: two halves in parallel, join, add the mix, encode.
# Usage: scripts/render_ep4.sh [OUT.mp4]   (backdrops must exist: scripts/build_backdrops.sh)
#   EP4_FORMAT=reel scripts/render_ep4.sh [OUT.mp4]   the 9:16 reel (1080 x 1920): intermediates in out/ep4_reel/full/,
#                                                     default output out/ep4_reel/ep4_reel.mp4. Same mix (out/ep4/mix.wav).
set -euo pipefail
cd "$(dirname "$0")/.."
export EP4_FORMAT="${EP4_FORMAT:-landscape}"
if [ "$EP4_FORMAT" = "reel" ]; then DIR=out/ep4_reel; NAME=ep4_reel.mp4; else DIR=out/ep4; NAME=ep4.mp4; fi
OUT="${1:-$DIR/$NAME}"; D=$DIR/full; mkdir -p "$D"
MIX=out/ep4/mix.wav                       # the sound is the same file for both formats
[ -f "$MIX" ] || EP4_FORMAT=landscape STEMS=1 python3 -m ep4.audio "$MIX"   # the approved landscape mix
python3 -m ep4.video "$D/a.mp4" 0 36 > "$D/a.log" 2>&1 &
python3 -m ep4.video "$D/b.mp4" 36 72.05 > "$D/b.log" 2>&1 &
wait
printf "file 'a.mp4'\nfile 'b.mp4'\n" > "$D/list.txt"
ffmpeg -v error -y -f concat -safe 0 -i "$D/list.txt" -i "$MIX" -map 0:v -map 1:a \
  -c:v libx264 -crf 20 -preset medium -pix_fmt yuv420p -c:a aac -b:a 256k -shortest -movflags +faststart "$OUT"
echo "wrote $OUT"
