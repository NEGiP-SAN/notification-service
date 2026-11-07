import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotificationNotFoundError
from app.db.database import get_db
from app.notifications.schemas import (
    NotificationCreate,
    NotificationResponse,
)
from app.notifications.service import NotificationService

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


def get_notification_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> NotificationService:
    return NotificationService(session)


NotificationServiceDep = Annotated[
    NotificationService,
    Depends(get_notification_service),
]


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification(
    payload: NotificationCreate,
    service: NotificationServiceDep,
):
    logger.info(
        "Notification creation requested",
        extra={"channel": payload.channel},
    )

    notification = await service.create_notification(payload)

    logger.info(
        "Notification created successfully",
        extra={"notification_id": notification.id},
    )

    return notification


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
async def get_notification(
    notification_id: int,
    service: NotificationServiceDep,
):
    logger.info(
        "Notification retrieval requested",
        extra={"notification_id": notification_id},
    )

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


@router.get(
    "",
    response_model=list[NotificationResponse],
)
async def list_notifications(
    service: NotificationServiceDep,
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


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
async def mark_notification_as_read(
    notification_id: int,
    service: NotificationServiceDep,
):
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
