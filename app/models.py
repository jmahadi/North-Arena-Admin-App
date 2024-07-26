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
    transaction = relationship("Transaction", back_populates="booking", uselist=False)
    
    def __repr__(self):
        return f'<Booking {self.name} for {self.date} at {self.time_slot}>'
    


class TransactionStatus(enum.Enum):
    PENDING = "Pending"
    SUCCESSFUL = "Successful"
    PARTIAL = "Partial"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey('bookings.id'), nullable=False)
    total_price = Column(Float, nullable=False)
    booking_payment = Column(Float, default=500)
    fee_payment = Column(Float, default=0)
    discount = Column(Float, default=0)
    other_adjustments = Column(Float, default=0)  # For disputes or other adjustments
    leftover = Column(Float, default=0)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING)
    
    cash_payment = Column(Float, default=0)
    mobile_banking_payment = Column(Float, default=0)
    bank_transfer_payment = Column(Float, default=0)
    
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc).replace(tzinfo=None), onupdate=datetime.now(timezone.utc).replace(tzinfo=None))

    booking = relationship("Booking", back_populates="transaction")
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

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