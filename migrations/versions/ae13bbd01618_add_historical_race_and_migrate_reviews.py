"""Add historical race model and migrate reviews

Revision ID: new_migration_id
Revises: previous_migration_id
Create Date: 2024-02-11 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'new_migration_id'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Only modify race_review table since historical_race already exists
    connection = op.get_bind()
    
    # 1. Add historical_race_id to race_review if it doesn't exist
    try:
        op.add_column('race_review',
            sa.Column('historical_race_id', sa.Integer(), nullable=True)
        )
    except Exception as e:
        print("Column might already exist, continuing...")
    
    # 2. Migrate existing data
    # First, copy existing race names to historical_race table
    connection.execute(text("""
        INSERT OR IGNORE INTO historical_race (name, location)
        SELECT DISTINCT race_name, 'San Diego, CA'
        FROM race_review
        WHERE race_name IS NOT NULL
    """))
    
    # Then, update reviews with corresponding historical_race_id
    connection.execute(text("""
        UPDATE race_review
        SET historical_race_id = (
            SELECT id FROM historical_race
            WHERE historical_race.name = race_review.race_name
        )
        WHERE historical_race_id IS NULL
    """))
    
    # 3. Create foreign key if it doesn't exist
    try:
        op.create_foreign_key(
            'fk_review_historical_race',
            'race_review', 'historical_race',
            ['historical_race_id'], ['id']
        )
    except Exception as e:
        print("Foreign key might already exist, continuing...")
    
    # 4. Make historical_race_id not nullable
    try:
        op.alter_column('race_review', 'historical_race_id',
            existing_type=sa.Integer(),
            nullable=False
        )
    except Exception as e:
        print("Column constraint might already be set, continuing...")
    
    # 5. Drop old columns if they exist
    try:
        op.drop_column('race_review', 'location')
    except Exception as e:
        print("Column 'location' might already be dropped, continuing...")
        
    try:
        op.drop_column('race_review', 'race_name')
    except Exception as e:
        print("Column 'race_name' might already be dropped, continuing...")

def downgrade():
    # Add back old columns
    op.add_column('race_review',
        sa.Column('race_name', sa.String(length=150))
    )
    op.add_column('race_review',
        sa.Column('location', sa.String(length=100))
    )

    # Copy data back
    connection = op.get_bind()
    connection.execute(text("""
        UPDATE race_review
        SET race_name = (
            SELECT name FROM historical_race
            WHERE historical_race.id = race_review.historical_race_id
        ),
        location = 'San Diego, CA'
    """))

    # Make race_name not nullable
    op.alter_column('race_review', 'race_name',
        existing_type=sa.String(length=150),
        nullable=False
    )

    # Drop new column and table
    op.drop_constraint('fk_review_historical_race', 'race_review', type_='foreignkey')
    op.drop_column('race_review', 'historical_race_id')