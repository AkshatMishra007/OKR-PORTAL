"""Ensure organization_id exists on batches table

Revision ID: 0005_batches_organization_id
Revises: 0004_add_closed_to_batches
Create Date: 2026-08-21 11:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0005_batches_organization_id'
down_revision = '0004_add_closed_to_batches'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table('batches'):
        columns = [c['name'] for c in inspector.get_columns('batches')]
        if 'organization_id' not in columns:
            op.add_column(
                'batches',
                sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True)
            )
            op.create_index(op.f('ix_batches_organization_id'), 'batches', ['organization_id'], unique=False)


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table('batches'):
        columns = [c['name'] for c in inspector.get_columns('batches')]
        if 'organization_id' in columns:
            op.drop_index(op.f('ix_batches_organization_id'), table_name='batches')
            op.drop_column('batches', 'organization_id')
