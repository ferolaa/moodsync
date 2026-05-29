"""
state.py  —  MoodSync Day 1, Task 2  (THE CONTRACT)

This is the single most important file in the project. Both teammates code
against it. The input threads (emotion / gesture / voice) only WRITE to it.
The main loop only READS from it. That read/write split IS your multimodal
fusion layer.

Rules everyone agrees to:
  * Input threads call state.update(...) or the set_* helpers. They never read.
  * The main loop calls state.snapshot() once per frame, then reads the copy.
  * Never read individual fields off the live object from outside — always
    snapshot first, so you act on a consistent picture.

Run this file directly to see a tiny demo of a writer thread + reader loop:
    python state.py
"""

from dataclasses import dataclass, replace
import threading
import time


# ----- Allowed values (keep these tight; they double as documentation) -----
MOODS = ("happy", "sad", "angry", "neutral")
GESTURES = ("swipe_left", "swipe_right", "palm_open", "palm_closed", "")
VOICE_COMMANDS = ("play", "pause", "next", "relax", "energy", "")
PLAYLISTS = ("calm", "upbeat", "focus")


@dataclass
class AppState:
    # --- Perception: written by the input threads ---
    mood: str = "neutral"          # one of MOODS
    mood_confidence: float = 0.0   # 0.0 - 1.0
    mood_updated_at: float = 0.0   # time.time() when last set

    last_gesture: str = ""         # one of GESTURES
    gesture_updated_at: float = 0.0

    last_voice_command: str = ""   # one of VOICE_COMMANDS
    voice_updated_at: float = 0.0

    movement_level: float = 0.0    # optional: 0.0 (still) - 1.0 (very active)

    # --- Player: written by the main loop / audio module ---
    volume: float = 0.6            # 0.0 - 1.0
    is_playing: bool = False
    current_track: str = ""        # file name currently playing
    current_playlist: str = "calm" # one of PLAYLISTS

    # --- Fusion bookkeeping (Day 5 uses this) ---
    last_manual_command_at: float = 0.0  # set when voice/gesture overrides mood


class SharedState:
    """Thread-safe wrapper around AppState."""

    def __init__(self):
        self._state = AppState()
        self._lock = threading.Lock()

    def update(self, **kwargs):
        """Generic write. Pass any AppState field(s): update(volume=0.8)."""
        with self._lock:
            for key, value in kwargs.items():
                if not hasattr(self._state, key):
                    raise AttributeError(f"AppState has no field '{key}'")
                setattr(self._state, key, value)

    def snapshot(self) -> AppState:
        """Return a consistent frozen copy. The main loop calls this each frame."""
        with self._lock:
            return replace(self._state)

    # ----- Convenience writers for the input threads (auto-timestamp) -----
    def set_mood(self, mood: str, confidence: float):
        self.update(mood=mood, mood_confidence=confidence,
                    mood_updated_at=time.time())

    def set_gesture(self, gesture: str):
        self.update(last_gesture=gesture, gesture_updated_at=time.time(),
                    last_manual_command_at=time.time())

    def set_voice(self, command: str):
        self.update(last_voice_command=command, voice_updated_at=time.time(),
                    last_manual_command_at=time.time())


# ----- Demo: a writer thread feeding a reader loop (delete in real project) -----
if __name__ == "__main__":
    state = SharedState()

    def fake_emotion_thread():
        for mood in ("neutral", "sad", "sad", "happy"):
            state.set_mood(mood, confidence=0.75)
            time.sleep(0.5)

    threading.Thread(target=fake_emotion_thread, daemon=True).start()

    print("Reader loop (Ctrl+C to stop):")
    for _ in range(10):
        s = state.snapshot()
        print(f"  mood={s.mood:8s} conf={s.mood_confidence:.2f} "
              f"playlist={s.current_playlist} vol={s.volume:.1f}")
        time.sleep(0.25)
