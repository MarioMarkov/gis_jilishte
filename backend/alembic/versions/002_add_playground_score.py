"""Add score_playground column

Revision ID: 002
Revises: 001
Create Date: 2026-03-25
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("grid_cells", sa.Column("score_playground", sa.Float))


def downgrade():
    op.drop_column("grid_cells", "score_playground")
