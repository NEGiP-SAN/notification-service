import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Notification,
    NotificationChannel,
    NotificationStatus,
)


@pytest.mark.anyio
async def test_notification_defaults(db_session):
    notification = Notification(
        recipient="test@user.com",
        title="Test Notification",
        body="This is a test message",
    )

    db_session.add(notification)

    await db_session.flush()
    await db_session.refresh(notification)

    assert notification.id is not None
    assert notification.channel == NotificationChannel.IN_APP
    assert notification.status == NotificationStatus.PENDING
    assert notification.created_at is not None


@pytest.mark.anyio
async def test_notification_requires_recipient(db_session):
    notification = Notification(
        recipient=None,
        title="Test Notification",
        body="This is a test message",
    )

    db_session.add(notification)

    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()

    error_msg = 'null value in column "recipient"'
    assert error_msg in str(exc.value)


@pytest.mark.anyio
async def test_notification_requires_title(db_session):
    notification = Notification(
        recipient="test@user.com",
        title=None,
        body="This is a test message",
    )

    db_session.add(notification)

    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()

    error_msg = 'null value in column "title"'
    assert error_msg in str(exc.value)


@pytest.mark.anyio
async def test_notification_requires_body(db_session):
    notification = Notification(
        recipient="test@user.com",
        title="Test Notification",
        body=None,
    )

    db_session.add(notification)

    with pytest.raises(IntegrityError) as exc:
        await db_session.flush()

    error_msg = 'null value in column "body"'
    assert error_msg in str(exc.value)


@pytest.mark.anyio
async def test_notification_enum_persistence(db_session):
    notification = Notification(
        recipient="test@user.com",
        channel=NotificationChannel.EMAIL,
        title="Test Notification",
        body="This is a test message",
        status=NotificationStatus.SENT,
    )

    db_session.add(notification)

    await db_session.flush()
    await db_session.refresh(notification)

    saved_notification = await db_session.get(
        Notification,
        notification.id,
    )

    assert saved_notification is not None
    assert saved_notification.channel == NotificationChannel.EMAIL
    assert saved_notification.status == NotificationStatus.SENT


@pytest.mark.anyio
async def test_notification_nullable_fields(db_session):
    notification = Notification(
        recipient="test@user.com",
        title="Test Notification",
        body="This is a test message",
    )

    db_session.add(notification)

    await db_session.flush()
    await db_session.refresh(notification)

    saved_notification = await db_session.get(
        Notification,
        notification.id,
    )

    assert saved_notification is not None
    assert saved_notification.metadata_json is None
    assert saved_notification.read_at is None
