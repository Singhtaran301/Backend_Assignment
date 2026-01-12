import asyncio
import sys
import os

# Setup Path
sys.path.append(os.getcwd())

from src.core.database import AsyncSessionLocal
from src.modules.auth.models import User, Profile, UserRole
from src.common.utils import get_password_hash

async def create_admin():
    async with AsyncSessionLocal() as db:
        print("\n🔐 --- Create System Administrator ---")
        
        email = input("Enter Admin Email: ").strip()
        password = input("Enter Admin Password: ").strip()

        if not email or not password:
            print("❌ Error: Email and Password cannot be empty.")
            return

        try:
            # 1. Check if user exists
            from sqlalchemy.future import select
            stmt = select(User).where(User.email == email)
            result = await db.execute(stmt)
            if result.scalars().first():
                print("❌ Error: User with this email already exists.")
                return

            # 2. Hash Password
            hashed_password = get_password_hash(password)

            # 3. Create USER directly (Bypassing Repository to force Role)
            new_user = User(
                email=email,
                password_hash=hashed_password,
                role=UserRole.ADMIN,  # <--- FORCED ROLE
                is_active=True,
                is_verified=True
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

            # 4. Create PROFILE
            new_profile = Profile(
                user_id=new_user.id,
                full_name="Super Admin",
                phone_number="0000000000"
            )
            db.add(new_profile)
            await db.commit()
            
            print(f"\n✅ SUCCESS! Admin created: {email}")
            print(f"👉 Login now at POST /auth/login")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ FAILED: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(create_admin())