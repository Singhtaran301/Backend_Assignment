from fastapi import HTTPException
from src.modules.availability.repository import AvailabilityRepository
from src.modules.availability.schemas import SlotCreate

class AvailabilityService:
    def __init__(self, repository: AvailabilityRepository):
        self.repository = repository

    async def create_availability_slot(self, user_id: str, slot_data: SlotCreate):
        # 1. Check for Overlap
        has_overlap = await self.repository.check_overlap(
            user_id, slot_data.start_time, slot_data.end_time
        )
        if has_overlap:
            raise HTTPException(status_code=400, detail="Time slot overlaps with an existing slot")

        # 2. Create
        return await self.repository.create_slot(
            user_id, slot_data.start_time, slot_data.end_time
        )

    async def list_slots(self, doctor_id: str):
        return await self.repository.get_doctor_slots(doctor_id)