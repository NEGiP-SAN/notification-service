from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotificationNotFoundError
from app.database import engine, get_db
from app.schemas import (
    NotificationCreate,
    NotificationResponse,
)
from app.service import NotificationService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # startup
    yield
    # shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)


# tells you the application process is responding
@app.get("/health")
def health():
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not available",
        ) from err

    return {
        "status": "ready",
        "database": "connected",
    }


@app.post("/notification", response_model=NotificationResponse)
async def create_notification(
    payload: NotificationCreate,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = NotificationService(session)

    return await service.create_notification(payload)


@app.get("/notification", response_model=list[NotificationResponse])
async def list_notifications(
    session: Annotated[AsyncSession, Depends(get_db)],
    recipient: Annotated[str, Query(min_length=1, max_length=90)],
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    service = NotificationService(session)

    notifications = await service.list_notifications(
        recipient=recipient,
        limit=limit,
        offset=offset,
    )

    return notifications


@app.get(
    "/notification/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification(
    notification_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = NotificationService(session)
    try:
        notification = await service.get_notification(
            notification_id=notification_id,
        )
        return notification

    except NotificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )


@app.patch("/notification/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    session: Annotated[AsyncSession, Depends(get_db)],
):
    service = NotificationService(session)

    try:
        return await service.mark_as_read(
            notification_id=notification_id,
        )

    except NotificationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
