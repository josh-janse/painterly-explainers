"""Episode 4 sound mix: rebuild of ep4_audio2.py in "track" mode (docs/SPEC_ep4.md §5).

    python3 -m ep4.audio OUT.wav            # from the repo root
    STEMS=1        also writes OUT_fx.wav, OUT_music.wav, OUT_amb.wav, OUT_vo.wav (pre master fade / limiter)
    AMB_GONE_DIP=1 restores v9's room/clock drop-out around "Gone" (default 0: no pause, owner change 1)
    PRESENCE_DB    voice presence boost at 3.2 kHz, Q 0.9 (default 0.0, capped at +1.0)
    COMP_THR_DB    voice compressor threshold (default -26, spec; -20 keeps every syllable under 3 dB of reduction)
    BED_TRIM_DB    trim on music + ambience + effects (default -0.9 dB: keeps v9's balance against the quieter clean voice)

Owner changes against v9: the music runs under the whole video (no "Gone" gate), and the voice and master use a
clean chain (gentle compression, voiced RMS -18 dBFS, look-ahead true-peak limiter at -1.0 dBTP; no tanh anywhere).
Output is 24-bit PCM, 48 kHz stereo. Reads only the timeline and assets/; also rewrites assets/sfx/credits.md.
"""
import json, os, subprocess, sys

import numpy as np
from scipy import ndimage as ndi
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from ep4.timeline import (A_OFF, ANNOT, ANS_TYPE, ANS2_TYPE, CARD0, CARD_GAP, END, FLY_HOME, FLY_OUT, FORGET,
                              IT_SWEEP, Q2_TYPE, REPLY_TYPE, T, VO_END, VO_GAPS, v)
except ImportError:
    # private copy of spec §2.1 (used only if ep4/timeline.py is missing)
    A_OFF = 1.5
    P = [0.0, 9.76, 16.70, 23.20, 28.69, 40.00, 48.47, 60.87]
    VO_END = 67.55
    def v(a): return a + A_OFF
    END = round(v(VO_END) + 3.0, 2)
    T = dict(s1=(0, v(P[1])), s2=(v(P[1]), v(P[2]) - 0.7),
             w3=(v(P[2]) - 0.7, v(P[2])), s3=(v(P[2]), v(P[3]) - 0.6),
             w4=(v(P[3]) - 0.6, v(P[3])), s4=(v(P[3]), v(P[4]) - 0.7),
             w5=(v(P[4]) - 0.7, v(P[4])), s5=(v(P[4]), v(P[5]) - 0.6),
             w6=(v(P[5]) - 0.6, v(P[5])), s6=(v(P[5]), v(P[6]) - 0.6),
             w7=(v(P[6]) - 0.6, v(P[6])), s7=(v(P[6]), v(P[7]) - 1.2),
             f8=(v(P[7]) - 1.2, v(P[7])), s8=(v(P[7]), END))
    FLY_OUT = (3.2, 2.4); REPLY_TYPE = (0.6, 24.0); FORGET = 2.6; Q2_TYPE = (1.5, 16.0)
    ANS_TYPE = (4.3, 14.0); IT_SWEEP = 6.0; CARD0, CARD_GAP = 2.7, 1.2; ANS2_TYPE = (9.2, 24.0)
    FLY_HOME = (0.8, 4.2); ANNOT = (7.1, 7.6, 8.3)
    VO_GAPS = [(8.44, 9.76), (15.03, 16.70), (22.20, 23.20), (27.07, 28.69), (38.55, 40.00), (46.73, 48.47), (59.43, 60.87)]

SR = 48000
N = int(END * SR)
GONE = v(38.11)
AMB_GONE_DIP = os.environ.get("AMB_GONE_DIP", "0") not in ("", "0", "false", "False")
PRESENCE_DB = min(1.0, float(os.environ.get("PRESENCE_DB", "0.0")))
VOICE_RMS_DB = -18.0
CEIL_DB = -1.0
MUSIC_DB = -16.5          # v9 track-mode music gain (spec §5.6)
COMP_THR_DB = float(os.environ.get("COMP_THR_DB", "-26.0"))
# The clean voice sits 0.9 dB below v9's (v9 voiced mix RMS -17.2 dBFS measured on ref/v9_track_audio.wav, the new
# voice -18.0). To keep v9's balance against the voice, music, ambience and effects are all trimmed by the same amount.
BED_TRIM_DB = float(os.environ.get("BED_TRIM_DB", "-0.9"))


