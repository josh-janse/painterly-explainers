#!/bin/sh
# Downloads every CC0 texture scan the renderer uses into ./tex (run from the renderer/ folder).
#   ./fetch_textures.sh          -> everything the current posters need
#   ./fetch_textures.sh --all    -> also the grounds that were tested and rejected (fabric / extra plasters), for the study scripts
set -e
mkdir -p tex
# --- Poly Haven (archived Coastal Dusk v2b; still the engine's fallback TEX) ---
B=https://dl.polyhaven.org/file/ph-assets/Textures/png/2k
curl -sL $B/white_stucco/white_stucco_disp_2k.png         -o tex/white_stucco_Displacement.png
curl -sL $B/plaster_grey_04/plaster_grey_04_rough_2k.png   -o tex/plaster_grey_04_Rough.png
curl -sL $B/white_plaster_02/white_plaster_02_rough_2k.png -o tex/white_plaster_02_Rough.png
curl -sL $B/rough_linen/rough_linen_rough_2k.png           -o tex/rough_linen_Rough.png
# --- ambientCG ---
acg() {  # acg <AssetId> <Res> <pattern...>
  id=$1; res=$2; shift 2
  curl -sL "https://ambientcg.com/get?file=${id}_${res}-JPG.zip" -o /tmp/${id}.zip
  for p in "$@"; do unzip -o -q -j /tmp/${id}.zip "*_${p}.jpg" -d tex; done
}
for i in 001 002 003 004 005 006; do acg Paper$i 2K Color Displacement Roughness; done      # paper grounds (001, 002, 006 in use)
for i in 001 002 003 004 005 006; do acg Paint$i 1K Displacement; done                     # brushed-paint height (paint body, gouache bristles)
acg Smear007 1K Color Opacity NormalGL                                                      # palette-knife smear surface
acg Plaster001 1K Displacement                                                              # in-segment dry-brush catch (rocks, concrete)
acg Cork002 1K Color                                                                        # character lab M-B: cork / sponge skin material (luminance only)
acg Fabric085 1K Displacement                                                               # character lab M-B: knit material (stocking-stitch relief)
# --- A real watercolour wash, used ONLY as pigment-density detail inside the procedural watercolour-water washes (swatch_board_watercolour.py).
#     One 548 x 493 px window of clean grey-green sky wash from Winslow Homer, "Sloop, Nassau" (1899, watercolour; The Met, object 11139).
#     Public domain (Homer died 1910; Commons: PD-Art / PD-old-100) and released by The Met under Open Access (CC0).
#     https://commons.wikimedia.org/wiki/File:Winslow_Homer_-_Sloop,_Nassau_(1899).jpg   https://www.metmuseum.org/art/collection/search/11139
curl -sL -A "painterly-posters/1.0" -o /tmp/wc_sloop.jpg \
  "https://upload.wikimedia.org/wikipedia/commons/9/97/Winslow_Homer_-_Sloop%2C_Nassau_%281899%29.jpg"
python3 - <<'PY'
from PIL import Image
Image.open("/tmp/wc_sloop.jpg").convert("L").crop((2545, 377, 3093, 870)).save("tex/wash_Homer_sloop_sky.png")      # file is 3807 x 2654
PY
if [ "$1" = "--all" ]; then
  for a in Fabric011 Fabric013 Fabric019 Fabric031 Plaster002 Plaster003 Plaster004 Plaster006 Plaster007; do acg $a 1K Displacement; done
fi
echo "textures in ./tex:"; ls tex | wc -l
