from unittest.mock import AsyncMock

import pytest

from app.notifications.channels.email import provider
from app.notifications.channels.email.provider import EmailProvider


@pytest.mark.anyio
async def test_send_email(monkeypatch):
    mock_send = AsyncMock()
    monkeypatch.setattr(provider.aiosmtplib, "send", mock_send)

    email_provider = EmailProvider()

    await email_provider.send_email(
        recipient="test@example.com",
        subject="Test subject",
        body="Test body",
    )

    mock_send.assert_awaited_once()

    message = mock_send.await_args.args[0]

    assert message["To"] == "test@example.com"
    assert message["Subject"] == "Test subject"
    assert message.get_content() == "Test body\n"


@pytest.mark.anyio
async def test_send_email_failure(monkeypatch):
    mock_send = AsyncMock(
        side_effect=provider.aiosmtplib.SMTPException("SMTP error"),
    )
    monkeypatch.setattr(provider.aiosmtplib, "send", mock_send)

    email_provider = EmailProvider()

    with pytest.raises(provider.aiosmtplib.SMTPException):
        await email_provider.send_email(
            recipient="test@example.com",
            subject="Test subject",
            body="Test body",
        )
