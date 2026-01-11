from sqlalchemy.future import select
from sqlalchemy import and_
from src.modules.availability.models import AvailabilitySlot

class AvailabilityRepository:
    def __init__(self, db):
        self.db = db

    async def check_overlap(self, doctor_id: str, start: str, end: str):
        """Returns True if there is an overlapping slot."""
        query = select(AvailabilitySlot).where(
            and_(
                AvailabilitySlot.doctor_id == doctor_id,
                AvailabilitySlot.start_time < end,  # New Start must be before Old End
                AvailabilitySlot.end_time > start   # New End must be after Old Start
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def create_slot(self, doctor_id: str, start: str, end: str):
        slot = AvailabilitySlot(
            doctor_id=doctor_id,
            start_time=start,
            end_time=end
        )
        self.db.add(slot)
        await self.db.commit()
        await self.db.refresh(slot)
        return slot

    async def get_doctor_slots(self, doctor_id: str):
        query = select(AvailabilitySlot).where(
            AvailabilitySlot.doctor_id == doctor_id
        ).order_by(AvailabilitySlot.start_time)
        result = await self.db.execute(query)
        return result.scalars().all()