from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

# Internal Imports
from src.core.database import get_db
from src.common.config import settings
from src.modules.auth.repository import AuthRepository
from src.modules.consultations.service import ConsultationService

router = APIRouter(prefix="/consultations", tags=["Consultations"])

# --- 1. USE HTTP BEARER (Simple "Paste Token" Box) ---
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), 
    db: AsyncSession = Depends(get_db)
):
    token = credentials.credentials  # Extract token directly
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decode the Token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Check if User Exists
    repo = AuthRepository(db)
    user = await repo.get_full_user_details(user_id) 
    if user is None:
        raise credentials_exception
    
    return user

# --- 2. THE SCHEMA ---
class PrescriptionCreate(BaseModel):
    booking_id: str
    diagnosis: str
    medications: str

# --- 3. THE ENDPOINTS ---
@router.post("/prescriptions")
async def create_prescription(
    data: PrescriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = ConsultationService(db)
    # Handle different return types from repo (dict or object)
    user_id = str(current_user["id"]) if isinstance(current_user, dict) else str(current_user.id)

    return await service.create_prescription(
        user_id, 
        data.booking_id, 
        data.diagnosis, 
        data.medications
    )

@router.get("/prescriptions/{booking_id}")
async def get_prescription(
    booking_id: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = ConsultationService(db)
    user_id = str(current_user["id"]) if isinstance(current_user, dict) else str(current_user.id)
    
    return await service.get_prescription(user_id, booking_id)