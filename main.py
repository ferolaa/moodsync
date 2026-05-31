"""
main.py — MoodSync (Day 4+): shared camera, dashboard WITH live video feed.
One Camera reads frames; emotion + gesture threads and the dashboard all use it.
Run:  python main.py    (close window or Ctrl+C to stop)
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
from fusion import playlist_for_mood
from camera import Camera
from inputs.emotion import run_emotion_thread
from inputs.gestures import run_gesture_thread

MUSIC_DIR = "music"
EXTS = (".mp3", ".wav", ".ogg")
HOLD = 3
OVERRIDE = 10
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


def list_tracks(p):
    d = os.path.join(MUSIC_DIR, p)
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(EXTS)]


def play_from(p, state):
    tr = list_tracks(p)
    if not tr:
        state.update(is_playing=False, current_track="", current_playlist=p)
        return
    t = random.choice(tr)
    pygame.mixer.music.load(t)
    pygame.mixer.music.set_volume(state.snapshot().volume)
    pygame.mixer.music.play()
    state.update(is_playing=True, current_track=os.path.basename(t), current_playlist=p)


def frame_to_surface(frame):
    """BGR numpy frame -> pygame surface, resized for the panel."""
    frame = cv2.resize(frame, (VIDEO_W, VIDEO_H))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = np.rot90(frame)            # pygame surfarray expects this orientation
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

    play_from(state.snapshot().current_playlist, state)

    ws, wp, last_g = None, None, 0.0
    mood_history = deque(maxlen=130)
    last_sample = 0.0

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            s = state.snapshot()
            pygame.mixer.music.set_volume(s.volume)

            if s.gesture_updated_at > last_g:
                last_g = s.gesture_updated_at
                g = s.last_gesture
                if g in ("swipe_left", "swipe_right"):
                    play_from(s.current_playlist, state)
                elif g == "palm_closed":
                    pygame.mixer.music.pause(); state.update(is_playing=False)
                elif g == "palm_open":
                    pygame.mixer.music.unpause(); state.update(is_playing=True)

            manual = (time.time() - s.last_manual_command_at) < OVERRIDE
            target = playlist_for_mood(s.mood)
            if not manual and target != s.current_playlist:
                if wp != target:
                    wp, ws = target, time.time()
                elif time.time() - ws >= HOLD:
                    play_from(target, state); wp, ws = None, None
            else:
                wp, ws = None, None

            if time.time() - last_sample > 0.5:
                mood_history.append(s.mood)
                last_sample = time.time()

            # ---------- draw ----------
            screen.fill(BG)
            mood_color = MOOD_COLORS.get(s.mood, DIM)

            screen.blit(f_sm.render("MOOD", True, DIM), (40, 30))
            screen.blit(f_big.render(s.mood.upper(), True, mood_color), (40, 48))

            screen.blit(f_sm.render("NOW PLAYING", True, DIM), (40, 140))
            screen.blit(f_med.render(s.current_track or "(nothing)", True, FG), (40, 162))
            screen.blit(f_sm.render("playlist: " + s.current_playlist, True, DIM), (40, 196))

            status = "PLAYING" if s.is_playing else "PAUSED"
            screen.blit(f_med.render(status, True, FG), (40, 232))
            screen.blit(f_sm.render("last gesture: " + (s.last_gesture or "-"), True, DIM), (40, 266))

            screen.blit(f_sm.render("VOLUME", True, DIM), (40, 304))
            pygame.draw.rect(screen, (45, 45, 55), (40, 328, 480, 22), border_radius=11)
            pygame.draw.rect(screen, mood_color, (40, 328, int(480 * s.volume), 22), border_radius=11)
            screen.blit(f_sm.render("%d%%" % int(s.volume * 100), True, FG), (532, 327))

            screen.blit(f_sm.render("MOOD TIMELINE", True, DIM), (40, 380))
            base_y = 470
            for i, m in enumerate(mood_history):
                c = MOOD_COLORS.get(m, DIM)
                pygame.draw.rect(screen, c, (40 + i * 5, base_y - 55, 4, 55))

            # live video panel (top-right)
            frame = camera.read()
            vx, vy = W - VIDEO_W - 40, 40
            if frame is not None:
                surf = frame_to_surface(frame)
                screen.blit(surf, (vx, vy))
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
