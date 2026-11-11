"""Initial TRACE schema baseline."""
from alembic import op
from app.db import Base
from app import models  # noqa: F401

revision="0001_initial_schema"
down_revision=None
branch_labels=None
depends_on=None

def upgrade():
    # Initial baseline revision. Future revisions use explicit Alembic DDL.
    Base.metadata.create_all(bind=op.get_bind())

def downgrade():
    Base.metadata.drop_all(bind=op.get_bind())
