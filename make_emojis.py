"""
make_emojis.py — generate emoji PNGs from the macOS color emoji font.
Creates emojis/happy.png, sad.png, surprised.png, neutral.png (transparent).
Run:  python make_emojis.py
"""
import os
from PIL import Image, ImageFont, ImageDraw

OUT = "emojis"
SIZE = 120
FONT_PATH = "/System/Library/Fonts/Apple Color Emoji.ttc"

EMOJI = {
    "happy":     "\U0001F600",
    "sad":       "\U0001F622",
    "surprised": "\U0001F632",
    "neutral":   "\U0001F610",
}


def load_font():
    """Apple Color Emoji only allows specific sizes; try the known good ones."""
    for px in (160, 96, 137, 109, 128):
        try:
            return ImageFont.truetype(FONT_PATH, px)
        except Exception:
            continue
    return None


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(FONT_PATH):
        print("Emoji font not found at", FONT_PATH)
        return
    font = load_font()
    if font is None:
        print("Could not load Apple Color Emoji at any size.")
        return

    for name, ch in EMOJI.items():
        img = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        try:
            draw.text((10, 10), ch, font=font, embedded_color=True)
        except Exception as e:
            print("draw failed for", name, ":", e)
            continue
        # crop to content, then resize to a clean square
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        img = img.resize((SIZE, SIZE), Image.LANCZOS)
        path = os.path.join(OUT, name + ".png")
        img.save(path)
        print("saved", path)
    print("Done.")


if __name__ == "__main__":
    main()
