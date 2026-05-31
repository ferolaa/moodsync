import os
import time
import random
import threading

import pygame

from state import SharedState
from fusion import playlist_for_mood
from inputs.emotion import run_emotion_thread

MUSIC_DIR = "music"
FRAMES_PER_SECOND = 4
AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg")
SWITCH_HOLD_SECONDS = 3


def list_tracks(playlist):
    folder = os.path.join(MUSIC_DIR, playlist)
    if not os.path.isdir(folder):
        return []
    return [os.path.join(folder, f) for f in sorted(os.listdir(folder))
            if f.lower().endswith(AUDIO_EXTENSIONS)]


def play_from(playlist, state):
    tracks = list_tracks(playlist)
    if not tracks:
        print("[!] No songs in music/" + playlist + "/ - add some.")
        state.update(is_playing=False, current_track="", current_playlist=playlist)
        return
    track = random.choice(tracks)
    pygame.mixer.music.load(track)
    pygame.mixer.music.set_volume(state.snapshot().volume)
    pygame.mixer.music.play()
    state.update(is_playing=True, current_track=os.path.basename(track),
                 current_playlist=playlist)
    print("[+] (" + playlist + ") playing: " + os.path.basename(track))


def main():
    state = SharedState()
    pygame.mixer.init()

    stop_event = threading.Event()
    t = threading.Thread(
        target=run_emotion_thread,
        kwargs={"state": state, "show_window": False, "stop_event": stop_event},
        daemon=True,
    )
    t.start()
    print("[emotion] thread started - a webcam window will open.")

    play_from(state.snapshot().current_playlist, state)

    wanted_since = None
    wanted_playlist = None

    print("Main loop running (Ctrl+C to stop). Make faces at the camera!")
    try:
        while True:
            s = state.snapshot()
            target = playlist_for_mood(s.mood)

            if target != s.current_playlist:
                if wanted_playlist != target:
                    wanted_playlist = target
                    wanted_since = time.time()
                elif time.time() - wanted_since >= SWITCH_HOLD_SECONDS:
                    play_from(target, state)
                    wanted_playlist = None
                    wanted_since = None
            else:
                wanted_playlist = None
                wanted_since = None

            line = "mood=" + s.mood + " -> want=" + target
            line += " | now=" + s.current_playlist + " track=" + s.current_track
            print(line)

            time.sleep(1.0 / FRAMES_PER_SECOND)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        stop_event.set()
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        time.sleep(0.3)
        print("Clean exit.")


if __name__ == "__main__":
    main()
