from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from uuid import UUID  # We import UUID directly
from datetime import date

# 1. Input Schema (What the user sends to Register)
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Must be at least 8 chars")
    full_name: str
    phone_number: Optional[str] = None
    role: str = "patient" # Default to patient

    @validator("role")
    def validate_role(cls, v):
        if v not in ["patient", "doctor"]:
            raise ValueError("Role must be patient, doctor")
        return v

# 2. Input Schema (What the user sends to Login)
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 3. Output Schema (What we send back - NO PASSWORDS!)
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    role: str
    is_active: bool
    
    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy objects

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    # For Doctors only
    specialization: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None

class ProfileResponse(BaseModel):
    id: UUID  # <--- FIXED: Removed 'uuid.' prefix
    email: str
    full_name: str
    role: str
    is_active: bool
    # We will flatten profile details here in the service
    phone_number: Optional[str] = None
    specialization: Optional[str] = None
    
    class Config:
        from_attributes = True