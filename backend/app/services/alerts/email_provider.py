"""Email abstraction — Resend-compatible by default, with a console
fallback for local dev/demo mode so nothing breaks without an API key."""
from abc import ABC, abstractmethod

from app.config import get_settings

settings = get_settings()


class EmailProvider(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str) -> bool:
        ...


class ResendEmailProvider(EmailProvider):
    def __init__(self):
        import resend
        resend.api_key = settings.resend_api_key
        self._resend = resend

    def send(self, to: str, subject: str, html_body: str) -> bool:
        try:
            self._resend.Emails.send({
                "from": settings.email_from,
                "to": [to],
                "subject": subject,
                "html": html_body,
            })
            return True
        except Exception:
            return False


class ConsoleEmailProvider(EmailProvider):
    """Local/dev/demo fallback — logs instead of sending."""
    def send(self, to: str, subject: str, html_body: str) -> bool:
        print(f"[console-email] to={to} subject={subject!r}\n{html_body}\n")
        return True


def get_email_provider() -> EmailProvider:
    if settings.email_provider == "resend" and settings.resend_api_key:
        return ResendEmailProvider()
    return ConsoleEmailProvider()
