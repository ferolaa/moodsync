"""
state.py  —  MoodSync shared state (THE CONTRACT)

Input threads (emotion / gesture / voice) only WRITE to this.
The main loop only READS from it via snapshot(). That split is the fusion layer.
"""

from dataclasses import dataclass, replace
import threading
import time


MOODS = ("happy", "sad", "angry", "neutral")
GESTURES = ("swipe_left", "swipe_right", "palm_open", "palm_closed", "")
VOICE_COMMANDS = ("play", "pause", "next", "relax", "energy", "")
PLAYLISTS = ("happy", "sad", "chill", "hype")


@dataclass
class AppState:
    # --- Perception: written by the input threads ---
    mood: str = "neutral"
    mood_confidence: float = 0.0
    mood_updated_at: float = 0.0

    last_gesture: str = ""
    gesture_updated_at: float = 0.0

    last_voice_command: str = ""
    voice_updated_at: float = 0.0

    movement_level: float = 0.0

    # --- Player: written by the main loop / audio module ---
    volume: float = 0.6
    is_playing: bool = False
    current_track: str = ""
    current_playlist: str = "chill"

    # --- Fusion bookkeeping ---
    last_manual_command_at: float = 0.0


class SharedState:
    """Thread-safe wrapper around AppState."""

    def __init__(self):
        self._state = AppState()
        self._lock = threading.Lock()

    def update(self, **kwargs):
        with self._lock:
            for key, value in kwargs.items():
                if not hasattr(self._state, key):
                    raise AttributeError("AppState has no field '" + key + "'")
                setattr(self._state, key, value)

    def snapshot(self):
        with self._lock:
            return replace(self._state)

    def set_mood(self, mood, confidence):
        self.update(mood=mood, mood_confidence=confidence,
                    mood_updated_at=time.time())

    def set_gesture(self, gesture):
        self.update(last_gesture=gesture, gesture_updated_at=time.time(),
                    last_manual_command_at=time.time())

    def set_voice(self, command):
        self.update(last_voice_command=command, voice_updated_at=time.time(),
                    last_manual_command_at=time.time())
