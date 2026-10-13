from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotificationNotFoundError
from app.models import Notification
from app.repository import NotificationRepository
from app.schemas import NotificationCreate


class NotificationService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NotificationRepository(session)

    async def create_notification(
        self,
        data: NotificationCreate,
    ) -> Notification:
        try:
            notification = await self.repo.create(
                data=data,
            )

            await self.session.commit()
            return notification

        except Exception:
            await self.session.rollback()
            raise

    async def get_notification(
        self,
        notification_id: int,
    ) -> Notification:
        notification = await self.repo.get_by_id(
            notification_id=notification_id,
        )

        if notification is None:
            raise NotificationNotFoundError

        return notification

    async def list_notifications(
        self,
        recipient: str,
        limit: int,
        offset: int,
    ) -> list[Notification]:

        return await self.repo.list_for_recipient(
            recipient=recipient,
            limit=limit,
            offset=offset,
        )

    async def mark_as_read(
        self,
        notification_id: int,
    ) -> Notification:
        try:
            notification = await self.repo.get_by_id(
                notification_id,
            )

            if notification is None:
                raise NotificationNotFoundError

            updated = await self.repo.mark_as_read(
                notification=notification,
            )

            await self.session.commit()
            return updated

        except Exception:
            await self.session.rollback()
            raise
