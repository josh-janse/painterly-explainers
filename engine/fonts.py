# Label font for sketches, guides and study sheets: the first sans font found on this machine, else Pillow's built-in one.
from PIL import ImageFont

_CANDIDATES = ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",          # Linux
               "/System/Library/Fonts/Supplemental/Arial.ttf",             # macOS
               "/System/Library/Fonts/Helvetica.ttc",
               "/Library/Fonts/Arial.ttf",
               "C:/Windows/Fonts/arial.ttf",                               # Windows
               "DejaVuSans.ttf"]                                           # anywhere on Pillow's font path

def label_font(size):
    size = int(size)
    for path in _CANDIDATES:
        try: return ImageFont.truetype(path, size)
        except OSError: continue
    return ImageFont.load_default(size=size)
