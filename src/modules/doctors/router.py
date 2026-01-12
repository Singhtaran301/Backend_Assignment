from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_db
from src.modules.doctors.service import DoctorService

router = APIRouter(prefix="/doctors", tags=["Public Search"])

@router.get("/search")
async def search_doctors(
    q: str = Query(None, description="Search by Doctor Name"),
    spec: str = Query(None, description="Filter by Specialization"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, le=50, description="Items per page (Max 50)"),
    db: AsyncSession = Depends(get_db)
):
    service = DoctorService(db)
    return await service.search_doctors(q, spec, page, limit)