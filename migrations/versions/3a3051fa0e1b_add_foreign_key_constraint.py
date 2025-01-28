"""add_foreign_key_constraint

Revision ID: 3a3051fa0e1b
Revises: new_migration_id
Create Date: 2024-11-10 13:59:37.609052

"""
from alembic import op
import sqlalchemy as sa


revision = '3a3051fa0e1b'  #matches file namee
down_revision = None  # could change if knew previous id
branch_labels = None
depends_on = None

def upgrade():
    # Create the foreign key constraint
    with op.batch_alter_table('race_review') as batch_op:
        batch_op.create_foreign_key(
            'fk_review_historical_race',
            'historical_race',
            ['historical_race_id'], ['id']
        )
        
        # Make historical_race_id not nullable
        batch_op.alter_column('historical_race_id',
            existing_type=sa.Integer(),
            nullable=False
        )

def downgrade():
    with op.batch_alter_table('race_review') as batch_op:
        batch_op.drop_constraint('fk_review_historical_race', type_='foreignkey')
        batch_op.alter_column('historical_race_id',
            existing_type=sa.Integer(),
            nullable=True
        )