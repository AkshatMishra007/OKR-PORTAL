"""Add closed_at and closed_by to batches table

Revision ID: 0004_add_closed_to_batches
Revises: 0003_create_okr_logs_table
Create Date: 2026-08-17 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0004_add_closed_to_batches'
down_revision = '0003_create_okr_logs_table'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('batches')] if inspector.has_table('batches') else []

    if 'closed_at' not in columns:
        op.add_column('batches', sa.Column('closed_at', sa.DateTime(), nullable=True))
    if 'closed_by' not in columns:
        op.add_column('batches', sa.Column('closed_by', postgresql.UUID(as_uuid=True), nullable=True))


def downgrade():
    op.drop_column('batches', 'closed_by')
    op.drop_column('batches', 'closed_at')
