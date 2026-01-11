from fastapi import HTTPException
from src.modules.bookings.repository import BookingRepository

class BookingService:
    def __init__(self, repository: BookingRepository):
        self.repository = repository
        self.db = repository.db 

    async def book_slot(self, idempotency_key: str, patient_id: str, slot_id: str):
        # 1. Check Idempotency 
        existing_key = await self.repository.get_idempotency_key(idempotency_key)
        if existing_key and existing_key.response_json:
            return existing_key.response_json 

        # 2. Register key
        if not existing_key:
            await self.repository.create_idempotency_key(idempotency_key)

        try:
            # 3. Start Transaction & LOCK the slot
            slot = await self.repository.get_slot_with_lock(slot_id)
            
            if not slot:
                raise HTTPException(status_code=404, detail="Slot not found")
            
            if slot.is_booked:
                raise HTTPException(status_code=409, detail="Slot already booked")

            # 4. Update Slot Status
            slot.is_booked = True
            slot.status = "BOOKED"

            # 5. Create Booking Record
            booking = await self.repository.create_booking(
                patient_id=patient_id,
                doctor_id=slot.doctor_id, 
                slot_id=slot_id
            )

            # --- 6.5 NEW: LOG THE ACTION ---
            await self.repository.log_action(
                performed_by=patient_id,
                action="BOOKING_CREATED",
                target_id=str(booking.id),
                details=f"Booked slot {slot_id} via key {idempotency_key}"
            )
            # -------------------------------

            # 6. Commit Transaction (Release Lock)
            await self.db.commit()
            await self.db.refresh(booking)

            # 7. Save Result for Idempotency
            response_data = {
                "id": str(booking.id),
                "status": booking.status,
                "slot_id": str(booking.slot_id),
                "patient_id": str(booking.patient_id),
                "created_at": booking.created_at.isoformat() if booking.created_at else None
            }
            await self.repository.save_idempotency_response(idempotency_key, response_data)

            return booking

        except Exception as e:
            await self.db.rollback() 
            raise e