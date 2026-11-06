# Architecture

## Runtime flow

1. FastAPI serves dashboard, merchant, transaction, relationship, and case endpoints.
2. `engine.py` supplies deterministic synthetic merchant observations and computes additive rule-based signals.
3. The React client fetches the API, renders portfolio metrics, merchant-level explanations, and the review queue.
4. Case status changes are handled by a human analyst through the API.

## Risk score

The current score is a transparent heuristic, not a statistical model. Independent checks compare five current merchant metrics with a fixed per-merchant demo baseline: transaction volume, average ticket, refund rate, late-hour activity, and top payment-instrument concentration. Signal points are summed and capped at 100. Thresholds map the score to low, medium, or high review priority.

The seasonal uplift scenario intentionally has elevated volume without correlated refund, ticket-size, late-hour, or concentration anomalies. It therefore remains low priority. The behaviour-shift scenario combines several deviations and receives a high score.

## Prototype limitations

- No persistence: cases are stored in process memory and reset when the API restarts.
- No identity, authentication, authorization, or tenant isolation.
- No real payment processor or PayU integration.
- No calibrated model, labelled training corpus, precision/recall evaluation, or drift monitoring.
- Synthetic graph fingerprints are illustrative only and are not evidence of real-world links.
