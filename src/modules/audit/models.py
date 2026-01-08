import uuid
from sqlalchemy import Column, ForeignKey, String, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    # Partitioning Note: In PROD, partition this table by range (created_at)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String, nullable=False) # e.g. "VIEW_PRESCRIPTION"
    resource_id = Column(UUID(as_uuid=True), nullable=True) # e.g. PrescriptionID
    
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)