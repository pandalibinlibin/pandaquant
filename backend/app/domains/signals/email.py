"""
Email push channel implementation
"""

from app.core.config import settings
from app.core.logging import get_logger
from app.domains.signals.base import ChannelType, PushChannel, PushResult
from app.utils import send_email

logger = get_logger(__name__)


class EmailChannel(PushChannel):
    """
    Email push channel for sending trading signals

    Uses existing email infrastructure from app.utils
    """

    def __init__(self):
        super().__init__(
            name="email",
            channel_type=ChannelType.EMAIL,
            enabled=True,
            max_retries=3,
        )

    async def push(
        self,
        signal_data: dict,
        recipients: list[str] | None = None,
    ) -> PushResult:
        """Push signal via email"""

        if not self.enabled:
            return PushResult(
                success=False,
                error="Channel is disabled",
            )

        if not recipients:
            recipients = [settings.FIRST_SUPERUSER]

        try:
            message = self._format_signal_message(signal_data)
            subject = f"Trading Signal: {signal_data.get("action", "UNKNOWN").upper()} {signal_data.get("symbol", "UNKNOWN")}"

            for recipient in recipients:
                send_email(
                    email_to=recipient,
                    subject=subject,
                    html_content=f"<pre>{message}</pre>",
                )

            logger.info(f"Signal pushed via email to {recipients}")

            return PushResult(
                success=True,
                message=f"Pushed via email to {len(recipients)} recipients",
            )
        except Exception as e:
            self._handle_error(e)
            return PushResult(success=False, error=str(e))

    async def health_check(self) -> bool:
        """Check if email service is configured"""

        try:
            if not settings.SMTP_HOST:
                return False

            return True

        except Exception as e:
            logger.error(f"Email health check failed: {str(e)}")
            return False
