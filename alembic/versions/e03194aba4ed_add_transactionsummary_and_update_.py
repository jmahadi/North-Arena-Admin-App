from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e03194aba4ed'
down_revision: Union[str, None] = '2d6142ad52a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def create_enum_if_not_exists(conn, enum_name, values):
    # Check if the enum already exists
    existing_enum = conn.execute(
        sa.text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :enum_name)"),
        {'enum_name': enum_name}
    ).scalar()

    if not existing_enum:
        op.execute(f"CREATE TYPE {enum_name} AS ENUM {values}")
    return existing_enum

def upgrade() -> None:
    conn = op.get_bind()

    # Create enum types if they don't exist
    
    transactiontype_exists = create_enum_if_not_exists(conn, 'transactiontype', "('BOOKING_PAYMENT', 'SLOT_PAYMENT', 'DISCOUNT', 'OTHER_ADJUSTMENT')")
    paymentmethod_exists = create_enum_if_not_exists(conn, 'paymentmethod', "('CASH', 'BKASH', 'NAGAD', 'CARD', 'BANK_TRANSFER')")

    # Update Transaction table
    if not transactiontype_exists:
        op.add_column('transactions', sa.Column('transaction_type', sa.Enum('BOOKING_PAYMENT', 'SLOT_PAYMENT', 'DISCOUNT', 'OTHER_ADJUSTMENT', name='transactiontype'), nullable=True))
    if not paymentmethod_exists:
        op.add_column('transactions', sa.Column('payment_method', sa.Enum('CASH', 'BKASH', 'NAGAD', 'CARD', 'BANK_TRANSFER', name='paymentmethod'), nullable=True))

    # Set default values for existing rows
    op.execute("UPDATE transactions SET transaction_type = 'BOOKING_PAYMENT', payment_method = 'CASH' WHERE transaction_type IS NULL OR payment_method IS NULL")
    
    # Now make the columns NOT NULL
    op.alter_column('transactions', 'transaction_type', nullable=False)
    op.alter_column('transactions', 'payment_method', nullable=False)
    
    # Drop columns that are no longer needed
    columns_to_drop = ['total_price', 'booking_payment', 'fee_payment', 'discount', 'other_adjustments', 
                       'leftover', 'status', 'cash_payment', 'mobile_banking_payment', 'bank_transfer_payment', 
                       'updated_by', 'updated_at']
    for column in columns_to_drop:
        op.drop_column('transactions', column)

    # Create TransactionSummary table
    op.create_table('transaction_summaries',
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('total_paid', sa.Float(), nullable=True),
        sa.Column('discount', sa.Float(), nullable=True),
        sa.Column('other_adjustments', sa.Float(), nullable=True),
        sa.Column('leftover', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ),
        sa.PrimaryKeyConstraint('booking_id')
    )


def downgrade():
    # Drop TransactionSummary table
    op.drop_table('transaction_summaries')

    # Revert changes to Transaction table
    op.add_column('transactions', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('transactions', sa.Column('updated_by', sa.Integer(), nullable=True))
    op.add_column('transactions', sa.Column('bank_transfer_payment', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('mobile_banking_payment', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('cash_payment', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('status', sa.Enum('PENDING', 'SUCCESSFUL', 'PARTIAL', name='transactionstatus'), nullable=True))
    op.add_column('transactions', sa.Column('leftover', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('other_adjustments', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('discount', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('fee_payment', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('booking_payment', sa.Float(), nullable=True))
    op.add_column('transactions', sa.Column('total_price', sa.Float(), nullable=True))
    op.drop_column('transactions', 'payment_method')
    op.drop_column('transactions', 'transaction_type')

    # We don't drop the enum types in downgrade as they might be used elsewhere
