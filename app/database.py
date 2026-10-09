from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

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
        yield session


class Base(DeclarativeBase):
    pass
