"""
check_setup.py  —  MoodSync Day 1, Task 1

Confirms the demo laptop's webcam, microphone, and speakers all work,
and that pygame's audio mixer initializes. Run this on the ACTUAL machine
you'll demo on.

    python check_setup.py

Each check prints PASS or FAIL. Get four PASSes before moving on.
"""

import sys
import time

results = {}


def check_webcam():
    """Open camera 0, grab a frame, show it for ~2 seconds."""
    try:
        import cv2
    except ImportError:
        print("  [FAIL] opencv-python not installed  ->  pip install opencv-python")
        return False

    cap = cv2.VideoCapture(0)  # try 1 or 2 here if you have multiple cameras
    if not cap.isOpened():
        print("  [FAIL] Could not open the webcam (is another app using it?)")
        return False

    # Macs often return empty frames for the first moment while the camera
    # wakes up. Give it a few tries before giving up.
    frame = None
    for _ in range(30):
        ok, frame = cap.read()
        if ok and frame is not None:
            break
        time.sleep(0.1)
    else:
        print("  [FAIL] Camera opened but never returned a frame")
        cap.release()
        return False

    print("  Showing webcam for 2s — you should see yourself. Press any key to skip.")
    end = time.time() + 2
    while time.time() < end:
        ok, frame = cap.read()
        if ok:
            cv2.imshow("Webcam check (press any key)", frame)
        if cv2.waitKey(1) != -1:
            break
    cap.release()
    cv2.destroyAllWindows()
    print(f"  [PASS] Webcam works — frame size {frame.shape[1]}x{frame.shape[0]}")
    return True


def check_microphone():
    """Record 2 seconds and report the input level."""
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print("  [FAIL] sounddevice/numpy not installed  ->  pip install sounddevice numpy")
        return False

    fs = 44100
    print("  Recording 2s — please SPEAK into the mic now...")
    try:
        rec = sd.rec(int(2 * fs), samplerate=fs, channels=1)
        sd.wait()
    except Exception as e:
        print(f"  [FAIL] Could not record: {e}")
        return False

    level = float(np.abs(rec).mean())
    print(f"  Measured input level: {level:.5f}")
    if level < 0.0005:
        print("  [FAIL] Almost no signal — wrong input device, muted, or no permission")
        return False
    print("  [PASS] Microphone is picking up sound")
    return True


def check_speakers():
    """Play a short 440 Hz beep so you can confirm you hear it."""
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print("  [FAIL] sounddevice/numpy not installed")
        return False

    fs = 44100
    t = np.linspace(0, 1.0, int(fs * 1.0), endpoint=False)
    tone = 0.3 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
    print("  Playing a 1s beep — confirm you HEAR it...")
    try:
        sd.play(tone, fs)
        sd.wait()
    except Exception as e:
        print(f"  [FAIL] Could not play audio: {e}")
        return False

    answer = input("  Did you hear the beep? [y/n]: ").strip().lower()
    if answer.startswith("y"):
        print("  [PASS] Speakers work")
        return True
    print("  [FAIL] No sound — check output device / volume")
    return False


def check_pygame_mixer():
    """The real music player uses pygame.mixer — confirm it initializes."""
    try:
        import pygame
    except ImportError:
        print("  [FAIL] pygame not installed  ->  pip install pygame")
        return False
    try:
        pygame.mixer.init()
        pygame.mixer.quit()
    except Exception as e:
        print(f"  [FAIL] pygame.mixer would not start: {e}")
        return False
    print("  [PASS] pygame audio mixer initializes")
    return True


if __name__ == "__main__":
    print("\n=== MoodSync setup check ===")
    print(f"Python {sys.version.split()[0]}  (3.11 or 3.10 recommended)\n")

    print("[1/4] Webcam");      results["webcam"] = check_webcam();        print()
    print("[2/4] Microphone");  results["mic"] = check_microphone();       print()
    print("[3/4] Speakers");    results["speakers"] = check_speakers();    print()
    print("[4/4] pygame mixer");results["mixer"] = check_pygame_mixer();   print()

    print("=== Summary ===")
    for name, ok in results.items():
        print(f"  {name:10s}: {'PASS' if ok else 'FAIL'}")
    if all(results.values()):
        print("\nAll good — hardware is ready. Move on to the State object.\n")
    else:
        print("\nFix the FAILs above before continuing.\n")
