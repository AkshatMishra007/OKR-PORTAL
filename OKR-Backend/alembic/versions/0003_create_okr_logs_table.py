"""Create okr_logs table for audit logging

Revision ID: 0003_create_okr_logs_table
Revises: 0002_refactor_batch_membership
Create Date: 2026-08-17 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0003_create_okr_logs_table'
down_revision = '0002_refactor_batch_membership'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if not inspector.has_table('okr_logs'):
        op.create_table(
            'okr_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('weekly_no', sa.Integer(), nullable=False),
            sa.Column('current_user', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('datetime', sa.DateTime(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
            sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
            sa.Column('deleted_at', sa.DateTime(), nullable=True),
        )
        op.create_index(op.f('ix_okr_logs_current_user'), 'okr_logs', ['current_user'], unique=False)


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table('okr_logs'):
        op.drop_index(op.f('ix_okr_logs_current_user'), table_name='okr_logs')
        op.drop_table('okr_logs')
