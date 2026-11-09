import logging

from app.notifications.channels.email.provider import EmailProvider
from app.notifications.models import Notification

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self, provider: EmailProvider | None = None):
        self.provider = provider or EmailProvider()

    async def send(self, notification: Notification) -> None:
        await self.provider.send_email(
            recipient=notification.recipient,
            subject=notification.title,
            body=notification.body,
        )

        logger.info(
            "Email sent successfully",
            extra={"notification_id": notification.id},
        )
