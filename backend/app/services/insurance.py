from __future__ import annotations

from typing import Dict

from app.schemas import InsuranceInfo

BASE_RATES = {
    "therapy_session": 140.0,
    "psychiatry_eval": 260.0,
    "psychiatry_followup": 180.0,
}

COVERAGE_TABLE = {
    "Aetna": {"PPO": 0.72, "HMO": 0.66, "EPO": 0.64, "None": 0.0},
    "BlueCross": {"PPO": 0.7, "HMO": 0.65, "EPO": 0.62, "None": 0.0},
    "Cigna": {"PPO": 0.68, "HMO": 0.62, "EPO": 0.6, "None": 0.0},
    "United": {"PPO": 0.67, "HMO": 0.61, "EPO": 0.59, "None": 0.0},
    "SelfPay": {"PPO": 0.0, "HMO": 0.0, "EPO": 0.0, "None": 0.0},
}


def _care_plan_units(care_pathway: str) -> Dict[str, int]:
    if care_pathway == "therapy_only":
        return {"therapy_session": 4}
    if care_pathway == "psychiatry_only":
        return {"psychiatry_eval": 1, "psychiatry_followup": 1}
    return {"therapy_session": 2, "psychiatry_eval": 1, "psychiatry_followup": 1}


def estimate_cost(care_pathway: str, insurance: InsuranceInfo) -> Dict[str, object]:
    units = _care_plan_units(care_pathway)
    gross_breakdown = {service: round(BASE_RATES[service] * count, 2) for service, count in units.items()}
    gross_monthly = round(sum(gross_breakdown.values()), 2)

    base_coverage = COVERAGE_TABLE[insurance.provider][insurance.plan_type]
    effective_coverage = base_coverage
    deductible_note = "Deductible met. Coinsurance applied."

    if insurance.provider == "SelfPay":
        effective_coverage = 0.0
        deductible_note = "Self-pay selected. Full listed rates apply."
    elif not insurance.deductible_met:
        effective_coverage = max(base_coverage - 0.35, 0.1)
        deductible_note = "Deductible not met. Estimate assumes temporary lower coverage."

    patient_monthly = round(gross_monthly * (1 - effective_coverage), 2)
    total_visits = max(sum(units.values()), 1)
    per_visit = round(patient_monthly / total_visits, 2)

    patient_breakdown = {
        service: round(cost * (1 - effective_coverage), 2) for service, cost in gross_breakdown.items()
    }

    return {
        "per_visit_estimate": per_visit,
        "monthly_estimate": patient_monthly,
        "coverage_rate": round(effective_coverage, 2),
        "deductible_note": deductible_note,
        "breakdown": patient_breakdown,
    }
