# MerchantScope

**Explainable merchant-behaviour risk intelligence for payment ecosystems.**

MerchantScope helps risk and operations teams investigate unusual changes in merchant behaviour. It combines merchant baselines, interpretable signals, relationship context, and human-reviewed cases. It is a decision-support prototype: it does not authorize, decline, freeze, or block payments.

> **Prototype data notice:** the included dataset and scenarios are synthetic and generated locally for demonstration. They are not PayU data, customer records, or evidence of real fraud.

## What works in this prototype
- Merchant portfolio and transaction overview from a deterministic synthetic dataset.
- Explainable risk scoring with signal-level reasons (volume shift, refund ratio, ticket-size shift, night activity, and concentration).
- Three demo scenarios: stable bakery, legitimate seasonal uplift, and suspicious behavioural shift.
- Human-in-the-loop investigation queue and case status updates.
- Relationship view for shared device/IP/payment-instrument fingerprints (synthetic graph edges).
- FastAPI backend and React + TypeScript frontend.

## Architecture
- `backend/`: FastAPI REST API, deterministic scenario generator, explainable scoring, in-memory demo case workflow.
- `frontend/`: Vite + React + TypeScript dashboard.

## Run locally
Requirements: Python 3.11+, Node.js 20+.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL (normally http://localhost:5173). The frontend expects the API at `http://127.0.0.1:8000`; set `VITE_API_URL` to override it.

## Checks
```bash
cd backend && pytest -q
cd frontend && npm run build
```

## Safety and limitations
- Scores are heuristic, illustrative prioritization signals, not calibrated probabilities or a fraud verdict.
- All sample merchants, transactions, identifiers, and graph links are synthetic.
- Production use requires authorized data integrations, privacy/legal review, access controls, audit logging, model validation, monitoring, and human approval policies.
- No automated adverse action is implemented.

## License
MIT. See `LICENSE`.
