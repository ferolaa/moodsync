import os
os.environ["GLOG_minloglevel"] = "3"

import time
from collections import deque

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "hand_landmarker.task"
CAMERA_INDEX = 1
SWIPE_COOLDOWN = 1.0
SWIPE_MIN_DX = 0.25

TIPS = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}
PIPS = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}
WRIST = 0


def _count_extended(lm):
    n = 0
    for f in TIPS:
        if lm[TIPS[f]].y < lm[PIPS[f]].y:
            n += 1
    return n


def run_gesture_thread(state, stop_event=None):
    base = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.HandLandmarkerOptions(
        base_options=base, num_hands=1,
        running_mode=vision.RunningMode.IMAGE,
    )
    landmarker = vision.HandLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[gestures] Could not open camera index", CAMERA_INDEX)
        return

    prev_open = None
    last_swipe_time = 0.0
    x_history = deque(maxlen=6)

    while stop_event is None or not stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)

        if result.hand_landmarks:
            lm = result.hand_landmarks[0]

            height = 1.0 - lm[WRIST].y
            vol = max(0.0, min(1.0, height))
            state.update(volume=round(vol, 2))

            is_open = _count_extended(lm) >= 3
            if prev_open is not None and is_open != prev_open:
                state.set_gesture("palm_open" if is_open else "palm_closed")
            prev_open = is_open

            x_history.append(lm[WRIST].x)
            if len(x_history) == x_history.maxlen:
                dx = x_history[-1] - x_history[0]
                now = time.time()
                if abs(dx) > SWIPE_MIN_DX and now - last_swipe_time > SWIPE_COOLDOWN:
                    state.set_gesture("swipe_right" if dx > 0 else "swipe_left")
                    last_swipe_time = now
                    x_history.clear()
        else:
            prev_open = None
            x_history.clear()

        time.sleep(0.03)

    cap.release()
