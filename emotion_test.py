"""
emotion_test.py — MediaPipe face -> simple emotion, live from webcam.
Rule-based: reads facial 'blendshapes' and maps them to a mood.
Run:  python emotion_test.py   — press q to quit.
"""
import os
os.environ["GLOG_minloglevel"] = "3"

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Load the face landmarker with blendshapes turned on
base = python.BaseOptions(model_asset_path="face_landmarker.task")
options = vision.FaceLandmarkerOptions(
    base_options=base,
    output_face_blendshapes=True,
    num_faces=1,
    running_mode=vision.RunningMode.IMAGE,
)
landmarker = vision.FaceLandmarker.create_from_options(options)


def score(blendshapes, name):
    for b in blendshapes:
        if b.category_name == name:
            return b.score
    return 0.0


def classify(bs):
    smile     = (score(bs, "mouthSmileLeft")  + score(bs, "mouthSmileRight"))  / 2
    frown     = (score(bs, "mouthFrownLeft")  + score(bs, "mouthFrownRight"))  / 2
    brow_down = (score(bs, "browDownLeft")    + score(bs, "browDownRight"))    / 2
    jaw_open  =  score(bs, "jawOpen")
    brow_up   =  score(bs, "browInnerUp")

    if smile > 0.4:
        return "happy", smile
    if brow_down > 0.4:
        return "angry", brow_down
    if jaw_open > 0.4 and brow_up > 0.3:
        return "surprised", jaw_open
    if frown > 0.2:
        return "sad", frown
    return "neutral", 0.5


cap = cv2.VideoCapture(1)  # your camera is on index 1
if not cap.isOpened():
    print("Could not open camera index 1 — try 0.")
    raise SystemExit

print("Camera open. Make faces! Press q to quit.")
while True:
    ok, frame = cap.read()
    if not ok:
        continue

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect(mp_image)

    if result.face_blendshapes:
        emotion, conf = classify(result.face_blendshapes[0])
        text, color = "%s (%.2f)" % (emotion, conf), (0, 255, 0)
    else:
        text, color = "no face", (0, 0, 255)

    cv2.putText(frame, text, (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)
    cv2.imshow("Emotion test (press q to quit)", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
