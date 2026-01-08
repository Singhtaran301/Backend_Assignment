import uuid
from sqlalchemy import Column, ForeignKey, Boolean, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctor_profiles.id"), nullable=False, index=True)
    
    start_time = Column(TIMESTAMP(timezone=True), nullable=False)
    end_time = Column(TIMESTAMP(timezone=True), nullable=False)
    
    is_booked = Column(Boolean, default=False, index=True)
    
    # 🔒 CONCURRENCY LOCK: Increment this on every update.
    # If DB version != Request version -> Reject.
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    # We use string reference "DoctorProfile" to avoid circular imports if needed, 
    # but since Doctor is in Auth, ensure you import it if creating relationships directly.