def db(x): return 10 ** (x / 20)
def todb(x): return 20 * np.log10(max(float(x), 1e-12))
def rms(x): return float(np.sqrt(np.mean(np.asarray(x, np.float64) ** 2)))


# ------------------------------------------------------------ loading
MAN = json.load(open(os.path.join(ROOT, "assets", "sfx", "manifest.json")))["sounds"]
USE = ["sea", "gulls", "room", "clock", "slide_a", "slide_b", "settle", "flutter", "whoosh", "tape", "air", "typewriter"]
CACHE = {}


def decode(fn, ch=2):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", fn, "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch).copy()


def load(key):
    if key not in CACHE:
        CACHE[key] = decode(os.path.join(ROOT, MAN[key]["file"]))
    return CACHE[key]


# ------------------------------------------------------------ core helpers (spec §5.2)
def seg(x, t0, dur, fi=0.02, fo=0.08):
    i0, i1 = int(t0 * SR), int((t0 + dur) * SR)
    if i1 > len(x):                      # loop a short source with a 0.25 s crossfade instead of returning a short clip
        xf = int(0.25 * SR); out = x.copy()
        while len(out) < i1:
            r = np.linspace(0, 1, xf, dtype=np.float32)[:, None]
            out = np.concatenate([out[:-xf], out[-xf:] * (1 - r) + x[:xf] * r, x[xf:]])
        x = out
    y = x[i0:i1].copy(); n = len(y); t = np.arange(n) / SR
    y *= (np.clip(t / max(fi, 1e-3), 0, 1) * np.clip((n / SR - t) / max(fo, 1e-3), 0, 1))[:, None].astype(np.float32)
    return y


def rms_to(x, d): return x * db(d) / (np.sqrt((x ** 2).mean()) + 1e-9)
def peak_to(x, d): return x * db(d) / (np.abs(x).max() + 1e-9)


mix = np.zeros((N, 2), np.float32)       # effects
amb = np.zeros((N, 2), np.float32)       # ambience, ducked separately


def place(x, t0, pan=None, bus=None):
    """add a stereo clip at t0; with pan (-1..1, scalar or per-sample) it is folded to mono and panned"""
    bus = mix if bus is None else bus
    i0 = int(t0 * SR)
    if i0 >= N: return
    n0 = len(x)
    if pan is not None:
        pan = np.asarray(pan, np.float32)
        if pan.ndim and len(pan) != n0:  # per-sample pan built for a slightly different length: stretch it to the clip
            pan = np.interp(np.linspace(0, 1, n0), np.linspace(0, 1, len(pan)), pan).astype(np.float32)
    if i0 < 0:
        x = x[-i0:]; pan = pan[-i0:] if pan is not None and pan.ndim else pan; i0 = 0
    x = x[: N - i0]
    if pan is not None:
        if pan.ndim: pan = pan[: len(x)]
        m = x.mean(1); p = np.broadcast_to(pan, m.shape)
        x = np.stack([m * np.cos((p + 1) * np.pi / 4), m * np.sin((p + 1) * np.pi / 4)], 1) * 1.414
    bus[i0:i0 + len(x)] += x.astype(np.float32)


# ------------------------------------------------------------ dynamics
def peaking(x, f0, gain_db, q):
    A = 10 ** (gain_db / 40); w0 = 2 * np.pi * f0 / SR; al = np.sin(w0) / (2 * q); c = np.cos(w0)
    b = np.array([1 + al * A, -2 * c, 1 - al * A]); a = np.array([1 + al / A, -2 * c, 1 - al / A])
    return signal.lfilter(b / a[0], a / a[0], x)


