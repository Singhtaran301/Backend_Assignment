import uuid
from datetime import datetime, timezone
from fastapi import HTTPException, status
from src.modules.auth.repository import AuthRepository
from src.modules.auth.schemas import UserCreate, UserLogin
from src.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token, 
    get_password_hash
)

class AuthService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    async def register_user(self, user_in: UserCreate):
        # 1. Check if email exists
        existing_user = await self.repository.get_user_by_email(user_in.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2. Prepare data
        user_data = {"email": user_in.email, "password": user_in.password}
        profile_data = {"full_name": user_in.full_name, "phone_number": user_in.phone_number}

        # 3. Create User
        return await self.repository.create_user(user_data, profile_data, user_in.role)

    async def login_user(self, login_in: UserLogin):
        # 1. Find User
        user = await self.repository.get_user_by_email(login_in.email)
        if not user or not verify_password(login_in.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        # 2. Generate Tokens
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)

        # 3. Store Refresh Token Hash in DB (Secure Rotation)
        # We hash the token itself so if DB is leaked, attackers can't use the tokens.
        token_hash = get_password_hash(refresh_token) 
        
        await self.repository.store_refresh_token(
            user_id=user.id,
            token_hash=token_hash
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def rotate_tokens(self, old_refresh_token: str):
        """
        Takes an old token, invalidates it, and issues a new pair.
        """
        # 1. Find the token in DB (by verifying hash match would be ideal, 
        # but for simplicity we verify validity and user first).
        # In a real system, you decode the JWT to get user_id first.
        from jose import jwt
        from src.common.config import settings
        
        try:
            payload = jwt.decode(old_refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id = payload.get("sub")
            if payload.get("type") != "refresh":
                 raise HTTPException(status_code=401, detail="Invalid token type")
        except Exception:
             raise HTTPException(status_code=401, detail="Invalid refresh token")

        # 2. Check if this token is active in DB (Reuse Detection)
        # We need to find the specific token entry. 
        # Ideally, the frontend sends the token ID, or we match hash.
        # For this assignment, we will rotate by User ID (simplification).
        
        # Revoke OLD tokens
        await self.repository.revoke_all_user_tokens(user_id)

        # 3. Issue NEW tokens
        new_access = create_access_token(subject=user_id)
        new_refresh = create_refresh_token(subject=user_id)
        
        # 4. Store NEW token
        new_hash = get_password_hash(new_refresh)
        await self.repository.store_refresh_token(user_id, new_hash)

        return {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer"
        }
    async def logout_user(self, user_id: str):
        """
        Securely logs out by removing all refresh tokens from DB.
        """
        await self.repository.revoke_all_user_tokens(user_id)
    async def get_user_profile(self, user_id: str):
        return await self.repository.get_full_user_details(user_id)

    async def update_user_profile(self, user_id: str, update_data: UserCreate):
        # Convert Pydantic model to dict, excluding None
        data = update_data.dict(exclude_unset=True)
        
        # Update DB
        await self.repository.update_profile(user_id, data)
        
        # Log it
        await self.repository.log_action(
            performed_by=user_id,
            action="PROFILE_UPDATE",
            target_id=user_id,
            details=str(data)
        )
        
        return await self.get_user_profile(user_id)