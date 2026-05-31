"""
gesture_test.py — MediaPipe Hands, live gesture read from webcam.
Shows: extended-finger count, open/closed, hand height. Press q to quit.
"""
import os
os.environ["GLOG_minloglevel"] = "3"

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base = python.BaseOptions(model_asset_path="hand_landmarker.task")
options = vision.HandLandmarkerOptions(
    base_options=base,
    num_hands=1,
    running_mode=vision.RunningMode.IMAGE,
)
landmarker = vision.HandLandmarker.create_from_options(options)

# landmark indices
TIPS = {"index": 8, "middle": 12, "ring": 16, "pinky": 20}
PIPS = {"index": 6, "middle": 10, "ring": 14, "pinky": 18}
WRIST = 0


def count_extended(lm):
    """How many of the 4 fingers are extended (tip above pip)."""
    n = 0
    for f in TIPS:
        if lm[TIPS[f]].y < lm[PIPS[f]].y:   # up = smaller y
            n += 1
    return n


cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("Could not open camera index 1.")
    raise SystemExit

print("Camera open. Show your hand! Press q to quit.")
while True:
    ok, frame = cap.read()
    if not ok:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect(mp_image)

    if result.hand_landmarks:
        lm = result.hand_landmarks[0]
        fingers = count_extended(lm)
        state = "OPEN palm" if fingers >= 3 else "CLOSED fist"
        height = 1.0 - lm[WRIST].y    # 0 (bottom) .. 1 (top)
        text = state + "  fingers=" + str(fingers) + "  height=" + ("%.2f" % height)
        color = (0, 255, 0)
    else:
        text, color = "no hand", (0, 0, 255)

    cv2.putText(frame, text, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.imshow("Gesture test (press q to quit)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