def compress(x, thr_db=-26.0, ratio=1.5, att=0.010, rel=0.150, knee_db=6.0):
    """feed-forward compressor on a 1 kHz control signal (recovered), with a soft knee; returns (y, gr_db at 1 kHz)"""
    dec = SR // 1000
    lev = np.sqrt(np.maximum(signal.sosfilt(signal.butter(1, 40, "lowpass", fs=SR, output="sos"), x ** 2), 1e-12))[::dec]
    o = 20 * np.log10(lev) - thr_db; s = 1 - 1 / ratio
    if knee_db > 0:
        over = np.where(o <= -knee_db / 2, 0.0, np.where(o >= knee_db / 2, o * s, s * (o + knee_db / 2) ** 2 / (2 * knee_db)))
    else:
        over = np.maximum(0, o) * s
    g = np.zeros_like(over); ka, kr = np.exp(-1 / (att * 1000)), np.exp(-1 / (rel * 1000)); cur = 0.0
    for i, ov in enumerate(over):
        k = ka if ov > cur else kr; cur = k * cur + (1 - k) * ov; g[i] = cur
    return x * db(-np.interp(np.arange(len(x)) / dec, np.arange(len(g)), g)), g


def true_peak_ps(x, os_=4, chunk=1 << 17, pad=256):
    """per-sample true-peak estimate (4x oversampled, max over the samples' channels), computed in chunks"""
    x2 = x[:, None] if x.ndim == 1 else x
    n = len(x2); pk = np.empty(n)
    for s in range(0, n, chunk):
        a, b = max(0, s - pad), min(n, s + chunk + pad)
        up = signal.resample_poly(x2[a:b].astype(np.float64), os_, 1, axis=0)
        p = np.abs(up).max(1)[: (b - a) * os_].reshape(b - a, os_).max(1)
        e = min(n, s + chunk); pk[s:e] = p[s - a: s - a + (e - s)]
    return pk


def tp_limit(x, ceiling_db=CEIL_DB, look_ms=5.0, rel_ms=80.0, os_=4, block=48):
    """look-ahead true-peak limiter for mono (N,) or linked multichannel (N, C) float arrays (spec §5.3)"""
    x2 = x[:, None] if x.ndim == 1 else x
    n = len(x2); c = db(ceiling_db)
    pk = true_peak_ps(x2, os_)
    g_req = np.minimum(1.0, c / np.maximum(pk, 1e-12))
    L = max(1, int(look_ms * SR / 1000))
    g_hold = ndi.minimum_filter1d(g_req, size=L + 1, origin=-(L // 2))          # min over [n, n+L]
    h = np.hanning(L + 2)[1:-1]; h /= h.sum()
    # smooth ramp over [n-L, n]; padded with unity in front so the first L samples are not faded in (a partial
    # kernel sum there would pull the gain towards 0)
    g_att = np.minimum(np.convolve(np.concatenate([np.ones(len(h)), g_hold]), h, mode="full")[len(h): len(h) + n], g_hold)
    nb = (n + block - 1) // block
    gb = np.pad(g_att, (0, nb * block - n), constant_values=1.0).reshape(nb, block).min(1)
    kr = np.exp(-block / (rel_ms * SR / 1000)); out = np.empty(nb); cur = 1.0
    for i, gv in enumerate(gb):
        cur = gv if gv < cur else cur * kr + gv * (1 - kr); out[i] = cur
    g = np.minimum(np.interp(np.arange(n), np.arange(nb) * block + block / 2, out), g_att)
    y = np.clip(x2 * g[:, None], -c, c)                                          # safety; should be a no-op
    return (y[:, 0] if x.ndim == 1 else y).astype(np.float32), g


def lufs(x):
    """approximate integrated loudness, BS.1770 K-weighting with the -70 / -10 LU gates (48 kHz)"""
    x2 = x[:, None] if x.ndim == 1 else x
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x2.astype(np.float64), axis=0), axis=0)
    blk, hop = int(0.4 * SR), int(0.1 * SR)
    cs = np.concatenate([np.zeros((1, y.shape[1])), np.cumsum(y ** 2, 0)])
    st = np.arange(0, len(y) - blk, hop)
    z = ((cs[st + blk] - cs[st]) / blk).sum(1)
    l = -0.691 + 10 * np.log10(np.maximum(z, 1e-12))
    z = z[l > -70]
    if not len(z): return -99.0
    rel = -0.691 + 10 * np.log10(z.mean()) - 10
    z = z[-0.691 + 10 * np.log10(z) > rel]
    return float(-0.691 + 10 * np.log10(z.mean()))


