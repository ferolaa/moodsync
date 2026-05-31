"""
fusion.py — turns a detected mood into a playlist choice.
This is the 'multimodal fusion' rule layer (simple + rule-based on purpose).
"""

# detected moods: happy / sad / angry / neutral / surprised
# playlists:      happy / sad / chill / hype
MOOD_TO_PLAYLIST = {
    "happy":     "happy",
    "sad":       "sad",
    "angry":     "hype",
    "surprised": "hype",
    "neutral":   "chill",
}


def playlist_for_mood(mood):
    return MOOD_TO_PLAYLIST.get(mood, "chill")
