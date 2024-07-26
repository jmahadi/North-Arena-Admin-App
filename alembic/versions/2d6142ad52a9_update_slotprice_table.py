"""Update SlotPrice table

Revision ID: 2d6142ad52a9
Revises: 32eb3f4b5a7b
Create Date: 2024-07-26 00:00:50.469535

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2d6142ad52a9'
down_revision = '32eb3f4b5a7b'
branch_labels = None
depends_on = None

def upgrade():
    # Create the enum type
    op.execute("CREATE TYPE dayofweek AS ENUM ('SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY')")
    
    # Add the new columns
    op.add_column('slot_prices', sa.Column('day_of_week', postgresql.ENUM('SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', name='dayofweek'), nullable=True))
    op.add_column('slot_prices', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('slot_prices', sa.Column('end_date', sa.Date(), nullable=True))
    op.add_column('slot_prices', sa.Column('is_default', sa.Boolean(), nullable=True))
    
    # Set default values
    op.execute("UPDATE slot_prices SET day_of_week = 'SUNDAY', is_default = TRUE")
    
    # Make day_of_week not nullable
    op.alter_column('slot_prices', 'day_of_week', nullable=False)

def downgrade():
    op.drop_column('slot_prices', 'is_default')
    op.drop_column('slot_prices', 'end_date')
    op.drop_column('slot_prices', 'start_date')
    op.drop_column('slot_prices', 'day_of_week')
    op.execute("DROP TYPE dayofweek")
