import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotificationNotFoundError
from app.core.logging import configure_logging
from app.database import engine, get_db
from app.schemas import (
    NotificationCreate,
    NotificationResponse,
)
from app.service import NotificationService

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


@app.post(
    "/notification",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    payload: NotificationCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    logger.info(
        "Notification creation requested",
        extra={"channel": payload.channel},
    )

    service = NotificationService(session)

    notification = await service.create_notification(payload)

    logger.info(
        "Notification created successfully",
        extra={"notification_id": notification.id},
    )

    return notification


@app.get(
    "/notification/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification(
    notification_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    logger.info(
        "Notification retrieval requested",
        extra={"notification_id": notification_id},
    )

    service = NotificationService(session)

    try:
        notification = await service.get_notification(
            notification_id=notification_id,
        )

        logger.info(
            "Notification retrieved successfully",
            extra={"notification_id": notification_id},
        )

        return notification

    except NotificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        ) from None


@app.get("/notification", response_model=list[NotificationResponse])
async def list_notifications(
    session: Annotated[AsyncSession, Depends(get_db)],
    recipient: Annotated[str, Query(min_length=1, max_length=90)],
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    logger.info(
        "Notification list requested",
        extra={
            "recipient": recipient,
            "limit": limit,
            "offset": offset,
        },
    )

    service = NotificationService(session)

    notifications = await service.list_notifications(
        recipient=recipient,
        limit=limit,
        offset=offset,
    )

    logger.info(
        "Notification list retrieved",
        extra={"result_count": len(notifications)},
    )

    return notifications


@app.patch("/notification/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = NotificationService(session)

    try:
        notification = await service.mark_as_read(
            notification_id=notification_id,
        )

        logger.info(
            "Notification marked as read",
            extra={"notification_id": notification_id},
        )

        return notification

    except NotificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        ) from None
