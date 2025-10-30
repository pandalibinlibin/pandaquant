"""
Signal push service
"""

from typing import Any

from app.core.logging import get_logger
from app.domains.signals.base import PushChannel, PushResult
from app.domains.signals.email import EmailChannel
from app.domains.signals.wechat import WeChatWorkChannel

logger = get_logger(__name__)


class SignalPushService:
    """
    Signal push service for managing multiple push channels

    Supports:
    - WeChat Work push
    - Email push
    - Multiple channels simultaneously
    """

    def __init__(self):
        self.channels: dict[str, PushChannel] = {}
        self._init_channels()

    def _init_channels(self) -> None:
        """Initialize all available push channels"""

        try:
            wechat_channel = WeChatWorkChannel()
            self.channels["wechat"] = wechat_channel
            logger.info("WeChat Work channel initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize WeChat Work channel: {str(e)}")

        try:
            email_channel = EmailChannel()
            self.channels["email"] = email_channel
            logger.info("Email channel initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize Email channel: {str(e)}")

    async def push_signal(
        self,
        signal_data: dict[str, Any],
        channels: list[str] | None = None,
        recipients: list[str] | None = None,
    ) -> dict[str, PushResult]:
        """
        Push signal to specified channels

        Args:
            signal_data: Signal information to push
            channels: List of channel names to use (default: all enabled channels)
            recipients: Optional list of specific recipients

        Returns:
            Dict mapping channel names to push results
        """

        if channels is None:
            channels = [
                name for name, channel in self.channels.items() if channel.enabled
            ]

        results = {}

        for channel_name in channels:
            if channel_name not in self.channels:
                logger.warning(f"Channel {channel_name} not found, skipping")
                results[channel_name] = PushResult(
                    success=False,
                    error=f"Channel {channel_name} not found",
                )
                continue

            channel = self.channels[channel_name]

            try:
                result = await channel.push(signal_data, recipients)
                results[channel_name] = result

                if result.success:
                    logger.info(
                        f"Signal pushed successfully to {channel_name}: {result.message}"
                    )
                else:
                    logger.error(
                        f"Failed to push signal to {channel_name}: {result.error}"
                    )

            except Exception as e:
                logger.error(f"Error pushing signal to {channel_name}: {str(e)}")
                results[channel_name] = PushResult(
                    success=False,
                    error=str(e),
                )

        return results

    async def check_health(self) -> dict[str, bool]:
        """
        Check health status of all channels

        Returns:
            Dict mapping channel names to health status
        """

        health_status = {}

        for name, channel in self.channels.items():
            try:
                is_healthy = await channel.health_check()
                health_status[name] = is_healthy

                if is_healthy:
                    logger.info(f"Channel {name} is healthy")
                else:
                    logger.warning(f"Channel {name} health check failed")

            except Exception as e:
                logger.error(f"Error checking health of channel {name}: {str(e)}")
                health_status[name] = False

        return health_status


signal_push_service = SignalPushService()
