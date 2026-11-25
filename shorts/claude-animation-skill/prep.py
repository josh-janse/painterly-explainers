"""Inputs the beats need from Episode 4, made without changing any ep4 file:

  paint   9:16 dusk plate, saving the canvas after every painting pass  -> out/tl/*.jpg, out/plates/dusk.jpg
  stems   Episode 4's voice, effects and sea stems, no music track       -> out/audio/mix*.wav

Each step writes a patched copy of an ep4 module next to the original (it has to sit in the ep4 package for its
imports), runs it, and deletes it again.

    python3 prep.py paint
    python3 prep.py stems
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = HERE / "out"

SNAP_HOOK = '''
_SD = os.environ["SNAPDIR"]; _N = [0]
def _snap(tag):
    Image.fromarray(np.clip(canvas * 255, 0, 255).astype(np.uint8)).save(f"{_SD}/{_N[0]:03d}_{tag}.jpg", quality=90); _N[0] += 1
for _nm in ("paint", "apply_strokes", "soft_strokes"):
    _f = globals()[_nm]
    def _w(*a, _f=_f, **k):
        r = _f(*a, **k); _snap(_nm); return r
    globals()[_nm] = _w
'''

def run_patched(src, dst, edit, args, env):
    s = (REPO / "ep4" / src).read_text()
    (REPO / "ep4" / dst).write_text(edit(s))
    try:
        subprocess.run([sys.executable, "-m", f"ep4.{dst[:-3]}", *args], cwd=REPO, env={**os.environ, **env}, check=True)
    finally:
        (REPO / "ep4" / dst).unlink(missing_ok=True)

def paint():
    anchor = 'exec(open(os.path.join(_ENG, "figures.py")).read())\n'
    def edit(s):
        assert anchor in s, "backdrops.py changed: update the snapshot hook anchor"
        return s.replace(anchor, anchor + SNAP_HOOK, 1)
    (OUT / "tl").mkdir(parents=True, exist_ok=True)
    for f in (OUT / "tl").glob("*.jpg"):
        f.unlink()
    run_patched("backdrops.py", "_tl_backdrops.py", edit, ["dusk", "--out", str(OUT / "plates")],
                {"EP4_FORMAT": "reel", "SNAPDIR": str(OUT / "tl")})
    # the finished plate is the last key of the time-lapse
    import shutil
    n = len(list((OUT / "tl").glob("*.jpg")))
    shutil.copy(OUT / "plates" / "dusk.jpg", OUT / "tl" / f"{n:03d}_final.jpg")

def stems():
    line = 'trk = decode(os.path.join(ROOT, "assets", "audio", "ref_jamal.mp3"))[:N]'
    def edit(s):
        assert line in s, "audio.py changed: update the music line"
        return s.replace(line, "trk = np.zeros((N, 2), np.float32)  # no music track in this build")
    (OUT / "audio").mkdir(parents=True, exist_ok=True)
    run_patched("audio.py", "_audio_nomusic.py", edit, [str(OUT / "audio" / "mix.wav")], {"STEMS": "1"})

if __name__ == "__main__":
    {"paint": paint, "stems": stems}[sys.argv[1]]()
