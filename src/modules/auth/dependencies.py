from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # <--- CHANGED
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.auth.repository import AuthRepository
from src.common.config import settings
from src.modules.auth.models import User

# Changed from OAuth2PasswordBearer to HTTPBearer for simpler "Paste Token" UI
security = HTTPBearer() 

async def get_current_user(
    token_obj: HTTPAuthorizationCredentials = Depends(security), # <--- CHANGED
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Extract the token string from the security object
    token = token_obj.credentials 

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    repository = AuthRepository(db)
    user = await repository.get_full_user_details(user_id)
    
    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user

def require_role(required_role: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if not current_user.is_active:
             raise HTTPException(status_code=400, detail="Inactive user")

        # Handle Enum vs String comparison
        user_role_value = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
        
        if user_role_value != required_role:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {required_role} required"
            )
        return current_user
    return role_checker