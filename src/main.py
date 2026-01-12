from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- NEW IMPORT
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- NEW IMPORTS FOR RATE LIMITING ---
from fastapi_limiter import FastAPILimiter
from src.common.cache import cache

from src.modules.auth.router import router as auth_router
from src.modules.availability.router import router as availability_router
from src.modules.bookings.router import router as booking_router
from src.modules.payment.router import router as payment_router
from src.modules.bookings.jobs import cancel_stale_bookings
from src.modules.consultations.router import router as consultation_router
from src.modules.doctors.router import router as doctors_router
from src.modules.admin.router import router as admin_router
from src.common.idempotency import IdempotencyMiddleware

# 2. Setup Scheduler
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print("🚀 LIFESPAN STARTING: Initializing Scheduler...")
    
    # 1. Initialize Rate Limiter (NEW)
    print("🛡️ Initializing Rate Limiter...")
    await FastAPILimiter.init(cache.redis)
    
    # 2. Run the janitor every 60 seconds
    scheduler.add_job(cancel_stale_bookings, 'interval', seconds=60)
    scheduler.start()
    
    yield # The app runs here
    
    # --- SHUTDOWN ---
    print("🛑 SHUTDOWN: Stopping Scheduler...")
    scheduler.shutdown()

# 3. Create App with Lifespan
app = FastAPI(
    title="Amrutam Telemedicine API",
    description="Production-grade Backend for Telemedicine",
    version="1.0.0",
    lifespan=lifespan 
)

# --- NEW: CORS MIDDLEWARE (Security Phase) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"], # Frontend + Swagger
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(IdempotencyMiddleware)

# Include Routers
app.include_router(auth_router)
app.include_router(availability_router)
app.include_router(booking_router)
app.include_router(payment_router)
app.include_router(consultation_router)
app.include_router(doctors_router)
app.include_router(admin_router)

@app.get("/health")
def health_check():
    return {"status": "active", "service": "Amrutam API"}
  
@app.get("/")
def root():
    return {"message": "Welcome to Amrutam API. Go to /docs for Swagger UI"}