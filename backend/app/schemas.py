from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal

from pydantic import BaseModel, Field


class SymptomChecklist(BaseModel):
    low_mood: bool = False
    panic_attacks: bool = False
    attention_issues: bool = False
    sleep_issues: bool = False
    appetite_changes: bool = False
    racing_thoughts: bool = False
    trauma_flashbacks: bool = False
    suicidal_thoughts: bool = False


class InsuranceInfo(BaseModel):
    provider: Literal["Aetna", "BlueCross", "Cigna", "United", "SelfPay"]
    plan_type: Literal["PPO", "HMO", "EPO", "None"]
    deductible_met: bool = False


class CarePreferences(BaseModel):
    visit_mode: Literal["Virtual", "In-Person", "Either"] = "Either"
    provider_gender_preference: Literal["No Preference", "Female", "Male", "Non-binary"] = "No Preference"
    language: Literal["English", "Spanish"] = "English"
    availability: Literal["Weekday Morning", "Weekday Evening", "Weekend", "Flexible"] = "Flexible"


class IntakeRequest(BaseModel):
    patient_name: str = Field(min_length=2, max_length=120)
    age: int = Field(ge=13, le=95)
    symptoms_text: str = Field(min_length=10, max_length=2500)
    symptom_duration_weeks: int = Field(ge=1, le=520)
    severity_score: int = Field(ge=1, le=10)
    checklist: SymptomChecklist
    prior_treatment: str = Field(min_length=2, max_length=1200)
    medication_history: str = Field(min_length=2, max_length=1200)
    insurance: InsuranceInfo
    care_preferences: CarePreferences


class CostEstimate(BaseModel):
    per_visit_estimate: float
    monthly_estimate: float
    coverage_rate: float
    deductible_note: str
    breakdown: Dict[str, float]


class ModelExplanation(BaseModel):
    top_keywords: List[str]
    keyword_contributions: Dict[str, float]
    rule_triggers: List[str]
    summary: str


class ProviderMatch(BaseModel):
    provider_name: str
    specialty: str
    score: float
    reason: str


class IntakeResponse(BaseModel):
    session_id: str
    created_at: datetime
    predicted_condition: str
    confidence: float
    care_recommendation: str
    triage_level: Literal["Standard", "Priority", "Urgent"]
    care_pathway: str
    cost_estimate: CostEstimate
    model_explanation: ModelExplanation
    provider_matches: List[ProviderMatch]


class SessionSummary(BaseModel):
    session_id: str
    patient_name: str
    created_at: datetime
    predicted_condition: str
    care_recommendation: str
    monthly_estimate: float


class AnalyticsResponse(BaseModel):
    total_sessions: int
    by_condition: Dict[str, int]
    avg_monthly_estimate: float
