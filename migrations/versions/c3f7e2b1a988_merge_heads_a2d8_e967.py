"""merge heads: a2d8f3b4c5de, e967e6a86746

Revision ID: c3f7e2b1a988
Revises: ('a2d8f3b4c5de', 'e967e6a86746')
Create Date: 2025-11-25 20:50:00.000000

This is a no-op merge script to join two migration branches into one head.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3f7e2b1a988'
down_revision = ('a2d8f3b4c5de', 'e967e6a86746')
branch_labels = None
depends_on = None


def upgrade():
    # Merge-only migration: no DB changes here
    pass


def downgrade():
    # Downgrading a merge is unusual and not supported by default.
    raise NotImplementedError('Downgrade of merge revision is not supported by this script')
