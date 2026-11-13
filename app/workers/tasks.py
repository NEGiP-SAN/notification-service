import asyncio
import logging
import sys

from app.notifications.models import NotificationStatus
from app.notifications.service import NotificationService
from app.workers.celery_app import celery_app
from app.workers.database import CelerySessionLocal

logger = logging.getLogger(__name__)

# Windows-specific asyncio configuration
if sys.platform == "win32":
    asyncio.set_event_loop_policy(
        asyncio.WindowsSelectorEventLoopPolicy(),
    )


async def process_notification(notification_id: int):
    async with CelerySessionLocal() as session:
        service = NotificationService(session)

        # Fetch notification
        notification = await service.get_notification(
            notification_id=notification_id,
        )

        # Prevent duplicate processing of notifications
        if notification.status == NotificationStatus.SENT:
            logger.info(
                "Notification %s already sent. Skipping.",
                notification_id,
            )

            return

        # Mark notification as processing
        notification.status = NotificationStatus.PROCESSING

        await session.commit()

        try:
            # Dispatch through the appropriate channel
            await service.dispatch(notification)

        except Exception as exc:
            notification.status = NotificationStatus.FAILED
            notification.error_message = str(exc)

            # Persist failure before Celery retries
            await session.commit()

            logger.exception(
                "Notification %s delivery failed",
                notification_id,
            )

            raise

        else:
            # Delivery succeeded
            notification.status = NotificationStatus.SENT
            notification.error_message = None

            await session.commit()

            logger.info(
                "Notification %s sent successfully",
                notification_id,
            )


@celery_app.task(
    name="send_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def send_notification_task(self, notification_id: int):
    try:
        asyncio.run(
            process_notification(notification_id),
        )

    except Exception as exc:
        logger.warning(
            "Retrying notification %s. Attempt %s",
            notification_id,
            self.request.retries + 1,
        )

        raise self.retry(
            exc=exc,
            # An explicit countdown overrides
            # the task's "default_retry_delay"
            countdown=60,
        )
