from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.auth.dependencies import require_role
from src.modules.bookings.schemas import BookingCreate, BookingResponse
from src.modules.bookings.service import BookingService
from src.modules.bookings.repository import BookingRepository

router = APIRouter(prefix="/bookings", tags=["Bookings"])

def get_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    repo = BookingRepository(db)
    return BookingService(repo)

@router.post("/", response_model=BookingResponse)
async def create_booking(
    booking_data: BookingCreate,
    idempotency_key: str = Header(..., description="Unique key for this request"),
    current_user = Depends(require_role("patient")), # Only Patients book!
    service: BookingService = Depends(get_service)
):
    """
    Transactional Booking.
    Locks the slot -> Checks Availability -> Books it.
    """
    result = await service.book_slot(
        idempotency_key, 
        current_user.id, 
        booking_data.slot_id
    )
    
    # Handle the dictionary return from idempotency check vs object return
    if isinstance(result, dict):
        # Convert dict back to object for Pydantic response if needed, 
        # or we can rely on Pydantic to parse dicts too.
        # Ideally, we should fetch the booking object again, but for now:
        return result
        
    return result