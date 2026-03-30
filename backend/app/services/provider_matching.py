from __future__ import annotations

from typing import Dict, List

from app.schemas import CarePreferences

PROVIDERS = [
    {
        "provider_name": "Dr. Alina Torres",
        "specialty": "Anxiety & Depression",
        "conditions": {"anxiety", "depression"},
        "visit_modes": {"Virtual", "In-Person"},
        "languages": {"English", "Spanish"},
        "availability": {"Weekday Evening", "Flexible"},
    },
    {
        "provider_name": "Dr. Marcus Lee",
        "specialty": "Adult ADHD",
        "conditions": {"adhd", "anxiety"},
        "visit_modes": {"Virtual"},
        "languages": {"English"},
        "availability": {"Weekday Morning", "Flexible"},
    },
    {
        "provider_name": "Dr. Nia Watson",
        "specialty": "Trauma & PTSD",
        "conditions": {"ptsd", "depression"},
        "visit_modes": {"Virtual", "In-Person"},
        "languages": {"English"},
        "availability": {"Weekend", "Weekday Evening"},
    },
    {
        "provider_name": "Dr. Evan Campbell",
        "specialty": "Mood Disorders",
        "conditions": {"bipolar", "depression"},
        "visit_modes": {"Virtual"},
        "languages": {"English"},
        "availability": {"Weekday Evening", "Flexible"},
    },
]


def _score_provider(condition: str, preference: CarePreferences, provider: Dict[str, object]) -> tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    if condition in provider["conditions"]:
        score += 0.45
        reasons.append("Specializes in your likely care need")

    if preference.visit_mode == "Either" or preference.visit_mode in provider["visit_modes"]:
        score += 0.2
        reasons.append("Supports your preferred visit format")

    if preference.language in provider["languages"]:
        score += 0.2
        reasons.append("Matches language preference")

    if preference.availability in provider["availability"] or "Flexible" in provider["availability"]:
        score += 0.15
        reasons.append("Has appointment windows aligned with your schedule")

    return round(score, 2), reasons


def match_providers(condition: str, preference: CarePreferences, top_k: int = 3):
    scored = []
    for provider in PROVIDERS:
        score, reasons = _score_provider(condition, preference, provider)
        scored.append(
            {
                "provider_name": provider["provider_name"],
                "specialty": provider["specialty"],
                "score": score,
                "reason": "; ".join(reasons),
            }
        )

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
