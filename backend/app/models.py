from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient_name: Mapped[str] = mapped_column(String(120))
    age: Mapped[int] = mapped_column(Integer)
    insurance_provider: Mapped[str] = mapped_column(String(120))
    insurance_plan: Mapped[str] = mapped_column(String(50))
    deductible_met: Mapped[int] = mapped_column(Integer, default=0)

    symptoms_text: Mapped[str] = mapped_column(Text)
    checklist_json: Mapped[str] = mapped_column(Text)
    history_json: Mapped[str] = mapped_column(Text)
    preferences_json: Mapped[str] = mapped_column(Text)

    ml_condition: Mapped[str] = mapped_column(String(80))
    ml_confidence: Mapped[float] = mapped_column(Float)
    rule_condition: Mapped[str] = mapped_column(String(80))
    final_condition: Mapped[str] = mapped_column(String(80))
    care_recommendation: Mapped[str] = mapped_column(String(120))
    triage_level: Mapped[str] = mapped_column(String(30), default="Standard")
    care_pathway: Mapped[str] = mapped_column(String(60), default="therapy_only")

    monthly_estimate: Mapped[float] = mapped_column(Float)
    per_visit_estimate: Mapped[float] = mapped_column(Float)
    estimate_breakdown_json: Mapped[str] = mapped_column(Text)

    explanation_json: Mapped[str] = mapped_column(Text)
    provider_matches_json: Mapped[str] = mapped_column(Text)
