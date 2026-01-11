import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from src.core.database import AsyncSessionLocal
from src.modules.bookings.models import Booking, BookingStatus
from src.modules.availability.models import AvailabilitySlot
from src.modules.auth.models import AuditLog

async def cancel_stale_bookings():
    print("🧹 Janitor: Waking up...") # <--- Debug 1
    
    async with AsyncSessionLocal() as db:
        try:
            # Use timezone-aware UTC time
            now = datetime.now(timezone.utc)
            threshold = now - timedelta(seconds=30) 
            
            print(f"🕒 Checking for bookings created before: {threshold}") # <--- Debug 2

            query = select(Booking).where(
                Booking.status == BookingStatus.PENDING,
                Booking.created_at < threshold
            )
            result = await db.execute(query)
            stale_bookings = result.scalars().all()

            print(f"🔎 Found {len(stale_bookings)} stale bookings.") # <--- Debug 3

            if not stale_bookings:
                return 

            for booking in stale_bookings:
                print(f"💀 Killing booking {booking.id} created at {booking.created_at}") # <--- Debug 4
                
                # A. Cancel
                booking.status = BookingStatus.CANCELLED
                
                # B. Release Slot
                slot_query = select(AvailabilitySlot).where(AvailabilitySlot.id == booking.slot_id)
                slot_result = await db.execute(slot_query)
                slot = slot_result.scalars().first()
                
                if slot:
                    slot.is_booked = False
                    slot.status = "OPEN"
                    print(f"🔓 Released slot {slot.id}")

                # C. Audit
                log = AuditLog(
                    action="AUTO_TIMEOUT",
                    performed_by=booking.patient_id,
                    target_id=str(booking.id),
                    details="Booking cancelled due to payment timeout."
                )
                db.add(log)

            await db.commit()
            print("✅ Cleanup commit successful.")
            
        except Exception as e:
            print(f"❌ Janitor Error: {e}")
            await db.rollback()