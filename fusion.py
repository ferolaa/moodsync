# Turns a detected mood into a playlist choice.


# detected moods: happy / sad / surprised / neutral
# playlists:      happy / sad / chill / hype
MOOD_TO_PLAYLIST = {
    "happy":     "happy",
    "sad":       "sad",
    "surprised": "hype",
    "neutral":   "chill",
}


def playlist_for_mood(mood):
    return MOOD_TO_PLAYLIST.get(mood, "chill")
