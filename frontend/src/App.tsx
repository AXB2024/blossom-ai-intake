import { FormEvent, useEffect, useMemo, useState } from 'react';
import { fetchAnalytics, fetchSessions, processIntake } from './api/client';
import { AnalyticsSummary, IntakePayload, IntakeResult, SessionSummary, SymptomChecklist } from './types';

const STEP_TITLES = ['Insurance Basics', 'Symptom Intake', 'History & Preferences'];

const CHECKLIST_FIELDS: { key: keyof SymptomChecklist; label: string }[] = [
  { key: 'low_mood', label: 'Low mood or sadness' },
  { key: 'panic_attacks', label: 'Panic attacks' },
  { key: 'attention_issues', label: 'Focus/attention issues' },
  { key: 'sleep_issues', label: 'Sleep disturbance' },
  { key: 'appetite_changes', label: 'Appetite changes' },
  { key: 'racing_thoughts', label: 'Racing thoughts' },
  { key: 'trauma_flashbacks', label: 'Trauma flashbacks/nightmares' },
  { key: 'suicidal_thoughts', label: 'Suicidal thoughts (urgent)' }
];

const DEFAULT_FORM: IntakePayload = {
  patient_name: '',
  age: 24,
  symptoms_text: '',
  symptom_duration_weeks: 8,
  severity_score: 5,
  checklist: {
    low_mood: false,
    panic_attacks: false,
    attention_issues: false,
    sleep_issues: false,
    appetite_changes: false,
    racing_thoughts: false,
    trauma_flashbacks: false,
    suicidal_thoughts: false
  },
  prior_treatment: 'No prior treatment',
  medication_history: 'No prior psychiatric medications',
  insurance: {
    provider: 'Aetna',
    plan_type: 'PPO',
    deductible_met: false
  },
  care_preferences: {
    visit_mode: 'Virtual',
    provider_gender_preference: 'No Preference',
    language: 'English',
    availability: 'Weekday Evening'
  }
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(value);
}

