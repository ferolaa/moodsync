"""
inputs/gestures.py — hand gestures reading from a shared Camera.
Writes volume (continuous) + gesture events to shared state.
"""
import os
os.environ["GLOG_minloglevel"] = "3"

import time
from collections import deque

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

MODEL_PATH = "hand_landmarker.task"
SWIPE_COOLDOWN = 1.0
SWIPE_MIN_DX = 0.2

TIPS = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}
PIPS = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}
WRIST = 0


def _count_extended(lm):
    n = 0
    for f in TIPS:
        if lm[TIPS[f]].y < lm[PIPS[f]].y:
            n += 1
    return n


def _check_thumbs(lm):
    if _count_extended(lm) > 0:
        return None
    
    t_tip = lm[4].y
    t_ip = lm[3].y
    t_mcp = lm[2].y
    
    if t_tip < t_ip and t_ip < t_mcp and (t_mcp - t_tip) > 0.05:
        return "up"
    if t_tip > t_ip and t_ip > t_mcp and (t_tip - t_mcp) > 0.05:
        return "down"
    return None


def run_gesture_thread(state, camera, stop_event=None):
    base = python.BaseOptions(model_asset_path=MODEL_PATH)
    options = vision.HandLandmarkerOptions(
        base_options=base, num_hands=1,
        running_mode=vision.RunningMode.IMAGE)
    landmarker = vision.HandLandmarker.create_from_options(options)

    prev_open = None
    open_history = deque(maxlen=5)
    last_swipe_time = 0.0
    x_history = deque(maxlen=15)

    while stop_event is None or not stop_event.is_set():
        frame = camera.read()
        if frame is None:
            time.sleep(0.03)
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = landmarker.detect(mp_image)

        if result.hand_landmarks:
            lm = result.hand_landmarks[0]
            height = 1.0 - lm[WRIST].y
            vol = max(0.0, min(1.0, height))
            state.update(volume=round(vol, 2))

            thumb_state = _check_thumbs(lm)
            if thumb_state == "up":
                state.set_face_tracking(False)
            elif thumb_state == "down":
                state.set_face_tracking(True)

            if thumb_state is not None:
                current_state = "thumb"
            else:
                current_state = True if _count_extended(lm) >= 3 else False
                
            open_history.append(current_state)
            
            if len(open_history) == open_history.maxlen:
                if all(s == True for s in open_history):
                    current_stable = True
                elif all(s == False for s in open_history):
                    current_stable = False
                elif all(s == "thumb" for s in open_history):
                    current_stable = "thumb"
                else:
                    current_stable = prev_open

                if prev_open is not None and current_stable != prev_open:
                    if current_stable == True:
                        state.set_gesture("palm_open")
                    elif current_stable == False:
                        state.set_gesture("palm_closed")
                
                if current_stable is not None:
                    prev_open = current_stable

            x_history.append(lm[WRIST].x)
            if len(x_history) >= 5:
                dx = x_history[-1] - x_history[0]
                now = time.time()
                if abs(dx) > SWIPE_MIN_DX and now - last_swipe_time > SWIPE_COOLDOWN:
                    state.set_gesture("swipe_right" if dx > 0 else "swipe_left")
                    last_swipe_time = now
                    x_history.clear()
        else:
            if len(x_history) >= 5:
                dx = x_history[-1] - x_history[0]
                now = time.time()
                if abs(dx) > SWIPE_MIN_DX and now - last_swipe_time > SWIPE_COOLDOWN:
                    state.set_gesture("swipe_right" if dx > 0 else "swipe_left")
                    last_swipe_time = now
            prev_open = None
            open_history.clear()
            x_history.clear()
        time.sleep(0.03)
