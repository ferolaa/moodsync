import os, time, random, threading
import pygame
from state import SharedState
from fusion import playlist_for_mood
from inputs.emotion import run_emotion_thread
from inputs.gestures import run_gesture_thread

MUSIC_DIR = "music"
FPS = 8
EXTS = (".mp3", ".wav", ".ogg")
HOLD = 3
OVERRIDE = 10

def list_tracks(p):
    d = os.path.join(MUSIC_DIR, p)
    if not os.path.isdir(d):
        return []
    return [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.lower().endswith(EXTS)]

def play_from(p, state):
    tr = list_tracks(p)
    if not tr:
        print("[!] No songs in music/" + p + "/")
        state.update(is_playing=False, current_track="", current_playlist=p)
        return
    t = random.choice(tr)
    pygame.mixer.music.load(t)
    pygame.mixer.music.set_volume(state.snapshot().volume)
    pygame.mixer.music.play()
    state.update(is_playing=True, current_track=os.path.basename(t), current_playlist=p)
    print("[+] (" + p + ") " + os.path.basename(t))

def main():
    state = SharedState()
    pygame.mixer.init()
    stop = threading.Event()
    threading.Thread(target=run_emotion_thread, kwargs={"state": state, "show_window": False, "stop_event": stop}, daemon=True).start()
    threading.Thread(target=run_gesture_thread, kwargs={"state": state, "stop_event": stop}, daemon=True).start()
    print("[threads] started.")
    play_from(state.snapshot().current_playlist, state)
    ws, wp, last_g = None, None, 0.0
    print("Running (Ctrl+C to stop). Make faces / use your hand!")
    try:
        while True:
            s = state.snapshot()
            pygame.mixer.music.set_volume(s.volume)
            if s.gesture_updated_at > last_g:
                last_g = s.gesture_updated_at
                g = s.last_gesture
                if g in ("swipe_left", "swipe_right"):
                    print("[gesture] next"); play_from(s.current_playlist, state)
                elif g == "palm_closed":
                    print("[gesture] pause"); pygame.mixer.music.pause(); state.update(is_playing=False)
                elif g == "palm_open":
                    print("[gesture] play"); pygame.mixer.music.unpause(); state.update(is_playing=True)
            manual = (time.time() - s.last_manual_command_at) < OVERRIDE
            target = playlist_for_mood(s.mood)
            if not manual and target != s.current_playlist:
                if wp != target:
                    wp, ws = target, time.time()
                elif time.time() - ws >= HOLD:
                    play_from(target, state); wp, ws = None, None
            else:
                wp, ws = None, None
            print("mood=" + s.mood + " want=" + target + " now=" + s.current_playlist + " vol=" + ("%.2f" % s.volume) + " playing=" + str(s.is_playing))
            time.sleep(1.0 / FPS)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        stop.set(); pygame.mixer.music.stop(); pygame.mixer.quit(); time.sleep(0.3); print("Clean exit.")

if __name__ == "__main__":
    main()
