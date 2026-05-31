"""
main.py — MoodSync (Day 4): live pygame dashboard + emotion + gestures + music.

The dashboard window runs on the MAIN thread (required on macOS).
Emotion and gesture detection run as background threads writing to shared state.
This loop reads state, drives the music, and draws the dashboard ~30fps.
Run:  python main.py    (close the window or Ctrl+C to stop)
"""
import os
import time
import random
import threading
from collections import deque

import pygame

from state import SharedState
from fusion import playlist_for_mood
from inputs.emotion import run_emotion_thread
from inputs.gestures import run_gesture_thread

MUSIC_DIR = "music"
EXTS = (".mp3", ".wav", ".ogg")
HOLD = 3
OVERRIDE = 10
FPS = 30

W, H = 900, 560
BG = (18, 18, 24)
FG = (235, 235, 245)
DIM = (120, 120, 140)

MOOD_COLORS = {
    "happy":     (255, 205, 60),
    "sad":       (90, 130, 230),
    "angry":     (230, 70, 70),
    "surprised": (200, 120, 230),
    "neutral":   (130, 140, 160),
}


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


def main():
    state = SharedState()
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("MoodSync")
    clock = pygame.time.Clock()
    f_big = pygame.font.SysFont("Helvetica", 64, bold=True)
    f_med = pygame.font.SysFont("Helvetica", 28)
    f_sm = pygame.font.SysFont("Helvetica", 20)

    stop = threading.Event()
    threading.Thread(target=run_emotion_thread,
                     kwargs={"state": state, "show_window": False, "stop_event": stop},
                     daemon=True).start()
    threading.Thread(target=run_gesture_thread,
                     kwargs={"state": state, "stop_event": stop},
                     daemon=True).start()

    play_from(state.snapshot().current_playlist, state)

    ws, wp, last_g = None, None, 0.0
    mood_history = deque(maxlen=120)  # for the timeline graph
    last_sample = 0.0

    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            s = state.snapshot()
            pygame.mixer.music.set_volume(s.volume)

            # handle gesture events
            if s.gesture_updated_at > last_g:
                last_g = s.gesture_updated_at
                g = s.last_gesture
                if g in ("swipe_left", "swipe_right"):
                    play_from(s.current_playlist, state)
                elif g == "palm_closed":
                    pygame.mixer.music.pause(); state.update(is_playing=False)
                elif g == "palm_open":
                    pygame.mixer.music.unpause(); state.update(is_playing=True)

            # mood-driven playlist switch
            manual = (time.time() - s.last_manual_command_at) < OVERRIDE
            target = playlist_for_mood(s.mood)
            if not manual and target != s.current_playlist:
                if wp != target:
                    wp, ws = target, time.time()
                elif time.time() - ws >= HOLD:
                    play_from(target, state); wp, ws = None, None
            else:
                wp, ws = None, None

            # sample mood for timeline (~2/sec)
            if time.time() - last_sample > 0.5:
                mood_history.append(s.mood)
                last_sample = time.time()

            # ---------- draw ----------
            screen.fill(BG)
            mood_color = MOOD_COLORS.get(s.mood, DIM)

            # mood (big)
            screen.blit(f_sm.render("MOOD", True, DIM), (40, 30))
            screen.blit(f_big.render(s.mood.upper(), True, mood_color), (40, 50))

            # current track / playlist
            screen.blit(f_sm.render("NOW PLAYING", True, DIM), (40, 150))
            track = s.current_track or "(nothing)"
            screen.blit(f_med.render(track, True, FG), (40, 172))
            screen.blit(f_sm.render("playlist: " + s.current_playlist, True, DIM), (40, 208))

            # play/pause + last gesture
            status = "PLAYING" if s.is_playing else "PAUSED"
            screen.blit(f_med.render(status, True, FG), (640, 50))
            screen.blit(f_sm.render("last gesture: " + (s.last_gesture or "-"), True, DIM), (640, 90))

            # volume bar
            screen.blit(f_sm.render("VOLUME", True, DIM), (40, 250))
            pygame.draw.rect(screen, (45, 45, 55), (40, 275, 500, 24), border_radius=12)
            pygame.draw.rect(screen, mood_color, (40, 275, int(500 * s.volume), 24), border_radius=12)
            screen.blit(f_sm.render("%d%%" % int(s.volume * 100), True, FG), (555, 274))

            # mood timeline (bottom)
            screen.blit(f_sm.render("MOOD TIMELINE", True, DIM), (40, 340))
            base_y = 480
            bar_w = 6
            for i, m in enumerate(mood_history):
                c = MOOD_COLORS.get(m, DIM)
                x = 40 + i * (bar_w + 1)
                pygame.draw.rect(screen, c, (x, base_y - 60, bar_w, 60))

            screen.blit(f_sm.render("close window or Ctrl+C to quit", True, DIM), (40, H - 30))

            pygame.display.flip()
            clock.tick(FPS)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        pygame.mixer.music.stop()
        pygame.quit()
        time.sleep(0.3)


if __name__ == "__main__":
    main()
