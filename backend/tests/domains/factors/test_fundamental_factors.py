import pytest
import pandas as pd
import numpy as np
from app.domains.factors.fundamental import FinancialRatioFactor


class TestFinancialRatioFactor:
    def test_pe_ratio_initialization(self):
        pe = FinancialRatioFactor(ratio_type="pe_ratio")

        assert pe.name == "FinancialRatio_pe_ratio"
        assert pe.ratio_type == "pe_ratio"
        assert "Financial ratio factor: pe_ratio" in pe.description

    def test_pb_ratio_initialization(self):
        pb = FinancialRatioFactor(ratio_type="pb_ratio")

        assert pb.name == "FinancialRatio_pb_ratio"
        assert pb.ratio_type == "pb_ratio"
        assert "Financial ratio factor: pb_ratio" in pb.description

    def test_pe_ratio_qlib_integration(self):
        pe = FinancialRatioFactor(ratio_type="pe_ratio")

        expression = pe.get_qlib_expression()
        assert "PE($close)" in expression

        dependencies = pe.get_qlib_dependencies()
        assert "$close" in dependencies

        params = pe.get_qlib_parameters()
        assert params["ratio_type"] == "pe_ratio"

    def test_pb_ratio_qlib_integration(self):
        pb = FinancialRatioFactor(ratio_type="pb_ratio")

        expression = pb.get_qlib_expression()
        assert "PB($close)" in expression

        dependencies = pb.get_qlib_dependencies()
        assert "$close" in dependencies

        params = pb.get_qlib_parameters()
        assert params["ratio_type"] == "pb_ratio"
