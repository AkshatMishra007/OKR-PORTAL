"""Refactor Batch Membership to use OrganizationMember and remove uq_organization_member constraint

Revision ID: 0002_refactor_batch_membership
Revises: 0001_remove_required_percentage
Create Date: 2026-08-12 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_refactor_batch_membership'
down_revision = '0001_remove_required_percentage'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if inspector.has_table('organization_members'):
        op.execute("ALTER TABLE organization_members DROP CONSTRAINT IF EXISTS uq_organization_member")
    if inspector.has_table('batch_members'):
        op.execute("DROP TABLE IF EXISTS batch_members CASCADE")


def downgrade():
    pass
