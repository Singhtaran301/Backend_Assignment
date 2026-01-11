from pydantic import BaseModel, validator
from datetime import datetime
from typing import List
from uuid import UUID

class SlotCreate(BaseModel):
    start_time: datetime
    end_time: datetime

    @validator("end_time")
    def check_time_order(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("End time must be after start time")
        return v

class SlotResponse(BaseModel):
    id: UUID
    doctor_id: UUID
    start_time: datetime
    end_time: datetime
    is_booked: bool
    status: str

    class Config:
        from_attributes = True