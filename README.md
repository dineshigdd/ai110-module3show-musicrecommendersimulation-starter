# 🎵 Music Recommender Simulation

## Project Summary

This simulation demonstrates the mechanics of a recommendation engine by translating user 'taste profiles' and song attributes into structured data. By applying a weighted scoring model—using mathematical rules to compare features like mood and energy—the system calculates a numerical match for each track and ranks them accordingly. Through evaluating the results, I identified where the system succeeds and where it encounters 'silent failures' due to a limited catalog. This process highlights the core challenges of real-world AI recommenders, specifically the critical need for massive datasets and behavioral feedback to improve accuracy. 


## How The System Works

### How does real-world recommendations works in Streaming Platforms
Streaming Platforms broadly uses two techniques of recommendation systems
1. Collaborative Filtering
    - Uses other users’ behavior
    - ex: If users similar to you love a song you haven’t heard → recommend it
2. Content-Based Filtering
    - Uses attributes of the content itself
    - ex: If you like slow acoustic songs → recommend similar songs (tempo, genre, mood)

Modern platforms combine both methods and AI models:
- Deep learning (neural networks)
- Natural language processing (for titles, comments, descriptions)
- Audio analysis (tempo, pitch, energy)

And Continuous Feedback Loop make sure that every interaction updates your profile. If you:
Skip a song = negative signal
Replay a song = strong positive signal
Like/save a song = explicit preference

This improves the recommendation systems with real time data.

### How My system works
My recommendation system uses five features:
1. genre 
2. mood 
3. energy
4. acousticness
5. tempo 

- Genre is the coarsest filter with  broad categorical bucket (rock, pop, jazz…), with a similarity matrix that gives partial credit to related genres.

* Mood is equally weighted but more 'emotionally precise' with binary match (no partial credit), with a harsher mismatch penalty.

* Energy continuous and context-critical.It uses Gaussian function.

* Acousticness (1.0) is a low-priority texture preference. 

* Tempo (0.5):  Tempo (BPM) has the lowest weight in the scoring system 

* There is also penalties for mistmached genre  or mismatched mood 

* What features does each `Song` use in your system
  The system is designed to score and rank songs based on five features. The Song class , therefore,has five mains attributes:
  1. genre
  2. mood
  3. energy, 
  4. acousticness
  5. tempo.
  
  In additon , it also has title and artist as attributes.

- What information does your `UserProfile` store
  The UserProfile class has five attributes
  1. favorite_genre.
  2. favorite_mood
  3. target_energy
  4. likes_acoustic
  5. target_tempo(optional) 

- How does your `Recommender` compute a score for each song
    The recommend() method in Recommender utilizes _profile_to_prefs() to convert UserProfile to a dictionary,and convert songs to a dictionary,and finally uses  score_song to get a score for each song.

- How do you choose which songs to recommend
  The songs are ranked in descending order. Therefore, the higher the score, the closer the song is to the user preference
  

## Potential bias of this system
The system struggles with users who prefer mid-range energy (not too calm, not too intense) because most songs in the catalog cluster at the extremes — very high or very low energy — so the math never finds a close match for them. 

Mood is treated as all-or-nothing, meaning "chill" and "relaxed" are considered completely different even though in real life they feel almost the same, so a user gets penalized unfairly for near-matches. The acoustic preference is forced into a yes-or-no choice, which ignores users who enjoy a mix of both acoustic and electronic sounds. 

The genre similarity map was written by hand, so genres like reggae, latin, and classical have fewer connections than pop or rock — fans of those genres get harsher penalties even when a reasonable alternative exists. When a user skips optional preferences like tempo or acousticness, their scores look artificially high on the 0–10 scale, making weak recommendations appear more confident than they actually are. 

Finally, users with a rare combination — like blues and sad — get hit with multiple penalties at once, leaving the system with almost no signal to rank songs, so the bottom results are essentially random.



###
Song object

