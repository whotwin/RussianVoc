"""Data importer for vocabulary from openrussian-data."""
import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Optional
import json
import csv
import httpx

from src.data.db import init_db_sync
from src.data.schedule import (
    insert_word,
    insert_translation,
    insert_example,
    insert_declension,
    insert_conjugation,
    insert_stress,
)
from src.core.declension import (
    decline_noun,
    decline_adjective,
    conjugate_verb,
    predict_stress,
)
from src.core.cefr_levelizer import assign_cefr_level

logger = logging.getLogger(__name__)

OPEN_RUSSIAN_DATA_URL = "https://raw.githubusercontent.com/tatuylonen/openrussian-data/main"


async def fetch_json(path: str) -> Optional[dict]:
    """Fetch JSON data from openrussian-data repository."""
    url = f"{OPEN_RUSSIAN_DATA_URL}/{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


async def import_words_from_openrussian(
    cefr_levels: list[str] = None, max_words: int = None
) -> int:
    """Import words from openrussian-data GitHub repository."""
    if cefr_levels is None:
        cefr_levels = ["A1", "A2", "B1", "B2"]

    init_db_sync()

    count = 0
    try:
        words_data = await fetch_json("words.jsonl")
        if words_data:
            for line in words_data.splitlines():
                if not line.strip():
                    continue
                try:
                    word = json.loads(line)
                    await _import_single_word(word)
                    count += 1
                    if max_words and count >= max_words:
                        break
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Import failed: {e}")

    logger.info(f"Imported {count} words")
    return count


async def _import_single_word(data: dict) -> None:
    """Import a single word from openrussian-data format."""
    lemma = data.get("word", "")
    if not lemma:
        return

    # Determine CEFR level from frequency
    frequency = data.get("rank", 100000)
    cefr_level = assign_cefr_level(frequency)

    # Predict stress
    stress_pos = predict_stress(lemma)
    stressed = lemma[:stress_pos] + "\u0301" + lemma[stress_pos:]

    # Get part of speech
    pos = data.get("pos", "other")

    # Insert word
    word_id = await insert_word(lemma, stressed, pos, cefr_level, frequency)

    if word_id:
        # Insert translations
        for translation in data.get("translations", []):
            await insert_translation(word_id, translation)

        # Insert examples
        for ex in data.get("examples", []):
            russian = ex.get("russian", "")
            english = ex.get("english", "")
            if russian and english:
                await insert_example(word_id, russian, english)

        # Generate declensions/conjugations with pymorphy2
        if pos in ("noun",):
            decls = decline_noun(lemma, stressed)
            for key, val in decls.items():
                parts = key.split("_")
                case = parts[0]
                number = parts[1]
                await insert_declension(word_id, case, number, val["form"], val["form_stressed"])

        elif pos in ("verb",):
            cons = conjugate_verb(lemma, stressed)
            for key, val in cons.items():
                parts = key.split("_")
                tense = parts[0]
                person = parts[1]
                number = parts[2]
                await insert_conjugation(word_id, tense, person, number, val["form"], val["form_stressed"])

        elif pos in ("adjective",):
            decls = decline_adjective(lemma, stressed)
            for key, val in decls.items():
                parts = key.split("_")
                case = parts[0]
                gender_or_number = parts[1]
                await insert_declension(word_id, case, gender_or_number, val["form"], val["form_stressed"])

        # Insert stress info
        await insert_stress(word_id, stressed, stress_pos)


async def import_from_csv(filepath: Path) -> int:
    """Import words from a CSV file.

    Expected CSV columns: lemma, stressed, pos, cefr_level, translation, example_en, example_ru
    """
    init_db_sync()
    count = 0

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            lemma = row.get("lemma", "").strip()
            if not lemma:
                continue

            stressed = row.get("stressed", lemma)
            pos = row.get("pos", "other")
            cefr = row.get("cefr_level", "B1")
            translation = row.get("translation", "")
            example_ru = row.get("example_ru", "")
            example_en = row.get("example_en", "")

            word_id = await insert_word(lemma, stressed, pos, cefr)
            if translation:
                await insert_translation(word_id, translation)
            if example_ru and example_en:
                await insert_example(word_id, example_ru, example_en)

            count += 1

    logger.info(f"Imported {count} words from CSV")
    return count


