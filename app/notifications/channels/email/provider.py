from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


class EmailProvider:
    async def send_email(
        self,
        recipient: str,
        subject: str,
        body: str,
    ) -> None:
        message = EmailMessage()

        message["From"] = settings.mail_from
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(body)

        await aiosmtplib.send(
            message,
            hostname=settings.mail_server,
            port=settings.mail_port,
            username=settings.mail_username,
            password=settings.mail_password,
            start_tls=settings.mail_use_tls,
        )
