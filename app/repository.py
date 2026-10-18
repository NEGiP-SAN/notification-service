import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Notification, NotificationStatus
from app.schemas import NotificationCreate

# Use DEBUG for database operations in the repo layer,
# while successful creation/update events are logged
# at INFO level in the service layer
logger = logging.getLogger(__name__)


class NotificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        data: NotificationCreate,
    ) -> Notification:
        notification = Notification(
            recipient=data.recipient,
            channel=data.channel,
            title=data.title,
            body=data.body,
            metadata_json=data.metadata_json,
            status=NotificationStatus.PENDING,
        )

        self.session.add(notification)
        await self.session.flush()
        await self.session.refresh(notification)

        logger.debug(
            "Notification inserted and refreshed",
            extra={"notification_id": notification.id},
        )

        return notification

    async def get_by_id(
        self,
        notification_id: int,
    ) -> Notification | None:
        notification = await self.session.get(
            Notification,
            notification_id,
        )

        logger.debug(
            "Notification lookup completed",
            extra={
                "notification_id": notification_id,
                "found": notification is not None,
            },
        )

        return notification

    async def list_for_recipient(
        self,
        recipient: str,
        limit: int,
        offset: int,
    ) -> list[Notification]:
        result = await self.session.scalars(
            select(Notification)
            .where(Notification.recipient == recipient)
            .order_by(
                Notification.created_at.desc(),
                Notification.id.desc(),
            )
            .limit(limit)
            .offset(offset)
        )

        notifications = result.all()

        logger.debug(
            "Notification query completed",
            extra={
                "result_count": len(notifications),
                "limit": limit,
                "offset": offset,
            },
        )

        return list(notifications)

    async def mark_as_read(
        self,
        notification: Notification,
    ) -> Notification:
        if notification.read_at is None:
            notification.read_at = datetime.now(UTC)

            await self.session.flush()

            logger.debug(
                "Notification read_at timestamp updated",
                extra={"notification_id": notification.id},
            )
        else:
            logger.debug(
                "Notification was already marked as read",
                extra={"notification_id": notification.id},
            )

        return notification
