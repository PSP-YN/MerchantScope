# Security and data handling

- Demo mode is explicitly synthetic and is the default for local judging. Production mode does not auto-seed or auto-create tables, and disables synthetic scenario and benchmark endpoints.
- Production mode requires four distinct role-specific bearer tokens of at least 32 characters: TRACE_ANALYST_TOKEN, TRACE_INVESTIGATOR_TOKEN, TRACE_ADMIN_TOKEN, and TRACE_REVIEWER_TOKEN. The browser client keeps the entered token in memory only; it is not written to local storage.
- CORS origins are configured through CORS_ORIGINS; do not use wildcard origins with credentials. OPTIONS preflight is allowed before bearer-token checks.
- Use TLS, managed secrets, least-privilege database roles, private networking, backups, and retention controls in deployment.
- Identifiers are pseudonymous in the data model; production tokenization must occur before ingestion.
- Assessments, investigation updates, verification requests, and intervention decisions are written to the audit log.
- No endpoint freezes, terminates, declines, or blocks a merchant or payment.
- Proposed interventions remain pending until a separate reviewer/admin approves or rejects them.
- Never commit .env files, access tokens, private keys, or real payment/customer data.
