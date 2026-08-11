"""
Email delivery, behind a provider interface.

CareerAI needs transactional email in two places right now (password reset,
and the email-verification link that Module 1 stubs out for later
enforcement). Rather than call an SMTP/SES/SendGrid SDK directly from
auth_service, everything goes through EmailProvider so production email
can be wired in later by writing one class and flipping EMAIL_PROVIDER —
no call sites change. This mirrors the LLM provider abstraction planned
for app/ai in Module 3, for the same reason.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    @abstractmethod
    async def send(self, to: str, subject: str, body: str) -> None: ...


class ConsoleEmailProvider(EmailProvider):
    """Dev-mode provider: logs the email instead of sending it, so the
    password-reset flow is fully testable with zero external config."""

    async def send(self, to: str, subject: str, body: str) -> None:
        logger.info(
            "=== EMAIL (console provider — dev mode only) ===\nTo: %s\nSubject: %s\n\n%s\n"
            "=================================================",
            to,
            subject,
            body,
        )


def get_email_provider() -> EmailProvider:
    # Extend here as needed, e.g.:
    # if settings.EMAIL_PROVIDER == "smtp": return SMTPEmailProvider()
    return ConsoleEmailProvider()


class EmailService:
    def __init__(self, provider: EmailProvider | None = None):
        self.provider = provider or get_email_provider()

    async def send_password_reset_email(self, to: str, reset_link: str) -> None:
        await self.provider.send(
            to=to,
            subject="Reset your CareerAI password",
            body=f"Click the link below to reset your password. This link expires in 30 minutes.\n\n{reset_link}",
        )

    async def send_verification_email(self, to: str, verify_link: str) -> None:
        await self.provider.send(
            to=to,
            subject="Verify your CareerAI account",
            body=f"Click the link below to verify your email address.\n\n{verify_link}",
        )
