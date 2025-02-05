"""Add detailed payment breakdowns to TransactionSummary

Revision ID: e5dfe22c12a6
Revises: 60c111a2a525
Create Date: 2024-07-27 19:56:02.363700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5dfe22c12a6'
down_revision: Union[str, None] = '60c111a2a525'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('transaction_summaries', sa.Column('booking_cash_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('booking_bkash_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('booking_nagad_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('booking_card_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('booking_bank_transfer_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('slot_cash_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('slot_bkash_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('slot_nagad_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('slot_card_payment', sa.Float(), nullable=True))
    op.add_column('transaction_summaries', sa.Column('slot_bank_transfer_payment', sa.Float(), nullable=True))
    op.alter_column('transaction_summaries', 'cash_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'bkash_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'nagad_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'card_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'bank_transfer_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'booking_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'slot_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=True,
               existing_server_default=sa.text("'0'::double precision"))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('transaction_summaries', 'slot_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'booking_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'bank_transfer_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'card_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'nagad_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'bkash_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text("'0'::double precision"))
    op.alter_column('transaction_summaries', 'cash_payment',
               existing_type=sa.DOUBLE_PRECISION(precision=53),
               nullable=False,
               existing_server_default=sa.text("'0'::double precision"))
    op.drop_column('transaction_summaries', 'slot_bank_transfer_payment')
    op.drop_column('transaction_summaries', 'slot_card_payment')
    op.drop_column('transaction_summaries', 'slot_nagad_payment')
    op.drop_column('transaction_summaries', 'slot_bkash_payment')
    op.drop_column('transaction_summaries', 'slot_cash_payment')
    op.drop_column('transaction_summaries', 'booking_bank_transfer_payment')
    op.drop_column('transaction_summaries', 'booking_card_payment')
    op.drop_column('transaction_summaries', 'booking_nagad_payment')
    op.drop_column('transaction_summaries', 'booking_bkash_payment')
    op.drop_column('transaction_summaries', 'booking_cash_payment')
    # ### end Alembic commands ###
