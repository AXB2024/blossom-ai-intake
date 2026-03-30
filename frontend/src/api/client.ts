import { AnalyticsSummary, IntakePayload, IntakeResult, SessionSummary } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json'
    },
    ...options
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed (${response.status})`);
  }

  return response.json() as Promise<T>;
}

export function processIntake(payload: IntakePayload): Promise<IntakeResult> {
  return request<IntakeResult>('/api/intake/process', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export function fetchSessions(): Promise<SessionSummary[]> {
  return request<SessionSummary[]>('/api/sessions');
}

export function fetchAnalytics(): Promise<AnalyticsSummary> {
  return request<AnalyticsSummary>('/api/analytics/common-issues');
}
