import csv
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

# Scoring weights — updated for expanded 18-song catalog:
#   Genre (2.0):       Still the top filter but reduced from 3.0 — 13 of 15
#                      genres have only 1 song, so a 3.0 weight turned the
#                      recommender into a lookup table for most users.
#   Mood  (2.5):       Raised above genre — expanded moods (lonely, anxious,
#                      dreamy, mysterious) are now emotionally specific enough
#                      to be the strongest differentiating signal.
#   Energy(2.0):       Raised from 1.5 — catalog spread is 0.28–0.95,
#                      Gaussian now has real room to discriminate.
#   Acousticness(1.0): Unchanged — still least defining texture preference.
#   Tempo (0.5):       New — 60–168 BPM spread is large enough to add signal;
#                      half-weight keeps it from dominating.
# Max possible score = 2.0 + 2.5 + 2.0 + 1.0 + 0.5 = 8.0
WEIGHT_GENRE        = 2.0
WEIGHT_MOOD         = 2.5
WEIGHT_ENERGY       = 2.0
WEIGHT_ACOUSTICNESS = 1.0
WEIGHT_TEMPO        = 0.5

# Tempo normalization range (BPM → [0, 1] before Gaussian)
TEMPO_MIN = 60
TEMPO_MAX = 180

def _gaussian_sim(x: float, y: float, sigma: float = 0.25) -> float:
    """
    Gaussian (RBF) similarity kernel.
    Returns 1.0 when x == y, decays smoothly to ~0 as |x - y| grows.
    sigma=0.25 means a gap of 0.25 scores ~0.61, a gap of 0.5 scores ~0.14.
    """
    return math.exp(-((x - y) ** 2) / (2 * sigma ** 2))


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_tempo: Optional[float] = None  # BPM; optional for backwards compatibility


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    print(f"Loading songs from {csv_path}...")
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": float(row["tempo_bpm"]),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    
    print(f"Loaded songs: {len(songs)}")
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Content-based scoring using a weighted sum of feature similarities.

    Binary features (genre, mood) use exact match.
    Continuous features (energy, acousticness) use a Gaussian (RBF) kernel
    so songs *closer* to the user's target score higher — not just
    songs that happen to be high or low.

    Returns (score, reasons):
      score   — float in [0, 8.0]; higher is a better match
      reasons — human-readable explanation of what matched
    """
    score = 0.0
    reasons = []

    # --- Genre: binary match, weight 3.0 ---
    # Heaviest weight: genre defines the fundamental sound palette.
    if song["genre"].lower() == user_prefs.get("genre", "").lower():
        score += WEIGHT_GENRE
        reasons.append(f"genre matches ({song['genre']})  +{WEIGHT_GENRE:.1f}")

    # --- Mood: binary match, weight 2.5 ---
    # Second heaviest: mood defines emotional experience within a genre.
    if song["mood"].lower() == user_prefs.get("mood", "").lower():
        score += WEIGHT_MOOD
        reasons.append(f"mood matches ({song['mood']})  +{WEIGHT_MOOD:.1f}")

    # --- Energy: Gaussian similarity, weight 2.0 ---
    # Continuous [0, 1]. Gaussian rewards proximity — a song 0.1 away
    # scores ~0.92×, a song 0.5 away scores ~0.14×.
    energy_sim = _gaussian_sim(song["energy"], user_prefs.get("energy", 0.5))
    energy_pts = WEIGHT_ENERGY * energy_sim
    score += energy_pts
    if energy_sim >= 0.90:
        reasons.append(f"energy is an excellent match ({song['energy']:.2f})  +{energy_pts:.2f}")
    elif energy_sim >= 0.60:
        reasons.append(f"energy is near your preference ({song['energy']:.2f})  +{energy_pts:.2f}")

    # --- Acousticness: Gaussian similarity, weight 1.0 ---
    # Map bool preference to a target in [0, 1], then apply same kernel.
    likes_acoustic = user_prefs.get("likes_acoustic")
    if likes_acoustic is not None:
        target_ac = 1.0 if likes_acoustic else 0.0
        ac_sim = _gaussian_sim(song["acousticness"], target_ac)
        ac_pts = WEIGHT_ACOUSTICNESS * ac_sim
        score += ac_pts
        if ac_sim >= 0.90:
            reasons.append(f"acousticness is exactly what you prefer ({song['acousticness']:.2f})  +{ac_pts:.2f}")
        elif ac_sim >= 0.60:
            reasons.append(f"acousticness fits your taste ({song['acousticness']:.2f})  +{ac_pts:.2f}")

    # --- Tempo: Gaussian similarity, weight 0.5 ---
    # Normalize BPM to [0, 1] before applying Gaussian so sigma=0.25 is
    # meaningful. A 30 BPM gap on a 60–180 range = 0.25 normalized → ~0.61 sim.
    target_tempo = user_prefs.get("target_tempo")
    if target_tempo is not None:
        song_tempo_norm   = (song["tempo_bpm"] - TEMPO_MIN) / (TEMPO_MAX - TEMPO_MIN)
        target_tempo_norm = (target_tempo      - TEMPO_MIN) / (TEMPO_MAX - TEMPO_MIN)
        tempo_sim = _gaussian_sim(song_tempo_norm, target_tempo_norm)
        tempo_pts = WEIGHT_TEMPO * tempo_sim
        score += tempo_pts
        if tempo_sim >= 0.90:
            reasons.append(f"tempo is an excellent match ({song['tempo_bpm']:.0f} BPM)  +{tempo_pts:.2f}")
        elif tempo_sim >= 0.60:
            reasons.append(f"tempo is close to your preference ({song['tempo_bpm']:.0f} BPM)  +{tempo_pts:.2f}")

    return score, reasons


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores and ranks all songs, returning the top-k recommendations.
    Each item is (song_dict, score, explanation).
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        explanation = "; ".join(reasons) if reasons else "general match"
        scored.append((song, score, explanation))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _profile_to_prefs(self, user: UserProfile) -> Dict:
        return {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
            "target_tempo": user.target_tempo,
        }

    def _song_to_dict(self, song: Song) -> Dict:
        return asdict(song)

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        prefs = self._profile_to_prefs(user)
        scored = []
        for song in self.songs:
            score, _ = score_song(prefs, self._song_to_dict(song))
            scored.append((song, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [song for song, _ in scored[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        prefs = self._profile_to_prefs(user)
        _, reasons = score_song(prefs, self._song_to_dict(song))
        return "; ".join(reasons) if reasons else "general match based on your profile"
