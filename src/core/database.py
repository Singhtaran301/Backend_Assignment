from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from src.common.config import settings

# 1. Create the Database Engine
# We use settings.DATABASE_URL which comes from your .env file
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"), # Log SQL queries in dev
    future=True,
    pool_pre_ping=True,
)

# 2. Create the Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)

# 3. The "Base" Class [THIS WAS MISSING]
# All your models (User, Booking, etc.) inherit from this.
Base = declarative_base()

# 4. The Dependency (for FastAPI)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()