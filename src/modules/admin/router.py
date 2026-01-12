from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.admin.service import AdminService
# We reuse the auth logic to identify the user
from src.modules.consultations.router import get_current_user 

router = APIRouter(prefix="/admin", tags=["Admin & Analytics"])

# --- DEPENDENCY: STRICT ADMIN CHECK (FIXED) ---
def require_admin(current_user = Depends(get_current_user)):
    # 1. Safely extract the role
    role = getattr(current_user, "role", None)
    if role is None and isinstance(current_user, dict):
        role = current_user.get("role")
    
    # 2. Debugging: Print exactly what we got (Look at Docker Logs if this fails)
    print(f"🔍 ADMIN CHECK DEBUG -> User ID: {getattr(current_user, 'id', 'Unknown')}")
    print(f"🔍 ADMIN CHECK DEBUG -> Raw Role: {role} (Type: {type(role)})")

    # 3. Normalize the Role to a simple string
    role_str = ""
    if hasattr(role, "value"):
        # If it's an Enum (UserRole.ADMIN), extract the value "admin"
        role_str = str(role.value).lower()
    else:
        # If it's already a string, just lower it
        role_str = str(role).lower()

    print(f"🔍 ADMIN CHECK DEBUG -> Normalized Role: '{role_str}'")

    # 4. The Comparison
    # We accept 'admin' (standard) or 'userrole.admin' (just in case str() behaved weirdly)
    if role_str not in ["admin", "userrole.admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Admin privileges required. (Detected role: {role_str})"
        )
    
    return current_user

# --- ROUTES ---
@router.get("/analytics/consultations")
async def daily_consultations(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin) 
):
    service = AdminService(db)
    return await service.get_daily_consultations(days)

@router.get("/analytics/revenue")
async def revenue_summary(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    service = AdminService(db)
    return await service.get_revenue_summary()

@router.get("/analytics/doctors")
async def doctor_utilization(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(require_admin)
):
    service = AdminService(db)
    return await service.get_doctor_stats(limit)