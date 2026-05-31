"""
inputs/emotion.py — background thread: webcam face -> mood -> shared state.
Uses MediaPipe face blendshapes + simple rules. Smooths over recent frames.
"""
import os
os.environ["GLOG_minloglevel"] = "3"

import threading
import time
from collections import deque, Counter

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "face_landmarker.task"
CAMERA_INDEX = 1          # your camera
SMOOTH_WINDOW = 10        # how many recent frames to vote over


def _score(blendshapes, name):
    for b in blendshapes:
        if b.category_name == name:
            return b.score
    return 0.0


def _classify(bs):
    smile     = (_score(bs, "mouthSmileLeft")  + _score(bs, "mouthSmileRight")) / 2
    frown     = (_score(bs, "mouthFrownLeft")  + _score(bs, "mouthFrownRight")) / 2
    brow_down = (_score(bs, "browDownLeft")    + _score(bs, "browDownRight"))   / 2
    jaw_open  =  _score(bs, "jawOpen")
    brow_up   =  _score(bs, "browInnerUp")

    if smile > 0.4:
        return "happy", smile
    if brow_down > 0.4:
        return "angry", brow_down
    if jaw_open > 0.4 and brow_up > 0.3:
        return "surprised", jaw_open
    if frown > 0.2:
        return "sad", frown
    return "neutral", 0.5


def run_emotion_thread(state, show_window=False, stop_event=None):
    """Loop forever (until stop_event): detect mood, write to state."""
    base = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.FaceLandmarkerOptions(
        base_options=base,
        output_face_blendshapes=True,
        num_faces=1,
        running_mode=vision.RunningMode.IMAGE,
    )
    landmarker = vision.FaceLandmarker.create_from_options(options)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print("[emotion] Could not open camera index", CAMERA_INDEX)
        return

    recent = deque(maxlen=SMOOTH_WINDOW)

    while stop_event is None or not stop_event.is_set():
        ok, frame = cap.read()
        if not ok:
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)

        if result.face_blendshapes:
            emotion, conf = _classify(result.face_blendshapes[0])
            recent.append(emotion)
            # majority vote over the recent window = stable mood
            voted = Counter(recent).most_common(1)[0][0]
            state.set_mood(voted, conf)

            if show_window:
                cv2.putText(frame, "%s (%.2f)" % (voted, conf), (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        if show_window:
            cv2.imshow("emotion (q to quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                if stop_event:
                    stop_event.set()
                break

        time.sleep(0.03)  # ~30 fps cap

    cap.release()
    if show_window:
        cv2.destroyAllWindows()
