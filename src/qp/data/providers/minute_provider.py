# qp/data/providers/minute_provider.py
"""分钟线数据提供者"""
from __future__ import annotations
import os
import pandas as pd
import akshare as ak
from typing import Optional
from .base import BaseProvider
from ..types import BarData, Exchange, Interval, df_to_bars

# 列名映射
COLUMN_MAPPING = {
    "时间": "datetime",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "turnover"
}

# 分钟线周期映射
MINUTE_INTERVAL_MAPPING = {
    Interval.MIN1: "1",
    Interval.MIN5: "5", 
    Interval.MIN15: "15",
    Interval.MIN30: "30",
    Interval.HOUR1: "60"
}

# 复权类型映射
ADJUST_MAPPING = {
    "none": "",
    "qfq": "qfq",  # 前复权
    "hfq": "hfq"   # 后复权
}


class MinuteProvider(BaseProvider):
    """分钟线数据提供者"""
    
    def __init__(self):
        """初始化"""
        pass

    def _fetch_minute_data(self, symbol: str, interval: Interval, 
                          start: pd.Timestamp, end: pd.Timestamp, 
                          adjust: str) -> pd.DataFrame:
        """获取分钟线数据"""
        # 获取分钟周期参数
        period = MINUTE_INTERVAL_MAPPING.get(interval)
        if not period:
            raise ValueError(f"不支持的分钟线周期: {interval}")
        
        # 使用AKShare获取分钟线数据
        df = ak.stock_zh_a_hist_min_em(
            symbol=symbol,
            period=period,
            start_date=start.strftime("%Y%m%d %H:%M:%S"),
            end_date=end.strftime("%Y%m%d %H:%M:%S"),
            adjust=ADJUST_MAPPING[adjust]
        )
        
        if df.empty:
            return pd.DataFrame(columns=["datetime", "open", "high", "low", "close", "volume", "turnover"])
        
        # 重命名列
        df = df.rename(columns=COLUMN_MAPPING)
        
        # 转换日期时间
        df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize("UTC")
        
        # 确保数据类型正确
        for col in ["open", "high", "low", "close", "volume", "turnover"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        return df[["datetime", "open", "high", "low", "close", "volume", "turnover"]]

    def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                   start: pd.Timestamp, end: pd.Timestamp, adjust: str = "qfq") -> list[BarData]:
        """
        查询K线数据
        
        Args:
            symbol: 股票代码 (如: '000001')
            exchange: 交易所
            interval: 时间周期
            start: 开始时间
            end: 结束时间
            adjust: 复权类型 ('none', 'qfq', 'hfq')
            
        Returns:
            K线数据列表
        """
        # 检查是否支持分钟线
        if interval not in MINUTE_INTERVAL_MAPPING:
            raise NotImplementedError(f"MinuteProvider不支持周期: {interval}")
        
        # 获取数据
        df = self._fetch_minute_data(symbol, interval, start, end, adjust)
        
        if df.empty:
            return []
        
        # 转换为BarData对象
        return df_to_bars(df, symbol, exchange, interval)

    def get_realtime_minute(self, symbol: str, exchange: Exchange, 
                           interval: Interval = Interval.MIN1) -> Optional[BarData]:
        """
        获取实时分钟线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            
        Returns:
            最新的分钟线数据
        """
        # 获取最近1分钟的数据
        end_time = pd.Timestamp.now(tz="UTC")
        start_time = end_time - pd.Timedelta(minutes=5)  # 获取最近5分钟确保有数据
        
        bars = self.query_bars(symbol, exchange, interval, start_time, end_time)
        return bars[-1] if bars else None

    def get_today_minutes(self, symbol: str, exchange: Exchange, 
                         interval: Interval = Interval.MIN1) -> list[BarData]:
        """
        获取今日分钟线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            
        Returns:
            今日分钟线数据列表
        """
        today = pd.Timestamp.now(tz="UTC").normalize()
        tomorrow = today + pd.Timedelta(days=1)
        
        return self.query_bars(symbol, exchange, interval, today, tomorrow)

    def get_latest_n_minutes(self, symbol: str, exchange: Exchange, 
                            interval: Interval, n: int = 100) -> list[BarData]:
        """
        获取最新N条分钟线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            n: 数据条数
            
        Returns:
            最新N条分钟线数据
        """
        end_time = pd.Timestamp.now(tz="UTC")
        # 根据周期计算开始时间
        if interval == Interval.MIN1:
            start_time = end_time - pd.Timedelta(minutes=n)
        elif interval == Interval.MIN5:
            start_time = end_time - pd.Timedelta(minutes=n * 5)
        elif interval == Interval.MIN15:
            start_time = end_time - pd.Timedelta(minutes=n * 15)
        elif interval == Interval.MIN30:
            start_time = end_time - pd.Timedelta(minutes=n * 30)
        elif interval == Interval.HOUR1:
            start_time = end_time - pd.Timedelta(hours=n)
        else:
            raise ValueError(f"不支持的周期: {interval}")
        
        bars = self.query_bars(symbol, exchange, interval, start_time, end_time)
        return bars[-n:] if len(bars) > n else bars
