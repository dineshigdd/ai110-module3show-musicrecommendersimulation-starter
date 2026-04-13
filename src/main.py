"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs, compute_active_weight


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
    # --- ADVERSARIAL / EDGE CASE PROFILES ---
    {
        # Conflicting signal: high energy usually pairs with intense/happy,
        # but mood is sad. Tests whether energy can overpower mood mismatch.
        "name": "[EDGE] High Energy + Sad Mood",
        "prefs": {
            "genre": "blues",
            "mood": "sad",
            "energy": 0.90,
            "likes_acoustic": False,
            "target_tempo": 155,
        },
    },
    {
        # Genre that does not exist in the catalog at all.
        # Every song takes the -0.5 mismatch penalty.
        # Tests: does the system still rank meaningfully using mood/energy alone?
        "name": "[EDGE] Unknown Genre",
        "prefs": {
            "genre": "k-pop",
            "mood": "happy",
            "energy": 0.75,
            "likes_acoustic": False,
            "target_tempo": 120,
        },
    },
    {
        # Energy 0.5 is the dead-centre of [0, 1].
        # Gaussian from 0.5 gives every song a partial score — nothing stands out.
        # Tests: do rankings collapse into a near-tie where binary features decide?
        "name": "[EDGE] Ambiguous Energy (0.5)",
        "prefs": {
            "genre": "jazz",
            "mood": "relaxed",
            "energy": 0.50,
            "likes_acoustic": None,   # no acousticness preference at all
            "target_tempo": None,     # no tempo preference at all
        },
    },
    {
        # Contradictory texture: wants acoustic sound but very high energy.
        # Acoustic songs in the catalog cluster at low energy (0.28–0.37).
        # Tests: can any single song satisfy both without scoring low overall?
        "name": "[EDGE] Acoustic + High Energy",
        "prefs": {
            "genre": "folk",
            "mood": "uplifting",
            "energy": 0.92,
            "likes_acoustic": True,
            "target_tempo": 140,
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

    active_weight = compute_active_weight(user_prefs)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"\n  #{rank}  {song['title']}  —  {song['artist']}")
        normalized = (score / active_weight) * 10
        print(f"      Score : {normalized:.1f} / 10  (active features max: {active_weight:.1f})")
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
