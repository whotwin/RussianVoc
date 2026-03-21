"""Word processing: stress marking, normalization, search."""
import re
from typing import Optional


def add_stress_mark(lemma: str, stress_pos: int) -> str:
    """Add combining acute accent (U+0301) at stress position.

    stress_pos is 0-indexed from the start of the word.
    """
    if stress_pos < 0 or stress_pos >= len(lemma):
        return lemma
    return lemma[:stress_pos] + "\u0301" + lemma[stress_pos:]


def remove_stress_marks(word: str) -> str:
    """Remove combining accent marks from a word."""
    return word.replace("\u0301", "")


def normalize_text(text: str) -> str:
    """Normalize text for searching: lowercase, remove stress marks."""
    return remove_stress_marks(text).lower().strip()


def cyrillic_to_latin(text: str) -> str:
    """Convert Cyrillic to Latin transliteration (approximate)."""
    cyrillic = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    latin = "abvgdeezhziyklmnoprsftkhcshshch'ye'yu"
    mapping = dict(zip(cyrillic, latin))

    result = []
    for ch in text.lower():
        if ch in mapping:
            result.append(mapping[ch])
        else:
            result.append(ch)
    return "".join(result)


def highlight_stress(word: str) -> str:
    """Return word with stress highlighted using combining acute accent."""
    # This is a placeholder - actual stress comes from word_stress table
    return word


def is_cyrillic(text: str) -> bool:
    """Check if text contains Cyrillic characters."""
    cyrillic_pattern = re.compile(r"[\u0400-\u04FF]")
    return bool(cyrillic_pattern.search(text))


def split_word_syllables(word: str) -> list[str]:
    """Split a Russian word into syllables (approximate)."""
    # Russian syllables typically end with a vowel
    vowels = "аеёиоуыэюяaeiouy"
    syllables = []
    current = ""

    for ch in word.lower():
        current += ch
        if ch in vowels:
            syllables.append(current)
            current = ""

    if current:
        syllables[-1] += current if syllables else current

    return syllables


def fuzzy_match(query: str, target: str) -> bool:
    """Simple fuzzy matching between query and target."""
    query_norm = normalize_text(query)
    target_norm = normalize_text(target)
    return query_norm in target_norm or target_norm in query_norm


def get_word_start(query: str, target: str) -> bool:
    """Check if query matches the start of target."""
    return normalize_text(target).startswith(normalize_text(query))
