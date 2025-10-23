# quant/datahub/providers/yfinance_provider.py
"""Yahoo Finance数据提供者"""
from __future__ import annotations
import pandas as pd
import yfinance as yf
from .base import BaseProvider
from ..types import Exchange, Interval, BarData, df_to_bars

# 列名映射
COLUMN_MAPPING = {
    "Date": "datetime",
    "Open": "open",
    "High": "high",
    "Low": "low",
    "Close": "close",
    "Volume": "volume"
}


class YFProvider(BaseProvider):
    """Yahoo Finance数据提供者"""
    
    def __init__(self):
        """初始化"""
        pass

    def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                   start: pd.Timestamp, end: pd.Timestamp, adjust: str = "none") -> list[BarData]:
        """
        查询K线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            start: 开始日期
            end: 结束日期
            adjust: 复权类型 ('none', 'qfq')
            
        Returns:
            K线数据列表
        """
        # yfinance auto_adjust参数自动进行前复权
        auto_adjust = (adjust != "none")
        
        # 下载数据
        df = yf.download(
            symbol,
            start=start.tz_convert(None),
            end=end.tz_convert(None),
            auto_adjust=auto_adjust,
            interval="1d",
            progress=False
        )
        
        # 重命名列
        df = df.reset_index().rename(columns=COLUMN_MAPPING)
        
        # 转换日期为UTC
        df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize("UTC")
        
        # 选择需要的列
        df = df[["datetime", "open", "high", "low", "close", "volume"]]
        
        return df_to_bars(df, symbol, exchange, interval)
