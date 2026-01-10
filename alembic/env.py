import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

# Import Config and Models
from src.common.config import settings
from src.core.database import Base

# Import ALL Models
from src.modules.auth.models import User, Profile, DoctorProfile
from src.modules.availability.models import AvailabilitySlot
from src.modules.bookings.models import Booking
from src.modules.clinical.models import Prescription
from src.modules.payment.models import Payment
from src.modules.audit.models import AuditLog
from src.modules.analytics.models import DailyMetric

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set DB URL
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Run migrations in 'online' mode (Async version)."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())