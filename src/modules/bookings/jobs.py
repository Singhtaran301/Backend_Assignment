import logging
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.future import select
from src.core.database import AsyncSessionLocal
from src.modules.bookings.models import Booking, BookingStatus
from src.modules.availability.models import AvailabilitySlot
from src.modules.audit.models import AuditLog # Ensure correct import path

# Setup structured logging
logger = logging.getLogger(__name__)

async def cancel_stale_bookings(max_retries: int = 3):
    """
    Background Janitor: Cancels PENDING bookings older than 30 seconds.
    Includes per-item error handling and retry logic.
    """
    logger.info("🧹 Janitor: Waking up for stale booking cleanup...")
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Identify Target Bookings
            now = datetime.now(timezone.utc)
            threshold = now - timedelta(minutes=10)
            
            query = select(Booking).where(
                Booking.status == BookingStatus.PENDING,
                Booking.created_at < threshold
            )
            result = await db.execute(query)
            stale_bookings = result.scalars().all()

            if not stale_bookings:
                return 

            logger.info(f"🔎 Found {len(stale_bookings)} stale bookings to process.")

            for booking in stale_bookings:
                retry_count = 0
                while retry_count < max_retries:
                    try:
                        # --- START ATOMIC TRANSACTION PER BOOKING ---
                        # Release Slot
                        slot_query = select(AvailabilitySlot).where(AvailabilitySlot.id == booking.slot_id)
                        slot_result = await db.execute(slot_query)
                        slot = slot_result.scalars().first()
                        
                        if slot:
                            slot.is_booked = False
                            slot.status = "OPEN"

                        # Update Booking Status
                        booking.status = BookingStatus.CANCELLED
                        
                        # Audit Log Entry
                        log = AuditLog(
                            action="AUTO_TIMEOUT",
                            performed_by=booking.patient_id,
                            target_id=str(booking.id),
                            details=f"Payment timeout. Attempt {retry_count + 1}"
                        )
                        db.add(log)

                        # Commit individual booking to avoid batch failure
                        await db.commit()
                        logger.info(f"✅ Successfully timed out booking {booking.id}")
                        break # Success - move to next booking

                    except Exception as item_error:
                        retry_count += 1
                        await db.rollback()
                        
                        # Exponential Backoff Logic
                        wait_time = 2 ** retry_count 
                        logger.warning(f"⚠️ Failed booking {booking.id}. Retry {retry_count}/{max_retries} in {wait_time}s. Error: {item_error}")
                        
                        if retry_count >= max_retries:
                            # DEAD-LETTER STRATEGY: Log permanent failure to Audit for Admin review
                            logger.error(f"❌ DEAD-LETTER: Booking {booking.id} failed after {max_retries} retries.")
                            # Optional: Send notification to Admin or write to a dedicated 'failed_jobs' table
                        
                        await asyncio.sleep(wait_time)

        except Exception as global_error:
            logger.error(f"🚨 Global Janitor Failure: {global_error}")
            await db.rollback()