# Vendored painterly engine

A vendored snapshot of the painterly renderer from the `painterly-posters` repo, copied so this repo is self-contained.

- Source: `painterly-posters/renderer/` at commit `58446555c1a68efe9c1c0d919372b276c8663c3e`
- Copied: 2026-11-19
- Files: `engine.py`, `marks.py`, `figures.py`, `figures2.py`, `perspective.py`, `fonts.py`, `fetch_textures.sh` (unmodified)
- Added here: `smoke_engine.py`

These files are a snapshot, not a live dependency. Changes made upstream do not reach this copy; re-copy them deliberately and update the commit above. Local fixes should be kept small and noted here.

## How the modules load

They are not imported. A script sets config globals (`SEED`, `PAPER_RGB`, `EDGE_TOOTH`, `TEX`, optionally `PAGE_MM`), sets `sys.argv = [name, DPI, OUT]`, then `exec`s the modules into its own namespace in this order:

```
engine.py -> marks.py -> figures.py -> figures2.py -> perspective.py
```

`engine.py` reads `sys.argv` and the config globals at exec time, so they must be set first. Texture paths are `tex/...`, relative to the working directory, so run scripts from `engine/` (or `chdir` there before the execs). See `smoke_engine.py` for the minimal pattern.

## Textures

```bash
cd engine
./fetch_textures.sh      # Poly Haven + ambientCG CC0 scans into engine/tex/ (gitignored)
python3 smoke_engine.py 40 ../out/smoke_40.png
```

The script's last step (a Winslow Homer wash crop from Wikimedia, `tex/wash_Homer_sloop_sky.png`) is only used by a posters-repo study board, not by these modules. If Wikimedia rate-limits it, the script exits at that step after everything else has downloaded.
