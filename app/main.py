import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import configure_logging
from app.db.database import engine, get_db
from app.notifications.router import router

configure_logging()


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("Notification service starting")

    yield

    logger.info("Notification service shutting down")

    await engine.dispose()

    logger.info("Database engine disposed")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.include_router(router)


# tells you the application process is responding
@app.get("/health")
def health():
    logger.debug("Liveness health check requested")

    return {
        "status": "ok",
        "service": settings.app_name,
    }


# checks whether the application can reach PostgreSQL
@app.get("/health/ready")
async def readiness(
    session: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        await session.execute(text("SELECT 1"))

    except SQLAlchemyError as err:
        logger.exception("Database readiness check failed")

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        ) from err

    logger.info("Database readiness check successful")

    return {
        "status": "ready",
        "database": "connected",
    }
