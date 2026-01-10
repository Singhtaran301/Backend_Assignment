from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.auth.repository import AuthRepository
from src.common.config import settings
from src.modules.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    repository = AuthRepository(db)
    # We use get_full_user_details because we know it exists from Phase 5
    user = await repository.get_full_user_details(user_id) 
    
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user

def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        # 1. Check if active (using the correct variable name)
        if not current_user.is_active:
             raise HTTPException(status_code=400, detail="Inactive user")

        # 2. Check Role (Handle Enum vs String comparison)
        # We compare the value of the enum (e.g., "admin") with the required string
        user_role_value = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
        
        if user_role_value != required_role:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} required"
            )
        return current_user
    return role_checker