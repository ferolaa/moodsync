"""
main.py — MoodSync: ONE song morphs flavor in place as mood changes.

The current song keeps playing; when mood flips between calm/hype flavors,
the SAME song reloads in the new flavor and resumes near the same position.
Song only changes on swipe (next). Variants from make_variants.py.
Run:  python main.py
"""
import os
import time
import random
import threading
from collections import deque

import cv2
import numpy as np
import pygame

from state import SharedState
from camera import Camera
from inputs.emotion import run_emotion_thread
from inputs.gestures import run_gesture_thread

MUSIC_DIR = "music"
VARIANT_DIR = "variants"
EXTS = (".mp3", ".wav", ".ogg")
FLAVOR_HOLD = 2.0     # mood must hold this long before flavor morphs
FPS = 30

W, H = 980, 620
BG = (18, 18, 24)
FG = (235, 235, 245)
DIM = (120, 120, 140)
MOOD_COLORS = {
    "happy": (255, 205, 60), "sad": (90, 130, 230), "angry": (230, 70, 70),
    "surprised": (200, 120, 230), "neutral": (130, 140, 160),
}
VIDEO_W, VIDEO_H = 360, 270

PLAYLIST = "chill"     # the single playlist we morph within

# each mood maps to a flavor; "neutral" -> original (no variant file)
MOOD_TO_FLAVOR = {
    "happy": "happy",
    "sad": "sad",
    "angry": "angry",
    "surprised": "surprised",
    "neutral": "neutral",
}


def flavor_for_mood(mood):
    return MOOD_TO_FLAVOR.get(mood, "neutral")


def list_songs():
    d = os.path.join(MUSIC_DIR, PLAYLIST)
    if not os.path.isdir(d):
        return []
    return [f for f in sorted(os.listdir(d)) if f.lower().endswith(EXTS)]


def resolve(song_filename, flavor):
    """Path to the flavored variant of a song, or the original if missing."""
    stem = os.path.splitext(song_filename)[0]
    cand = os.path.join(VARIANT_DIR, PLAYLIST, stem + "__" + flavor + ".mp3")
    if os.path.isfile(cand):
        return cand
    return os.path.join(MUSIC_DIR, PLAYLIST, song_filename)


class Player:
    """Tracks the current song, its flavor, and playback position."""
    def __init__(self, state):
        self.state = state
        self.songs = list_songs()
        self.idx = 0
        self.flavor = "calm"
        self.song = self.songs[0] if self.songs else None
        self.base_offset = 0.0      # position we started this segment at
        self.segment_start = 0.0    # wall-clock when this segment began

    def elapsed(self):
        return self.base_offset + (time.time() - self.segment_start)

    def _start(self, at_seconds):
        path = resolve(self.song, self.flavor)
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.state.snapshot().volume)
            pygame.mixer.music.play(start=max(0.0, at_seconds))
        except Exception:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            at_seconds = 0.0
        self.base_offset = at_seconds
        self.segment_start = time.time()
        tag = self.song + "  [" + self.flavor + "]"
        self.state.update(is_playing=True, current_track=tag, current_playlist=PLAYLIST)

    def play_current(self):
        if not self.song:
            return
        self._start(0.0)

    def morph_to(self, new_flavor):
        """Same song, new flavor, resume near current position."""
        pos = self.elapsed()
        self.flavor = new_flavor
        self._start(pos)

    def next_song(self):
        if not self.songs:
            return
        self.idx = (self.idx + 1) % len(self.songs)
        self.song = self.songs[self.idx]
        self._start(0.0)


def frame_to_surface(frame):
    frame = cv2.resize(frame, (VIDEO_W, VIDEO_H))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)
    return pygame.surfarray.make_surface(frame)


