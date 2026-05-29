# MoodSync — A Multimodal Emotion-Aware Music Interface

A music player that adapts to the user in real time using **four input modalities**
— facial emotion, hand gestures, voice commands, and (optionally) body movement —
and responds by switching playlists, adjusting volume, and giving visual feedback.

Built for a Multimodal Interaction course as a 1-week, 2-person project.

## How it works

Independent input threads (emotion, gesture, voice) write to a single shared
state object. The main loop reads that state each frame and acts on it. That
read/write split is the multimodal fusion layer: a manual command (voice or
gesture) temporarily overrides mood-based behavior.

```
 webcam ─► emotion thread ─┐
 webcam ─► gesture thread ─┼─► SharedState ─► main loop ─► music player + dashboard
 mic    ─► voice thread   ─┘      (state.py)
```

## Setup

Use **Python 3.11 or 3.10** (newer versions may lack wheels for mediapipe / FER).

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python check_setup.py           # confirm webcam, mic, speakers all PASS
```

`requirements.txt` holds only the core libraries needed to verify hardware.
The heavier ML libraries are added as each feature is built:

- Day 2 (emotion): `pip install fer`  *(or `deepface` — pick one)*
- Day 3 (gestures): `pip install mediapipe`
- Day 4 (voice): `pip install vosk`  + download a Vosk model into `models/`

## Adding music

Audio files are **not** committed (see `.gitignore`). Each person adds their own
local files into these folders:

```
music/calm/      music/upbeat/      music/focus/
```

Drop ~5 tracks per folder. The `.gitkeep` files keep the empty folders in git.

## Repository structure

```
.
├── README.md
├── requirements.txt
├── check_setup.py        # Day 1 hardware check
├── state.py              # THE CONTRACT — shared state object
├── main.py               # main loop (Day 1+)
├── inputs/               # Person 1
│   ├── emotion.py
│   ├── gestures.py
│   └── voice.py
├── audio/                # Person 2
│   ├── player.py
│   └── playlists.py
├── ui/                   # Person 2
│   └── dashboard.py
└── music/                # local audio (gitignored)
    ├── calm/  upbeat/  focus/
```

## Work split

- **Person 1 — perception:** `inputs/` (emotion, gestures, voice). Threads that
  only *write* to `SharedState`.
- **Person 2 — interaction:** `audio/` + `ui/` + `main.py`. Reads `SharedState`
  via `snapshot()` and drives playback and the dashboard.

Working in separate folders keeps merge conflicts rare. Pull before you push.

## The one rule everyone follows

Input threads only **write** (`set_mood` / `set_gesture` / `set_voice`).
The main loop only **reads** (`snapshot()`). Never read live fields from outside
the main loop — always snapshot first.
