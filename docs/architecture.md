# TRACE architecture

TRACE is a merchant-risk decision-support prototype. It is not a payment authorization, blocking, or fraud-verdict system.

## Runtime flow
1. FastAPI receives normalized merchant and transaction data through validated merchant-creation and batch-ingestion endpoints.
2. SQLAlchemy persists merchants, profiles, transactions, context events, features, risk assessments, signals, graph entities, investigations, interventions, and audit records.
3. Pandas and NumPy compute merchant-specific historical and current-window features.
4. Statistical rules and Isolation Forest identify deviations; NetworkX evaluates shared pseudonymous entities.
5. An explainable weighted score is normalized over available dimensions. Missing dimensions reduce confidence and are excluded from the score denominator.
6. Analysts open investigations, request verification, and record outcomes. Consequential interventions require separate reviewer approval; no payment action is executed.
7. Model evaluation compares a static threshold baseline with TRACE against scenario labels generated independently from features.

## Risk model
Default weights: behaviour 25%, category consistency 25%, graph relationships 25%, payment anomalies 15%, unresolved context 10%. All five weights are configurable through environment variables. Components are normalized to 0–100. Available weights are renormalized when data is missing. Confidence is separate. Scores are review-priority indices, not probabilities.

## Data model
Normalized SQLAlchemy entities are in backend/app/models.py. SQLite is the zero-configuration local default; PostgreSQL URLs are supported through DATABASE_URL. The demo creates tables on startup; the migration directory contains the versioned schema bootstrap.

## Synthetic dataset
A deterministic seed generates 100 merchants in five categories and approximately 40,000 transactions over 90 days. All rows and entity fingerprints are synthetic. No PayU integration or real customer information is present.

## Production hardening still required
A payment-provider pilot requires authorized data access, production identity provider integration, tenant isolation, key management, database migrations in the deployment pipeline, retention controls, privacy/legal review, representative model validation, monitoring, incident response, and formal intervention governance.
