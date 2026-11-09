from unittest.mock import AsyncMock

import pytest
from aiosmtplib import SMTPException

from app.notifications.channels.email.service import EmailService
from app.notifications.models import Notification


@pytest.mark.anyio
async def test_send_email_success(
    db_session,
    monkeypatch,
):
    service = EmailService(db_session)

    mock_send = AsyncMock()

    monkeypatch.setattr(
        service.provider,
        "send_email",
        mock_send,
    )

    notification = Notification(
        recipient="test@example.com",
        title="Test title",
        body="Test body",
    )

    await service.send(notification)

    mock_send.assert_awaited_once_with(
        recipient="test@example.com",
        subject="Test title",
        body="Test body",
    )


@pytest.mark.anyio
async def test_send_email_failure(
    db_session,
    monkeypatch,
):
    service = EmailService(db_session)

    mock_send = AsyncMock(
        side_effect=SMTPException("SMTP error"),
    )

    monkeypatch.setattr(
        service.provider,
        "send_email",
        mock_send,
    )

    notification = Notification(
        recipient="test@example.com",
        title="Test title",
        body="Test body",
    )

    with pytest.raises(SMTPException, match="SMTP error"):
        await service.send(notification)
