import uuid
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload  # <--- 1. NEW IMPORT
from fastapi import HTTPException
from src.modules.consultations.models import Prescription
from src.modules.bookings.models import Booking
from src.common.security import encrypt_data, decrypt_data
from src.modules.auth.models import AuditLog

class ConsultationService:
    def __init__(self, db_session):
        self.db = db_session

    async def create_prescription(self, user_id: str, booking_id: str, diagnosis: str, medications: str):
        # 1. Fetch Booking
        booking = await self.db.get(Booking, booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # 2. Access Control
        if str(booking.doctor_id) != str(user_id):
            raise HTTPException(status_code=403, detail="Only the assigned doctor can prescribe.")

        # 3. Immutability Check
        stmt = select(Prescription).where(Prescription.booking_id == booking_id)
        existing = await self.db.execute(stmt)
        if existing.scalars().first():
            raise HTTPException(status_code=409, detail="Prescription already exists. Updates are not allowed.")

        # 4. Encrypt
        encrypted_diagnosis = encrypt_data(diagnosis)
        encrypted_meds = encrypt_data(medications)

        # 5. Save to DB (GENERATE ID MANUALLY)
        new_id = uuid.uuid4()
        prescription = Prescription(
            id=new_id,
            booking_id=booking_id,
            diagnosis=encrypted_diagnosis,
            medications=encrypted_meds
        )
        self.db.add(prescription)
        
        # 6. Audit Log
        self.db.add(AuditLog(
            action="PRESCRIPTION_CREATED",
            performed_by=user_id,
            target_id=str(new_id),
            details="Encrypted prescription created."
        ))
        
        await self.db.commit()
        return {"status": "created", "id": str(new_id)}

    async def get_prescription(self, user_id: str, booking_id: str):
        # 1. Fetch with EAGER LOADING (The Fix)
        # We tell DB to JOIN and fetch the booking table in one shot.
        stmt = (
            select(Prescription)
            .options(joinedload(Prescription.booking)) # <--- 2. CRITICAL FIX
            .where(Prescription.booking_id == booking_id)
        )
        result = await self.db.execute(stmt)
        prescription = result.scalars().first()
        
        if not prescription:
            raise HTTPException(status_code=404, detail="Prescription not found")

        # 2. Access Control
        # Now accessing .booking is safe because it's already loaded in memory
        booking = prescription.booking
        
        if str(booking.patient_id) != str(user_id) and str(booking.doctor_id) != str(user_id):
            raise HTTPException(status_code=403, detail="Access denied. You are not part of this consultation.")

        # Audit Access
        self.db.add(AuditLog(
            action="PRESCRIPTION_VIEWED",
            performed_by=user_id,
            target_id=str(prescription.id),
            details="Decrypted view access."
        ))
        await self.db.commit()

        # 3. Return Decrypted Data
        return {
            "id": prescription.id,
            "booking_id": prescription.booking_id,
            "diagnosis": decrypt_data(prescription.diagnosis),
            "medications": decrypt_data(prescription.medications),
            "created_at": prescription.created_at
        }