function conditionLabel(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function localRealtimeSignal(payload: IntakePayload): { message: string; pathwayHint: string } {
  const text = payload.symptoms_text.toLowerCase();

  const scores: Record<string, number> = {
    anxiety: 0,
    depression: 0,
    adhd: 0,
    ptsd: 0,
    bipolar: 0
  };

  if (/worry|panic|nervous|anxious/.test(text)) scores.anxiety += 2;
  if (/sad|hopeless|empty|worthless|low mood/.test(text)) scores.depression += 2;
  if (/focus|attention|distracted|impulsive/.test(text)) scores.adhd += 2;
  if (/trauma|flashback|nightmare|trigger/.test(text)) scores.ptsd += 2;
  if (/manic|euphoric|mood swings|high energy/.test(text)) scores.bipolar += 2;

  if (payload.checklist.low_mood) scores.depression += 1;
  if (payload.checklist.panic_attacks) scores.anxiety += 1;
  if (payload.checklist.attention_issues) scores.adhd += 1;
  if (payload.checklist.trauma_flashbacks) scores.ptsd += 2;
  if (payload.checklist.racing_thoughts) scores.bipolar += 1;

  const topCondition = Object.entries(scores).sort((a, b) => b[1] - a[1])[0];

  if (!payload.symptoms_text.trim() || payload.symptoms_text.trim().length < 20) {
    return {
      message: 'Add a little more detail about your symptoms to improve recommendation quality.',
      pathwayHint: 'Pending full intake details'
    };
  }

  const likely = conditionLabel(topCondition[0]);

  if (payload.checklist.suicidal_thoughts) {
    return {
      message: 'High-risk signal detected. Prioritize urgent psychiatry + therapy triage.',
      pathwayHint: 'Urgent combined care'
    };
  }

  if (payload.severity_score >= 7 || topCondition[0] === 'bipolar' || topCondition[0] === 'ptsd') {
    return {
      message: `Early signal suggests ${likely} patterns. Combined therapy + psychiatry may fit best.`,
      pathwayHint: 'Combined care likely'
    };
  }

  if (topCondition[0] === 'adhd') {
    return {
      message: 'Attention-related signals detected. Psychiatry-first ADHD evaluation may help.',
      pathwayHint: 'Psychiatry-first likely'
    };
  }

  return {
    message: `Current symptom pattern looks closer to ${likely}. A therapy-first care path may be effective.`,
    pathwayHint: 'Therapy-first likely'
  };
}

function coverageHint(provider: string, planType: string): string {
  const hintTable: Record<string, string> = {
    Aetna: 'Typically lower out-of-pocket for PPO plans.',
    BlueCross: 'Good network depth for therapy providers.',
    Cigna: 'Cost can vary by in-network psychiatric providers.',
    United: 'Verify psychiatry copays before booking.',
    SelfPay: 'No insurance applied. Full listed rates expected.'
  };

  if (planType === 'HMO') return 'HMO selected: referrals may be required for specialist visits.';
  return hintTable[provider] ?? 'Coverage details will be estimated after intake analysis.';
}

function App() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState<IntakePayload>(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<IntakeResult | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [sessions, setSessions] = useState<SessionSummary[]>([]);

  const signal = useMemo(() => localRealtimeSignal(form), [form]);

  useEffect(() => {
    void refreshInsights();
  }, []);

  async function refreshInsights(): Promise<void> {
    try {
      const [analyticsData, sessionsData] = await Promise.all([fetchAnalytics(), fetchSessions()]);
      setAnalytics(analyticsData);
      setSessions(sessionsData.slice(0, 5));
    } catch {
      setAnalytics(null);
      setSessions([]);
    }
  }

  function canAdvanceFrom(currentStep: number): boolean {
    if (currentStep === 0) return form.patient_name.trim().length > 1 && form.age >= 13;
    if (currentStep === 1) return form.symptoms_text.trim().length >= 20;
    if (currentStep === 2) {
      return form.prior_treatment.trim().length > 2 && form.medication_history.trim().length > 2;
    }
    return true;
  }

  function handleNextStep(): void {
    if (!canAdvanceFrom(step)) {
      setError('Please complete the required fields in this step before continuing.');
      return;
    }
    setError('');
    setStep((prev) => Math.min(prev + 1, STEP_TITLES.length - 1));
  }

  function handlePreviousStep(): void {
    setError('');
    setStep((prev) => Math.max(prev - 1, 0));
  }

  function updateChecklist(field: keyof SymptomChecklist): void {
    setForm((prev) => ({
      ...prev,
      checklist: {
        ...prev.checklist,
        [field]: !prev.checklist[field]
      }
    }));
  }

  async function handleSubmit(event: FormEvent): Promise<void> {
    event.preventDefault();
    if (!canAdvanceFrom(2)) {
      setError('Please complete history and medication details to submit the intake.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const response = await processIntake(form);
      setResult(response);
      await refreshInsights();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Failed to process intake');
    } finally {
      setSubmitting(false);
    }
  }

  function resetFlow(): void {
    setForm(DEFAULT_FORM);
    setStep(0);
    setResult(null);
    setError('');
  }

  return (
    <div className="page-shell">
      <div className="page-glow" />
      <main className="layout">
        <section className="hero">
          <p className="eyebrow">Blossom Health | Smart Intake Console</p>
          <h1>AI-Powered Intake + Cost Transparency</h1>
          <p>
            Reduce onboarding friction, improve triage quality, and show estimated patient cost before booking.
          </p>
        </section>

        {!result ? (
          <section className="panel">
            <div className="stepper">
              {STEP_TITLES.map((label, index) => (
                <div key={label} className={`step-item ${index === step ? 'active' : ''}`}>
                  <span>{index + 1}</span>
                  <p>{label}</p>
                </div>
              ))}
            </div>

            <form onSubmit={handleSubmit}>
              {step === 0 && (
                <div className="step-grid">
                  <label>
                    Patient Name
                    <input
                      type="text"
                      value={form.patient_name}
                      onChange={(event) => setForm((prev) => ({ ...prev, patient_name: event.target.value }))}
                      placeholder="Taylor Morgan"
                    />
                  </label>

                  <label>
                    Age
                    <input
                      type="number"
                      min={13}
                      max={95}
                      value={form.age}
                      onChange={(event) => setForm((prev) => ({ ...prev, age: Number(event.target.value) }))}
                    />
                  </label>

                  <label>
                    Insurance Provider
                    <select
                      value={form.insurance.provider}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          insurance: {
                            ...prev.insurance,
                            provider: event.target.value as IntakePayload['insurance']['provider']
                          }
                        }))
                      }
                    >
                      <option>Aetna</option>
                      <option>BlueCross</option>
                      <option>Cigna</option>
                      <option>United</option>
                      <option>SelfPay</option>
                    </select>
                  </label>

                  <label>
                    Plan Type
                    <select
                      value={form.insurance.plan_type}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          insurance: {
                            ...prev.insurance,
                            plan_type: event.target.value as IntakePayload['insurance']['plan_type']
                          }
                        }))
                      }
                    >
                      <option>PPO</option>
                      <option>HMO</option>
                      <option>EPO</option>
                      <option>None</option>
                    </select>
                  </label>

                  <label className="checkbox-row">
                    <input
                      type="checkbox"
                      checked={form.insurance.deductible_met}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          insurance: { ...prev.insurance, deductible_met: event.target.checked }
                        }))
                      }
                    />
                    Deductible met
                  </label>

                  <div className="inline-note">{coverageHint(form.insurance.provider, form.insurance.plan_type)}</div>
                </div>
              )}

              {step === 1 && (
                <div className="step-grid">
                  <label className="span-full">
                    Describe Symptoms
                    <textarea
                      rows={5}
                      value={form.symptoms_text}
                      onChange={(event) => setForm((prev) => ({ ...prev, symptoms_text: event.target.value }))}
                      placeholder="For the past two months I have had panic episodes, low motivation, and trouble sleeping..."
                    />
                  </label>

                  <label>
                    Severity ({form.severity_score}/10)
                    <input
                      type="range"
                      min={1}
                      max={10}
                      value={form.severity_score}
                      onChange={(event) =>
                        setForm((prev) => ({ ...prev, severity_score: Number(event.target.value) }))
                      }
                    />
                  </label>

                  <label>
                    Duration (weeks)
                    <input
                      type="number"
                      min={1}
                      max={520}
                      value={form.symptom_duration_weeks}
                      onChange={(event) =>
                        setForm((prev) => ({ ...prev, symptom_duration_weeks: Number(event.target.value) }))
                      }
                    />
                  </label>

                  <div className="span-full checklist-grid">
                    {CHECKLIST_FIELDS.map((item) => (
                      <button
                        type="button"
                        key={item.key}
                        className={`chip ${form.checklist[item.key] ? 'chip-active' : ''}`}
                        onClick={() => updateChecklist(item.key)}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>

                  <div className="span-full signal-card">
                    <p className="signal-title">Real-time triage signal</p>
                    <p>{signal.message}</p>
                    <small>{signal.pathwayHint}</small>
                  </div>
                </div>
              )}

              {step === 2 && (
                <div className="step-grid">
                  <label className="span-full">
                    Prior Treatment History
                    <textarea
                      rows={3}
                      value={form.prior_treatment}
                      onChange={(event) => setForm((prev) => ({ ...prev, prior_treatment: event.target.value }))}
                    />
                  </label>

                  <label className="span-full">
                    Medication History
                    <textarea
                      rows={3}
                      value={form.medication_history}
                      onChange={(event) =>
                        setForm((prev) => ({ ...prev, medication_history: event.target.value }))
                      }
                    />
                  </label>

                  <label>
                    Visit Mode
                    <select
                      value={form.care_preferences.visit_mode}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          care_preferences: {
                            ...prev.care_preferences,
                            visit_mode: event.target.value as IntakePayload['care_preferences']['visit_mode']
                          }
                        }))
                      }
                    >
                      <option>Virtual</option>
                      <option>In-Person</option>
                      <option>Either</option>
                    </select>
                  </label>

                  <label>
                    Language
                    <select
                      value={form.care_preferences.language}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          care_preferences: {
                            ...prev.care_preferences,
                            language: event.target.value as IntakePayload['care_preferences']['language']
                          }
                        }))
                      }
                    >
                      <option>English</option>
                      <option>Spanish</option>
                    </select>
                  </label>

                  <label>
                    Availability
                    <select
                      value={form.care_preferences.availability}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          care_preferences: {
                            ...prev.care_preferences,
                            availability: event.target.value as IntakePayload['care_preferences']['availability']
                          }
                        }))
                      }
                    >
                      <option>Weekday Morning</option>
                      <option>Weekday Evening</option>
                      <option>Weekend</option>
                      <option>Flexible</option>
                    </select>
                  </label>

                  <label>
                    Provider Gender Preference
                    <select
                      value={form.care_preferences.provider_gender_preference}
                      onChange={(event) =>
                        setForm((prev) => ({
                          ...prev,
                          care_preferences: {
                            ...prev.care_preferences,
                            provider_gender_preference:
                              event.target.value as IntakePayload['care_preferences']['provider_gender_preference']
                          }
                        }))
                      }
                    >
                      <option>No Preference</option>
                      <option>Female</option>
                      <option>Male</option>
                      <option>Non-binary</option>
                    </select>
                  </label>
                </div>
              )}

              {error && <div className="error-box">{error}</div>}

              <div className="actions">
                <button type="button" className="btn-muted" onClick={handlePreviousStep} disabled={step === 0}>
                  Previous
                </button>

                {step < 2 ? (
                  <button type="button" className="btn-primary" onClick={handleNextStep}>
                    Continue
                  </button>
                ) : (
                  <button type="submit" className="btn-primary" disabled={submitting}>
                    {submitting ? 'Generating Recommendation...' : 'Generate Care Plan'}
                  </button>
                )}
              </div>
            </form>
          </section>
        ) : (
          <CareDashboard result={result} onReset={resetFlow} />
        )}

        <section className="panel analytics-panel">
          <h2>Operational Snapshot</h2>
          {analytics ? (
            <div className="metrics-row">
              <div className="metric-card">
                <span>Total Intake Sessions</span>
                <strong>{analytics.total_sessions}</strong>
              </div>
              <div className="metric-card">
                <span>Avg Estimated Monthly Cost</span>
                <strong>{formatCurrency(analytics.avg_monthly_estimate)}</strong>
              </div>
              <div className="metric-card">
                <span>Common Condition</span>
                <strong>{mostCommonCondition(analytics.by_condition)}</strong>
              </div>
            </div>
          ) : (
            <p className="muted">Analytics appears after at least one completed intake session.</p>
          )}

          <h3>Recent Sessions</h3>
          {sessions.length === 0 ? (
            <p className="muted">No sessions yet.</p>
          ) : (
            <div className="session-list">
              {sessions.map((session) => (
                <article key={session.session_id} className="session-card">
                  <p className="session-name">{session.patient_name}</p>
                  <p>{conditionLabel(session.predicted_condition)} • {session.care_recommendation}</p>
                  <small>{new Date(session.created_at).toLocaleString()} • {formatCurrency(session.monthly_estimate)}/mo</small>
                </article>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function mostCommonCondition(byCondition: Record<string, number>): string {
  const entries = Object.entries(byCondition);
  if (!entries.length) return 'Not enough data';
  const [condition] = entries.sort((a, b) => b[1] - a[1])[0];
  return conditionLabel(condition);
}

function CareDashboard({ result, onReset }: { result: IntakeResult; onReset: () => void }) {
  return (
    <section className="panel result-panel">
      <div className="result-header">
        <h2>Recommended Care Plan</h2>
        <button className="btn-muted" onClick={onReset}>
          Start New Intake
        </button>
      </div>

      <div className="metrics-row">
        <div className="metric-card">
          <span>Predicted Need</span>
          <strong>{conditionLabel(result.predicted_condition)}</strong>
          <small>Confidence: {(result.confidence * 100).toFixed(1)}%</small>
        </div>
        <div className="metric-card">
          <span>Triage Level</span>
          <strong>{result.triage_level}</strong>
          <small>{result.care_recommendation}</small>
        </div>
        <div className="metric-card">
          <span>Estimated Monthly Cost</span>
          <strong>{formatCurrency(result.cost_estimate.monthly_estimate)}</strong>
          <small>{formatCurrency(result.cost_estimate.per_visit_estimate)} per visit</small>
        </div>
      </div>

      <div className="dashboard-grid">
        <article className="dashboard-card">
          <h3>Cost Before Booking</h3>
          <p className="muted">Coverage: {(result.cost_estimate.coverage_rate * 100).toFixed(0)}%</p>
          <p className="muted">{result.cost_estimate.deductible_note}</p>
          <ul>
            {Object.entries(result.cost_estimate.breakdown).map(([item, value]) => (
              <li key={item}>
                <span>{item.replaceAll('_', ' ')}</span>
                <strong>{formatCurrency(value)}</strong>
              </li>
            ))}
          </ul>
        </article>

        <article className="dashboard-card">
          <h3>Explainable Recommendation</h3>
          <p>{result.model_explanation.summary}</p>
          <p className="muted">Top model keywords:</p>
          <div className="tag-wrap">
            {result.model_explanation.top_keywords.length ? (
              result.model_explanation.top_keywords.map((keyword) => (
                <span className="tag" key={keyword}>
                  {keyword} ({result.model_explanation.keyword_contributions[keyword]?.toFixed(3)})
                </span>
              ))
            ) : (
              <span className="muted">No strong text signal detected.</span>
            )}
          </div>
          <p className="muted">Rule triggers:</p>
          <ul>
            {result.model_explanation.rule_triggers.map((rule) => (
              <li key={rule}>{rule}</li>
            ))}
          </ul>
        </article>

        <article className="dashboard-card span-two">
          <h3>Provider Matching</h3>
          <div className="provider-grid">
            {result.provider_matches.map((provider) => (
              <div key={provider.provider_name} className="provider-card">
                <strong>{provider.provider_name}</strong>
                <p>{provider.specialty}</p>
                <small>Score: {(provider.score * 100).toFixed(0)}%</small>
                <p className="muted">{provider.reason}</p>
              </div>
            ))}
          </div>
          <small>Session ID: {result.session_id}</small>
        </article>
      </div>
    </section>
  );
}

export default App;
