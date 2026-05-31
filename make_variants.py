"""
make_variants.py — run ONCE to pre-render mood-flavored song versions.

For each song in music/<playlist>/, creates flavored versions in
variants/<playlist>/:  <song>__happy.mp3, __sad.mp3, __angry.mp3, __surprised.mp3
(neutral uses the untouched original, so no file is made for it.)
Run:  python make_variants.py
"""
import os
from pydub import AudioSegment

MUSIC_DIR = "music"
OUT_DIR = "variants"
EXTS = (".mp3", ".wav", ".ogg")


def _speed(seg, factor):
    new_rate = int(seg.frame_rate * factor)
    shifted = seg._spawn(seg.raw_data, overrides={"frame_rate": new_rate})
    return shifted.set_frame_rate(seg.frame_rate)


def make_happy(seg):
    # bright and bouncy: a touch faster, gentle volume lift
    seg = _speed(seg, 1.04)
    seg = seg + 1
    return seg


def make_sad(seg):
    # slow, muffled, quieter
    seg = seg - 5
    seg = seg.low_pass_filter(2500)
    seg = _speed(seg, 0.93)
    return seg


def make_angry(seg):
    # aggressive: bass boost + overall push (kept subtle to avoid nasty distortion)
    boosted = seg.low_pass_filter(150).apply_gain(7)
    seg = seg.overlay(boosted)
    seg = seg + 2
    return seg


def make_surprised(seg):
    # sharp and lively: faster, brighter (cut some low end so highs pop)
    seg = _speed(seg, 1.06)
    seg = seg.high_pass_filter(200)
    seg = seg + 1
    return seg


FLAVORS = {
    "happy": make_happy,
    "sad": make_sad,
    "angry": make_angry,
    "surprised": make_surprised,
}


def main():
    if not os.path.isdir(MUSIC_DIR):
        print("No music/ folder found.")
        return
    made = 0
    for playlist in sorted(os.listdir(MUSIC_DIR)):
        src_dir = os.path.join(MUSIC_DIR, playlist)
        if not os.path.isdir(src_dir):
            continue
        out_dir = os.path.join(OUT_DIR, playlist)
        os.makedirs(out_dir, exist_ok=True)
        for fname in sorted(os.listdir(src_dir)):
            if not fname.lower().endswith(EXTS):
                continue
            path = os.path.join(src_dir, fname)
            stem = os.path.splitext(fname)[0]
            print("Processing:", path)
            try:
                seg = AudioSegment.from_file(path)
            except Exception as e:
                print("  ! could not read:", e)
                continue
            for flavor, fn in FLAVORS.items():
                out = os.path.join(out_dir, stem + "__" + flavor + ".mp3")
                fn(seg).export(out, format="mp3")
                print("  ->", flavor, ":", out)
                made += 1
    print("\nDone. Created %d variant files in %s/." % (made, OUT_DIR))


if __name__ == "__main__":
    main()
