"""Remove required_percentage from tracker_entries

Revision ID: 0001_remove_required_percentage
Revises: 
Create Date: 2026-08-11 13:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_remove_required_percentage'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table('tracker_entries'):
        columns = [c['name'] for c in inspector.get_columns('tracker_entries')]
        if 'required_percentage' in columns:
            op.execute("ALTER TABLE tracker_entries DROP CONSTRAINT IF EXISTS ck_tracker_required_percentage")
            op.execute("ALTER TABLE tracker_entries DROP COLUMN IF EXISTS required_percentage")


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table('tracker_entries'):
        columns = [c['name'] for c in inspector.get_columns('tracker_entries')]
        if 'required_percentage' not in columns:
            op.add_column('tracker_entries', sa.Column('required_percentage', sa.Integer(), nullable=True))
            op.create_check_constraint(
                'ck_tracker_required_percentage',
                'tracker_entries',
                'required_percentage >= 0 AND required_percentage <= 100'
            )