def write_wav(fn, x):
    """24-bit PCM WAV through ffmpeg"""
    x = np.ascontiguousarray(np.clip(x, -1, 1).astype(np.float32))
    ch = 1 if x.ndim == 1 else x.shape[1]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(ch), "-i", "-",
                    "-c:a", "pcm_s24le", fn], input=x.tobytes(), check=True)


# ------------------------------------------------------------ the voice: clean chain (spec §5.3)
vo = decode(os.path.join(ROOT, "assets", "audio", "vo2.wav"), 1)[:, 0].astype(np.float64)
vo = signal.sosfilt(signal.butter(2, 80, "highpass", fs=SR, output="sos"), vo)
vo = vo / (np.abs(vo).max() + 1e-9) * db(-3)
vo, comp_gr = compress(vo, thr_db=COMP_THR_DB, ratio=1.5, att=0.010, rel=0.150, knee_db=6.0)
if PRESENCE_DB > 0:
    vo = peaking(vo, 3200, PRESENCE_DB, 0.9)
_e = np.sqrt(signal.sosfilt(signal.butter(1, 6.0, "lowpass", fs=SR, output="sos"), vo ** 2).clip(0))
_voiced = _e > _e.max() * 0.15
vo = vo * db(VOICE_RMS_DB) / (np.sqrt((vo[_voiced] ** 2).mean()) + 1e-9)
vo_pre = vo.copy()
vo, vo_g = tp_limit(vo)
VO = np.zeros(N, np.float32); i0 = int(A_OFF * SR)
VO[i0:i0 + len(vo)] = vo[: N - i0]
VO_PRE = np.zeros(N, np.float32); VO_PRE[i0:i0 + len(vo)] = vo_pre[: N - i0]

# ------------------------------------------------------------ speech envelope, ducking (spec §5.4)
venv = np.sqrt(signal.sosfilt(signal.butter(1, 6.0, "lowpass", fs=SR, output="sos"), VO.astype(np.float64) ** 2).clip(0))
speech = np.clip(venv / (venv.max() * 0.35 + 1e-9), 0, 1)
duck = 1 - 0.62 * speech                                                          # about -8 dB under the voice

# ------------------------------------------------------------ ambience
sea = load("sea")
place(rms_to(seg(sea, 20.0, T["w3"][1] + 0.3, 1.5, 1.0), -37), 0.0, bus=amb)                      # dusk, until the first paper wipe
t_n = T["f8"][0] + 0.5
place(rms_to(seg(sea, 110.0, END - t_n, 1.6, 1.4), -38), t_n, bus=amb)                             # night
GAPS = [(v(a), v(b)) for a, b in VO_GAPS]                                                         # pauses between paragraphs, video time
place(rms_to(seg(load("gulls"), 2.0, A_OFF + 0.6, 0.4, 0.5), -37), 0.0, bus=amb)                     # distant gulls before his first word
place(rms_to(seg(load("gulls"), 9.0, GAPS[0][1] - GAPS[0][0] + 0.8, 0.3, 0.6), -38), GAPS[0][0] - 0.1, bus=amb)   # and in the first pause
place(rms_to(seg(load("room"), 10.0, T["f8"][0] + 0.4 - T["w3"][1], 0.6, 0.8), -52), T["w3"][1], bus=amb)
for k in ("s3", "s5"):
    a, b = T[k]; place(rms_to(seg(load("clock"), 5.0 + a % 20, b - a, 0.5, 0.6), -47), a, pan=0.35, bus=amb)

# ------------------------------------------------------------ effects
wh = load("whoosh")
place(peak_to(seg(wh, 0.0, min(1.4, len(wh) / SR), 0.15, 0.5), -25), T["w3"][0] - 0.35,
      pan=np.linspace(0.45, -0.1, int(min(1.4, len(wh) / SR) * SR)))
