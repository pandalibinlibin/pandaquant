import pytest
import pandas as pd
import numpy as np
from app.domains.factors.report import MomentumFactor


class TestMomentumFactor:
    def test_momentum_initialization(self):
        momentum = MomentumFactor(lookback_period=20)

        assert momentum.name == "Momentum_20"
        assert momentum.lookback_period == 20
        assert "动量因子, 回望期20天" in momentum.description

    def test_momentum_report_info(self):
        momentum = MomentumFactor(
            lookback_period=20,
            report_source="金融工程报告",
            report_title="动量因子研究",
            report_author="量化研究团队",
            report_date="2024-01-01",
        )

        assert momentum.report_source == "金融工程报告"
        assert momentum.report_title == "动量因子研究"
        assert momentum.report_author == "量化研究团队"
        assert momentum.report_date == "2024-01-01"

    def test_momentum_qlib_integration(self):
        momentum = MomentumFactor(lookback_period=20)

        expression = momentum.get_qlib_expression()
        assert "Ref($close, 20) / $close - 1" in expression

        dependencies = momentum.get_qlib_dependencies()
        assert "$close" in dependencies

        params = momentum.get_qlib_parameters()
        assert params["lookback_period"] == 20
        assert params["report_source"] == "金融工程报告"

    def test_momentum_report_reference(self):
        momentum = MomentumFactor()

        report_ref = momentum.get_report_reference()
        assert "来源: 金融工程报告" in report_ref
        assert "标题: 动量因子研究" in report_ref
        assert "作者: 量化研究团队" in report_ref
