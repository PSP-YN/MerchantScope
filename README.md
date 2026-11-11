# TRACE — Transaction Reality & Activity Consistency Engine

**Merchant-risk intelligence for payment ecosystems. Built by CHAKRAVYUHA for the Follow The Money innovation challenge.**

TRACE helps payment risk teams distinguish legitimate merchant evolution from suspicious behavioural drift. It combines merchant-specific baselines, statistical anomaly detection, context events, pseudonymous entity graphs, explainable risk prioritization, and human-led investigation.

> **Data and integration notice:** The demo uses reproducible synthetic merchant and transaction data only. It is not connected to PayU and contains no real merchant, customer, payment, or settlement records. Scores are review-priority indices, not probabilities or findings of wrongdoing.

## Product modules

- Command Center with live database-derived portfolio metrics.
- Merchant Intelligence with historical baselines, current features, signal explanations, and declared context.
- Behaviour engine with rolling-window deviation features and Isolation Forest.
- Context events for festivals, channel expansion, new products, and changed operating hours; unverified context remains unverified.
- Network Explorer backed by pseudonymous device/customer/settlement identifiers and NetworkX graph analysis.
- Explainable weighted risk score with severity and confidence kept separate.
- Investigation workflow with notes, assignment, outcomes, and verification requests.
- Scenario Simulator that regenerates a merchant's synthetic 90-day ledger and runs the same backend assessment pipeline.
- Audit log and reviewer-approved intervention proposals.
- Model evaluation comparing static thresholds with TRACE using generated scenario labels.

## Stack

- Frontend: Next.js, React, TypeScript, Recharts, React Flow.
- Backend: FastAPI, Pydantic, SQLAlchemy.
- Storage: SQLite for local demo; PostgreSQL via DATABASE_URL.
- Analytics: Pandas, NumPy, scikit-learn Isolation Forest, NetworkX.
- Tests: Pytest, FastAPI integration tests, Playwright browser acceptance tests, Next.js production build CI.

## Quick start

Requirements: Python 3.11, 3.12 or 3.13 (3.12 recommended), Node.js 20+, npm.

For a single-command local startup, run `bash scripts/dev.sh` from the repository root. It creates the backend virtual environment, installs dependencies, copies local example environment files when absent, and starts the API and frontend. Stop both services with Ctrl+C.

### 1. Start the API

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

On first demo start, TRACE creates the relational schema and seeds 100 synthetic merchants with approximately 40,000 transactions across 90 days. The process is deterministic in scenario assignment and random seed; transaction IDs and timestamps are generated at seed time. PostgreSQL production mode requires a PostgreSQL `DATABASE_URL` and four distinct role tokens of at least 32 characters. Production startup applies the checked-in Alembic migration head; demo mode uses SQLite and does not require secrets.

API documentation: http://127.0.0.1:8000/docs. The API includes merchant creation, transaction batch ingestion, structured context declaration/review, merchant assessment, scenario execution, investigation and intervention workflows, audit retrieval, and model evaluation.

### 2. Start the frontend

In a second terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://127.0.0.1:3000.

### 3. Run tests and evaluation

```bash
cd backend
pytest -q
cd ../evaluation
python run.py
cd ../frontend
npm run test:e2e
```

Frontend production build:

```bash
cd frontend
npm run build
npm run test:e2e
```

## Database

SQLite is the default local database. For PostgreSQL, set DATABASE_URL to a PostgreSQL SQLAlchemy URL, for example:

```text
postgresql+psycopg://user:password@host:5432/trace
```

Schema definitions are in backend/app/models.py. Alembic configuration and the initial schema migration are in backend/migrations. For a fresh database, run:

```bash
cd backend
alembic upgrade head
```

## Risk methodology

Weights: behaviour deviation 25%, merchant-category consistency 25%, graph risk 25%, payment anomalies 15%, unresolved contextual inconsistencies 10%. Components are normalized to 0–100. When behavioural history is insufficient, unavailable dimensions are excluded and the remaining weights are renormalized. Confidence is reported separately.

The Isolation Forest decision function is an anomaly signal, not a calibrated fraud probability. Shared identifiers are investigative leads, not proof. Declared context events are unverified until reviewed. No payment is declined, frozen, or blocked by TRACE.

See docs/model-methodology.md and docs/architecture.md.

## Production boundary

This repository is a hackathon-grade functional prototype, not a certified payment risk product. A real pilot requires authorized payment-provider integration, identity-provider SSO, tenant isolation, production secrets, TLS, database access controls, privacy/legal review, data retention, independent model validation, monitoring, incident response, and documented human intervention governance. No live PayU integration is claimed.

## License

MIT. See LICENSE.
