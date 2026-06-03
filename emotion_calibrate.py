"""
emotion_calibrate.py — shows the RAW facial scores the classifier uses,
so we can set thresholds that fit YOUR face.

Run:  python emotion_calibrate.py
Make each expression and watch the numbers. Press q to quit.
Tell Claude the values you see for SAD and ANGRY faces especially.
"""
import os
os.environ["GLOG_minloglevel"] = "3"

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base = python.BaseOptions(model_asset_path="face_landmarker.task")
options = vision.FaceLandmarkerOptions(
    base_options=base, output_face_blendshapes=True,
    num_faces=1, running_mode=vision.RunningMode.IMAGE)
landmarker = vision.FaceLandmarker.create_from_options(options)


def score(bs, name):
    for b in bs:
        if b.category_name == name:
            return b.score
    return 0.0


cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("camera 1 failed"); raise SystemExit

print("Make faces. Watch the 5 numbers. Press q to quit.\n")
while True:
    ok, frame = cap.read()
    if not ok:
        continue
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    res = landmarker.detect(img)
    if res.face_blendshapes:
        bs = res.face_blendshapes[0]
        smile = (score(bs, "mouthSmileLeft") + score(bs, "mouthSmileRight")) / 2
        frown = (score(bs, "mouthFrownLeft") + score(bs, "mouthFrownRight")) / 2
        brow_down = (score(bs, "browDownLeft") + score(bs, "browDownRight")) / 2
        jaw = score(bs, "jawOpen")
        brow_up = score(bs, "browInnerUp")
        lines = [
            "smile     %.2f" % smile,
            "frown     %.2f" % frown,
            "brow_down %.2f" % brow_down,
            "jaw_open  %.2f" % jaw,
            "brow_up   %.2f" % brow_up,
        ]
        for i, t in enumerate(lines):
            cv2.putText(frame, t, (20, 40 + i * 32),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "no face", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    cv2.imshow("calibrate (q to quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
