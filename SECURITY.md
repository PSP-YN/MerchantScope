# Security policy

MerchantScope is an early-stage demonstration prototype. Do not connect production payment, merchant, customer, or cardholder data.

## Reporting
Please do not open public issues for exploitable vulnerabilities involving credentials, personal data, or infrastructure. Contact the repository maintainer privately through GitHub's security advisory feature.

## Current security boundaries
- The API binds to localhost in the documented development command.
- CORS is restricted to the local Vite development origins.
- No authentication, authorization, persistence, or production deployment controls are implemented yet.
- All bundled records are synthetic.
- The app has no payment execution, payment blocking, payout control, or other adverse-action capability.

Before any real-data pilot, implement authenticated access, role-based authorization, tenant isolation, secrets management, encryption, audit trails, retention controls, threat modelling, dependency scanning, and independent security review.
