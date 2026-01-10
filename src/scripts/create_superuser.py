import asyncio
import sys
import os
# Add the project root to python path so imports work
sys.path.append(os.getcwd())

from src.core.database import AsyncSessionLocal
from src.modules.auth.repository import AuthRepository

async def create_admin():
    async with AsyncSessionLocal() as db:
        repo = AuthRepository(db)
        print("--- Creating Superuser ---")
        email = input("Enter Admin Email: ")
        password = input("Enter Admin Password: ")

        try:
            # We reuse create_user but force the role to 'admin'
            # verifying validation logic is bypassed here since we call repo directly
            user_data = {"email": email, "password": password}
            profile_data = {"full_name": "System Admin"}

            await repo.create_user(user_data, profile_data, role="admin")
            print(f"✅ Success! Admin created: {email}")
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_admin())