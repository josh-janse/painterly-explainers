#!/usr/bin/env bash
# Regenerate every ep4 backdrop plate in out/ep4/ (SPEC §3.1), two renders at a time.
# Needs the engine textures first:  (cd engine && ./fetch_textures.sh)
# Usage: scripts/build_backdrops.sh [-j N] [--check]     (--check also makes out/ep4/check_backdrops.jpg)
set -euo pipefail
cd "$(dirname "$0")/.."
JOBS=2; CHECK=0
while [ $# -gt 0 ]; do
  case "$1" in
    -j) JOBS="$2"; shift 2 ;;
    --check) CHECK=1; shift ;;
    *) echo "unknown arg $1" >&2; exit 2 ;;
  esac
done
mkdir -p out/ep4/logs
[ -f engine/tex/white_stucco_Displacement.png ] || { echo "engine/tex missing: run (cd engine && ./fetch_textures.sh)" >&2; exit 1; }

# name|env|scene  (each line is one render; ~1-1.5 min each for dusk/night/uncle, ~10 s for a paper plate)
JOBLIST="dusk||dusk
dusk_nc|NOCLOUDS=1|dusk
dusk_off|WINDOW_OFF=1|dusk
night||night
night_nc|NOCLOUDS=1|night
uncle||uncle
paper_yellow||paper_yellow
paper_pink||paper_pink
paper_cream||paper_cream"

run_one() {
  IFS='|' read -r name envs scene <<< "$1"
  local t0=$SECONDS
  if env $envs python3 -m ep4.backdrops "$scene" > "out/ep4/logs/$name.log" 2>&1; then
    echo "ok   $name ($((SECONDS - t0)) s)"
  else
    echo "FAIL $name (see out/ep4/logs/$name.log)"; return 1
  fi
}
export -f run_one
echo "$JOBLIST" | xargs -P "$JOBS" -I{} bash -c 'run_one "$@"' _ {}

if [ "$CHECK" = 1 ]; then python3 -m ep4.check_backdrops; fi
ls -la out/ep4 | grep -E '\.(jpg|png|npz)$'
