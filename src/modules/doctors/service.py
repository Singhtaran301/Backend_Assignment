from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from src.modules.auth.models import User, DoctorProfile, Profile, UserRole
from src.common.cache import cache

class DoctorService:
    def __init__(self, db_session):
        self.db = db_session

    async def search_doctors(self, query: str = None, specialization: str = None, page: int = 1, limit: int = 10):
        # 1. CACHE CHECK (Fast Path)
        cache_key = f"doctors:search:{query}:{specialization}:{page}:{limit}"
        cached_result = await cache.get_cached_data(cache_key)
        if cached_result:
            return cached_result

        # 2. BUILD QUERY
        stmt = (
            select(User)
            .join(DoctorProfile, User.id == DoctorProfile.user_id)
            .join(Profile, User.id == Profile.user_id)
            .where(User.role == UserRole.DOCTOR)
            .where(User.is_active == True)
            .options(joinedload(User.doctor_profile), joinedload(User.profile))
        )

        # 3. APPLY FILTERS
        if query:
            stmt = stmt.where(Profile.full_name.ilike(f"%{query}%"))
        
        if specialization:
            stmt = stmt.where(DoctorProfile.specialization.ilike(f"%{specialization}%"))

        # 4. PAGINATION
        offset = (page - 1) * limit
        stmt = stmt.offset(offset).limit(limit)

        # 5. EXECUTE
        result = await self.db.execute(stmt)
        doctors = result.unique().scalars().all()

        # 6. FORMAT RESPONSE
        data = []
        for doc in doctors:
            name = doc.profile.full_name if doc.profile else "Unknown"
            spec = doc.doctor_profile.specialization if doc.doctor_profile else "General"
            exp = doc.doctor_profile.experience_years if doc.doctor_profile else 0
            
            # --- THE FIX: Convert Decimal to Float ---
            raw_fee = doc.doctor_profile.consultation_fee if doc.doctor_profile else 0.0
            fee = float(raw_fee) # <--- JSON can handle float, but not Decimal

            data.append({
                "id": str(doc.id),
                "name": name,
                "specialization": spec,
                "experience": exp,
                "consultation_fee": fee
            })
        
        response = {
            "data": data,
            "meta": {"page": page, "limit": limit, "count": len(data)}
        }

        # 7. SAVE TO CACHE (Now safe because Fee is a float)
        await cache.set_cached_data(cache_key, response)

        return response