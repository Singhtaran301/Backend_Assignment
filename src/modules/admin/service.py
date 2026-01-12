from sqlalchemy import func, desc
from sqlalchemy.future import select
from src.modules.bookings.models import Booking, BookingStatus
from src.modules.auth.models import DoctorProfile, User
# --- NEW IMPORTS: We now look at the actual money table ---
from src.modules.payment.models import Payment, PaymentStatus
from datetime import datetime, timedelta

class AdminService:
    def __init__(self, db_session):
        self.db = db_session

    async def get_daily_consultations(self, days: int = 7):
        start_date = datetime.utcnow() - timedelta(days=days)
        stmt = (
            select(
                func.date(Booking.created_at).label("date"),
                func.count(Booking.id).label("count")
            )
            .where(Booking.created_at >= start_date)
            .where(Booking.status != BookingStatus.CANCELLED) 
            .group_by(func.date(Booking.created_at))
            .order_by(desc("date"))
        )
        result = await self.db.execute(stmt)
        return [{"date": str(row.date), "count": row.count} for row in result]

    async def get_revenue_summary(self):
        """
        Calculates ACTUAL revenue from the 'payments' table.
        Logic: Sum of all amounts where status is 'SUCCESS'.
        """
        stmt = (
            select(func.sum(Payment.amount))
            .where(Payment.status == PaymentStatus.SUCCESS) # Only count successful transactions
        )
        
        result = await self.db.execute(stmt)
        total = result.scalar()
        
        # Safety: Convert Decimal to float, default to 0.0 if None
        total_float = float(total) if total else 0.0
        
        return {"total_revenue": total_float, "currency": "USD"}

    async def get_doctor_stats(self, limit: int = 5):
        stmt = (
            select(
                DoctorProfile.specialization,
                func.count(Booking.id).label("total_consultations")
            )
            .select_from(Booking)
            .join(User, Booking.doctor_id == User.id)
            .join(DoctorProfile, User.id == DoctorProfile.user_id)
            # We count confirmed bookings as valid consultations for stats
            .where(Booking.status == BookingStatus.CONFIRMED)
            .group_by(DoctorProfile.specialization)
            .order_by(desc("total_consultations"))
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return [{"specialization": row.specialization, "count": row.total_consultations} for row in result]