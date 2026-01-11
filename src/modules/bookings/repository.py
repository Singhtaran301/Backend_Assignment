from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError
from src.modules.bookings.models import Booking, IdempotencyKey, BookingStatus
from src.modules.availability.models import AvailabilitySlot
from src.modules.auth.models import AuditLog  # <--- CRITICAL IMPORT

class BookingRepository:
    def __init__(self, db):
        self.db = db

    async def get_idempotency_key(self, key: str):
        query = select(IdempotencyKey).where(IdempotencyKey.key == key)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_idempotency_key(self, key: str):
        record = IdempotencyKey(key=key)
        self.db.add(record)
        try:
            await self.db.flush()
        except IntegrityError:
            return None 
        return record

    async def save_idempotency_response(self, key: str, data: dict):
        record = await self.get_idempotency_key(key)
        if record:
            record.response_json = data
            await self.db.commit()

    async def get_slot_with_lock(self, slot_id: str):
        query = select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id).with_for_update()
        result = await self.db.execute(query)
        return result.scalars().first()

    async def create_booking(self, patient_id: str, doctor_id: str, slot_id: str):
        booking = Booking(
            patient_id=patient_id,
            doctor_id=doctor_id,
            slot_id=slot_id,
            status=BookingStatus.PENDING
        )
        self.db.add(booking)
        await self.db.flush()
        return booking

    # --- ADD THIS METHOD COMPLETELY ---
    async def log_action(self, performed_by: str, action: str, target_id: str, details: str):
        log = AuditLog(
            performed_by=performed_by,
            action=action,
            target_id=target_id,
            details=details
        )
        self.db.add(log)
        # Note: No await db.commit() here, because it runs inside the main transaction