import uuid
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.payment.models import Payment, PaymentStatus
from src.modules.bookings.models import Booking, BookingStatus
from src.modules.availability.models import AvailabilitySlot
from src.modules.auth.models import AuditLog

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment_intent(self, booking_id: str, amount: float):
        """Step 1: User clicks 'Pay'. We create a record."""
        # Check if booking exists
        booking = await self.db.get(Booking, booking_id)
        if not booking:
            return None

        payment = Payment(
            booking_id=booking_id,
            amount=amount,
            status=PaymentStatus.PENDING,
            transaction_id=f"tx_{uuid.uuid4().hex[:10]}" # Mock Bank ID
        )
        self.db.add(payment)
        await self.db.commit()
        return payment

    async def process_webhook(self, transaction_id: str, status: str, signature: str):
        """
        Step 2: The 'Bank' calls us back.
        CRITICAL: This handles the State Machine transitions.
        """
        # 1. Verify Signature (Mock)
        if signature != "valid_secret_key":
            raise ValueError("Invalid Webhook Signature")

        # 2. Find Payment
        query = select(Payment).where(Payment.transaction_id == transaction_id)
        result = await self.db.execute(query)
        payment = result.scalars().first()
        
        if not payment:
            return "Payment Not Found"

        # 3. Idempotency Check (If already processed, stop)
        if payment.status != PaymentStatus.PENDING:
            return "Already Processed"

        # 4. Fetch Booking & Slot
        booking = await self.db.get(Booking, payment.booking_id)
        slot = await self.db.get(AvailabilitySlot, booking.slot_id)

        # 5. Handle Logic
        if status == "SUCCESS":
            payment.status = PaymentStatus.SUCCESS
            booking.status = BookingStatus.CONFIRMED
            # Audit
            self.db.add(AuditLog(
                action="PAYMENT_SUCCESS", 
                target_id=str(booking.id), 
                details=f"Payment {payment.amount} received.",
                performed_by=booking.patient_id
            ))

        elif status == "FAILED":
            payment.status = PaymentStatus.FAILED
            booking.status = BookingStatus.FAILED
            
            # CRITICAL: RELEASE THE SLOT
            slot.is_booked = False
            slot.status = "OPEN"
            
            # Audit
            self.db.add(AuditLog(
                action="PAYMENT_FAILED", 
                target_id=str(booking.id), 
                details="Payment failed. Slot released.",
                performed_by=booking.patient_id
            ))

        await self.db.commit()
        return {"status": "updated", "new_state": booking.status}