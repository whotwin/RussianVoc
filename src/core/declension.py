"""Russian declension and conjugation using pymorphy3."""
from typing import Optional

# Russian grammatical cases
CASES = ["nomn", "gent", "datv", "accs", "ablt", "loct"]
CASE_NAMES = {
    "nomn": "Именительный (Кто? Что?)",
    "gent": "Родительный (Кого? Чего?)",
    "datv": "Дательный (Кому? Чему?)",
    "accs": "Винительный (Кого? Что?)",
    "ablt": "Творительный (Кем? Чем?)",
    "loct": "Предложный (О ком? О чём?)",
}

PERSONS = ["1per", "2per", "3per"]
PERSON_NAMES = {"1per": "1-е лицо", "2per": "2-е лицо", "3per": "3-е лицо"}

TENSES = ["pres", "past", "futr"]
TENSE_NAMES = {"pres": "Настоящее", "past": "Прошедшее", "futr": "Будущее"}

_morph = None


def _get_morph():
    """Lazily initialize pymorphy3 MorphAnalyzer."""
    global _morph
    if _morph is None:
        import pymorphy3
        _morph = pymorphy3.MorphAnalyzer()
    return _morph


def get_word_analysis(word: str):
    """Get pymorphy3 analysis for a word."""
    return _get_morph().parse(word)


def get_normal_form(word: str) -> Optional[str]:
    parses = get_word_analysis(word)
    if parses:
        return parses[0].normal_form
    return None


def get_pos(word: str) -> Optional[str]:
    parses = get_word_analysis(word)
    if not parses:
        return None
    p = parses[0]
    tag = str(p.tag)
    if "NOUN" in tag:
        return "noun"
    elif "VERB" in tag or "INFN" in tag:
        return "verb"
    elif "ADJF" in tag or "ADJS" in tag:
        return "adjective"
    elif "ADVB" in tag:
        return "adverb"
    elif "PRON" in tag or "NPRO" in tag:
        return "pronoun"
    elif "PREP" in tag:
        return "preposition"
    elif "CONJ" in tag:
        return "conjunction"
    elif "NUMR" in tag:
        return "numeral"
    elif "INTJ" in tag:
        return "interjection"
    else:
        return "other"


def predict_stress(word: str) -> int:
    """Predict stress position using pymorphy2."""
    try:
        parses = get_word_analysis(word)
        if parses:
            p = parses[0]
            # Try to get predicted accent
            if hasattr(p, "accented"):
                accented = p.accented
                for i, char in enumerate(word):
                    if i < len(accented):
                        pass
            # Fallback: use last vowel position as heuristic
            for i in range(len(word) - 1, -1, -1):
                ch = word[i].lower()
                if ch in "аеёиоуыэюя":
                    return i
            # First vowel fallback
            for i, ch in enumerate(word.lower()):
                if ch in "аеёиоуыэюя":
                    return i
    except Exception:
        pass
    return 0


def decline_noun(word: str, stressed: str = None) -> dict:
    """Generate noun declensions for all cases (singular + plural)."""
    result = {}
    parses = get_word_analysis(word)
    if not parses:
        return result

    p = parses[0]
    for case in CASES:
        singular = p.inflect({case})
        if singular:
            form = singular.word
            result[f"{case}_singular"] = {"form": form, "form_stressed": form}

        plural = p.inflect({case, "plur"})
        if plural:
            form = plural.word
            result[f"{case}_plural"] = {"form": form, "form_stressed": form}

    return result


def conjugate_verb(word: str, stressed: str = None) -> dict:
    """Generate verb conjugations for all persons and tenses."""
    result = {}
    parses = get_word_analysis(word)
    if not parses:
        return result

    p = parses[0]
    for tense in TENSES:
        for person in PERSONS:
            for number in ["sing", "plur"]:
                tag_set = {tense, person}
                if number == "sing":
                    tag_set.add("sing")
                else:
                    tag_set.add("plur")

                inflected = p.inflect(tag_set)
                if inflected:
                    form = inflected.word
                    result[f"{tense}_{person}_{number}"] = {
                        "form": form,
                        "form_stressed": form,
                    }

    return result


def decline_adjective(word: str, stressed: str = None) -> dict:
    """Generate adjective declensions."""
    result = {}
    parses = get_word_analysis(word)
    if not parses:
        return result

    p = parses[0]
    genders = ["masc", "femn", "neut"]

    for gender in genders:
        for case in CASES:
            inflected = p.inflect({case, gender})
            if inflected:
                form = inflected.word
                result[f"{case}_{gender}"] = {"form": form, "form_stressed": form}

    for case in CASES:
        inflected = p.inflect({case, "plur"})
        if inflected:
            form = inflected.word
            result[f"{case}_plural"] = {"form": form, "form_stressed": form}

    return result


def format_declension_table(decls: dict) -> list[list[str]]:
    """Format declension results as a table."""
    table = []
    singular = {k: v for k, v in decls.items() if "singular" in k}
    plural = {k: v for k, v in decls.items() if "plural" in k}

    case_order = ["nomn", "gent", "datv", "accs", "ablt", "loct"]
    case_short = ["Им", "Род", "Дат", "Вин", "Твор", "Пред"]

    for i, case in enumerate(case_order):
        sing_val = singular.get(f"{case}_singular", {}).get("form_stressed", "—")
        plur_val = plural.get(f"{case}_plural", {}).get("form_stressed", "—")
        table.append([case_short[i], sing_val, plur_val])

    return table
