from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from src.modules.auth.models import User, Profile, DoctorProfile
from src.core.security import get_password_hash

class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        """Finds a user by email (for Login check)."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create_user(self, user_data: dict, profile_data: dict, role: str):
        """
        Transactional Create: Creates User + Profile together.
        """
        # 1. Hash the password before saving
        hashed_pw = get_password_hash(user_data["password"])
        
        # 2. Create User Object
        new_user = User(
            email=user_data["email"],
            password_hash=hashed_pw,
            role=role,
            is_active=True
        )
        self.db.add(new_user)
        await self.db.flush() # Flush to generating new_user.id
        
        # 3. Create Profile linked to User
        new_profile = Profile(
            user_id=new_user.id,
            full_name=profile_data["full_name"],
            phone_number=profile_data.get("phone_number")
        )
        self.db.add(new_profile)
        
        # 4. If Doctor, create Doctor Profile too
        if role == "doctor":
            # (Logic for doctor profile would go here if needed immediately)
            pass

        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user