| Field | Type | Used in scoring? |
| :--- | :--- | :--- |
| **id** | int | No — identifier only |
| **title** | str | No — display only |
| **artist** | str | No — display only |
| **genre** | str | Yes — matched against user preference |
| **mood** | str | Yes — matched against user preference |
| **energy** | float | Yes — Gaussian similarity against target |
| **tempo_bpm** | float | Yes — Gaussian similarity against target_tempo (optional) |
| **valence** | float | No — loaded but never scored |
| **danceability** | float | No — loaded but never scored |
| **acousticness** | float | Yes — Gaussian similarity against target |

UserProfile object
| Field | Type | Used in scoring? |
| :--- | :--- | :--- |
| **favorite_genre** | str | Yes — similarity matrix match against song.genre |
| **favorite_mood** | str | Yes — binary match against song.mood |
| **target_energy** | float | Yes — target for Gaussian similarity |
| **likes_acoustic** | bool | Yes — maps to 1.0 or 0.0, then Gaussian similarity |
| **target_tempo** | float (optional) | Yes — normalized BPM target for Gaussian similarity; skipped if not provided |


### Comparrion between real-world recommedation system and this system
| Feature | This System | Real-world |
| :--- | :--- | :--- |
| **Data source** | Hand-picked attributes (genre, mood) | Billions of implicit signals (play-throughs, skips, repeat plays, time of day) |
| **Method** | Content-based filtering | Collaborative filtering + content + deep learning |
| **User model** | Static profile dict | Continuously updated from behavior |
| **What "similar" means** | Feature distance | Users who listen like you also liked this |
| **Cold start** | Works immediately | Needs listening history to work well |
---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Experiments You Tried

- **What happened when you changed the genre weight from 3.0 to 2.5**  
Lowering genre from 3.0 to 2.5 and raising mood to match it (also 2.5) made the system less rigid. Previously, a genre mismatch was so costly that mood, energy, and tempo could rarely overcome it. At equal weights, a song with a perfect mood match but a related genre (e.g. pop for a k-pop user) can now compete with a genre-exact but mood-mismatched song. The rankings became more emotionally sensitive and less genre-locked.

- **What happened when you added tempo to the score**  
Adding tempo (weight 0.5) with a normalized Gaussian on BPM [0, 1] produced small but meaningful tie-breaking effects. For profiles with very close #1 and #2 scores (like Road Trip), tempo nudged the ranking in favor of the song whose BPM was closer to the target. It had no visible effect on already-confident profiles (like Gym Session) where genre and mood already dominated the score.

- **How did your system behave for different types of users**  
Well-defined profiles (Gym Session, Late Night Study, Sunday Morning) produced confident top picks with large gaps between #1 and #2. Edge case profiles exposed weaknesses: Road Trip struggled because no song perfectly matched rock + energetic, compressing all scores into a narrow band. The Unknown Genre (k-pop) profile surprisingly produced a high-confidence result (8.6/10) because the similarity matrix partially rescued pop songs. The Ambiguous Energy (0.5) profile showed how binary features completely take over when continuous features give equal scores to every song.

---

## Limitations and Risks

Summarize some limitations of your recommender.

- **human-assigned and sparse labels**  
The labels are human-assigned and sparse. For example,
genre = "lofi", mood = "happy". Real systems infer these implicitly from
behavior at scale — if 90% of listeners play a song at 1am on weekdays,
the system classifies it as "chill" without anyone labeling it. 

- **Not teachable**   
The system does not use any teachable models, which means the system cannot improve from user feedback (weights genre=2.5, mood=2.5, energy=1.8, acousticness=1.0, tempo=0.5 are hand-coded constants).

- **Static user profile**  
  User preferences never update. Skipping or replaying  songs has no effect on future recommendations.

- **No diversity control**  
  If five songs all share the same genre, all five get recommended even if they sound nearly identical.

- **Tiny catalog**  
  18 songs. Real systems operate on millions.

- **Unused features**  
  valence and danceability are loaded but never scored, leaving signal on the table.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)