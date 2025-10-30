"""
Signal pushing channel abstract base class
"""

from abc import ABC, abstractmethod
from enum import Enum

from app.core.logging import get_logger

logger = get_logger(__name__)


class ChannelType(str, Enum):
    """Push channel types"""

    WECHAT = "wechat"
    EMAIL = "email"
    DINGTALK = "dingtalk"


class ChannelStatus(str, Enum):
    """Push channel status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


class PushResult:
    """Push result wrapper"""

    def __init__(
        self,
        success: bool,
        message: str = "",
        error: str | None = None,
    ):
        self.success = success
        self.message = message
        self.error = error

    def __repr__(self) -> str:
        return f"PushResult(success={self.success}, message={self.message})"


class PushChannel(ABC):
    """
    Abstract base class for signal push channels

    Each channel implementation should:
    1. Implement push() method to send signals
    2. Implement health_check() to verify channel availability
    3. Handle errors and retries
    """

    def __init__(
        self,
        name: str,
        channel_type: ChannelType,
        enabled: bool = True,
        max_retries: int = 3,
    ):
        self.name = name
        self.channel_type = channel_type
        self.enabled = enabled
        self.max_retries = max_retries
        self.status = ChannelStatus.ACTIVE
        self.error_count = 0

    @abstractmethod
    async def push(
        self,
        signal_data: dict,
        recipients: list[str] | None = None,
    ) -> PushResult:
        """
        Push signal to channel

        Args:
            signal_data: Signal information to push
            recipients: Optional list of specific recipients

        Returns:
            PushResult with success status and message
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if channel is healthy and available

        Returns:
            True if channel is available, False otherwise

        """
        pass

    def _format_signal_message(self, signal_data: dict) -> str:
        """
        Format signal data into human-readable message

        Args:
            signal_data: Signal information

        Returns:
            Formatted message string
        """

        action = signal_data.get("action", "UNKNOWN")
        symbol = signal_data.get("symbol", "UNKNOWN")
        target_price = signal_data.get("target_price", 0.0)
        strength = signal_data.get("strength", 0.0)
        strategy = signal_data.get("strategy", "UNKNOWN")
        timestamp = signal_data.get("timestamp", "")

        message = f"""
        📊 Trading Signal Alert

            Strategy: {strategy}
            Symbol: {symbol}
            Action: {action.upper()}
            Price:  {target_price:.2f}
            Strength: {strength:.2%}
            Time: {timestamp}

            Please review and act accordingly.""".strip()

        return message

    def _handle_error(self, error: Exception) -> None:
        """
        Handle push errors and update channel status

        Args:
            error: Exception that occurred
        """

        self.error_count += 1
        logger.error(
            f"Push error in channel {self.name}: {str(error)}, "
            f"error_count={self.error_count}"
        )
        if self.error_count >= self.max_retries:
            self.status = ChannelStatus.ERROR
            self.enabled = False
            logger.warning(
                f"Channel {self.name} disabled after {self.error_count} errors"
            )

    def reset_errors(self) -> None:
        """Reset error count and restore channel status"""

        self.error_count = 0
        self.status = ChannelStatus.ACTIVE
        self.enabled = True
        logger.info(f"Channel {self.name} errors reset, status restored to ACTIVE")
