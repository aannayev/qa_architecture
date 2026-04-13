from __future__ import annotations

from app.domain.models import Difficulty, Question

SEED_QUESTIONS: list[dict] = [
    {
        "external_id": "hist-ancient-001",
        "topic": "ancient-world",
        "difficulty": Difficulty.EASY,
        "prompt": "In which modern country were the Pyramids of Giza built?",
        "options": ["Egypt", "Greece", "Italy", "Iraq"],
        "correct_index": 0,
        "explanation": "The Pyramids of Giza were built in ancient Egypt during the Old Kingdom.",
    },
    {
        "external_id": "hist-ancient-002",
        "topic": "ancient-world",
        "difficulty": Difficulty.MEDIUM,
        "prompt": "Who was the first Roman emperor?",
        "options": ["Julius Caesar", "Augustus", "Nero", "Constantine"],
        "correct_index": 1,
        "explanation": "Augustus (Octavian) became the first Roman emperor in 27 BC.",
    },
    {
        "external_id": "hist-medieval-001",
        "topic": "medieval",
        "difficulty": Difficulty.EASY,
        "prompt": "Which event is commonly used to mark the start of the High Middle Ages?",
        "options": [
            "Fall of Rome",
            "Battle of Hastings",
            "First Crusade",
            "Discovery of America",
        ],
        "correct_index": 2,
        "explanation": "Historians commonly date the High Middle Ages from around the First Crusade (1096).",
    },
    {
        "external_id": "hist-modern-001",
        "topic": "modern",
        "difficulty": Difficulty.MEDIUM,
        "prompt": "In what year did World War II end?",
        "options": ["1943", "1944", "1945", "1946"],
        "correct_index": 2,
        "explanation": "World War II ended in 1945 with Germany's surrender in May and Japan's in September.",
    },
    {
        "external_id": "hist-modern-002",
        "topic": "modern",
        "difficulty": Difficulty.HARD,
        "prompt": "Which treaty formally ended the Thirty Years' War?",
        "options": [
            "Treaty of Versailles",
            "Peace of Westphalia",
            "Treaty of Utrecht",
            "Congress of Vienna",
        ],
        "correct_index": 1,
        "explanation": "The Peace of Westphalia (1648) ended the Thirty Years' War and reshaped European sovereignty.",
    },
]


def build_seed_questions() -> list[Question]:
    return [Question(**data) for data in SEED_QUESTIONS]
