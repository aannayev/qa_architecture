from __future__ import annotations

from app.domain.models import Difficulty, Question

SEED_QUESTIONS: list[dict] = [
    {
        "external_id": "phys-mech-001",
        "topic": "mechanics",
        "difficulty": Difficulty.EASY,
        "prompt": "Which equation expresses Newton's second law of motion?",
        "options": ["E = mc^2", "F = ma", "V = IR", "pV = nRT"],
        "correct_index": 1,
        "explanation": "Newton's second law states that the net force on an object equals its mass times its acceleration: F = ma.",
    },
    {
        "external_id": "phys-mech-002",
        "topic": "mechanics",
        "difficulty": Difficulty.MEDIUM,
        "prompt": "What is the SI unit of force?",
        "options": ["Joule", "Pascal", "Newton", "Watt"],
        "correct_index": 2,
        "explanation": "The Newton (N) is the SI unit of force, defined as the force needed to accelerate 1 kg at 1 m/s^2.",
    },
    {
        "external_id": "phys-thermo-001",
        "topic": "thermodynamics",
        "difficulty": Difficulty.MEDIUM,
        "prompt": "Which law of thermodynamics expresses conservation of energy?",
        "options": [
            "Zeroth law",
            "First law",
            "Second law",
            "Third law",
        ],
        "correct_index": 1,
        "explanation": "The first law of thermodynamics is the law of conservation of energy applied to thermodynamic systems.",
    },
    {
        "external_id": "phys-em-001",
        "topic": "electromagnetism",
        "difficulty": Difficulty.EASY,
        "prompt": "Approximately what is the speed of light in vacuum?",
        "options": [
            "3 x 10^6 m/s",
            "3 x 10^7 m/s",
            "3 x 10^8 m/s",
            "3 x 10^9 m/s",
        ],
        "correct_index": 2,
        "explanation": "The speed of light in vacuum is approximately 3 x 10^8 m/s (exactly 299,792,458 m/s).",
    },
    {
        "external_id": "phys-modern-001",
        "topic": "modern-physics",
        "difficulty": Difficulty.HARD,
        "prompt": "Which particle was confirmed at the LHC in 2012, completing the Standard Model?",
        "options": ["Top quark", "Tau neutrino", "Higgs boson", "W boson"],
        "correct_index": 2,
        "explanation": "The Higgs boson was confirmed at CERN's Large Hadron Collider in 2012 — the last missing piece of the Standard Model.",
    },
]


def build_seed_questions() -> list[Question]:
    return [Question(**data) for data in SEED_QUESTIONS]
