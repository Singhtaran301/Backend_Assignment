import uuid
import enum
from sqlalchemy import Column, String, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base

class BookingStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Who is booking?
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Who are they seeing?
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Which inventory item? (The Slot)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("availability_slots.id"), unique=True, nullable=False)
    
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])
    slot = relationship("AvailabilitySlot")

class IdempotencyKey(Base):
    """
    Prevents duplicate requests. 
    If a user clicks 'Pay' twice, we check this table.
    """
    __tablename__ = "idempotency_keys"
    __table_args__ = {'extend_existing': True}

    key = Column(String, primary_key=True, index=True)
    response_json = Column(JSON, nullable=True) # Store the success response to replay it
    created_at = Column(DateTime(timezone=True), server_default=func.now())