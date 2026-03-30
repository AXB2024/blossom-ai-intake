# Blossom Smart Intake

AI-powered intake + cost transparency system inspired by Blossom Health's telehealth operations.

## Problem
Blossom-like telehealth teams face four recurring bottlenecks:
- Patients do not understand likely costs before booking.
- Onboarding is slow and form-heavy.
- Manual triage/scheduling creates operational overhead.
- Patients are uncertain about therapy vs psychiatry vs both.

## Solution
This project ships a full-stack **Smart Intake & Cost Transparency** workflow:
- Multi-step patient onboarding with clean UX.
- Hybrid triage engine (rules + ML) for likely condition classification.
- Explainable AI output showing keywords and rule triggers.
- Insurance-aware cost estimate before booking.
- Provider matching and operational analytics snapshot.

## Tech Stack
- Frontend: React + TypeScript + Vite
- Backend: FastAPI + SQLAlchemy
- ML: TF-IDF + Logistic Regression (scikit-learn)
- Database: SQLite (drop-in replaceable with PostgreSQL)

## Project Structure
```text
blossom-smart-intake/
├── backend/
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── ml/
│   │   │   ├── model.py
│   │   │   ├── train.py
│   │   │   ├── embedding_upgrade.py
│   │   │   ├── training_data.py
│   │   │   └── artifacts/
│   │   └── services/
│   │       ├── insurance.py
│   │       ├── provider_matching.py
│   │       └── triage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── styles.css
│   │   └── types.ts
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   └── vite.config.ts
└── README.md
```

## How It Works
1. Patient completes intake (symptoms, severity, history, insurance, preferences).
2. Backend runs hybrid triage:
   - ML model predicts condition class from symptom text.
   - Rule system scores checklist and risk factors.
   - Final class combines ML probability + rule score.
3. Care pathway is selected (`therapy_only`, `psychiatry_only`, `combined`).
4. Insurance cost estimator calculates per-visit and monthly out-of-pocket estimate.
5. Explainability layer returns top keywords and rule triggers.
6. Session, prediction, and estimate are persisted for operations/analytics.

## API Endpoints
- `GET /health`
- `POST /api/intake/process`
- `GET /api/sessions`
- `GET /api/sessions/{session_id}`
- `GET /api/analytics/common-issues`

## Local Setup
### 1. Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Optional: retrain the model artifacts
```bash
python -m app.ml.train
```

### 2. Frontend
```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend runs at `http://localhost:5173` and calls backend at `http://localhost:8000`.

## Why This Matters for Startups Like Blossom
- **Conversion lift**: cost visibility reduces drop-off before booking.
- **Ops leverage**: triage automation cuts manual review time.
- **Trust**: explainable recommendations are easier for patients and clinical teams to accept.
- **Scalability**: structured intake sessions become analytics-ready product data.

## Production Upgrade Ideas
- Swap SQLite with PostgreSQL.
- Add auth + HIPAA-safe logging/redaction.
- Replace synthetic training set with de-identified historical intake data.
- Upgrade classifier to sentence embeddings (`sentence-transformers`).
- Add scheduling optimization against real provider calendars.
