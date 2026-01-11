import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Boolean, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False)
    
    is_booked = Column(Boolean, default=False, index=True)
    
    # We use this for "Locking" later (Phase 7)
    # Status: "OPEN", "LOCKED", "BOOKED"
    status = Column(String, default="OPEN") 

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship back to Doctor (User)
    doctor = relationship("User", backref="slots")