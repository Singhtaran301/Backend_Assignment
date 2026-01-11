from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class BookingCreate(BaseModel):
    slot_id: UUID

class BookingResponse(BaseModel):
    id: UUID
    slot_id: UUID
    status: str
    patient_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True