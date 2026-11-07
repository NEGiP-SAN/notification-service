import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotificationNotFoundError
from app.notifications.channels.email.service import EmailService
from app.notifications.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)
from app.notifications.repository import NotificationRepository
from app.notifications.schemas import NotificationCreate

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NotificationRepository(session)

        self.email_service = EmailService(session)
        # self.sms_service = SMSService()
        # self.push_service = PushService()
        # self.in_app_service = InAppService()

    async def dispatch(self, notification: Notification):
        if notification.channel == NotificationChannel.EMAIL:
            await self.email_service.send(notification)

    async def create_notification(
        self,
        data: NotificationCreate,
    ) -> Notification:
        try:
            notification = await self.repo.create(data=data)

            # Mark notification as processing
            notification.status = NotificationStatus.PROCESSING
            await self.session.commit()

            logger.debug(
                "Notification created and transaction committed",
                extra={
                    "notification_id": notification.id,
                    "channel": notification.channel,
                },
            )

            try:
                await self.dispatch(notification)

                notification.status = NotificationStatus.SENT
                notification.error_message = None

            except Exception as exc:
                notification.status = NotificationStatus.FAILED
                notification.error_message = str(exc)

                logger.exception(
                    "Notification delivery failed",
                    extra={
                        "notification_id": notification.id,
                        "channel": notification.channel,
                    },
                )

            await self.session.commit()

            return notification

        except Exception:
            logger.exception(
                "Notification operation failed; rolling back",
            )

            try:
                await self.session.rollback()
            except Exception:
                logger.exception(
                    "Rollback failed after notification creation failure",
                )

            raise

    async def get_notification(
        self,
        notification_id: int,
    ) -> Notification:
        notification = await self.repo.get_by_id(
            notification_id=notification_id,
        )

        if notification is None:
            logger.warning(
                "Notification lookup failed: not found",
                extra={"notification_id": notification_id},
            )
            raise NotificationNotFoundError

        logger.debug(
            "Notification retrieved from repository",
            extra={"notification_id": notification_id},
        )

        return notification

    async def list_notifications(
        self,
        recipient: str,
        limit: int,
        offset: int,
    ) -> list[Notification]:
        notifications = await self.repo.list_for_recipient(
            recipient=recipient,
            limit=limit,
            offset=offset,
        )

        logger.debug(
            "Notification list retrieved from repository",
            extra={"result_count": len(notifications)},
        )

        return notifications

    async def mark_as_read(
        self,
        notification_id: int,
    ) -> Notification:
        try:
            notification = await self.repo.get_by_id(
                notification_id,
            )

            if notification is None:
                logger.warning(
                    "Cannot mark notification as read: Not Found",
                    extra={"notification_id": notification_id},
                )
                raise NotificationNotFoundError

            updated = await self.repo.mark_as_read(
                notification=notification,
            )

            await self.session.commit()

            logger.debug(
                "Notification marked as read and transaction committed",
                extra={"notification_id": notification_id},
            )

            return updated

        except Exception:
            logger.exception(
                "Mark-as-read operation failed; rolling back",
                extra={"notification_id": notification_id},
            )

            try:
                await self.session.rollback()
            except Exception:
                logger.exception(
                    "Rollback failed during mark-as-read operation",
                    extra={"notification_id": notification_id},
                )

            raise
