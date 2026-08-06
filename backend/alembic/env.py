from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.models.app.session import AppSession
from app.models.app.user import AppUser
from config import settings
from database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
APPLICATION_OWNED_TABLES = {"app_users", "app_sessions"}


def include_application_objects(
    object_,
    name: str | None,
    type_: str,
    reflected: bool,
    compare_to,
) -> bool:
    """Keep FreeRADIUS-owned tables outside Alembic autogeneration."""
    if type_ == "table":
        return name in APPLICATION_OWNED_TABLES

    table = getattr(object_, "table", None)
    table_name = getattr(table, "name", None)
    return table_name is None or table_name in APPLICATION_OWNED_TABLES


def run_migrations_offline() -> None:
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_object=include_application_objects,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_object=include_application_objects,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
