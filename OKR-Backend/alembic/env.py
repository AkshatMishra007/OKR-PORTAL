import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Add project root directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, DATABASE_URL

# Import all models so metadata is complete
import app.users.models  # noqa
import app.organizations.models  # noqa
import app.rbac.models  # noqa
import app.batches.models  # noqa
import app.organization_members.models  # noqa
import app.my_okr.models  # noqa
import app.fogs_hurdles.models  # noqa
import app.weekly_update.models  # noqa
import app.tracker_entries.models  # noqa
import app.queries.models  # noqa
import app.query_activity.models  # noqa
import app.okr_logs.models  # noqa

# Alembic Config object
config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = DATABASE_URL
    connectable = engine_from_config(
        configuration,
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
