from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IntakeSession
from app.schemas import AnalyticsResponse, IntakeRequest, IntakeResponse, SessionSummary
from app.services.insurance import estimate_cost
from app.services.provider_matching import match_providers
from app.services.triage import HybridTriageService

router = APIRouter(tags=["intake"])
triage_service = HybridTriageService()


@router.post("/intake/process", response_model=IntakeResponse)
def process_intake(payload: IntakeRequest, db: Session = Depends(get_db)) -> IntakeResponse:
    triage_result = triage_service.process(payload)
    cost_result = estimate_cost(triage_result["care_pathway"], payload.insurance)
    provider_matches = match_providers(triage_result["predicted_condition"], payload.care_preferences)

    record = IntakeSession(
        patient_name=payload.patient_name,
        age=payload.age,
        insurance_provider=payload.insurance.provider,
        insurance_plan=payload.insurance.plan_type,
        deductible_met=1 if payload.insurance.deductible_met else 0,
        symptoms_text=payload.symptoms_text,
        checklist_json=json.dumps(payload.checklist.model_dump()),
        history_json=json.dumps(
            {
                "symptom_duration_weeks": payload.symptom_duration_weeks,
                "prior_treatment": payload.prior_treatment,
                "medication_history": payload.medication_history,
                "severity_score": payload.severity_score,
            }
        ),
        preferences_json=json.dumps(payload.care_preferences.model_dump()),
        ml_condition=triage_result["ml_condition"],
        ml_confidence=triage_result["confidence"],
        rule_condition=triage_result["rule_condition"],
        final_condition=triage_result["predicted_condition"],
        care_recommendation=triage_result["care_recommendation"],
        triage_level=triage_result["triage_level"],
        care_pathway=triage_result["care_pathway"],
        monthly_estimate=cost_result["monthly_estimate"],
        per_visit_estimate=cost_result["per_visit_estimate"],
        estimate_breakdown_json=json.dumps(cost_result),
        explanation_json=json.dumps(triage_result["model_explanation"]),
        provider_matches_json=json.dumps(provider_matches),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return IntakeResponse(
        session_id=record.id,
        created_at=record.created_at,
        predicted_condition=triage_result["predicted_condition"],
        confidence=triage_result["confidence"],
        care_recommendation=triage_result["care_recommendation"],
        triage_level=triage_result["triage_level"],
        care_pathway=triage_result["care_pathway"],
        cost_estimate=cost_result,
        model_explanation=triage_result["model_explanation"],
        provider_matches=provider_matches,
    )


@router.get("/sessions", response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_db)) -> list[SessionSummary]:
    sessions = db.query(IntakeSession).order_by(IntakeSession.created_at.desc()).limit(50).all()

    return [
        SessionSummary(
            session_id=row.id,
            patient_name=row.patient_name,
            created_at=row.created_at,
            predicted_condition=row.final_condition,
            care_recommendation=row.care_recommendation,
            monthly_estimate=row.monthly_estimate,
        )
        for row in sessions
    ]


@router.get("/sessions/{session_id}", response_model=IntakeResponse)
def get_session(session_id: str, db: Session = Depends(get_db)) -> IntakeResponse:
    row = db.query(IntakeSession).filter(IntakeSession.id == session_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    cost = json.loads(row.estimate_breakdown_json)
    explanation = json.loads(row.explanation_json)
    provider_matches = json.loads(row.provider_matches_json)

    return IntakeResponse(
        session_id=row.id,
        created_at=row.created_at,
        predicted_condition=row.final_condition,
        confidence=row.ml_confidence,
        care_recommendation=row.care_recommendation,
        triage_level=row.triage_level,
        care_pathway=row.care_pathway,
        cost_estimate=cost,
        model_explanation=explanation,
        provider_matches=provider_matches,
    )


@router.get("/analytics/common-issues", response_model=AnalyticsResponse)
def common_issues(db: Session = Depends(get_db)) -> AnalyticsResponse:
    total_sessions = db.query(func.count(IntakeSession.id)).scalar() or 0

    grouped = (
        db.query(IntakeSession.final_condition, func.count(IntakeSession.id))
        .group_by(IntakeSession.final_condition)
        .all()
    )
    by_condition = {condition: count for condition, count in grouped}

    avg_monthly = db.query(func.avg(IntakeSession.monthly_estimate)).scalar() or 0.0

    return AnalyticsResponse(
        total_sessions=total_sessions,
        by_condition=by_condition,
        avg_monthly_estimate=round(float(avg_monthly), 2),
    )
