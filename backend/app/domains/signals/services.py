"""
Signal push service
"""

from typing import Any

from uuid import UUID
from sqlmodel import Session, select
from app.core.db import engine
from app.models import Signal

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

    def list_signals(
        self,
        symbol: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        """List signals with optional filtering from database"""
        with Session(engine) as session:
            statement = select(Signal)

            if symbol:
                statement = statement.where(Signal.symbol == symbol)

            total_statement = statement
            total = len(session.exec(total_statement).all())

            statement = statement.offset((page - 1) * size).limit(size)
            signals = session.exec(statement).all()

            signal_list = []
            for signal in signals:
                signal_list.append(
                    {
                        "id": str(signal.id),
                        "symbol": signal.symbol,
                        "action": signal.status,
                        "confidence": signal.signal_strength,
                        "strategy_name": signal.strategy_name,
                        "timestamp": signal.created_at.isoformat() + "Z",
                        "metadata": {
                            "message": signal.message,
                            "price": signal.price,
                            "quantity": signal.quantity,
                        },
                    }
                )

            return {"data": signal_list, "total": total, "page": page, "size": size}

    def get_signal(self, signal_id: str) -> dict[str, Any] | None:
        """Get specific signal by ID from database"""
        with Session(engine) as session:
            signal = session.get(Signal, UUID(signal_id))
            if not signal:
                return None

            return {
                "id": str(signal.id),
                "symbol": signal.symbol,
                "action": signal.status,
                "confidence": signal.signal_strength,
                "strategy_name": signal.strategy_name,
                "timestamp": signal.created_at.isoformat() + "Z",
                "metadata": {
                    "message": signal.message,
                    "price": signal.price,
                    "quantity": signal.quantity,
                },
            }

    def create_signal(self, signal_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new signal in database"""
        with Session(engine) as session:
            # 验证策略名称必须提供
            strategy_name = signal_data.get("strategy_name")
            if not strategy_name:
                raise ValueError("strategy_name is required")
            
            # 验证策略是否在代码注册表中
            from app.domains.strategies.services import StrategyService
            strategy_service = StrategyService()
            registered_strategies = strategy_service.list_strategies()
            if strategy_name not in registered_strategies:
                raise ValueError(
                    f"Strategy '{strategy_name}' not found in registered strategies. "
                    f"Available strategies: {', '.join(registered_strategies)}"
                )

            signal = Signal(
                strategy_name=strategy_name,
                symbol=signal_data["symbol"],
                signal_strength=signal_data["confidence"],
                status=signal_data["action"],
                message=signal_data.get("metadata", {}).get("message"),
                price=signal_data.get("metadata", {}).get("price"),
                quantity=signal_data.get("metadata", {}).get("quantity"),
                created_by=UUID(signal_data["created_by"]),
            )

            session.add(signal)
            session.commit()
            session.refresh(signal)

            logger.info(f"Created signal in database: {signal.id}")

            return {
                "id": str(signal.id),
                "symbol": signal.symbol,
                "action": signal.status,
                "confidence": signal.signal_strength,
                "strategy_name": signal.strategy_name,
                "timestamp": signal.created_at.isoformat() + "Z",
                "metadata": {
                    "message": signal.message,
                    "price": signal.price,
                    "quantity": signal.quantity,
                },
            }


signal_push_service = SignalPushService()
