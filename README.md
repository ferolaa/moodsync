# MoodSync — A Multimodal Emotion-Aware Music Player

MoodSync is a music player that reacts to **your face and your hands**. It watches
you through the webcam, figures out your mood and your hand gestures, and changes
the music to match — no keyboard or mouse needed.

It was built for a Multimodal Interaction course.

---

## What it does

**Your face picks the music.**
The webcam reads your facial expression and sorts it into one of four moods:

- 😀 happy  → plays the *happy* playlist
- 😢 sad    → plays the *sad* playlist
- 😮 surprised → plays the *hype* playlist
- 😐 neutral → plays the *chill* playlist

When you change your expression, the music changes to fit. Switching *into* a mood
is quick (about 1 second). Going *back to neutral* is a little slower (about 2
seconds) so the music doesn't jump around every time your face relaxes for a moment.

**Your hand controls the player.**
The webcam also tracks one hand:

- Move your hand **up/down** → turns the volume up/down
- **Open palm** → play
- **Closed fist** → pause
- **Swipe** left or right → next song

If you use a hand gesture, the app stops auto-changing the music for a few seconds,
so your manual choice isn't immediately overridden by your mood. (This is the
"fusion" rule — your direct command wins over the automatic behavior.)

**A live dashboard shows everything.**
A window displays your current mood (in big colored text), the song playing, a
volume bar, your last gesture, a timeline of your moods over time, the live camera
feed, and an emoji that matches your mood.

---

## How it works (the simple version)

Three things run at the same time:

1. An **emotion reader** watches the camera and writes your mood down.
2. A **gesture reader** watches the camera and writes your hand actions down.
3. The **main program** reads what those two wrote and changes the music + draws
   the dashboard.

They all share **one camera** and **one shared notebook** (called the "state").
The readers only *write* to the notebook; the main program only *reads* from it.
This keeps everything simple and avoids conflicts.

It uses **MediaPipe** (Google's free vision tool) to read the face and hands —
no internet, no training, no AI servers. The mood is decided by simple rules
(big smile = happy, etc.).

---

## What's in the project

```
moodsync/
├── main.py              The app. Run this.
├── state.py             The shared "notebook" all parts read/write.
├── fusion.py            The rule that maps a mood to a playlist.
├── camera.py            Reads the webcam once, shares frames with everyone.
├── inputs/
│   ├── emotion.py       Watches your face, writes your mood.
│   └── gestures.py      Watches your hand, writes volume + gestures.
├── check_setup.py       Tests that your webcam, mic, and speakers work.
├── make_emojis.py       Makes the emoji images (run once).
├── emojis/              The emoji pictures (happy/sad/surprised/neutral).
├── music/               Your songs, in mood folders (see below).
│   ├── happy/   sad/   chill/   hype/
├── face_landmarker.task The face model (downloaded, see setup).
├── hand_landmarker.task The hand model (downloaded, see setup).
└── requirements.txt     The list of libraries needed.
```

---

## Setup (step by step)

You need a Mac with a webcam. These steps assume you're starting fresh.

**1. Use Python 3.11.**
Newer Python versions don't work well with the vision libraries. If you have
[Homebrew](https://brew.sh):

```bash
brew install python@3.11
```

**2. Get the code and make a clean environment.**

```bash
cd moodsync
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate
```

Your terminal line should now start with `(venv)`.

**3. Install the libraries.**

```bash
pip install -r requirements.txt
```

**4. Download the two MediaPipe model files** (put them in the project folder):

```bash
curl -o face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
curl -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
```

**5. Make the emoji pictures** (one time):

```bash
python make_emojis.py
```

**6. Add your music.**
Put a few song files (`.mp3`) into each mood folder:

```
music/happy/    music/sad/    music/chill/    music/hype/
```

**7. (Optional) Check your hardware works:**

```bash
python check_setup.py
```

---

## Running it

```bash
source venv/bin/activate   # if not already active
python main.py
```

A window opens. Make faces and use your hand. Close the window (or press Ctrl+C
in the terminal) to stop.

**Note on the camera:** this project opens camera number **1**. If you see no
video, your webcam might be camera **0** instead. Change `CAMERA_INDEX = 1` to
`CAMERA_INDEX = 0` in `camera.py`.

---

## Libraries used

- **mediapipe** — reads the face and hands from the camera
- **opencv** — handles the webcam and images
- **pygame** — plays the music and draws the dashboard
- **pillow** — makes the emoji images
- **numpy** / **sounddevice** — helpers for images and the hardware check

(Install all of them with `pip install -r requirements.txt`.)

---

## Key terms (for the report)

- **Affective computing** — technology that responds to human emotion.
- **Multimodal interaction** — using more than one input channel (here: face + hands).
- **Multimodal fusion** — combining those inputs into one decision (our rule that
  a hand gesture overrides the mood-based music choice).
- **Adaptive interface** — a system that changes its behavior based on the user
  (the music adapting to your mood).

---

## Known limits

- Emotion is detected by simple rules from face shape, not a trained emotion model,
  so it works best with clear expressions and good lighting.
- *Angry* was removed because it was hard to detect reliably; the app uses four
  moods (happy, sad, surprised, neutral).
- The music swaps songs to match the mood; it does not change the audio of a single
  song in real time.
