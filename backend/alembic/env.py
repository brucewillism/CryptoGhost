"""CryptoGhost - Alembic migrations."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from backend.shared.config import get_settings
from backend.shared.database import Base
from backend.shared import models, models_intelligence, models_quant, models_investment, models_v5, models_v6  # noqa: F401

config = context.config
get_settings.cache_clear()
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url_sync.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from urllib.parse import unquote, urlparse

    from sqlalchemy import create_engine
    from sqlalchemy.engine.url import URL

    parsed = urlparse(settings.database_url_sync)
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=parsed.username,
        password=unquote(parsed.password or ""),
        host=parsed.hostname or "127.0.0.1",
        port=parsed.port or 5432,
        database=parsed.path.lstrip("/"),
    )
    connectable = create_engine(db_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
