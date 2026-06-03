"""
inputs/emotion.py — emotion detection reading from a shared Camera.
Detects: happy / sad / surprised / neutral. (Angry removed — unreliable.)
"""
import os
os.environ["GLOG_minloglevel"] = "3"

import time
from collections import deque, Counter

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "face_landmarker.task"
SMOOTH_WINDOW = 10


def _score(bs, name):
    for b in bs:
        if b.category_name == name:
            return b.score
    return 0.0


def _classify(bs):
    smile = (_score(bs, "mouthSmileLeft") + _score(bs, "mouthSmileRight")) / 2
    frown = (_score(bs, "mouthFrownLeft") + _score(bs, "mouthFrownRight")) / 2
    jaw_open = _score(bs, "jawOpen")
    brow_up = _score(bs, "browInnerUp")
    if smile > 0.4:
        return "happy", smile
    if jaw_open > 0.4 and brow_up > 0.3:
        return "surprised", jaw_open
    if frown > 0.2:
        return "sad", frown
    return "neutral", 0.5


def run_emotion_thread(state, camera, stop_event=None):
    base = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.FaceLandmarkerOptions(
        base_options=base, output_face_blendshapes=True,
        num_faces=1, running_mode=vision.RunningMode.IMAGE)
    landmarker = vision.FaceLandmarker.create_from_options(options)

    recent = deque(maxlen=SMOOTH_WINDOW)
    while stop_event is None or not stop_event.is_set():
        frame = camera.read()
        if frame is None:
            time.sleep(0.03)
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)
        if result.face_blendshapes:
            emotion, conf = _classify(result.face_blendshapes[0])
            recent.append(emotion)
            voted = Counter(recent).most_common(1)[0][0]
            state.set_mood(voted, conf)
        time.sleep(0.05)
