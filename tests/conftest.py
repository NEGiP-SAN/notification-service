import asyncio
import os
import sys

# Set the test database URL before importing application settings
DATABASE_URL = "postgresql+psycopg://testuser:testpass@localhost/test_database"
os.environ["DATABASE_URL"] = DATABASE_URL

# Windows-specific asyncio configuration
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.database import Base, get_db
from app.main import app
from app.models import Notification  # noqa: F401

pytest_plugins = ["anyio"]


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )

    try:
        yield engine
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
async def setup_database(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield
    finally:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(
    test_engine,
    setup_database,
) -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.connect() as conn:
        trans = await conn.begin()

        test_session_factory = async_sessionmaker(
            bind=conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async with test_session_factory() as session:
            yield session

        # Check whether the transaction is still active
        # before attempting to roll it back
        if trans.is_active:
            await trans.rollback()


@pytest.fixture
async def client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient]:
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test.com",
    ) as async_client:
        yield async_client

    app.dependency_overrides.clear()
