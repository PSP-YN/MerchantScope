# Security and data handling

- Demo mode is explicitly synthetic and is the default for local judging.
- Production mode requires role-specific bearer tokens through TRACE_ANALYST_TOKEN, TRACE_INVESTIGATOR_TOKEN, and TRACE_ADMIN_TOKEN.
- CORS origins are configured through CORS_ORIGINS; do not use wildcard origins with credentials.
- Use TLS, managed secrets, least-privilege database roles, private networking, backups, and retention controls in deployment.
- Identifiers are pseudonymous in the data model; production tokenization must occur before ingestion.
- Assessments, investigation updates, verification requests, and intervention decisions are written to the audit log.
- No endpoint freezes, terminates, declines, or blocks a merchant or payment.
- Proposed interventions remain pending until a separate reviewer/admin approves or rejects them.
- Never commit .env files, access tokens, private keys, or real payment/customer data.
