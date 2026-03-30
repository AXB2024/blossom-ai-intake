export type InsuranceProvider = 'Aetna' | 'BlueCross' | 'Cigna' | 'United' | 'SelfPay';
export type PlanType = 'PPO' | 'HMO' | 'EPO' | 'None';

export interface SymptomChecklist {
  low_mood: boolean;
  panic_attacks: boolean;
  attention_issues: boolean;
  sleep_issues: boolean;
  appetite_changes: boolean;
  racing_thoughts: boolean;
  trauma_flashbacks: boolean;
  suicidal_thoughts: boolean;
}

export interface CarePreferences {
  visit_mode: 'Virtual' | 'In-Person' | 'Either';
  provider_gender_preference: 'No Preference' | 'Female' | 'Male' | 'Non-binary';
  language: 'English' | 'Spanish';
  availability: 'Weekday Morning' | 'Weekday Evening' | 'Weekend' | 'Flexible';
}

export interface IntakePayload {
  patient_name: string;
  age: number;
  symptoms_text: string;
  symptom_duration_weeks: number;
  severity_score: number;
  checklist: SymptomChecklist;
  prior_treatment: string;
  medication_history: string;
  insurance: {
    provider: InsuranceProvider;
    plan_type: PlanType;
    deductible_met: boolean;
  };
  care_preferences: CarePreferences;
}

export interface CostEstimate {
  per_visit_estimate: number;
  monthly_estimate: number;
  coverage_rate: number;
  deductible_note: string;
  breakdown: Record<string, number>;
}

export interface ModelExplanation {
  top_keywords: string[];
  keyword_contributions: Record<string, number>;
  rule_triggers: string[];
  summary: string;
}

export interface ProviderMatch {
  provider_name: string;
  specialty: string;
  score: number;
  reason: string;
}

export interface IntakeResult {
  session_id: string;
  created_at: string;
  predicted_condition: string;
  confidence: number;
  care_recommendation: string;
  triage_level: 'Standard' | 'Priority' | 'Urgent';
  care_pathway: string;
  cost_estimate: CostEstimate;
  model_explanation: ModelExplanation;
  provider_matches: ProviderMatch[];
}

export interface SessionSummary {
  session_id: string;
  patient_name: string;
  created_at: string;
  predicted_condition: string;
  care_recommendation: string;
  monthly_estimate: number;
}

export interface AnalyticsSummary {
  total_sessions: number;
  by_condition: Record<string, number>;
  avg_monthly_estimate: number;
}