for i, k in enumerate(("w4", "w5", "w6", "w7")):
    a, b = T[k]
    sl = load("slide_a" if i % 2 == 0 else "slide_b")
    place(peak_to(seg(sl, 0.0, min(len(sl) / SR, b - a + 0.5), 0.01, 0.2), -21), a - 0.05, pan=0.3 if k in ("w4", "w7") else 0.0)
    place(peak_to(seg(load("settle"), 0.0, 0.55), -25), b - 0.03)

place(peak_to(seg(load("slide_b"), 0.0, 1.0, 0.01, 0.25), -27), T["s3"][0] + 1.2, pan=0.55)        # the letter slides in from the right
place(peak_to(seg(load("settle"), 0.0, 0.4), -33), T["s3"][0] + 0.75, pan=-0.35)                    # the envelope lands in his head


def flight(t0, dur, pan0, pan1, launch_gain, whoosh_gain):
    fl = load("flutter"); wh = load("whoosh")
    place(peak_to(seg(fl, 0.0, min(1.2, len(fl) / SR), 0.01, 0.4), launch_gain), t0, pan=pan0)
    w = seg(wh, 0.0, len(wh) / SR, 0.05, 0.4); n = len(w)
    place(peak_to(w, whoosh_gain), t0 + max(0.0, (dur - n / SR) / 2), pan=np.linspace(pan0, pan1, n))


flight(T["s2"][0] + FLY_OUT[0], FLY_OUT[1], -0.7, 0.55, -24, -25)
flight(T["s8"][0] + FLY_HOME[0], FLY_HOME[1], 0.5, -0.5, -30, -23)
place(peak_to(seg(load("flutter"), 0.2, 0.9, 0.02, 0.4), -24), T["s8"][0] + FLY_HOME[0] + FLY_HOME[1] - 0.3, pan=-0.5)   # it arrives, close

place(peak_to(seg(load("slide_b"), 0.0, 0.45, 0.01, 0.15), -30), T["s6"][0] + IT_SWEEP, pan=-0.15)  # highlighter swipe on "it"
place(peak_to(seg(load("slide_b"), 0.0, 0.45, 0.01, 0.15), -31), T["s7"][0] + ANNOT[0], pan=-0.3)   # scene 7: the swipe on "it",
place(peak_to(seg(load("slide_a"), 0.1, 0.7, 0.05, 0.2), -35), T["s7"][0] + ANNOT[1], pan=np.linspace(-0.2, 0.2, int(0.7 * SR)))   # the pen arrow,
place(peak_to(seg(load("slide_b"), 0.0, 0.5, 0.01, 0.15), -31), T["s7"][0] + ANNOT[2], pan=-0.35)   # and the swipe on "spinach omelette"

for i in range(3):                                                                                  # letters land and are taped down
    t0 = T["s7"][0] + CARD0 + CARD_GAP * i
    place(peak_to(seg(load("slide_a"), 0.0, 0.5, 0.01, 0.15), -27), t0, pan=-0.4)
    place(peak_to(seg(load("settle"), 0.0, 0.45), -25), t0 + 0.42, pan=-0.4)
    place(peak_to(seg(load("tape"), 0.0, 0.7, 0.01, 0.2), -25), t0 + 0.48, pan=-0.3)

place(rms_to(seg(load("air"), 0.0, 6.0, 1.0, 2.2), -40), T["s5"][0] + FORGET, pan=0.35)            # the words leave his head

# ------------------------------------------------------------ typewriter (spec §5.5)
tw = load("typewriter"); twm = tw.mean(1)
env = np.convolve(np.abs(twm), np.ones(96) / 96, "same"); de = np.diff(env, prepend=0); thr = env.max() * 0.25
onsets, last = [], -SR
for i in np.where((env > thr) & (de > 0))[0]:
    if i - last > int(0.12 * SR): onsets.append(i)
    last = i
