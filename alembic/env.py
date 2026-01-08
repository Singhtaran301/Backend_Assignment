import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# [CRITICAL] Add the project root to python path so we can import 'src'
sys.path.append(os.getcwd())

# Import your Config and Models
from src.common.config import settings
from src.core.database import Base

# IMPORT ALL YOUR MODELS HERE (So Alembic detects them)
# If you miss one here, it won't be created in the DB!
from src.modules.auth.models import User, Profile, DoctorProfile
from src.modules.availability.models import AvailabilitySlot
from src.modules.bookings.models import Booking
from src.modules.clinical.models import Prescription
from src.modules.payment.models import Payment
from src.modules.audit.models import AuditLog
from src.modules.search import * # Optional if search has models

config = context.config

# Setup Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the Database URL from your .env (via config.py)
# This overrides whatever is in alembic.ini
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

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()