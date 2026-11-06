# Contributing

1. Open an issue describing the problem or proposed change.
2. Keep changes scoped and explain assumptions, especially for risk signals.
3. Never add real merchant, customer, card, or payment data. Use clearly labelled synthetic fixtures.
4. Add or update tests for API behaviour and scoring logic.
5. Run backend tests and the frontend production build before opening a pull request.

```bash
cd backend && .venv/bin/pytest -q
cd ../frontend && npm run build
```

Risk scores must remain explainable. Do not present heuristic scores as probabilities or implement automatic adverse actions without an explicit, reviewed product and governance decision.
