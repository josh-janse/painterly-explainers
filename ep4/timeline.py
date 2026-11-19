# Episode 4 timeline, taken from the voice-over's pauses. Shared by the picture (ep4_video.py) and the sound (ep4_audio2.py).
# All times in seconds. Audio times are positions in the voice file; the video starts A_OFF seconds before the voice.
A_OFF = 1.5
P = [0.0, 9.76, 16.70, 23.20, 28.69, 40.00, 48.47, 60.87]     # where each of the 8 paragraphs starts in vo2.wav (ElevenLabs, Sekou)
VO_END = 67.55
VO_FILE = "vo2.wav"
def v(a): return a + A_OFF
END = round(v(VO_END) + 3.0, 2)     # a little longer tail for the final chord

T = dict(s1=(0, v(P[1])), s2=(v(P[1]), v(P[2]) - 0.7),
         w3=(v(P[2]) - 0.7, v(P[2])), s3=(v(P[2]), v(P[3]) - 0.6),
         w4=(v(P[3]) - 0.6, v(P[3])), s4=(v(P[3]), v(P[4]) - 0.7),
         w5=(v(P[4]) - 0.7, v(P[4])), s5=(v(P[4]), v(P[5]) - 0.6),
         w6=(v(P[5]) - 0.6, v(P[5])), s6=(v(P[5]), v(P[6]) - 0.6),
         w7=(v(P[6]) - 0.6, v(P[6])), s7=(v(P[6]), v(P[7]) - 1.2),
         f8=(v(P[7]) - 1.2, v(P[7])), s8=(v(P[7]), END))

# moments inside scenes, in seconds from the scene's start, each tied to a line of the voice-over
FLY_OUT = (3.2, 2.4)        # s2: the letter leaves on "All you can do…" and lands just after "…is write"
READ_TILT = 1.6             # s3: he tips his head down on "he reads it carefully"
REPLY_TYPE = (0.6, 24.0)    # s4: reply starts typing (start, characters per second)
FORGET = 2.6                # s5: "he forgets everything": the letter leaves his head, the words start to drift
FADE_WORDS = (7.2, 9.5)    # s5: the words fade out, gone by "Gone"
Q2_TYPE = (1.5, 16.0)       # s6: the quoted letter types as it's read aloud
ANS_DOTS, ANS_TYPE = 3.9, (4.3, 14.0)   # s6: "…", then "Make what, dear?" on "he has no idea"
IT_SWEEP = 6.0              # s6: highlight on "it" as he says it
CARD0, CARD_GAP = 2.7, 1.2  # s7: letters drop in from "Every time you write"
ANS2_DOTS, ANS2_TYPE = 8.9, (9.2, 24.0) # s7: the reply, from "He reads it all again"
FLY_HOME = (0.8, 4.2)       # s8: the reply heads home
TILT = (0.6, 5.0)           # s1: the camera tilts down from the sky to the house ("…who lives far away")
LIGHT_ON = 4.2              # s1: the window lights up as the house comes into view
TITLE = (5.6, 10.6)         # s1: the episode title, after the reveal
HOLE_CLOSE = 9.3           # s5: the hole in his head closes, shut by "Gone"
ANNOT = (7.1, 7.6, 8.3)     # s7, on "He reads it all again": sweep "it", draw the arrow back to the reply, sweep "spinach omelette"
PARALLAX = 70               # s1: how much further the near plane (hill and sea) travels than the sky during the tilt, in source px
VO_GAPS = [(8.44, 9.76), (15.03, 16.70), (22.20, 23.20), (27.07, 28.69), (38.55, 40.00), (46.73, 48.47), (59.43, 60.87)]   # pauses between paragraphs in vo2.wav


# ---- helpers used by the renderer (SPEC §2.1 notes) ----
def in_(key, t):
    """True while t is inside segment T[key] (start inclusive, end exclusive)"""
    a, b = T[key]
    return a <= t < b

def frac(key, t):
    """0 at the start of T[key], 1 at its end (not clamped)"""
    a, b = T[key]
    return (t - a) / (b - a)

def local(key, t):
    """seconds since the start of T[key]"""
    return t - T[key][0]
