from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
# --- FIXED IMPORTS BELOW ---
from src.modules.auth.schemas import (
    UserCreate, 
    UserResponse, 
    UserLogin, 
    TokenResponse, 
    ProfileUpdate,   # <--- Added
    ProfileResponse  # <--- Added
)
from src.modules.auth.service import AuthService
from src.modules.auth.repository import AuthRepository
from src.modules.auth.dependencies import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["Authentication"])

def get_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    repository = AuthRepository(db)
    return AuthService(repository)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, service: AuthService = Depends(get_service)):
    return await service.register_user(user_data)

@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, service: AuthService = Depends(get_service)):
    return await service.login_user(login_data)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, service: AuthService = Depends(get_service)):
    return await service.rotate_tokens(refresh_token)

@router.post("/logout")
async def logout(
    current_user = Depends(get_current_user),
    service: AuthService = Depends(get_service)
):
    await service.logout_user(current_user.id)
    return {"message": "Logged out successfully"}

@router.get("/test/patient", dependencies=[Depends(require_role("patient"))])
def patient_only(): return {"msg": "Hello Patient!"}

@router.get("/test/doctor", dependencies=[Depends(require_role("doctor"))])
def doctor_only(): return {"msg": "Hello Doctor!"}

@router.get("/test/admin", dependencies=[Depends(require_role("admin"))])
def admin_only(): return {"msg": "Hello Admin!"}

@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user = Depends(get_current_user),
    service: AuthService = Depends(get_service)
):
    """Get current user's full profile."""
    user = await service.get_user_profile(current_user.id)
    
    return {
        "id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "full_name": user.profile.full_name if user.profile else "",
        "phone_number": user.profile.phone_number if user.profile else None,
        "specialization": user.doctor_profile.specialization if user.doctor_profile else None
    }

@router.put("/profile", response_model=ProfileResponse)
async def update_profile(
    data: ProfileUpdate,
    current_user = Depends(get_current_user),
    service: AuthService = Depends(get_service)
):
    """Update profile details."""
    updated_user = await service.update_user_profile(current_user.id, data)
    
    return {
        "id": updated_user.id,
        "email": updated_user.email,
        "role": updated_user.role,
        "is_active": updated_user.is_active,
        "full_name": updated_user.profile.full_name if updated_user.profile else "",
        "phone_number": updated_user.profile.phone_number if updated_user.profile else None,
        "specialization": updated_user.doctor_profile.specialization if updated_user.doctor_profile else None
    }