KEYS = []
for o in onsets:
    k = tw[max(0, o - int(0.004 * SR)): o + int(0.11 * SR)].copy(); n = len(k)
    k *= (np.clip(np.arange(n) / (0.002 * SR), 0, 1)[:, None] * np.clip((n - np.arange(n)) / (0.03 * SR), 0, 1)[:, None]).astype(np.float32)
    KEYS.append(peak_to(k, 0))
rk = np.random.default_rng(31)


def typing(text, t0, cps, gain=-26, pan=0.0):
    prev = -1
    for i, ch in enumerate(text):
        j = int(rk.integers(len(KEYS)))
        if j == prev: j = (j + 1) % len(KEYS)
        prev = j
        g = gain - (5 if ch == " " else 0) + rk.uniform(-1.5, 1.5)
        place(KEYS[j] * db(g), t0 + i / cps + rk.uniform(-0.008, 0.008), pan=pan + rk.uniform(-0.08, 0.08))


REPLY = "A spinach omelette. Wilt the spinach in butter, pour in three beaten eggs, fold it over and serve."
typing(REPLY, T["s4"][0] + REPLY_TYPE[0], REPLY_TYPE[1], pan=0.05)
typing("Thanks! Can you make it without eggs?", T["s6"][0] + Q2_TYPE[0], Q2_TYPE[1], gain=-27, pan=-0.05)
typing("Make what, dear?", T["s6"][0] + ANS_TYPE[0], ANS_TYPE[1], pan=0.05)
typing("Without eggs? Try spinach and cheese on toast.", T["s7"][0] + ANS2_TYPE[0], ANS2_TYPE[1], pan=0.3)

# ------------------------------------------------------------ music: track mode, no "Gone" gate (spec §5.6)
tt_ = np.arange(N) / SR
music = np.zeros((N, 2), np.float32)
trk = decode(os.path.join(ROOT, "assets", "audio", "ref_jamal.mp3"))[:N]
music[: len(trk)] = trk
del trk
music *= (db(MUSIC_DB) * (1 + (db(6.0) - 1) * np.clip((18.0 - tt_) / 3.0, 0, 1)))[:, None].astype(np.float32)   # quiet intro lifted
music *= (1 - 0.55 * speech)[:, None].astype(np.float32)
lift = np.clip((tt_ - (v(VO_END) - 0.3)) / 0.8, 0, 1)                         # up a little for the ending
music *= (1 + 0.6 * lift)[:, None].astype(np.float32)
_bs = np.stack([signal.sosfilt(signal.butter(2, [700, 4000], "bandstop", fs=SR, output="sos"), music[:, c]) for c in range(2)], 1)
music = (music * (1 - 0.5 * speech)[:, None] + _bs * (0.5 * speech)[:, None]).astype(np.float32)   # clear the speech band
del _bs
# (v9's "Gone" gate on the music is deliberately gone; no reverb in track mode)

# ------------------------------------------------------------ ambience around "Gone" (spec §5.7), off by default
if AMB_GONE_DIP:
    quiet = 1 - np.clip((tt_ - (GONE - 0.15)) / 0.15, 0, 1) * np.clip((T["s6"][0] + 0.6 - tt_) / 0.6, 0, 1)
    amb *= quiet[:, None].astype(np.float32)

# ------------------------------------------------------------ mix and master (spec §5.8)
amb_bs = np.stack([signal.sosfilt(signal.butter(2, [900, 4500], "bandstop", fs=SR, output="sos"), amb[:, c]) for c in range(2)], 1)
amb = (amb * (1 - speech)[:, None] + amb_bs * speech[:, None]).astype(np.float32)   # the sea loses its hiss under the voice
del amb_bs
amb_d = (amb * duck[:, None]).astype(np.float32)
_bt = np.float32(db(BED_TRIM_DB)); mix *= _bt; music *= _bt; amb_d *= _bt
out = mix + music + amb_d + VO[:, None]
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "out", "ep4", "mix.wav")
os.makedirs(os.path.dirname(os.path.abspath(OUT)), exist_ok=True)
if os.environ.get("STEMS"):
    base = OUT[:-4] if OUT.endswith(".wav") else OUT
    for nm, x in (("fx", mix), ("music", music), ("amb", amb_d), ("vo", np.repeat(VO[:, None], 2, 1))):
        write_wav(f"{base}_{nm}.wav", x)
