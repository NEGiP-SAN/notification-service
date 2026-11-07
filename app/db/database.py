import logging

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)

logger.info("Initializing database engine")

engine = create_async_engine(
    settings.database_url,
    # Checks whether a pooled database connection is still alive before using it
    # If the connection is stale or disconnected, SQLAlchemy attempts to reconnect
    pool_pre_ping=True,
    # Log SQL statements
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        logger.debug("Database session opened")

        try:
            yield session

        except Exception:
            logger.exception("Database session encountered an exception")
            raise

        finally:
            logger.debug("Database session closed")


class Base(DeclarativeBase):
    pass
