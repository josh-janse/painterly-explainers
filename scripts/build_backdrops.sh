#!/usr/bin/env bash
# Regenerate every ep4 backdrop plate (SPEC §3.1), two renders at a time.
# Needs the engine textures first:  (cd engine && ./fetch_textures.sh)
# Usage: scripts/build_backdrops.sh [-j N] [--check] [--format landscape|reel] [NAME ...]
#   --format reel (or env EP4_FORMAT=reel): the 9:16 plates, 1080 x 1920, into out/ep4_reel/ (docs/REEL_LAYOUT.md §4).
#                 Landscape (the default) writes out/ep4/ -- the approved plates; rebuilding them is byte-identical.
#   --check       also makes <out>/check_backdrops.jpg
#   NAME ...      only these plates (e.g. dusk dusk_nc); default all
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS=2; CHECK=0; FMT="${EP4_FORMAT:-landscape}"; ONLY=()
while [ $# -gt 0 ]; do
  case "$1" in
    -j) JOBS="$2"; shift 2 ;;
    --check) CHECK=1; shift ;;
    --format) FMT="$2"; shift 2 ;;
    --format=*) FMT="${1#--format=}"; shift ;;
    -*) echo "unknown arg $1" >&2; exit 2 ;;
    *) ONLY+=("$1"); shift ;;
  esac
done
case "$FMT" in
  landscape) OUTD=out/ep4 ;;
  reel) OUTD=out/ep4_reel ;;
  *) echo "--format must be landscape or reel, not $FMT" >&2; exit 2 ;;
esac
export EP4_FORMAT="$FMT"
mkdir -p "$OUTD/logs"
[ -f engine/tex/white_stucco_Displacement.png ] || { echo "engine/tex missing: run (cd engine && ./fetch_textures.sh)" >&2; exit 1; }

# name|env|scene  (each line is one render; ~1-1.5 min each for dusk/night/uncle, ~10 s for a paper plate).
# Reel paper plates are the approved landscape sheets turned 90 deg (they need out/ep4/paper_*.jpg); the uncle is
# repainted at 1.25x. night_off is not used by the video (the night window never switches) and is not built.
JOBLIST="dusk||dusk
dusk_nc|NOCLOUDS=1|dusk
dusk_off|WINDOW_OFF=1|dusk
night||night
night_nc|NOCLOUDS=1|night
uncle||uncle
paper_yellow||paper_yellow
paper_pink||paper_pink
paper_cream||paper_cream"
if [ ${#ONLY[@]} -gt 0 ]; then
  JOBLIST=$(echo "$JOBLIST" | grep -E "^($(IFS='|'; echo "${ONLY[*]}"))\|" || true)
  [ -n "$JOBLIST" ] || { echo "no plate matches: ${ONLY[*]}" >&2; exit 2; }
fi

run_one() {
  IFS='|' read -r name envs scene <<< "$1"
  local t0=$SECONDS
  if env $envs python3 -m ep4.backdrops "$scene" > "$OUTD/logs/$name.log" 2>&1; then
    echo "ok   $name ($((SECONDS - t0)) s)"
  else
    echo "FAIL $name (see $OUTD/logs/$name.log)"; return 1
  fi
}
export -f run_one
export OUTD
echo "format $FMT -> $OUTD"
echo "$JOBLIST" | xargs -P "$JOBS" -I{} bash -c 'run_one "$@"' _ {}

if [ "$CHECK" = 1 ]; then python3 -m ep4.check_backdrops; fi
ls -la "$OUTD" | grep -E '\.(jpg|png|npz)$'
