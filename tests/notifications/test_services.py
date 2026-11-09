from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotificationNotFoundError
from app.notifications.models import NotificationChannel
from app.notifications.service import NotificationService
from tests.helpers import (
    create_notification,
    make_notification_data,
)

# =====================================================
#  Create Notification Service Test
# =====================================================


@pytest.mark.anyio
async def test_create_notification_success(
    db_session,
):
    service = NotificationService(db_session)

    data = make_notification_data(
        recipient="test-user",
        channel=NotificationChannel.EMAIL,
        title="Test notification",
        body="Test body",
    )

    notification = await service.create_notification(data)

    assert notification.id is not None
    assert notification.recipient == "test-user"
    assert notification.title == "Test notification"
    assert notification.body == "Test body"


@pytest.mark.anyio
async def test_create_notification_rolls_back_on_failure(
    monkeypatch,
):
    # spec restricts a mock to attributes
    # and methods available on a particular class
    session = AsyncMock(spec=AsyncSession)

    service = NotificationService(session)

    mock_send = AsyncMock()
    monkeypatch.setattr(service.email_service, "send", mock_send)

    # side_effect tells a mock what to do when it is called
    # It can raise an exception, return different values,
    # or execute a function
    service.repo.create = AsyncMock(
        side_effect=RuntimeError("Database error"),
    )

    data = make_notification_data()

    with pytest.raises(RuntimeError, match="Database error"):
        await service.create_notification(data)

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()

    mock_send.assert_not_awaited()


@pytest.mark.anyio
async def test_create_notification_dispatches_email(
    db_session,
    monkeypatch,
):
    service = NotificationService(db_session)

    mock_send = AsyncMock()

    monkeypatch.setattr(
        service.email_service,
        "send",
        mock_send,
    )

    data = make_notification_data(
        recipient="test@example.com",
        channel=NotificationChannel.EMAIL,
        title="Test notification",
        body="Test body",
    )

    notification = await service.create_notification(data)

    mock_send.assert_awaited_once_with(notification)


# =====================================================
#  Get Notification by ID Service Tests
# =====================================================


@pytest.mark.anyio
async def test_get_notification_success(
    db_session,
):
    service = NotificationService(db_session)

    data = await create_notification(
        session=db_session,
        recipient="test-user",
        title="Welcome!",
    )

    notification = await service.get_notification(
        notification_id=data.id,
    )

    assert notification.id == data.id
    assert notification.recipient == "test-user"
    assert notification.title == "Welcome!"


@pytest.mark.anyio
async def test_get_notification_failure(db_session):
    service = NotificationService(db_session)

    with pytest.raises(NotificationNotFoundError):
        await service.get_notification(3)


# =====================================================
#  List Notification of a User Service Tests
# =====================================================


@pytest.mark.anyio
async def test_list_notifications_success(db_session):
    service = NotificationService(db_session)

    notification1 = await create_notification(
        db_session,
        recipient="test-user",
        title="Notification1",
        body="Test Notification1",
    )
    notification2 = await create_notification(
        db_session,
        recipient="test-user",
        title="Notification2",
        body="Test Notification2",
    )
    notification3 = await create_notification(
        db_session,
        recipient="test-user",
        title="Notification3",
        body="Test Notification3",
    )

    notifications = await service.list_notifications(
        recipient="test-user",
        limit=10,
        offset=0,
    )

    assert len(notifications) == 3
    assert all(
        notification in notifications
        for notification in (
            notification1,
            notification2,
            notification3,
        )
    )


@pytest.mark.anyio
async def test_list_notifications_failure(db_session):
    service = NotificationService(db_session)

    notifications = await service.list_notifications(
        recipient="random-user",
        limit=10,
        offset=0,
    )

    assert notifications == []


# =====================================================
#  Mark Notification as Read Service Tests
# =====================================================


@pytest.mark.anyio
async def test_mark_as_read_success(
    db_session,
):
    service = NotificationService(db_session)

    notification = await create_notification(
        db_session,
        recipient="test-user",
        title="Test Title",
    )

    assert notification.read_at is None

    updated_notification = await service.mark_as_read(
        notification_id=notification.id,
    )

    assert updated_notification.id == notification.id
    assert updated_notification.read_at is not None
    assert updated_notification.read_at.tzinfo is not None


@pytest.mark.anyio
async def test_mark_as_read_notification_not_found(
    db_session,
):
    service = NotificationService(db_session)

    with pytest.raises(NotificationNotFoundError):
        await service.mark_as_read(notification_id=3)


@pytest.mark.anyio
async def test_mark_as_read_rolls_back_on_failure(
    db_session,
):
    session = AsyncMock(spec=AsyncSession)
    service = NotificationService(session)

    service.repo.mark_as_read = AsyncMock(
        side_effect=RuntimeError("Database error"),
    )

    notification = await create_notification(db_session)

    # make get_by_id() return the notification
    # so the service does not raise NotificationNotFoundError
    service.repo.get_by_id = AsyncMock(
        return_value=notification,
    )

    with pytest.raises(RuntimeError, match="Database error"):
        await service.mark_as_read(notification.id)

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
