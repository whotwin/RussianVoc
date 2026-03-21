# Russian Flashcard App — Русские карточки

A spaced repetition flashcard app for learning Russian vocabulary (CEFR A1-B2), built with KivyMD.

## Features

- **Spaced Repetition (SM-2)** — Optimized review scheduling
- **4 CEFR Levels** — A1, A2, B1, B2 vocabulary
- **Flashcard Study** — Flip cards with quality rating (Again/Hard/Good/Easy)
- **Dictionary Search** — Find words by Russian or English
- **Declensions & Conjugations** — Full paradigm tables via pymorphy2
- **TTS Audio** — Silero TTS pronunciation
- **Stress Marking** — Accurate Cyrillic stress marks
- **Daily Reminders** — Desktop/mobile notifications
- **Progress Stats** — Streak tracking, accuracy, review history

## Setup

```bash
# Install dependencies
pip install -e .

# Seed sample data
python seed_db.py

# Run on desktop
python run.py
```

## Android Build

```bash
# Install buildozer
pip install buildozer

# Build debug APK
buildozer android debug

# Build release APK
buildozer android release
```

## Project Structure

```
src/
├── main.py              # KivyMD App entry point
├── config.py            # Configuration & settings
├── data/
│   ├── db.py            # SQLite connection management
│   ├── schema.sql       # Database schema
│   ├── schedule.py      # Vocabulary data access
│   └── user_progress.py # SM-2 progress tracking
├── core/
│   ├── word_processor.py   # Stress, normalization
│   ├── declension.py        # pymorphy2 morphology
│   ├── audio_service.py     # Silero TTS
│   └── cefr_levelizer.py   # CEFR level assignment
├── ui/
│   ├── screens/         # Home, Study, Dictionary, Plan, Progress
│   └── widgets/         # Flashcard, WordCard, ProgressBar
└── services/
    ├── notification_service.py
    └── data_importer.py
```

## Database Schema

| Table | Purpose |
|---|---|
| `words` | Word lemma, stressed form, POS, CEFR level |
| `translations` | Russian/English translations |
| `examples` | Example sentences |
| `declensions` | Noun/adjective 6-case paradigm |
| `conjugations` | Verb 12-form paradigm |
| `user_progress` | SM-2 parameters per word |
| `study_plans` | CEFR level plans |
| `review_history` | Full review log |
| `streak` | Daily streak tracking |

## Technologies

- **KivyMD** — Material Design UI
- **pymorphy2** — Morphological analysis
- **Silero TTS** — Text-to-speech
- **plyer** — Cross-platform notifications
- **SQLite** — Local data storage
- **SM-2** — Spaced repetition algorithm
