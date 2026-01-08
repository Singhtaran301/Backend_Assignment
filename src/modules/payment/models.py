import uuid
from sqlalchemy import Column, ForeignKey, String, DECIMAL, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.core.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id = Column(UUID(as_uuid=True), ForeignKey("bookings.id"), nullable=False)
    
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="INR")
    
    # Stripe/Razorpay Transaction ID
    provider_payment_id = Column(String, nullable=True)
    
    status = Column(String, default="pending") # pending, paid, failed, refunded
    
    # 🔒 IDEMPOTENCY: Unique index prevents double-insert of same payment request
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())