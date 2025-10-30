"""
Tests for push channels
"""

import pytest
from app.domains.signals.base import ChannelType, ChannelStatus, PushResult, PushChannel
from app.domains.signals.wechat import WeChatWorkChannel
from app.domains.signals.email import EmailChannel


class TestPushResult:
    """Test PushResult class"""

    def test_push_result_success(self):
        """Test successful push result"""

        result = PushResult(success=True, message="Pushed successfully")

        assert result.success is True
        assert result.message == "Pushed successfully"
        assert result.error is None

    def test_push_result_failure(self):
        """Test failed push result"""
        result = PushResult(success=False, error="Connection failed")

        assert result.success is False
        assert result.error == "Connection failed"


class TestWeChatWorkChannel:
    """Test WeChat Work push channel"""

    def test_channel_initialization(self):
        """Test WeChat channel can be initialized"""
        channel = WeChatWorkChannel()

        assert channel.name == "wechat_work"
        assert channel.channel_type == ChannelType.WECHAT
        assert channel.enabled is True
        assert channel.status == ChannelStatus.ACTIVE


class TestEmailChannel:
    """Test Email push channel"""

    def test_channel_initialization(self):
        """Test Email channel can be initialized"""

        channel = EmailChannel()

        assert channel.name == "email"
        assert channel.channel_type == ChannelType.EMAIL
        assert channel.enabled is True
        assert channel.status == ChannelStatus.ACTIVE