async def seed_sample_data() -> int:
    """Seed database with a small sample of common Russian words."""
    init_db_sync()

    sample_words = [
        {
            "lemma": "дом",
            "stressed": "дом",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["house", "home"],
            "examples": [
                ("Это мой дом.", "This is my house."),
                ("Дом большой.", "The house is big."),
            ],
        },
        {
            "lemma": "вода",
            "stressed": "вода\u0301",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["water"],
            "examples": [
                ("Мне нужна вода.", "I need water."),
                ("Вода горячая.", "The water is hot."),
            ],
        },
        {
            "lemma": "книга",
            "stressed": "кни\u0301га",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["book"],
            "examples": [
                ("Это интересная книга.", "This is an interesting book."),
            ],
        },
        {
            "lemma": "есть",
            "stressed": "е\u0301сть",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to eat"],
            "examples": [
                ("Я хочу есть.", "I want to eat."),
            ],
        },
        {
            "lemma": "читать",
            "stressed": "чита\u0301ть",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to read"],
            "examples": [
                ("Я люблю читать.", "I like to read."),
            ],
        },
        {
            "lemma": "хороший",
            "stressed": "хоро\u0301ший",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["good"],
            "examples": [
                ("Это хорошая идея.", "This is a good idea."),
            ],
        },
        {
            "lemma": "большой",
            "stressed": "большо\u0301й",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["big", "large"],
            "examples": [
                ("Большой дом.", "A big house."),
            ],
        },
        {
            "lemma": "я",
            "stressed": "я",
            "pos": "pronoun",
            "cefr": "A1",
            "translations": ["I"],
            "examples": [
                ("Я студент.", "I am a student."),
            ],
        },
        {
            "lemma": "ты",
            "stressed": "ты",
            "pos": "pronoun",
            "cefr": "A1",
            "translations": ["you (informal)"],
            "examples": [
                ("Ты готов?", "Are you ready?"),
            ],
        },
        {
            "lemma": "он",
            "stressed": "он",
            "pos": "pronoun",
            "cefr": "A1",
            "translations": ["he"],
            "examples": [
                ("Он врач.", "He is a doctor."),
            ],
        },
        {
            "lemma": "она",
            "stressed": "она\u0301",
            "pos": "pronoun",
            "cefr": "A1",
            "translations": ["she"],
            "examples": [
                ("Она студентка.", "She is a student."),
            ],
        },
        {
            "lemma": "мы",
            "stressed": "мы",
            "pos": "pronoun",
            "cefr": "A1",
            "translations": ["we"],
            "examples": [
                ("Мы друзья.", "We are friends."),
            ],
        },
        {
            "lemma": "они",
            "stressed": "они\u0301",
            "pos": "pronoun",
            "cefr": "A1",
            "translations": ["they"],
            "examples": [
                ("Они учатся.", "They are studying."),
            ],
        },
        {
            "lemma": "в",
            "stressed": "в",
            "pos": "preposition",
            "cefr": "A1",
            "translations": ["in", "at"],
            "examples": [
                ("Он в школе.", "He is at school."),
            ],
        },
        {
            "lemma": "и",
            "stressed": "и",
            "pos": "conjunction",
            "cefr": "A1",
            "translations": ["and"],
            "examples": [
                ("Хлеб и масло.", "Bread and butter."),
            ],
        },
        {
            "lemma": "не",
            "stressed": "не",
            "pos": "particle",
            "cefr": "A1",
            "translations": ["not", "no"],
            "examples": [
                ("Я не знаю.", "I don't know."),
            ],
        },
        {
            "lemma": "что",
            "stressed": "что\u0301",
            "pos": "pronoun",
            "cefr": "A1",
            "translations": ["what", "that"],
            "examples": [
                ("Что это?", "What is this?"),
            ],
        },
        {
            "lemma": "это",
            "stressed": "это\u0301",
            "pos": "pronoun",
            "cefr": "A1",
            "translations": ["this", "it"],
            "examples": [
                ("Это книга.", "This is a book."),
            ],
        },
        {
            "lemma": "быть",
            "stressed": "быть",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to be"],
            "examples": [
                ("Я буду дома.", "I will be at home."),
            ],
        },
        {
            "lemma": "идти",
            "stressed": "идти\u0301",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to go", "to walk"],
            "examples": [
                ("Мы идём домой.", "We are going home."),
            ],
        },
    ]

    count = 0
    for w in sample_words:
        word_id = await insert_word(
            w["lemma"], w["stressed"], w["pos"], w["cefr"], count + 1
        )
        if word_id:
            for t in w["translations"]:
                await insert_translation(word_id, t)
            for r, e in w["examples"]:
                await insert_example(word_id, r, e)

            # Generate morphological forms
            if w["pos"] == "noun":
                decls = decline_noun(w["lemma"], w["stressed"])
                for key, val in decls.items():
                    parts = key.split("_")
                    await insert_declension(word_id, parts[0], parts[1], val["form"], val["form_stressed"])
            elif w["pos"] == "verb":
                cons = conjugate_verb(w["lemma"], w["stressed"])
                for key, val in cons.items():
                    parts = key.split("_")
                    await insert_conjugation(word_id, parts[0], parts[1], parts[2], val["form"], val["form_stressed"])
            elif w["pos"] == "adjective":
                decls = decline_adjective(w["lemma"], w["stressed"])
                for key, val in decls.items():
                    parts = key.split("_")
                    await insert_declension(word_id, parts[0], parts[1], val["form"], val["form_stressed"])

            stress_pos = w["stressed"].find("\u0301")
            await insert_stress(word_id, w["stressed"], stress_pos if stress_pos >= 0 else 0)
            count += 1

    logger.info(f"Seeded {count} sample words")
    return count
