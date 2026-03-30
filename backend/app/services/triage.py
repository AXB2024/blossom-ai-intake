from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from app.ml.model import TfidfConditionClassifier
from app.schemas import IntakeRequest

KEYWORD_RULES = {
    "anxiety": ["worry", "panic", "nervous", "anxious", "overthinking", "fear", "tense"],
    "depression": ["sad", "hopeless", "empty", "worthless", "low mood", "fatigue", "numb"],
    "adhd": ["focus", "distracted", "impulsive", "procrastinate", "forget", "attention"],
    "ptsd": ["trauma", "flashback", "nightmare", "unsafe", "trigger", "hypervigilance"],
    "bipolar": ["manic", "mood swings", "euphoric", "risky", "racing thoughts", "high energy"],
}


class HybridTriageService:
    def __init__(self) -> None:
        self.classifier = TfidfConditionClassifier()

    def process(self, intake: IntakeRequest) -> Dict[str, object]:
        ml_result = self.classifier.predict(intake.symptoms_text)
        rule_scores, rule_triggers = self._rule_scores(intake)

        combined_scores: Dict[str, float] = {}
        total_rule = sum(rule_scores.values()) or 1.0
        for condition, prob in ml_result["class_probabilities"].items():
            rule_component = rule_scores[condition] / total_rule
            combined_scores[condition] = round((0.7 * prob) + (0.3 * rule_component), 4)

        final_condition = max(combined_scores, key=combined_scores.get)
        confidence = combined_scores[final_condition]
        care = self._recommend_care(final_condition, intake)

        explanation_summary = (
            f"Model prediction leaned toward {final_condition} based on language patterns and symptom rules. "
            f"Top factors: {', '.join(ml_result['top_keywords'][:3]) or 'limited text signals'}"
        )

        return {
            "predicted_condition": final_condition,
            "confidence": confidence,
            "rule_condition": max(rule_scores, key=rule_scores.get),
            "ml_condition": ml_result["predicted_condition"],
            "care_recommendation": care["care_recommendation"],
            "care_pathway": care["care_pathway"],
            "triage_level": care["triage_level"],
            "class_probabilities": combined_scores,
            "model_explanation": {
                "top_keywords": ml_result["top_keywords"],
                "keyword_contributions": ml_result["keyword_contributions"],
                "rule_triggers": rule_triggers,
                "summary": explanation_summary,
            },
        }

    def _rule_scores(self, intake: IntakeRequest) -> tuple[Dict[str, float], List[str]]:
        text = intake.symptoms_text.lower()
        scores = defaultdict(lambda: 0.5)
        for condition in KEYWORD_RULES:
            scores[condition] = 0.5
        triggers: List[str] = []

        for condition, keywords in KEYWORD_RULES.items():
            for keyword in keywords:
                if keyword in text:
                    scores[condition] += 1.0
                    triggers.append(f"Mentioned '{keyword}'")

        if intake.checklist.low_mood:
            scores["depression"] += 1.8
            triggers.append("Checklist: low mood")
        if intake.checklist.panic_attacks:
            scores["anxiety"] += 1.8
            triggers.append("Checklist: panic attacks")
        if intake.checklist.attention_issues:
            scores["adhd"] += 2.0
            triggers.append("Checklist: attention issues")
        if intake.checklist.sleep_issues:
            scores["anxiety"] += 0.8
            scores["depression"] += 0.8
            triggers.append("Checklist: sleep issues")
        if intake.checklist.trauma_flashbacks:
            scores["ptsd"] += 2.3
            triggers.append("Checklist: trauma flashbacks")
        if intake.checklist.racing_thoughts:
            scores["bipolar"] += 1.6
            scores["anxiety"] += 0.5
            triggers.append("Checklist: racing thoughts")
        if intake.checklist.suicidal_thoughts:
            scores["depression"] += 2.5
            triggers.append("Checklist: suicidal thoughts")

        if intake.severity_score >= 8:
            scores["depression"] += 0.6
            scores["bipolar"] += 0.4
            scores["ptsd"] += 0.4
            triggers.append("High severity score")

        if intake.symptom_duration_weeks >= 24:
            scores["depression"] += 0.4
            scores["adhd"] += 0.4
            triggers.append("Long symptom duration")

        return dict(scores), triggers[:10]

    def _recommend_care(self, condition: str, intake: IntakeRequest) -> Dict[str, str]:
        severe = intake.severity_score >= 8
        medium = intake.severity_score >= 6

        if intake.checklist.suicidal_thoughts:
            return {
                "care_recommendation": "Urgent psychiatric evaluation + weekly therapy",
                "care_pathway": "combined",
                "triage_level": "Urgent",
            }

        if condition in {"bipolar", "ptsd"}:
            return {
                "care_recommendation": "Psychiatry + trauma-informed therapy",
                "care_pathway": "combined",
                "triage_level": "Priority" if medium else "Standard",
            }

        if condition == "adhd":
            if medium or severe:
                return {
                    "care_recommendation": "Psychiatry assessment + coaching/therapy",
                    "care_pathway": "combined",
                    "triage_level": "Priority",
                }
            return {
                "care_recommendation": "Psychiatry-focused ADHD evaluation",
                "care_pathway": "psychiatry_only",
                "triage_level": "Standard",
            }

        if condition == "depression":
            if severe:
                return {
                    "care_recommendation": "Psychiatry + therapy for stabilization",
                    "care_pathway": "combined",
                    "triage_level": "Priority",
                }
            return {
                "care_recommendation": "Therapy-first approach with monitoring",
                "care_pathway": "therapy_only",
                "triage_level": "Standard",
            }

        if condition == "anxiety":
            if medium:
                return {
                    "care_recommendation": "Therapy + optional psychiatry consult",
                    "care_pathway": "combined",
                    "triage_level": "Standard",
                }
            return {
                "care_recommendation": "Therapy-first anxiety program",
                "care_pathway": "therapy_only",
                "triage_level": "Standard",
            }

        return {
            "care_recommendation": "General therapy intake",
            "care_pathway": "therapy_only",
            "triage_level": "Standard",
        }
