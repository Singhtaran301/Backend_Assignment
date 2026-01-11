from sqlalchemy.future import select
from sqlalchemy import update
from sqlalchemy.orm import selectinload
from src.modules.auth.models import User, RefreshToken, Profile, DoctorProfile, AuditLog

class AuthRepository:
    def __init__(self, db):
        self.db = db

    # --- FIXED METHOD: Accepts 3 arguments now ---
    async def create_user(self, user_data: dict, profile_data: dict, role: str):
        # 1. Create the User (Account)
        new_user = User(**user_data)
        self.db.add(new_user)
        # Flush to generate the UUID
        await self.db.flush() 

        # 2. Create the Generic Profile (Name, Phone, etc.)
        new_profile = Profile(user_id=new_user.id, **profile_data)
        self.db.add(new_profile)

        # 3. Create Doctor Profile (Empty shell if role is doctor)
        if role == "doctor":
            # We MUST provide a default specialization to avoid database errors
            doctor_profile = DoctorProfile(
                user_id=new_user.id,
                specialization="General Physician",
                experience_years=0,
                consultation_fee=0.0
            )
            self.db.add(doctor_profile)

        # 4. Commit everything
        await self.db.commit()
        await self.db.refresh(new_user)
        
        # 5. Return user with loaded relationships
        return await self.get_full_user_details(new_user.id)

    async def get_user_by_email(self, email: str):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def store_refresh_token(self, user_id: str, token_hash: str, expires_at):
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.db.add(refresh_token)
        await self.db.commit()

    async def update_profile(self, user_id: str, data: dict):
        """Updates generic profile and doctor profile if applicable."""
        # 1. Update Generic Profile
        profile_fields = {"full_name", "phone_number", "dob", "gender"}
        profile_data = {k: v for k, v in data.items() if k in profile_fields and v is not None}
        
        if profile_data:
            stmt = update(Profile).where(Profile.user_id == user_id).values(**profile_data)
            await self.db.execute(stmt)

        # 2. Update Doctor Profile (if exists)
        doctor_fields = {"specialization", "experience_years", "consultation_fee"}
        doc_data = {k: v for k, v in data.items() if k in doctor_fields and v is not None}
        
        if doc_data:
            stmt = update(DoctorProfile).where(DoctorProfile.user_id == user_id).values(**doc_data)
            await self.db.execute(stmt)

        await self.db.commit()

    async def log_action(self, performed_by: str, action: str, target_id: str, details: str):
        log = AuditLog(
            performed_by=performed_by,
            action=action,
            target_id=target_id,
            details=details
        )
        self.db.add(log)
        await self.db.commit()

    async def get_full_user_details(self, user_id: str):
        """
        Fetches User + Profile + DoctorProfile eagerly.
        We MUST use selectinload to avoid 'MissingGreenlet' error.
        """
        query = (
            select(User)
            .options(
                selectinload(User.profile),       # Load the Profile
                selectinload(User.doctor_profile) # Load the Doctor Profile
            )
            .where(User.id == user_id)
        )
        result = await self.db.execute(query)
        return result.scalars().first()