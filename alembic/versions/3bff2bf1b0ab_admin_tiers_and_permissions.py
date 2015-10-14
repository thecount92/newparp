"""Admin tiers and permissions.

Revision ID: 3bff2bf1b0ab
Revises: 254b96b2e370
Create Date: 2015-09-24 23:32:04.359295

"""

# revision identifiers, used by Alembic.
revision = '3bff2bf1b0ab'
down_revision = '254b96b2e370'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa

from charat2.model import AdminTier, AdminTierPermission


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    permissions = (
        u'permissions',
        u'search_characters',
        u'announcements',
        u'broadcast',
        u'user_list',
        u'groups',
        u'log',
        u'spamless',
        u'ip_bans',
    )
    op.create_table('admin_tiers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.Unicode(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_table('admin_tier_permissions',
        sa.Column('admin_tier_id', sa.Integer(), nullable=False),
        sa.Column('permission', sa.Enum(
            *permissions,
            name='admin_tier_permissions_permission'
        ), nullable=False),
        sa.ForeignKeyConstraint(['admin_tier_id'], ['admin_tiers.id'], ),
        sa.PrimaryKeyConstraint('admin_tier_id', 'permission')
    )
    op.bulk_insert(AdminTier.__table__, [{'name': 'Hoofbeast tier'}])
    op.bulk_insert(
        AdminTierPermission.__table__,
        [{'admin_tier_id': 1, 'permission': permission} for permission in permissions],
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('admin_tier_permissions')
    op.drop_table('admin_tiers')
    ### end Alembic commands ###