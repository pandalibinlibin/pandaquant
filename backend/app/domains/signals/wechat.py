"""
WeChat Work push channel implementation
"""

import httpx

from app.core.config import settings
from app.core.logging import get_logger
from app.domains.signals.base import ChannelType, PushChannel, PushResult

logger = get_logger(__name__)


class WeChatWorkChannel(PushChannel):
    """
    WeChat work push channel for sending trading signals

    Requires configuration:
     - WECHAT_WORK_WEBHOOK_URL: Webhook URL from WeChat Work bot

    """

    def __init__(self, webhook_url: str | None = None):
        super().__init__(
            name="wechat_work",
            channel_type=ChannelType.WECHAT,
            enabled=True,
            max_retries=3,
        )

        self.wechat_webhook_url = webhook_url or getattr(
            settings, "WECHAT_WORK_WEBHOOK_URL", None
        )

    async def push(
        self,
        signal_data: dict,
        recipients: list[str] | None = None,
    ) -> PushResult:
        """Push signal to WeChat Work"""

        if not self.enabled:
            return PushResult(
                success=False,
                error="Channel is disabled",
            )

        if not self.wechat_webhook_url:
            return PushResult(
                success=False,
                error="WeChat Work webhook URL not configured",
            )

        try:
            message = self._format_signal_message(signal_data)

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": message,
                },
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(self.wechat_webhook_url, json=payload)
                response.raise_for_status()

            logger.info(f"Signal pushed to WeChat Work successfully")
            return PushResult(success=True, message="Pushed to WeChat Work")

        except Exception as e:
            self._handle_error(e)
            return PushResult(success=False, error=str(e))

    async def health_check(self) -> bool:
        """Check if WeChat Work webhook is accessible"""

        if not self.wechat_webhook_url:
            return False

        try:
            payload = {
                "msgtype": "text",
                "text": {"content": "Health check"},
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(self.wechat_webhook_url, json=payload)
                return response.status_code == 200

        except Exception as e:
            logger.error(f"WeChat Work health check failed: {str(e)}")
            return False
