# Short: Claude animation skill

A 9:16 Short, about 47 seconds, on how Episode 4 was made, in six steps. Claude makes steps 1 and 3 to 6 from the
project's own files. Josh films the hook and the ending (phone at the monitor) and decides what step 2 shows.

| Beat | Length | Made by | From |
|---|---|---|---|
| Hook | 4 s | Josh | Episode 4 on the monitor |
| Step 1 · study | 6 s | `beat_study.py` | The swatch book, recorded scrolling at 9:16 |
| Step 2 · story | 7 s | Josh | To decide |
| Step 3 · rough cut | 5 s | `beat_rough.py` | `docs/ref/canvas_v6` test frames, then the reel blockouts |
| Step 4 · paint | 6 s | `beat_paint.py` | The 9:16 dusk plate, one snapshot per painting pass |
| Step 5 · notes | 8 s | `beat_notes.py` | Four of Josh's notes, word for word, on the plates they changed |
| Step 6 · sound | 5 s | `beat_sound.py` | Episode 4's voice, effects and sea stems |
| Ending | 6 s | Josh | Episode 4 on the monitor |

## Build

```bash
SWATCH_HTML=/path/to/swatch-book.html ./build.sh
```

Everything lands in `out/` (gitignored). `prep.py` gets the plates and stems from Episode 4 without editing any ep4
file. `assemble.py` joins the beats with placeholders for Josh's parts and burns the current voice-over lines in at
the bottom, for timing only.

The swatch book isn't in the repo because this repo is public. Save it from its artifact as HTML and point
`SWATCH_HTML` at it.

## Open

- Music: Episode 4's reference track can't go in a public Short until its licence is known. The stems here are built
  without it.
- Voice-over: Josh records it in ElevenLabs once the hook and ending lines are settled.
