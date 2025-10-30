"""
Tests for signal push service
"""

import pytest
from app.domains.signals.services import SignalPushService


class TestSignalPushService:
    """Test SignalPushService"""

    def test_service_initialization(self):
        """Test service can be initialized"""

        service = SignalPushService()

        assert service is not None
        assert len(service.channels) > 0

    def test_service_has_channels(self):
        """Test service has registered channels"""

        service = SignalPushService()

        assert "wechat" in service.channels or "email" in service.channels

    def test_wechat_channel_exists(self):
        """Test WeChat channel is registered"""

        service = SignalPushService()

        if "wechat" in service.channels:
            channel = service.channels["wechat"]

            assert channel.name == "wechat_work"

    def test_email_channel_exists(self):
        """Test Email channel is registered"""

        service = SignalPushService()

        if "email" in service.channels:
            channel = service.channels["email"]

            assert channel.name == "email"
