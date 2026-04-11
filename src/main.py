"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


PROFILES = [
    {
        "name": "Gym Session",
        "prefs": {
            "genre": "pop",
            "mood": "intense",
            "energy": 0.92,
            "likes_acoustic": False,
            "target_tempo": 135,
        },
    },
    {
        "name": "Late Night Study",
        "prefs": {
            "genre": "lofi",
            "mood": "focused",
            "energy": 0.38,
            "likes_acoustic": True,
            "target_tempo": 78,
        },
    },
    {
        "name": "Sunday Morning",
        "prefs": {
            "genre": "bossa nova",
            "mood": "dreamy",
            "energy": 0.30,
            "likes_acoustic": True,
            "target_tempo": 75,
        },
    },
    {
        "name": "Road Trip",
        "prefs": {
            "genre": "rock",
            "mood": "energetic",
            "energy": 0.88,
            "likes_acoustic": False,
            "target_tempo": 150,
        },
    },
]


def print_recommendations(profile_name: str, user_prefs: dict, songs: list, k: int = 5) -> None:
    recommendations = recommend_songs(user_prefs, songs, k=k)

    print()
    print("=" * 55)
    print(f"  PROFILE : {profile_name}")
    print(f"  Genre: {user_prefs['genre']}  |  Mood: {user_prefs['mood']}  |  Energy: {user_prefs['energy']}  |  Tempo: {user_prefs.get('target_tempo', '—')} BPM")
    print("=" * 55)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        print(f"      Score : {score:.2f} / 8.0")
        print(f"      Song  : {song['genre']}  |  {song['mood']}  |  energy {song['energy']}  |  {song['tempo_bpm']:.0f} BPM")
        print(f"      Why   :")
        for reason in explanation.split(";"):
            print(f"        • {reason.strip()}")

    print()
    print("=" * 55)


def main() -> None:
    songs = load_songs("data/songs.csv")

    for profile in PROFILES:
        print_recommendations(profile["name"], profile["prefs"], songs, k=3)


if __name__ == "__main__":
    main()
