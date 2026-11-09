from unittest.mock import AsyncMock

import pytest
from aiosmtplib import SMTPException

from app.notifications.channels.email.service import EmailService
from app.notifications.models import Notification


@pytest.mark.anyio
async def test_send_email_success():
    mock_provider = AsyncMock()

    service = EmailService(mock_provider)

    notification = Notification(
        recipient="test@example.com",
        title="Test title",
        body="Test body",
    )

    await service.send(notification)

    mock_provider.send_email.assert_awaited_once_with(
        recipient="test@example.com",
        subject="Test title",
        body="Test body",
    )


@pytest.mark.anyio
async def test_send_email_failure():
    mock_provider = AsyncMock()

    mock_provider.send_email.side_effect = SMTPException("SMTP error")

    service = EmailService(mock_provider)

    notification = Notification(
        recipient="test@example.com",
        title="Test title",
        body="Test body",
    )

    with pytest.raises(SMTPException, match="SMTP error"):
        await service.send(notification)

    mock_provider.send_email.assert_awaited_once_with(
        recipient="test@example.com",
        subject="Test title",
        body="Test body",
    )
