# Database migrations

Run from the backend directory:

```bash
alembic upgrade head
alembic current
```

The initial revision establishes the v1 SQLAlchemy metadata as the baseline schema. Treat this revision as immutable after deployment; subsequent schema changes must be new, explicit Alembic revisions generated and reviewed before rollout. Production startup runs `alembic upgrade head` against the configured PostgreSQL database. Local demo mode creates the SQLite schema automatically.
