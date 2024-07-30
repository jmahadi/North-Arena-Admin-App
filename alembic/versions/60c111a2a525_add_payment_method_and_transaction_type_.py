"""Add payment method and transaction type fields to TransactionSummary

Revision ID: 60c111a2a525
Revises: 5bb0ab69e391
Create Date: 2024-07-27 18:46:51.010902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '60c111a2a525'
down_revision: Union[str, None] = '5bb0ab69e391'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
   # Add new columns to transaction_summaries table
    op.add_column('transaction_summaries', sa.Column('cash_payment', sa.Float(), nullable=True, server_default='0'))
    op.add_column('transaction_summaries', sa.Column('bkash_payment', sa.Float(), nullable=True, server_default='0'))
    op.add_column('transaction_summaries', sa.Column('nagad_payment', sa.Float(), nullable=True, server_default='0'))
    op.add_column('transaction_summaries', sa.Column('card_payment', sa.Float(), nullable=True, server_default='0'))
    op.add_column('transaction_summaries', sa.Column('bank_transfer_payment', sa.Float(), nullable=True, server_default='0'))
    op.add_column('transaction_summaries', sa.Column('booking_payment', sa.Float(), nullable=True, server_default='0'))
    op.add_column('transaction_summaries', sa.Column('slot_payment', sa.Float(), nullable=True, server_default='0'))

    # Set default values for existing rows
    op.execute("UPDATE transaction_summaries SET cash_payment = 0, bkash_payment = 0, nagad_payment = 0, card_payment = 0, bank_transfer_payment = 0, booking_payment = 0, slot_payment = 0")

    # Make the new columns non-nullable
    op.alter_column('transaction_summaries', 'cash_payment', nullable=False)
    op.alter_column('transaction_summaries', 'bkash_payment', nullable=False)
    op.alter_column('transaction_summaries', 'nagad_payment', nullable=False)
    op.alter_column('transaction_summaries', 'card_payment', nullable=False)
    op.alter_column('transaction_summaries', 'bank_transfer_payment', nullable=False)
    op.alter_column('transaction_summaries', 'booking_payment', nullable=False)
    op.alter_column('transaction_summaries', 'slot_payment', nullable=False)


def downgrade() -> None:
    op.drop_column('transaction_summaries', 'slot_payment')
    op.drop_column('transaction_summaries', 'booking_payment')
    op.drop_column('transaction_summaries', 'bank_transfer_payment')
    op.drop_column('transaction_summaries', 'card_payment')
    op.drop_column('transaction_summaries', 'nagad_payment')
    op.drop_column('transaction_summaries', 'bkash_payment')
    op.drop_column('transaction_summaries', 'cash_payment')
