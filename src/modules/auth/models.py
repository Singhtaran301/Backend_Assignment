import uuid
import enum
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, DECIMAL, Date, Enum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.core.database import Base

# Enum for Roles
class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.PATIENT, nullable=False)
    
    # Security Features
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    mfa_secret = Column(String, nullable=True) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    profile = relationship("Profile", back_populates="user", uselist=False)
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False)
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    full_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String, nullable=True)

    user = relationship("User", back_populates="profile")

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    specialization = Column(String, index=True, nullable=False)
    experience_years = Column(Integer, default=0)
    consultation_fee = Column(DECIMAL(10, 2), default=0.0)
    is_verified_by_admin = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="doctor_profile")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    revoked = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="refresh_tokens")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String, nullable=False) 
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_id = Column(UUID(as_uuid=True), nullable=True) 
    details = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())