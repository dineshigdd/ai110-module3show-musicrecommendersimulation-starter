# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

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
My recommendation sytem uses four features:
1. genre 
2. mood (defines the emotional experience )
3. energy
4. acousticness
5. tempo 

The reasoning for weight as follows:
Genre (2.5) is the coarsest filter. 
The system assumes that a person would choose genre regardless of energy or mood. For example . Some one that listen soft rock or jazz music frequenlty music would rarely listen hip-hop or metal song regardless of the enrgy and mood. 

Mood (2.5) is Second most defining after genre. A "happy" song and a "moody" song feel fundamentally different even in the same genre.

Energy (1.8) — continuous and context-critical 
When you are at the gym, you want to listen to high-energy songs. On the other hand, when you study, you prefer low-energy songs. However, within a session at the gym or during study time, you might tolerate some variance in these energy levels. Thus, the energy feature is continuous (not binary), requiring a smooth transition where the system picks songs with a similar 'vibe' rather than jumping abruptly between different levels.

Acousticness (1.0) is a low-priority texture preference. It represents the choice between Organic (acoustic) and Electronic (synthetic) sounds, based on the assumption that the 'instrument feel' is less important to the listener than the Genre or the Energy of the song.

Tempo (0.5):  Tempo (BPM) has the lowest weight in the scoring system because it's considered a secondary detail rather than a defining characteristic of a song

Based on these five features , the system calculte a maximum score of 8.3 when everything matches perfectly.
Max possible score = 2.5 + 2.5 + 1.8 + 1.0 + 0.5 = 8.3

There is also penalties for mistmached genre( -0.5 ) or mismatched mood( -1.0 )
Explain your design in plain language.
- What features does each `Song` use in your system
  - For example: genre, mood, energy, tempo

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

scoring system
=============
For genre and mood features
A binary score is used. If the genre doesn't match, the score drops significantly because the weight is high (2.5).

For continuous features (energy, acousticness), instead of linear 1 - |diff| ,use a Gaussian/RBF kernel:
sim(x, y) = exp(-(x - y)² / (2σ²)).

Why Gaussian 
 Linear penalizes all gaps equally — a song 0.1 away loses as much per unit as one 0.5 away. 
 The Gaussian function produces a bell curve providing smooth transition. The closer the song is to the choosen target energy, the more points it gets.Therefore, Gaussian is more realistic; small differences barely matter, large differences are heavily penalized. It also never goes negative.
 
 
Ex:
With σ=0.25: a song 0.1 away scores 0.92, a song 0.25 away scores 0.61, a song 0.5 away scores 0.14. Natural, smooth decay — rewards songs close to preference rather than just "any direction."

Summary of the scoring rule
## Scoring Rule (Max Score = 7.5)

| Feature | Type | Weight | Method |
| :--- | :--- | :--- | :--- |
| **Genre** | Binary | 3.0 | Exact match → full points or 0 |
| **Mood** | Binary | 2.0 | Exact match → full points or 0 |
| **Energy** | Continuous | 1.5 | Gaussian: $e^{-\frac{(x-y)^2}{2\sigma^2}}$, where $\sigma=0.25$ |
| **Acousticness** | Continuous | 1.0 | Same Gaussian, target = 1.0 or 0.0 |

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
| **tempo_bpm** | float | No — loaded but never scored |
| **valence** | float | No — loaded but never scored |
| **danceability** | float | No — loaded but never scored |
| **acousticness** | float | Yes — Gaussian similarity against target |

UserProfile object
| Field | Type | Used in scoring? |
| :--- | :--- | :--- |
| **favorite_genre** | str | Yes — binary match against song.genre |
| **favorite_mood** | str | Yes — binary match against song.mood |
| **target_energy** | float | Yes — target for Gaussian similarity |
| **likes_acoustic** | bool | Yes — maps to 1.0 or 0.0, then Gaussian similarity |


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

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

- **human-assigned and sparse labels**
The labels are human-assigned and sparse. For example,
genre = "lofi", mood = "happy". Real systems infer these implicitly from
behavior at scale — if 90% of listeners play a song at 1am on weekdays,
the system classifies it as "chill" without anyone labeling it. 

- **Not teachable** 
The system is does not use any teachable models,which means the system cannot improve from user feedback (weights (genre=3.0, mood=2.0, etc.) are hand-coded constants. ).

- **Static user profile** 
  User preferences never update. Skipping or replaying  songs has no effect on future recommendations.

- **No diversity control** — if five songs all share the same genre, all five get recommended even if they sound nearly identical.

- **Tiny catalog** — 18 songs. Real systems operate on millions.

- **Unused features** — valence, and danceability are loaded
  but never scored, leaving signal on the table.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this


---

## 7. `model_card_template.md`

Combines reflection and model card framing from the Module 3 guidance. :contentReference[oaicite:2]{index=2}  

```markdown
# 🎧 Model Card - Music Recommender Simulation

## 1. Model Name

Give your recommender a name, for example:

> VibeFinder 1.0

---

## 2. Intended Use

- What is this system trying to do
- Who is it for

Example:

> This model suggests 3 to 5 songs from a small catalog based on a user's preferred genre, mood, and energy level. It is for classroom exploration only, not for real users.

---

## 3. How It Works (Short Explanation)

Describe your scoring logic in plain language.

- What features of each song does it consider
- What information about the user does it use
- How does it turn those into a number

Try to avoid code in this section, treat it like an explanation to a non programmer.

---

## 4. Data

Describe your dataset.

- How many songs are in `data/songs.csv`
- Did you add or remove any songs
- What kinds of genres or moods are represented
- Whose taste does this data mostly reflect

---

## 5. Strengths

Where does your recommender work well

You can think about:
- Situations where the top results "felt right"
- Particular user profiles it served well
- Simplicity or transparency benefits

---

## 6. Limitations and Bias

Where does your recommender struggle

Some prompts:
- Does it ignore some genres or moods
- Does it treat all users as if they have the same taste shape
- Is it biased toward high energy or one genre by default
- How could this be unfair if used in a real product

---

## 7. Evaluation

How did you check your system

Examples:
- You tried multiple user profiles and wrote down whether the results matched your expectations
- You compared your simulation to what a real app like Spotify or YouTube tends to recommend
- You wrote tests for your scoring logic

You do not need a numeric metric, but if you used one, explain what it measures.

---

## 8. Future Work

If you had more time, how would you improve this recommender

Examples:

- Add support for multiple users and "group vibe" recommendations
- Balance diversity of songs instead of always picking the closest match
- Use more features, like tempo ranges or lyric themes

---

## 9. Personal Reflection

A few sentences about what you learned:

- What surprised you about how your system behaved
- How did building this change how you think about real music recommenders
- Where do you think human judgment still matters, even if the model seems "smart"

