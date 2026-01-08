import uuid
from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy import TIMESTAMP
from src.core.database import Base

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), unique=True, nullable=False)
    
    diagnosis = Column(Text, nullable=False)
    
    # Stores structure: [{"medicine": "Paracetamol", "dosage": "500mg", "freq": "BID"}]
    medications = Column(JSONB, nullable=False) 
    
    notes = Column(Text, nullable=True) # In production, Encrypt this field!
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())