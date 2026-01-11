from fastapi import HTTPException, status
from src.modules.auth.repository import AuthRepository
from src.modules.auth.schemas import UserCreate, UserLogin, TokenResponse, ProfileUpdate
from src.common.utils import get_password_hash, verify_password, create_access_token, create_refresh_token
from src.common.config import settings
from datetime import timedelta, datetime
from jose import jwt, JWTError
import uuid
class AuthService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    async def register_user(self, user_in: UserCreate):
        # 1. Check if email exists
        existing_user = await self.repository.get_user_by_email(user_in.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 2. Hash Password
        hashed_password = get_password_hash(user_in.password)

        # 3. Prepare User Data (Account)
        # We explicitly exclude profile fields here
        user_data = user_in.dict(exclude={"role", "full_name", "phone_number"})
        
        # --- THE FIX IS HERE ---
        user_data["password_hash"] = hashed_password
        if "password" in user_data:
            del user_data["password"]  # <--- CRITICAL: Remove raw password!
        # -----------------------

        user_data["role"] = user_in.role

        # 4. Prepare Profile Data
        profile_data = {
            "full_name": user_in.full_name,
            "phone_number": user_in.phone_number
        }

        # 5. Create in DB
        return await self.repository.create_user(user_data, profile_data, user_in.role)

    async def login_user(self, login_data: UserLogin) -> TokenResponse:
        # 1. Get User
        user = await self.repository.get_user_by_email(login_data.email)
        if not user:
            raise HTTPException(status_code=400, detail="Invalid credentials")

        # 2. Verify Password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(status_code=400, detail="Invalid credentials")
        
        # 3. Check Active Status
        if not user.is_active:
             raise HTTPException(status_code=400, detail="Inactive user")

        # 4. Generate Tokens
        access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # 5. Store Refresh Token
        await self.repository.store_refresh_token(
            user.id, 
            refresh_token, 
            datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )

        return TokenResponse(access_token=access_token, refresh_token=refresh_token)

    async def rotate_tokens(self, refresh_token: str) -> TokenResponse:
        # 1. Validate Token Structure
        try:
            payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # 2. Check DB (Is it blacklisted/revoked? Does it match?)
        # For now, we trust the JWT signature + user existence.
        # Ideally, we verify against the 'refresh_tokens' table here.
        
        # 3. Generate New Pair
        new_access_token = create_access_token(data={"sub": user_id})
        new_refresh_token = create_refresh_token(data={"sub": user_id})
        
        # 4. Update DB (Rotate)
        await self.repository.store_refresh_token(
            uuid.UUID(user_id), 
            new_refresh_token, 
            datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token)

    async def logout_user(self, user_id: str):
        # In a real system, you might delete the refresh token from DB
        # or blacklist the access token in Redis.
        pass
    
    # --- PHASE 5 METHODS (Profiles) ---
    async def get_user_profile(self, user_id: str):
        return await self.repository.get_full_user_details(user_id)

    async def update_user_profile(self, user_id: str, update_data: ProfileUpdate):
        data = update_data.dict(exclude_unset=True)
        await self.repository.update_profile(user_id, data)
        
        await self.repository.log_action(
            performed_by=user_id,
            action="PROFILE_UPDATE",
            target_id=user_id,
            details=str(data)
        )
        
        return await self.get_user_profile(user_id)