import uuid
import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, DECIMAL, Date, Enum, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base

# Enum for Roles (Strict Typing)
class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PATIENT, nullable=False)
    
    # Security Features
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True) # For Google Authenticator
    
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False)

class Profile(Base):
    """Generic Profile for all users (Name, DOB, Gender)"""
    __tablename__ = "profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")

class DoctorProfile(Base):
    """Specific Data for Doctors"""
    __tablename__ = "doctor_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    
    specialization = Column(String, index=True, nullable=False) # Indexed for Search!
    experience_years = Column(Integer, default=0)
    consultation_fee = Column(DECIMAL(10, 2), default=0.0)
    
    is_verified_by_admin = Column(Boolean, default=False) # Compliance
    
    user = relationship("User", back_populates="doctor_profile")