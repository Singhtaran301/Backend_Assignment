from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi_limiter import FastAPILimiter
from src.common.cache import cache

# --- NEW IMPORTS ---
from prometheus_fastapi_instrumentator import Instrumentator
from src.core.middleware import RequestIDMiddleware
# -------------------

from src.modules.auth.router import router as auth_router
from src.modules.availability.router import router as availability_router
from src.modules.bookings.router import router as booking_router
from src.modules.payment.router import router as payment_router
from src.modules.bookings.jobs import cancel_stale_bookings
from src.modules.consultations.router import router as consultation_router
from src.modules.doctors.router import router as doctors_router
from src.modules.admin.router import router as admin_router
from src.common.idempotency import IdempotencyMiddleware

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 LIFESPAN STARTING...")
    await FastAPILimiter.init(cache.redis)
    
    scheduler.add_job(cancel_stale_bookings, 'interval', seconds=60)
    scheduler.start()
    
    yield
    
    print("🛑 SHUTDOWN...")
    scheduler.shutdown()

app = FastAPI(
    title="Amrutam Telemedicine API",
    lifespan=lifespan
)

# --- 1. ADD METRICS (Prometheus) ---
# Exposes /metrics endpoint automatically
Instrumentator().instrument(app).expose(app)

# --- 2. ADD REQUEST ID MIDDLEWARE ---
# Must be added BEFORE other middleware to catch everything
app.add_middleware(RequestIDMiddleware)

# --- 3. EXISTING MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(IdempotencyMiddleware)

# Routers
app.include_router(auth_router)
app.include_router(availability_router)
app.include_router(booking_router)
app.include_router(payment_router)
app.include_router(consultation_router)
app.include_router(doctors_router)
app.include_router(admin_router)

@app.get("/health")
def health_check():
    return {"status": "active"}