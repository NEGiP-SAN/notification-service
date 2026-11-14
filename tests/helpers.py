from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.notifications.schemas import NotificationCreate


def make_notification_data(
    recipient: str = "test@user.com",
    channel: NotificationChannel = NotificationChannel.SMS,
    title: str = "Welcome Message",
    body: str = "Welcome to our application!",
    metadata_json: dict | None = None,
) -> NotificationCreate:

    return NotificationCreate(
        recipient=recipient,
        channel=channel,
        title=title,
        body=body,
        metadata_json=metadata_json,
    )


async def create_notification(
    session: AsyncSession,
    recipient: str = "test@user.com",
    channel: NotificationChannel = NotificationChannel.SMS,
    title: str = "Welcome Message",
    body: str = "Welcome to our application!",
    status: NotificationStatus = NotificationStatus.PENDING,
    error_message: str | None = None,
    metadata_json: dict | None = None,
    created_at: datetime = datetime.now(UTC),
    read_at: datetime | None = None,
) -> Notification:

    notification = Notification(
        recipient=recipient,
        channel=channel,
        title=title,
        body=body,
        status=status,
        error_message=error_message,
        metadata_json=metadata_json,
        created_at=created_at,
        read_at=read_at,
    )

    session.add(notification)

    await session.flush()
    await session.refresh(notification)

    return notification
