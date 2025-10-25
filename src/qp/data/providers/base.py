# qp/data/providers/base.py
from __future__ import annotations
from typing import Iterable, Optional
import pandas as pd
from ..types import (
    BarData, FinancialData, FundamentalData,
    Exchange, Interval, FinancialReportType
)


class BaseProvider:
    """统一数据提供者接口"""
    
    # ===== 原有K线接口 =====
    def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                   start: pd.Timestamp, end: pd.Timestamp, adjust: str="none") -> list[BarData]:
        raise NotImplementedError

    # ===== 财务数据接口 =====
    def query_financials(self, symbol: str, exchange: Exchange,
                         report_type: FinancialReportType,
                         start: pd.Timestamp, end: pd.Timestamp) -> list[FinancialData]:
        """
        查询财务报表数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型（资产负债表/利润表/现金流量表）
            start: 开始报告期
            end: 结束报告期
        """
        raise NotImplementedError("该Provider不支持财务数据查询")
    
    # ===== 基本面数据接口 =====
    def query_fundamentals(self, symbol: str, exchange: Exchange,
                          start: pd.Timestamp, end: pd.Timestamp) -> list[FundamentalData]:
        """
        查询基本面数据（日频）
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            start: 开始日期
            end: 结束日期
        """
        raise NotImplementedError("该Provider不支持基本面数据查询")
