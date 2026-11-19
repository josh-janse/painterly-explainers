# Fonts

Static TTFs for Pillow, loaded by `ep4.common.font(key, px)`. All are licensed under the
SIL Open Font License 1.1 (https://openfontlicense.org), which allows bundling and embedding.

| file | family / weight | source (npm package, file) | licence / copyright |
|---|---|---|---|
| `mono.ttf` | IBM Plex Mono 400 | `@fontsource/ibm-plex-mono@5.3.0`, `files/ibm-plex-mono-latin-400-normal.woff2` | OFL-1.1, (c) 2017 IBM Corp. |
| `mono5.ttf` | IBM Plex Mono 500 | `@fontsource/ibm-plex-mono@5.3.0`, `files/ibm-plex-mono-latin-500-normal.woff2` | OFL-1.1, (c) 2017 IBM Corp. |
| `sans.ttf` | Manrope 500 | `@fontsource/manrope@5.3.0`, `files/manrope-latin-500-normal.woff2` | OFL-1.1, (c) 2019 The Manrope Project Authors |
| `serif.ttf` | Source Serif 4 400 | `@fontsource/source-serif-4@5.3.1`, `files/source-serif-4-latin-400-normal.woff2` | OFL-1.1, (c) 2014-2021 Adobe |
| `serif_i.ttf` | Source Serif 4 400 italic | `@fontsource/source-serif-4@5.3.1`, `files/source-serif-4-latin-400-italic.woff2` | OFL-1.1, (c) 2014-2021 Adobe |
| `serif_b.ttf` | Source Serif 4 700 | `@fontsource/source-serif-4@5.3.1`, `files/source-serif-4-latin-700-normal.woff2` | OFL-1.1, (c) 2014-2021 Adobe |

These are the fontsource "latin" subsets (they include U+2026 "…" and the curly quotes/apostrophe).
(Manrope's internal style name reads "ExtraLight Medium" because fontsource instanced it from the variable
font; its OS/2 weight class is 500, which is what matters.)

## How they were made

```bash
npm pack @fontsource/ibm-plex-mono @fontsource/manrope @fontsource/source-serif-4
# untar each, then woff2 -> ttf:
pip install --break-system-packages fonttools brotli
python3 -c "from fontTools.ttLib import TTFont; f = TTFont('in.woff2'); f.flavor = None; f.save('out.ttf')"
```
