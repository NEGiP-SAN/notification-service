import logging
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest
from celery.exceptions import Retry

from app.notifications.channels.email.service import EmailService
from app.notifications.models import (
    NotificationChannel,
    NotificationStatus,
)
from app.workers import tasks
from tests.helpers import create_notification


# =========================================
# Fixtures
# =========================================
@pytest.fixture
def use_test_session(db_session, monkeypatch):
    """Make the worker use the test database session."""

    @asynccontextmanager
    async def test_session_context():
        yield db_session

    monkeypatch.setattr(
        tasks,
        "CelerySessionLocal",
        test_session_context,
    )


# =========================================
# process_notification() tests
# =========================================


@pytest.mark.anyio
async def test_process_notification_success(
    db_session,
    use_test_session,
    monkeypatch,
):
    notification = await create_notification(
        db_session,
        recipient="test@example.com",
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
    )

    send_mock = AsyncMock()

    monkeypatch.setattr(EmailService, "send", send_mock)

    await tasks.process_notification(notification.id)

    await db_session.refresh(notification)

    assert notification.status == NotificationStatus.SENT
    assert notification.error_message is None

    send_mock.assert_awaited_once_with(notification)


@pytest.mark.anyio
async def test_process_notification_already_sent(
    db_session,
    use_test_session,
    monkeypatch,
):
    notification = await create_notification(
        db_session,
        recipient="test@example.com",
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.SENT,
    )

    send_mock = AsyncMock()

    monkeypatch.setattr(EmailService, "send", send_mock)

    await tasks.process_notification(notification.id)

    await db_session.refresh(notification)

    assert notification.status == NotificationStatus.SENT

    send_mock.assert_not_awaited()


@pytest.mark.anyio
async def test_process_notification_failure(
    db_session,
    use_test_session,
    monkeypatch,
):
    notification = await create_notification(
        db_session,
        recipient="test@example.com",
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
    )

    send_mock = AsyncMock(
        side_effect=RuntimeError("SMTP connection failed"),
    )

    monkeypatch.setattr(EmailService, "send", send_mock)

    with pytest.raises(
        RuntimeError,
        match="SMTP connection failed",
    ):
        await tasks.process_notification(notification.id)

    await db_session.refresh(notification)

    assert notification.status == NotificationStatus.FAILED

    assert notification.error_message == "SMTP connection failed"

    send_mock.assert_awaited_once_with(notification)


@pytest.mark.anyio
async def test_process_notification_processing_status(
    db_session,
    use_test_session,
    monkeypatch,
):
    notification = await create_notification(
        db_session,
        recipient="test@example.com",
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.PENDING,
    )

    async def check_processing_status(notification):
        await db_session.refresh(notification)

        assert notification.status == NotificationStatus.PROCESSING

    send_mock = AsyncMock(
        side_effect=check_processing_status,
    )

    monkeypatch.setattr(EmailService, "send", send_mock)

    await tasks.process_notification(notification.id)

    await db_session.refresh(notification)

    assert notification.status == NotificationStatus.SENT


@pytest.mark.anyio
async def test_process_notification_clears_error_message(
    db_session,
    use_test_session,
    monkeypatch,
):
    notification = await create_notification(
        db_session,
        recipient="test@example.com",
        channel=NotificationChannel.EMAIL,
        status=NotificationStatus.FAILED,
        error_message="Delivery Failure",
    )

    send_mock = AsyncMock()

    monkeypatch.setattr(EmailService, "send", send_mock)

    assert notification.status == NotificationStatus.FAILED
    assert notification.error_message == "Delivery Failure"

    await tasks.process_notification(notification.id)

    await db_session.refresh(notification)

    assert notification.status == NotificationStatus.SENT
    assert notification.error_message is None

    send_mock.assert_awaited_once_with(notification)


# =========================================
# send_notification_task() tests
# =========================================


def test_send_notification_task_success(monkeypatch):
    run_mock = Mock()

    monkeypatch.setattr(tasks.asyncio, "run", run_mock)

    tasks.send_notification_task.run(1)

    run_mock.assert_called_once()

    # Close the coroutine created by process_notification
    # because asyncio.run was mocked
    coroutine = run_mock.call_args.args[0]
    coroutine.close()


def test_send_notification_task_retry(monkeypatch):
    def mock_run(coroutine):
        coroutine.close()
        raise RuntimeError("Processing failed")

    retry_mock = Mock(
        return_value=Retry("Retry requested"),
    )

    monkeypatch.setattr(tasks.asyncio, "run", mock_run)

    monkeypatch.setattr(
        tasks.send_notification_task,
        "retry",
        retry_mock,
    )

    with pytest.raises(Retry, match="Retry requested"):
        tasks.send_notification_task.run(1)

    retry_mock.assert_called_once()

    kwargs = retry_mock.call_args.kwargs

    assert kwargs["countdown"] == 60
    assert isinstance(kwargs["exc"], RuntimeError)
    assert str(kwargs["exc"]) == "Processing failed"


def test_send_notification_task_logs_retry(
    monkeypatch,
    caplog,
):
    def mock_run(coroutine):
        coroutine.close()
        raise RuntimeError("Delivery failed")

    retry_mock = Mock(
        return_value=Retry("Retry requested"),
    )

    monkeypatch.setattr(tasks.asyncio, "run", mock_run)

    monkeypatch.setattr(
        tasks.send_notification_task,
        "retry",
        retry_mock,
    )

    with caplog.at_level(logging.WARNING):
        with pytest.raises(Retry):
            tasks.send_notification_task.run(3)

    assert "Retrying notification 3" in caplog.text
    assert "Attempt 1" in caplog.text