out *= np.clip((END - tt_) / 1.2, 0, 1)[:, None].astype(np.float32)          # master fade over the last 1.2 s
pre_peak = todb(np.abs(out).max())
out, mg = tp_limit(out)
write_wav(OUT, out)

# ------------------------------------------------------------ credits (spec §5.1)
lines = ["# Episode 4 sound effects", "", "All from Freesound under CC0 (public domain). Voice: ElevenLabs (Sekou).", ""]
for key in USE:
    s = MAN[key]
    if s.get("title") and s.get("author"):
        lines.append(f"- {s['title']} by {s['author']} ({s['page']})")
    else:
        lines.append(f"- Freesound sound {s['id']}, typewriter keystrokes: title, author and licence to confirm on the page ({s['page']})")
lines += ["", "Music: \"Jamal\" (assets/audio/ref_jamal.mp3), the owner's reference track. Licence unknown: confirm before public posting.", ""]
open(os.path.join(ROOT, "assets", "sfx", "credits.md"), "w").write("\n".join(lines))

# ------------------------------------------------------------ report
def win(x, a, b): return x[int(a * SR): int(b * SR)]
vo_pk = true_peak_ps(vo)
res = vo.astype(np.float64) - vo_pre
vmask = _voiced[: len(vo)]
print(f"voice: voiced RMS {todb(rms(vo[vmask])):.2f} dBFS, compressor max GR {comp_gr.max():.2f} dB "
      f"(99.9th pct {np.percentile(comp_gr, 99.9):.2f}), true peak {todb(vo_pk.max()):.2f} dBTP")
print(f"voice limiter: {np.sum(vo_g < 0.999)} samples < -0.01 dB, {100 * np.mean(vo_g < db(-1)):.4f} % > 1 dB GR, "
      f"max GR {-todb(vo_g.min()):.2f} dB; limiter residual {todb(rms(res[vmask])):.1f} dBFS "
      f"= {todb(rms(vo_pre[vmask])) - todb(rms(res[vmask])):.1f} dB below the voice")
_k = len(vo) // 48 * 48; _X = vo_pre[:_k].reshape(-1, 48); _Y = vo[:_k].astype(np.float64).reshape(-1, 48)
_nl = (_Y - ((_X * _Y).sum(1) / np.maximum((_X * _X).sum(1), 1e-18))[:, None] * _X).ravel()   # minus a 1 ms block gain
print(f"voice limiter waveform error (residual after removing the 1 ms gain riding): {todb(rms(_nl[vmask[:_k]])):.1f} dBFS "
      f"= {todb(rms(vo_pre[vmask])) - todb(rms(_nl[vmask[:_k]])):.1f} dB below the voice")
print(f"voice RMS v(2)-v(2.8):{todb(rms(win(VO, v(2), v(2.8)))):.2f} dBFS")
print(f"master: pre-limiter peak {pre_peak:.2f} dBFS, true peak {todb(true_peak_ps(out).max()):.2f} dBTP, "
      f"{np.sum(mg < 0.999)} samples limited, max GR {-todb(mg.min()):.2f} dB, ~{lufs(out):.1f} LUFS integrated")
print("music / amb RMS per gap (dBFS): pre-roll " + f"{todb(rms(win(music, 0, A_OFF))):.1f} / {todb(rms(win(amb_d, 0, A_OFF))):.1f}")
for a, b in GAPS:
    print(f"  gap {a:6.2f}-{b:6.2f}: music {todb(rms(win(music, a, b))):6.1f}  amb {todb(rms(win(amb_d, a, b))):6.1f}")
print(f"  under voice v(2)-v(8) {todb(rms(win(music, v(2), v(8)))):.1f}, v(30)-v(37) {todb(rms(win(music, v(30), v(37)))):.1f}, "
      f"tail {todb(rms(win(music, v(VO_END), END - 1.2))):.1f}")
print(f"saved {OUT}: {N / SR:.2f}s, 24-bit, AMB_GONE_DIP={int(AMB_GONE_DIP)}, PRESENCE_DB={PRESENCE_DB}")
