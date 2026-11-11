# TRACE data dictionary

| Table | Purpose | Important fields |
|---|---|---|
| merchants | Merchant identity and declared business profile | id, name, category, declared_description, scenario_label, status |
| merchant_profiles | Merchant-specific historical baseline | baseline_days, baseline_daily_count, baseline_avg_ticket, baseline_refund_rate, baseline_failed_rate, baseline_night_share, baseline_customer_concentration |
| transactions | Normalized transaction events | merchant_id, amount, status, channel, customer_token, device_token, settlement_token, occurred_at, synthetic |
| merchant_events | Declared business context and verification state | event_type, description, verification_status, effective_at |
| behavioural_features | Persisted current-window features | transaction_count, daily_count, avg_ticket, refund_rate, failed_rate, night_share, customer_concentration |
| risk_assessments | Versioned risk prioritization result | risk_score, confidence, severity, explanation, components_json |
| risk_signals | Human-readable supporting evidence | key, label, points, detail, disposition |
| entity_nodes | Merchant and shared pseudonymous entities | entity_type, label, synthetic |
| entity_edges | Shared relationships and observed evidence | source_id, target_id, relation, evidence_count, first_seen, last_seen |
| investigations | Human-led case management | assessment_id, status, assigned_to, outcome |
| investigation_notes | Timestamped investigator notes | investigation_id, actor, note, created_at |
| interventions | Verification requests and proposed actions | action, reason, approval_status, approved_by |
| audit_logs | Operational audit history | actor, role, action, resource_type, resource_id, reason, created_at |

## Identifier handling
All generated identifiers are synthetic. For a real pilot, tokenize customer/device/settlement identifiers upstream using an approved provider-controlled scheme. Never store raw payment credentials or direct cardholder data in TRACE.

## Retention and tenancy
The prototype does not implement tenant partitioning or automated retention. Production deployment must define tenant ownership, retention windows, deletion workflows, access policies, and database row-level security before onboarding real payment-provider data.
