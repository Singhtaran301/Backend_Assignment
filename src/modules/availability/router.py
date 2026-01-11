from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.auth.dependencies import get_current_user, require_role
from src.modules.availability.schemas import SlotCreate, SlotResponse
from src.modules.availability.service import AvailabilityService
from src.modules.availability.repository import AvailabilityRepository

router = APIRouter(prefix="/availability", tags=["Availability"])

def get_service(db: AsyncSession = Depends(get_db)) -> AvailabilityService:
    repo = AvailabilityRepository(db)
    return AvailabilityService(repo)

@router.post("/slots", response_model=SlotResponse)
async def create_slot(
    slot_data: SlotCreate,
    current_user = Depends(require_role("doctor")), # Only Doctors!
    service: AvailabilityService = Depends(get_service)
):
    """Doctor creates a time slot (e.g., 9:00 - 10:00)."""
    return await service.create_availability_slot(current_user.id, slot_data)

@router.get("/slots", response_model=List[SlotResponse])
async def get_my_slots(
    current_user = Depends(require_role("doctor")),
    service: AvailabilityService = Depends(get_service)
):
    """Doctor sees their own schedule."""
    return await service.list_slots(current_user.id)