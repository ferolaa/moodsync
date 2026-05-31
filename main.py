"""
main.py  —  MoodSync Day 1 skeleton

Goal of this version: prove the core loop works end to end.
  * create the SharedState
  * play ONE real song from the current playlist folder
  * run a loop that reads the state ~4x/second and prints it

Run it:  python main.py    (Ctrl+C to stop)
Before running, drop an audio file into music/chill/  e.g. music/chill/song.mp3
"""

import os
import time
import random

import pygame

from state import SharedState, PLAYLISTS


MUSIC_DIR = "music"
FRAMES_PER_SECOND = 4
AUDIO_EXTENSIONS = (".mp3", ".wav", ".ogg")


def list_tracks(playlist):
    folder = os.path.join(MUSIC_DIR, playlist)
    if not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if f.lower().endswith(AUDIO_EXTENSIONS)
    ]


def play_track(path, volume):
    pygame.mixer.music.load(path)
    pygame.mixer.music.set_volume(volume)
    pygame.mixer.music.play()


def main():
    state = SharedState()
    pygame.mixer.init()

    playlist = state.snapshot().current_playlist
    tracks = list_tracks(playlist)

    if not tracks:
        print("\n[!] No audio files found in music/" + playlist + "/")
        print("    Add a song there (e.g. music/" + playlist + "/song.mp3) and rerun.\n")
    else:
        track = random.choice(tracks)
        play_track(track, state.snapshot().volume)
        state.update(is_playing=True, current_track=os.path.basename(track))
        print("\n[+] Playing: " + track + "\n")

    print("Main loop running (Ctrl+C to stop)...\n")
    try:
        while True:
            s = state.snapshot()
            print(
                "mood=%-8s conf=%.2f | playlist=%-6s track=%-20s | vol=%.1f playing=%s | gesture=%-12s voice=%s"
                % (s.mood, s.mood_confidence, s.current_playlist,
                   s.current_track, s.volume, s.is_playing,
                   s.last_gesture or "-", s.last_voice_command or "-")
            )
            time.sleep(1 / FRAMES_PER_SECOND)
    except KeyboardInterrupt:
        print("\n\nStopping...")
    finally:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        print("Clean exit. Bye.\n")


if __name__ == "__main__":
    main()
