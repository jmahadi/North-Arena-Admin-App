"""Add amount column to transactions table

Revision ID: 5bb0ab69e391
Revises: 39a6c6767833
Create Date: 2024-07-27 14:12:27.805144

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5bb0ab69e391'
down_revision: Union[str, None] = '39a6c6767833'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Add the column as nullable
    op.add_column('transactions', sa.Column('amount', sa.Float(), nullable=True))
    
    # Set a default value for existing rows (adjust the default value as needed)
    op.execute("UPDATE transactions SET amount = 0 WHERE amount IS NULL")
    
    # Now make the column NOT NULL
    op.alter_column('transactions', 'amount', nullable=False)

def downgrade():
    op.drop_column('transactions', 'amount')