def main():
    state = SharedState()
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("MoodSync")
    clock = pygame.time.Clock()
    f_big = pygame.font.SysFont("Helvetica", 60, bold=True)
    f_med = pygame.font.SysFont("Helvetica", 26)
    f_sm = pygame.font.SysFont("Helvetica", 18)

    camera = Camera().start()
    stop = threading.Event()
    threading.Thread(target=run_emotion_thread,
                     kwargs={"state": state, "camera": camera, "stop_event": stop},
                     daemon=True).start()
    threading.Thread(target=run_gesture_thread,
                     kwargs={"state": state, "camera": camera, "stop_event": stop},
                     daemon=True).start()

    player = Player(state)
    player.play_current()

    last_g = 0.0
    want_flavor = None
    want_since = None
    mood_history = deque(maxlen=130)
    last_sample = 0.0
    paused = False

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            s = state.snapshot()
            pygame.mixer.music.set_volume(s.volume)

            # gestures
            if s.gesture_updated_at > last_g:
                last_g = s.gesture_updated_at
                g = s.last_gesture
                if g in ("swipe_left", "swipe_right"):
                    player.next_song(); paused = False
                elif g == "palm_closed":
                    pygame.mixer.music.pause(); state.update(is_playing=False); paused = True
                elif g == "palm_open":
                    pygame.mixer.music.unpause(); state.update(is_playing=True); paused = False

            # morph flavor when mood's desired flavor holds long enough
            desired = flavor_for_mood(s.mood)
            if not paused and desired != player.flavor:
                if want_flavor != desired:
                    want_flavor = desired
                    want_since = time.time()
                elif time.time() - want_since >= FLAVOR_HOLD:
                    player.morph_to(desired)
                    want_flavor = None
                    want_since = None
            else:
                want_flavor = None
                want_since = None

            if time.time() - last_sample > 0.5:
                mood_history.append(s.mood)
                last_sample = time.time()

            # draw
            screen.fill(BG)
            mood_color = MOOD_COLORS.get(s.mood, DIM)
            screen.blit(f_sm.render("MOOD", True, DIM), (40, 30))
            screen.blit(f_big.render(s.mood.upper(), True, mood_color), (40, 48))

            screen.blit(f_sm.render("NOW PLAYING", True, DIM), (40, 140))
            screen.blit(f_med.render(s.current_track or "(nothing)", True, FG), (40, 162))
            screen.blit(f_sm.render("flavor: " + player.flavor, True, DIM), (40, 196))

            status = "PLAYING" if s.is_playing else "PAUSED"
            screen.blit(f_med.render(status, True, FG), (40, 232))
            screen.blit(f_sm.render("last gesture: " + (s.last_gesture or "-"), True, DIM), (40, 266))

            screen.blit(f_sm.render("VOLUME", True, DIM), (40, 304))
            pygame.draw.rect(screen, (45, 45, 55), (40, 328, 480, 22), border_radius=11)
            pygame.draw.rect(screen, mood_color, (40, 328, int(480 * s.volume), 22), border_radius=11)
            screen.blit(f_sm.render("%d%%" % int(s.volume * 100), True, FG), (532, 327))

            screen.blit(f_sm.render("MOOD TIMELINE", True, DIM), (40, 380))
            for i, m in enumerate(mood_history):
                c = MOOD_COLORS.get(m, DIM)
                pygame.draw.rect(screen, c, (40 + i * 5, 415, 4, 55))

            frame = camera.read()
            vx, vy = W - VIDEO_W - 40, 40
            if frame is not None:
                screen.blit(frame_to_surface(frame), (vx, vy))
            pygame.draw.rect(screen, DIM, (vx, vy, VIDEO_W, VIDEO_H), 2)
            screen.blit(f_sm.render("CAMERA", True, DIM), (vx, vy - 24))

            screen.blit(f_sm.render("close window or Ctrl+C to quit", True, DIM), (40, H - 28))
            pygame.display.flip()
            clock.tick(FPS)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        camera.stop()
        pygame.mixer.music.stop()
        pygame.quit()
        time.sleep(0.3)


if __name__ == "__main__":
    main()
