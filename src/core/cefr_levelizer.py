"""CEFR level assignment for Russian words."""
from typing import Optional

# Approximate frequency thresholds for Russian
# Based on corpus frequency data
CEFR_FREQUENCY_THRESHOLDS = {
    "A1": 3000,   # Most common 3000 words
    "A2": 5000,   # Next 2000
    "B1": 10000,  # Next 5000
    "B2": 20000,  # Next 10000
}

CEFR_DESCRIPTIONS = {
    "A1": {
        "name": "Beginner",
        "name_ru": "Начинающий",
        "description": "Basic words for everyday communication",
        "description_ru": "Базовые слова для повседневного общения",
        "word_count": "~3,000 words",
        "word_count_ru": "~3 000 слов",
        "estimated_weeks": 8,
        "color": "#4CAF50",
    },
    "A2": {
        "name": "Elementary",
        "name_ru": "Элементарный",
        "description": "Common words for routine situations",
        "description_ru": "Частые слова для повседневных ситуаций",
        "word_count": "~5,000 words",
        "word_count_ru": "~5 000 слов",
        "estimated_weeks": 12,
        "color": "#8BC34A",
    },
    "B1": {
        "name": "Intermediate",
        "name_ru": "Средний",
        "description": "Words for work, travel, and discussions",
        "description_ru": "Слова для работы, путешествий и обсуждений",
        "word_count": "~10,000 words",
        "word_count_ru": "~10 000 слов",
        "estimated_weeks": 20,
        "color": "#FF9800",
    },
    "B2": {
        "name": "Upper Intermediate",
        "name_ru": "Выше среднего",
        "description": "Advanced vocabulary for complex topics",
        "description_ru": "Продвинутая лексика для сложных тем",
        "word_count": "~20,000 words",
        "word_count_ru": "~20 000 слов",
        "estimated_weeks": 30,
        "color": "#F44336",
    },
}


def assign_cefr_level(frequency_rank: int) -> str:
    """Assign CEFR level based on corpus frequency rank."""
    if frequency_rank <= CEFR_FREQUENCY_THRESHOLDS["A1"]:
        return "A1"
    elif frequency_rank <= CEFR_FREQUENCY_THRESHOLDS["A2"]:
        return "A2"
    elif frequency_rank <= CEFR_FREQUENCY_THRESHOLDS["B1"]:
        return "B1"
    else:
        return "B2"


def get_level_progress(level: str, total_words: int, completed_words: int) -> float:
    """Calculate progress percentage for a level."""
    if total_words == 0:
        return 0.0
    return min(100.0, (completed_words / total_words) * 100)


def format_level_name(level: str, language: str = "en") -> str:
    """Get formatted level name."""
    if level not in CEFR_DESCRIPTIONS:
        return level
    info = CEFR_DESCRIPTIONS[level]
    if language == "ru":
        return info["name_ru"]
    return f"{level} - {info['name']}"


def get_cefr_info(level: str) -> dict:
    """Get full CEFR level information."""
    return CEFR_DESCRIPTIONS.get(level, {})
