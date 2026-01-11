from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from src.modules.auth.router import router as auth_router
from src.modules.availability.router import router as availability_router
from src.modules.bookings.router import router as booking_router
from src.modules.payment.router import router as payment_router
from src.modules.bookings.jobs import cancel_stale_bookings # <--- 1. Import the job

# 2. Setup Scheduler
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP ---
    print("🚀 LIFESPAN STARTING: Initializing Scheduler...")
    # Run the janitor every 60 seconds
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
    lifespan=lifespan # <--- CRITICAL: Connects the scheduler
)

# Include Routers
app.include_router(auth_router)
app.include_router(availability_router)
app.include_router(booking_router)
app.include_router(payment_router)

@app.get("/health")
def health_check():
    return {"status": "active", "service": "Amrutam API"}
  
@app.get("/")
def root():
    return {"message": "Welcome to Amrutam API. Go to /docs for Swagger UI"}