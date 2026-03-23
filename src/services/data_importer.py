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
        # A1 - Core vocabulary
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
        # A1 - Additional everyday words
        {
            "lemma": "мама",
            "stressed": "ма\u0301ма",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["mother", "mom"],
            "examples": [
                ("Моя мама дома.", "My mom is at home."),
            ],
        },
        {
            "lemma": "папа",
            "stressed": "па\u0301па",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["father", "dad"],
            "examples": [
                ("Папа на работе.", "Dad is at work."),
            ],
        },
        {
            "lemma": "друг",
            "stressed": "друг",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["friend"],
            "examples": [
                ("Мой лучший друг.", "My best friend."),
            ],
        },
        {
            "lemma": "школа",
            "stressed": "шко\u0301ла",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["school"],
            "examples": [
                ("Дети идут в школу.", "Children go to school."),
            ],
        },
        {
            "lemma": "работа",
            "stressed": "рабо\u0301та",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["work", "job"],
            "examples": [
                ("У меня много работы.", "I have a lot of work."),
            ],
        },
        {
            "lemma": "день",
            "stressed": "день",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["day"],
            "examples": [
                ("Какой сегодня день?", "What day is today?"),
                ("Хорошего дня!", "Have a good day!"),
            ],
        },
        {
            "lemma": "ночь",
            "stressed": "ночь",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["night"],
            "examples": [
                ("Спокойной ночи!", "Good night!"),
            ],
        },
        {
            "lemma": "время",
            "stressed": " вре\u0301мя",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["time"],
            "examples": [
                ("Сколько времени?", "What time is it?"),
            ],
        },
        {
            "lemma": "маленький",
            "stressed": "ма\u0301ленький",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["small", "little"],
            "examples": [
                ("Маленький дом.", "A small house."),
            ],
        },
        {
            "lemma": "новый",
            "stressed": "но\u0301вый",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["new"],
            "examples": [
                ("Новый дом.", "A new house."),
            ],
        },
        {
            "lemma": "старый",
            "stressed": "ста\u0301рый",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["old"],
            "examples": [
                ("Старый дом.", "An old house."),
            ],
        },
        {
            "lemma": "белый",
            "stressed": "бе\u0301лый",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["white"],
            "examples": [
                ("Белый снег.", "White snow."),
            ],
        },
        {
            "lemma": "чёрный",
            "stressed": "чёрный",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["black"],
            "examples": [
                ("Чёрная кошка.", "A black cat."),
            ],
        },
        {
            "lemma": "красный",
            "stressed": "кра\u0301сный",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["red"],
            "examples": [
                ("Красное яблоко.", "A red apple."),
            ],
        },
        {
            "lemma": "синий",
            "stressed": "си\u0301ний",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["blue"],
            "examples": [
                ("Синее небо.", "Blue sky."),
            ],
        },
        {
            "lemma": "писать",
            "stressed": "писа\u0301ть",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to write"],
            "examples": [
                ("Я пишу письмо.", "I am writing a letter."),
            ],
        },
        {
            "lemma": "говорить",
            "stressed": "говори\u0301ть",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to speak", "to talk"],
            "examples": [
                ("Я говорю по-русски.", "I speak Russian."),
            ],
        },
        {
            "lemma": "знать",
            "stressed": "знать",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to know"],
            "examples": [
                ("Я знаю это.", "I know this."),
            ],
        },
        {
            "lemma": "хотеть",
            "stressed": "хоте\u0301ть",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to want"],
            "examples": [
                ("Я хочу чаю.", "I want some tea."),
            ],
        },
        {
            "lemma": "мочь",
            "stressed": "мочь",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to be able", "can"],
            "examples": [
                ("Я могу это сделать.", "I can do this."),
            ],
        },
        {
            "lemma": "делать",
            "stressed": "де\u0301лать",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to do", "to make"],
            "examples": [
                ("Что ты делаешь?", "What are you doing?"),
            ],
        },
        {
            "lemma": "спать",
            "stressed": "спать",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to sleep"],
            "examples": [
                ("Я ложусь спать.", "I go to bed."),
            ],
        },
        {
            "lemma": "ходить",
            "stressed": "хо\u0301дить",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to walk", "to go"],
            "examples": [
                ("Я хожу в школу.", "I go to school."),
            ],
        },
        {
            "lemma": "ехать",
            "stressed": "е\u0301хать",
            "pos": "verb",
            "cefr": "A1",
            "translations": ["to go (by transport)"],
            "examples": [
                ("Мы едем в Москву.", "We are going to Moscow."),
            ],
        },
        {
            "lemma": "хлеб",
            "stressed": "хлеб",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["bread"],
            "examples": [
                ("Свежий хлеб.", "Fresh bread."),
            ],
        },
        {
            "lemma": "молоко",
            "stressed": "молоко\u0301",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["milk"],
            "examples": [
                ("Молоко свежее.", "The milk is fresh."),
            ],
        },
        {
            "lemma": "мясо",
            "stressed": "мя\u0301со",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["meat"],
            "examples": [
                ("Мясо вкусное.", "The meat is tasty."),
            ],
        },
        {
            "lemma": "овощи",
            "stressed": "ово\u0301щи",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["vegetables"],
            "examples": [
                ("Свежие овощи.", "Fresh vegetables."),
            ],
        },
        {
            "lemma": "фрукты",
            "stressed": "фру\u0301кты",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["fruits"],
            "examples": [
                ("Фрукты полезны.", "Fruits are healthy."),
            ],
        },
        {
            "lemma": "яблоко",
            "stressed": "я\u0301блоко",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["apple"],
            "examples": [
                ("Яблоко красное.", "The apple is red."),
            ],
        },
        {
            "lemma": "кошка",
            "stressed": "ко\u0301шка",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["cat"],
            "examples": [
                ("Кошка спит.", "The cat is sleeping."),
            ],
        },
        {
            "lemma": "собака",
            "stressed": "соба\u0301ка",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["dog"],
            "examples": [
                ("Собака лает.", "The dog is barking."),
            ],
        },
        {
            "lemma": "окно",
            "stressed": "окно\u0301",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["window"],
            "examples": [
                ("Окно открыто.", "The window is open."),
            ],
        },
        {
            "lemma": "дверь",
            "stressed": "дверь",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["door"],
            "examples": [
                ("Дверь закрыта.", "The door is closed."),
            ],
        },
        {
            "lemma": "улица",
            "stressed": "у\u0301лица",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["street"],
            "examples": [
                ("Улица тихая.", "The street is quiet."),
            ],
        },
        {
            "lemma": "город",
            "stressed": "го\u0301род",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["city", "town"],
            "examples": [
                ("Большой город.", "A big city."),
            ],
        },
        {
            "lemma": "страна",
            "stressed": "стра\u0301на",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["country"],
            "examples": [
                ("Моя страна — Россия.", "My country is Russia."),
            ],
        },
        {
            "lemma": "русский",
            "stressed": "ру\u0301сский",
            "pos": "adjective",
            "cefr": "A1",
            "translations": ["Russian"],
            "examples": [
                ("Русский язык.", "Russian language."),
            ],
        },
        {
            "lemma": "человек",
            "stressed": "челове\u0301к",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["person", "human"],
            "examples": [
                ("Хороший человек.", "A good person."),
            ],
        },
        {
            "lemma": "женщина",
            "stressed": "же\u0301нщина",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["woman"],
            "examples": [
                ("Эта женщина врач.", "This woman is a doctor."),
            ],
        },
        {
            "lemma": "мужчина",
            "stressed": "мужчи\u0301на",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["man"],
            "examples": [
                ("Мужчина работает.", "The man is working."),
            ],
        },
        {
            "lemma": "ребёнок",
            "stressed": "ребё\u0301нок",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["child"],
            "examples": [
                ("Ребёнок спит.", "The child is sleeping."),
            ],
        },
        {
            "lemma": "врач",
            "stressed": "врач",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["doctor"],
            "examples": [
                ("Врач помогает.", "The doctor helps."),
            ],
        },
        {
            "lemma": "учитель",
            "stressed": "учи\u0301тель",
            "pos": "noun",
            "cefr": "A1",
            "translations": ["teacher"],
            "examples": [
                ("Учитель объясняет.", "The teacher explains."),
            ],
        },
        # A2 vocabulary
        {
            "lemma": "понимать",
            "stressed": "понима\u0301ть",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to understand"],
            "examples": [
                ("Я не понимаю.", "I don't understand."),
            ],
        },
        {
            "lemma": "думать",
            "stressed": "ду\u0301мать",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to think"],
            "examples": [
                ("Я думаю о вас.", "I am thinking about you."),
            ],
        },
        {
            "lemma": "ждать",
            "stressed": "ждать",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to wait"],
            "examples": [
                ("Я жду автобус.", "I am waiting for the bus."),
            ],
        },
        {
            "lemma": "брать",
            "stressed": "брать",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to take"],
            "examples": [
                ("Возьми книгу.", "Take the book."),
            ],
        },
        {
            "lemma": "давать",
            "stressed": "дава\u0301ть",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to give"],
            "examples": [
                ("Дай мне воды.", "Give me some water."),
            ],
        },
        {
            "lemma": "помогать",
            "stressed": "помога\u0301ть",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to help"],
            "examples": [
                ("Я помогу тебе.", "I will help you."),
            ],
        },
        {
            "lemma": "любить",
            "stressed": "люби\u0301ть",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to love", "to like"],
            "examples": [
                ("Я люблю музыку.", "I love music."),
            ],
        },
        {
            "lemma": "видеть",
            "stressed": "ви\u0301деть",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to see"],
            "examples": [
                ("Я вижу тебя.", "I see you."),
            ],
        },
        {
            "lemma": "слышать",
            "stressed": "слы\u0301шать",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to hear"],
            "examples": [
                ("Я слышу музыку.", "I hear music."),
            ],
        },
        {
            "lemma": "учить",
            "stressed": "у\u0301чить",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to learn", "to teach"],
            "examples": [
                ("Я учу русский.", "I am learning Russian."),
            ],
        },
        {
            "lemma": "путешествовать",
            "stressed": "путешествовать",
            "pos": "verb",
            "cefr": "A2",
            "translations": ["to travel"],
            "examples": [
                ("Я люблю путешествовать.", "I love to travel."),
            ],
        },
        {
            "lemma": "интересный",
            "stressed": "интере\u0301сный",
            "pos": "adjective",
            "cefr": "A2",
            "translations": ["interesting"],
            "examples": [
                ("Интересная книга.", "An interesting book."),
            ],
        },
        {
            "lemma": "важный",
            "stressed": "ва\u0301жный",
            "pos": "adjective",
            "cefr": "A2",
            "translations": ["important"],
            "examples": [
                ("Важный вопрос.", "An important question."),
            ],
        },
        {
            "lemma": "тёплый",
            "stressed": "тёплый",
            "pos": "adjective",
            "cefr": "A2",
            "translations": ["warm"],
            "examples": [
                ("Тёплая погода.", "Warm weather."),
            ],
        },
        {
            "lemma": "холодный",
            "stressed": "холо\u0301дный",
            "pos": "adjective",
            "cefr": "A2",
            "translations": ["cold"],
            "examples": [
                ("Холодная зима.", "Cold winter."),
            ],
        },
        {
            "lemma": "погода",
            "stressed": "пого\u0301да",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["weather"],
            "examples": [
                ("Какая сегодня погода?", "What is the weather like today?"),
            ],
        },
        {
            "lemma": "вокзал",
            "stressed": "вокза\u0301л",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["railway station"],
            "examples": [
                ("Встретимся на вокзале.", "Let's meet at the station."),
            ],
        },
        {
            "lemma": "аэропорт",
            "stressed": "аэропо\u0301рт",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["airport"],
            "examples": [
                ("Самолёт в аэропорту.", "The plane is at the airport."),
            ],
        },
        {
            "lemma": "билет",
            "stressed": "биле\u0301т",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["ticket"],
            "examples": [
                ("Купить билет.", "To buy a ticket."),
            ],
        },
        {
            "lemma": "гостиница",
            "stressed": "гостини\u0301ца",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["hotel"],
            "examples": [
                ("Бронировать гостиницу.", "To book a hotel."),
            ],
        },
        {
            "lemma": "ресторан",
            "stressed": "рестора\u0301н",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["restaurant"],
            "examples": [
                ("Ужин в ресторане.", "Dinner at a restaurant."),
            ],
        },
        {
            "lemma": "магазин",
            "stressed": "магази\u0301н",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["shop", "store"],
            "examples": [
                ("Идти в магазин.", "To go to the store."),
            ],
        },
        {
            "lemma": "деньги",
            "stressed": "де\u0301ньги",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["money"],
            "examples": [
                ("Мне нужны деньги.", "I need money."),
            ],
        },
        {
            "lemma": "цена",
            "stressed": "цена\u0301",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["price"],
            "examples": [
                ("Какая цена?", "What is the price?"),
            ],
        },
        {
            "lemma": "время",
            "stressed": "вре\u0301мя",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["time"],
            "examples": [
                ("Нет времени.", "There is no time."),
            ],
        },
        {
            "lemma": "минута",
            "stressed": "мину\u0301та",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["minute"],
            "examples": [
                ("Одна минута.", "One minute."),
            ],
        },
        {
            "lemma": "час",
            "stressed": "час",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["hour"],
            "examples": [
                ("Один час.", "One hour."),
            ],
        },
        {
            "lemma": "неделя",
            "stressed": "неде\u0301ля",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["week"],
            "examples": [
                ("На следующей неделе.", "Next week."),
            ],
        },
        {
            "lemma": "месяц",
            "stressed": "ме\u0301сяц",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["month"],
            "examples": [
                ("Этот месяц.", "This month."),
            ],
        },
        {
            "lemma": "год",
            "stressed": "год",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["year"],
            "examples": [
                ("С Новым годом!", "Happy New Year!"),
            ],
        },
        {
            "lemma": "письмо",
            "stressed": "письмо\u0301",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["letter"],
            "examples": [
                ("Написать письмо.", "To write a letter."),
            ],
        },
        {
            "lemma": "телефон",
            "stressed": "телефо\u0301н",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["telephone", "phone"],
            "examples": [
                ("Звонить по телефону.", "To call by phone."),
            ],
        },
        {
            "lemma": "компьютер",
            "stressed": "компью\u0301тер",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["computer"],
            "examples": [
                ("Работать на компьютере.", "To work on a computer."),
            ],
        },
        {
            "lemma": "Интернет",
            "stressed": "Интерне\u0301т",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["internet"],
            "examples": [
                ("Искать в Интернете.", "To search on the internet."),
            ],
        },
        {
            "lemma": "рабочий",
            "stressed": "рабо\u0301чий",
            "pos": "adjective",
            "cefr": "A2",
            "translations": ["working", "worker"],
            "examples": [
                ("Рабочий день.", "Working day."),
            ],
        },
        {
            "lemma": "праздник",
            "stressed": "пра\u0301здник",
            "pos": "noun",
            "cefr": "A2",
            "translations": ["holiday", "festival"],
            "examples": [
                ("С праздником!", "Happy holiday!"),
            ],
        },
        {
            "lemma": "красивый",
            "stressed": "краси\u0301вый",
            "pos": "adjective",
            "cefr": "A2",
            "translations": ["beautiful"],
            "examples": [
                ("Красивый город.", "A beautiful city."),
            ],
        },
        {
            "lemma": "разный",
            "stressed": "ра\u0301зный",
            "pos": "adjective",
            "cefr": "A2",
            "translations": ["different", "various"],
            "examples": [
                ("Разные люди.", "Different people."),
            ],
        },
        {
            "lemma": "иностранный",
            "stressed": "иностра\u0301нный",
            "pos": "adjective",
            "cefr": "A2",
            "translations": ["foreign"],
            "examples": [
                ("Иностранный язык.", "Foreign language."),
            ],
        },
        # B1 vocabulary
        {
            "lemma": "объяснять",
            "stressed": "объясня\u0301ть",
            "pos": "verb",
            "cefr": "B1",
            "translations": ["to explain"],
            "examples": [
                ("Объясните, пожалуйста.", "Please explain."),
            ],
        },
        {
            "lemma": "развивать",
            "stressed": "развива\u0301ть",
            "pos": "verb",
            "cefr": "B1",
            "translations": ["to develop"],
            "examples": [
                ("Развивать навыки.", "To develop skills."),
            ],
        },
        {
            "lemma": "достигать",
            "stressed": "достига\u0301ть",
            "pos": "verb",
            "cefr": "B1",
            "translations": ["to achieve"],
            "examples": [
                ("Достигать цели.", "To achieve a goal."),
            ],
        },
        {
            "lemma": "возможность",
            "stressed": "возмо\u0301жность",
            "pos": "noun",
            "cefr": "B1",
            "translations": ["opportunity", "possibility"],
            "examples": [
                ("Большая возможность.", "A great opportunity."),
            ],
        },
        {
            "lemma": "решение",
            "stressed": "реше\u0301ние",
            "pos": "noun",
            "cefr": "B1",
            "translations": ["decision", "solution"],
            "examples": [
                ("Принять решение.", "To make a decision."),
            ],
        },
        {
            "lemma": "опыт",
            "stressed": "о\u0301пыт",
            "pos": "noun",
            "cefr": "B1",
            "translations": ["experience"],
            "examples": [
                ("Богатый опыт.", "Rich experience."),
            ],
        },
        {
            "lemma": "значительный",
            "stressed": "значи\u0301тельный",
            "pos": "adjective",
            "cefr": "B1",
            "translations": ["significant"],
            "examples": [
                ("Значительный прогресс.", "Significant progress."),
            ],
        },
        {
            "lemma": "традиция",
            "stressed": "тради\u0301ция",
            "pos": "noun",
            "cefr": "B1",
            "translations": ["tradition"],
            "examples": [
                ("Русские традиции.", "Russian traditions."),
            ],
        },
        # B2 vocabulary
        {
            "lemma": "содействие",
            "stressed": "соде\u0301йствие",
            "pos": "noun",
            "cefr": "B2",
            "translations": ["assistance", "support"],
            "examples": [
                ("Оказывать содействие.", "To provide assistance."),
            ],
        },
        {
            "lemma": "предусматривать",
            "stressed": "предусма\u0301тривать",
            "pos": "verb",
            "cefr": "B2",
            "translations": ["to provide for", "to envisage"],
            "examples": [
                ("Закон предусматривает.", "The law provides for."),
            ],
        },
        {
            "lemma": "обстоятельство",
            "stressed": "обстоя\u0301тельство",
            "pos": "noun",
            "cefr": "B2",
            "translations": ["circumstance"],
            "examples": [
                ("В зависимости от обстоятельств.", "Depending on circumstances."),
            ],
        },
        {
            "lemma": "исключительный",
            "stressed": "исключи\u0301тельный",
            "pos": "adjective",
            "cefr": "B2",
            "translations": ["exceptional"],
            "examples": [
                ("Исключительный случай.", "An exceptional case."),
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
