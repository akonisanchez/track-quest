"""merge multiple heads

Revision ID: a9a78db80a3c
Revises: 3a3051fa0e1b, new_migration_id
Create Date: 2024-11-10 14:05:44.142269

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9a78db80a3c'
down_revision = ('3a3051fa0e1b', 'new_migration_id')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
