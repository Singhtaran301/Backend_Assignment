import uuid
from sqlalchemy import Column, Date, Integer, DECIMAL, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.core.database import Base

class DailyMetric(Base):
    """
    Stores pre-aggregated stats for Admin Dashboard.
    Why? Querying this table is instant (O(1)), vs counting 
    millions of rows in bookings (O(N)).
    """
    __tablename__ = "daily_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date = Column(Date, unique=True, nullable=False, index=True)
    
    total_bookings = Column(Integer, default=0)
    completed_bookings = Column(Integer, default=0)
    cancelled_bookings = Column(Integer, default=0)
    
    total_revenue = Column(DECIMAL(10, 2), default=0.0)
    
    # Stores breakdown like {"cardio": 10, "derma": 5}
    specialization_stats = Column(JSON, default={})