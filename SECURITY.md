# Security policy

Report vulnerabilities privately to the repository maintainers; do not publish secrets, exploit details, or personal/payment data in public issues.

TRACE is a hackathon prototype and must not process real payment data without a security review. Before production use, deploy authenticated identity, tenant isolation, TLS, secret management, encryption at rest, backups, monitoring, retention/deletion controls, and a formal incident response process.

Never commit credentials or real customer/merchant transaction records. All committed sample data must be synthetic.
