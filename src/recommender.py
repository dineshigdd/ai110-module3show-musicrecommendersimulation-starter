import csv
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

# Scoring weights:
#   Genre (2.5):       Raised from 2.0 — genre is the primary filter;
#                      soft penalty on mismatch further reinforces this.
#   Mood  (2.5):       Equal to genre — emotionally specific moods deserve
#                      the same pull as genre identity.
#   Energy(1.8):       Slightly reduced from 2.0 — still a strong continuous
#                      signal but no longer equal to the binary features.
#   Acousticness(1.0): Unchanged — texture preference, least defining.
#   Tempo (0.5):       Unchanged — supporting context signal.
# Max possible score = 2.5 + 2.5 + 1.8 + 1.0 + 0.5 = 8.3
# (Genre mismatch penalty of -0.5 can push total below zero floor of 0.0)
WEIGHT_GENRE           = 2.5
WEIGHT_MOOD            = 2.5
WEIGHT_ENERGY          = 1.8
WEIGHT_ACOUSTICNESS    = 1.0
WEIGHT_TEMPO           = 0.5
GENRE_MISMATCH_PENALTY = 0.5   # subtracted when genre has no similarity at all
MOOD_MISMATCH_PENALTY  = 1.0   # subtracted when mood does NOT match

# MAX_SCORE is the theoretical ceiling when every feature is active and perfect.
MAX_SCORE = WEIGHT_GENRE + WEIGHT_MOOD + WEIGHT_ENERGY + WEIGHT_ACOUSTICNESS + WEIGHT_TEMPO

# Tempo normalization range (BPM → [0, 1] before Gaussian)
TEMPO_MIN = 60
TEMPO_MAX = 180

# Genre similarity matrix — partial credit for related genres.
# Values in (0, 1): 1.0 = identical, 0.0 = completely unrelated.
# Lookup is bidirectional: (a, b) == (b, a).
# Songs that match partially do NOT receive the mismatch penalty.
GENRE_SIMILARITY: Dict = {
    ("pop",        "k-pop"):     0.8,
    ("pop",        "indie pop"): 0.7,
    ("pop",        "r&b"):       0.5,
    ("pop",        "soul"):      0.4,
    ("rock",       "punk"):      0.6,
    ("rock",       "metal"):     0.5,
    ("rock",       "indie pop"): 0.4,
    ("lofi",       "ambient"):   0.6,
    ("lofi",       "jazz"):      0.5,
    ("jazz",       "bossa nova"):0.7,
    ("jazz",       "soul"):      0.5,
    ("jazz",       "r&b"):       0.4,
    ("hip-hop",    "trap"):      0.7,
    ("hip-hop",    "r&b"):       0.5,
    ("electronic", "synthwave"): 0.7,
    ("electronic", "trap"):      0.4,
    ("folk",       "country"):   0.7,
    ("folk",       "blues"):     0.5,
    ("country",    "blues"):     0.5,
    ("soul",       "r&b"):       0.7,
    ("funk",       "soul"):      0.6,
    ("funk",       "r&b"):       0.5,
    ("ambient",    "classical"): 0.4,
    ("latin",      "reggae"):    0.4,
    ("synthwave",  "electronic"):0.7,
}


def _genre_sim(g1: str, g2: str) -> float:
    """Returns similarity in [0, 1] between two genre strings.
    1.0 = exact match, uses GENRE_SIMILARITY for related pairs, 0.0 otherwise.
    Bidirectional: order of arguments does not matter.
    """
    g1, g2 = g1.lower(), g2.lower()
    if g1 == g2:
        return 1.0
    return GENRE_SIMILARITY.get((g1, g2)) or GENRE_SIMILARITY.get((g2, g1)) or 0.0


def compute_active_weight(user_prefs: Dict) -> float:
    """Returns the maximum achievable score for this profile.
    Only counts weights for features the user actually provided,
    so the /10 display scale is fair even when optional fields are absent.
    """
    weight = WEIGHT_GENRE + WEIGHT_MOOD + WEIGHT_ENERGY
    if user_prefs.get("likes_acoustic") is not None:
        weight += WEIGHT_ACOUSTICNESS
    if user_prefs.get("target_tempo") is not None:
        weight += WEIGHT_TEMPO
    return weight

def _gaussian_sim(x: float, y: float, sigma: float = 0.15) -> float:
    """
    Gaussian (RBF) similarity kernel.
    Returns 1.0 when x == y, decays smoothly to ~0 as |x - y| grows.
    sigma=0.15 (tightened from 0.25): a gap of 0.15 scores ~0.61,
    a gap of 0.30 scores ~0.14 — stricter, rewards closer matches more.
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

    # --- Genre: similarity matrix, weight 2.5 ---
    # Exact match → full credit. Related genre → partial credit via matrix.
    # Completely unrelated → 0 credit + mismatch penalty.
    user_genre = user_prefs.get("genre", "")
    if user_genre:
        sim = _genre_sim(song["genre"], user_genre)
        if sim == 1.0:
            genre_pts = WEIGHT_GENRE
            score += genre_pts
            reasons.append(f"genre matches ({song['genre']})  +{genre_pts:.2f}")
        elif sim > 0.0:
            genre_pts = WEIGHT_GENRE * sim
            score += genre_pts
            reasons.append(f"genre is similar ({song['genre']} ~ {user_genre}, sim={sim:.1f})  +{genre_pts:.2f}")
        else:
            score = max(0.0, score - GENRE_MISMATCH_PENALTY)
            reasons.append(f"genre mismatch ({song['genre']} != {user_genre})  -{GENRE_MISMATCH_PENALTY:.1f}")

    # --- Mood: binary match + mismatch penalty, weight 2.5 ---
    # Match → full credit. Mismatch → penalty applied (floored at 0).
    user_mood = user_prefs.get("mood", "")
    if user_mood:
        if song["mood"].lower() == user_mood.lower():
            score += WEIGHT_MOOD
            reasons.append(f"mood matches ({song['mood']})  +{WEIGHT_MOOD:.1f}")
        else:
            score = max(0.0, score - MOOD_MISMATCH_PENALTY)
            reasons.append(f"mood mismatch ({song['mood']} != {user_mood})  -{MOOD_MISMATCH_PENALTY:.1f}")

    # --- Energy: Gaussian similarity, weight 1.8 ---
    # sigma=0.15: stricter than before — a 0.15 gap scores ~0.61x,
    # a 0.30 gap scores ~0.14x. Rewards precise energy matches strongly.
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
    # Normalize BPM to [0, 1] before Gaussian so sigma=0.15 is meaningful.
    # A 18 BPM gap on a 60–180 range = 0.15 normalized → ~0.61 sim.
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
