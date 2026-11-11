# TRACE API reference

Interactive OpenAPI: http://127.0.0.1:8000/docs

All JSON endpoints return FastAPI validation errors for invalid request bodies. List endpoints are bounded and support pagination where applicable.

## Authentication and roles
- Demo: requests use X-Actor and X-Role headers. The local demo defaults to analyst; the frontend uses a demo admin identity.
- Production: every non-health API route requires Authorization: Bearer <role-token>. Configure four distinct, high-entropy tokens (minimum 32 characters): analyst, investigator, admin, reviewer.
- Analyst: assessments, ingestion, investigation creation/updates, verification requests, context declaration.
- Investigator: analyst actions plus intervention proposals and context review.
- Reviewer: context review and intervention approval/rejection.
- Admin: all prototype roles and demo administration.
- Production audit actor is derived from the authenticated role token, not a caller-supplied actor header.

## Portfolio and merchant APIs
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | Service and database health |
| GET | /api/dashboard | Database-derived portfolio metrics, risk trend, recent activity |
| GET | /api/merchants | Search/filter merchant portfolio |
| POST | /api/merchants | Create merchant and baseline profile |
| GET | /api/merchants/{merchant_id} | Merchant profile, baseline, current assessment, context and history |
| GET | /api/merchants/{merchant_id}/transactions | Paginated merchant transactions |
| GET | /api/merchants/{merchant_id}/features | Current merchant feature window |
| POST | /api/merchants/{merchant_id}/assess | Persist an explainable risk assessment |
| POST | /api/merchants/{merchant_id}/events | Declare structured business context |
| PATCH | /api/merchant-events/{event_id}/verification | Mark context unresolved, partially verified, verified, or rejected |

## Transaction and graph APIs
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/transactions | Retrieve recent transaction records |
| POST | /api/transactions/ingest | Validate and ingest a batch of up to 1,000 transactions |
| GET | /api/relationships | Retrieve shared merchant/device/customer/settlement graph |
| GET | /api/risk-config | Read configured component weights and score semantics |

## Scenario, investigation and governance APIs
| Method | Endpoint | Purpose |
|---|---|---|
| GET | /api/scenarios | List supported synthetic scenarios |
| POST | /api/scenarios/run | Replace a merchant demo ledger, rebuild graph, rerun detection, refresh open cases |
| GET / POST | /api/investigations | List cases / open a merchant case |
| PATCH | /api/investigations/{case_id} | Change status, assignment, outcome, and append a note |
| POST | /api/investigations/{case_id}/verification | Record a merchant verification request |
| POST | /api/investigations/{case_id}/interventions | Propose a review action; no payment action is executed |
| GET | /api/interventions | List verification requests and intervention proposals |
| PATCH | /api/interventions/{intervention_id}/approval | Reviewer/admin approval or rejection |
| GET | /api/audit | Retrieve append-only operational audit records |
| GET | /api/evaluation | Static-threshold versus TRACE synthetic benchmark |
| POST | /api/admin/seed | Reset/reseed synthetic demo data; disabled in production |

## Example batch ingestion
```json
{
  "transactions": [
    {
      "merchant_id": "m-0001",
      "amount": 425.5,
      "status": "settled",
      "channel": "upi",
      "customer_token": "customer:token:001",
      "device_token": "device:token:001",
      "settlement_token": "settlement:token:001",
      "synthetic": true
    }
  ]
}
```

Only pseudonymous identifiers belong in the token fields. Do not send PAN, CVV, bank credentials, passwords, or direct personal identifiers to the prototype.
