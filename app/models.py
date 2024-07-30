from sqlalchemy import Column, Integer, String , Date, DateTime, ForeignKey , Float , Boolean , Enum
from sqlalchemy.orm import relationship
from .database import Base
from passlib.context import CryptContext
from datetime import datetime , timezone
import enum

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    bookings = relationship("Booking", back_populates="user", foreign_keys="Booking.booked_by")
    modified_bookings = relationship("Booking", back_populates="last_modified_by_user", foreign_keys="Booking.last_modified_by")

    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)

    def check_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

    def __repr__(self):
        return f'<User {self.username}>'

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booked_by = Column(Integer, ForeignKey('users.id'))
    name = Column(String(25), nullable=False)
    phone = Column(String, nullable=False)
    booking_date  = Column(Date, nullable=False)
    time_slot = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None), onupdate=datetime.now(timezone.utc).replace(tzinfo=None))
    last_modified_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    user = relationship("User", foreign_keys=[booked_by])
    last_modified_by_user = relationship("User", foreign_keys=[last_modified_by])
    transactions = relationship("Transaction", back_populates="booking")
    transaction_summary = relationship("TransactionSummary", back_populates="booking", uselist=False)

    def __repr__(self):
        return f'<Booking {self.name} for {self.date} at {self.time_slot}>'
    

class TransactionStatus(enum.Enum):
    PENDING = "Pending"
    SUCCESSFUL = "Successful"
    PARTIAL = "Partial"



class TransactionType(enum.Enum):
    BOOKING_PAYMENT = "Booking Payment"
    SLOT_PAYMENT = "Slot Payment"
    DISCOUNT = "Discount"
    OTHER_ADJUSTMENT = "Other Adjustment"

class PaymentMethod(enum.Enum):
    CASH = "Cash"
    BKASH = "bKash"
    NAGAD = "Nagad"
    CARD = "Card"
    BANK_TRANSFER = "Bank Transfer"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    amount = Column(Float, nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None))
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_at = Column(DateTime, nullable=True)

    booking = relationship("Booking", back_populates="transactions")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])


class TransactionSummary(Base):
    __tablename__ = "transaction_summaries"

    booking_id = Column(Integer, ForeignKey('bookings.id'), primary_key=True)
    total_price = Column(Float, nullable=False)
    total_paid = Column(Float, default=0)
    cash_payment = Column(Float, default=0)
    bkash_payment = Column(Float, default=0)
    nagad_payment = Column(Float, default=0)
    card_payment = Column(Float, default=0)
    bank_transfer_payment = Column(Float, default=0)
    booking_payment = Column(Float, default=0)
    booking_payment_date = Column(Date, nullable=True)
    booking_cash_payment = Column(Float, default=0)
    booking_bkash_payment = Column(Float, default=0)
    booking_nagad_payment = Column(Float, default=0)
    booking_card_payment = Column(Float, default=0)
    booking_bank_transfer_payment = Column(Float, default=0)
    slot_payment = Column(Float, default=0)
    slot_cash_payment = Column(Float, default=0)
    slot_bkash_payment = Column(Float, default=0)
    slot_nagad_payment = Column(Float, default=0)
    slot_card_payment = Column(Float, default=0)
    slot_bank_transfer_payment = Column(Float, default=0)
    discount = Column(Float, default=0)
    other_adjustments = Column(Float, default=0)
    leftover = Column(Float, default=0)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None), onupdate=datetime.now(timezone.utc).replace(tzinfo=None))

    booking = relationship("Booking", back_populates="transaction_summary")




class DayOfWeek(enum.Enum):
    SUNDAY = "Sunday"
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"


class SlotPrice(Base):
    __tablename__ = "slot_prices"

    id = Column(Integer, primary_key=True, index=True)
    time_slot = Column(String, nullable=False)
    day_of_week = Column(Enum(DayOfWeek), nullable=False)
    price = Column(Float, nullable=False)
    start_date = Column(Date, nullable=True)  # For special events or promotions
    end_date = Column(Date, nullable=True)    # For special events or promotions
    is_default = Column(Boolean, default=True)  # To distinguish between default and special prices

    def __repr__(self):
        return f"<SlotPrice(time_slot='{self.time_slot}', day_of_week='{self.day_of_week}', price={self.price})>"