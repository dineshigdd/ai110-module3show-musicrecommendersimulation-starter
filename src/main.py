"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Starter example profile
    user_prefs = {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "likes_acoustic": False,
        "target_tempo": 120,
    }

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print()
    print("=" * 50)
    print("  TOP RECOMMENDATIONS")
    print(f"  Genre: {user_prefs['genre']}  |  Mood: {user_prefs['mood']}  |  Energy: {user_prefs['energy']}")
    print("=" * 50)

    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n#{rank}  {song['title']}  —  {song['artist']}")
        print(f"    Score : {score:.2f} / 8.0")
        print(f"    Genre : {song['genre']}  |  Mood: {song['mood']}  |  Energy: {song['energy']}  |  Tempo: {song['tempo_bpm']:.0f} BPM")
        print(f"    Why   :")
        for reason in explanation.split(";"):
            print(f"      • {reason.strip()}")

    print()
    print("=" * 50)


if __name__ == "__main__":
    main()
