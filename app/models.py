from sqlalchemy import Column, Integer, String , Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from passlib.context import CryptContext
from datetime import datetime , timezone

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

    def __repr__(self):
        return f'<Booking {self.name} for {self.date} at {self.time_slot}>'