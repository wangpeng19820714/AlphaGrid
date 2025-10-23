# quant/datahub/service.py
"""历史数据服务 - 统一数据导入、存储、查询接口"""
from __future__ import annotations
from typing import Iterable, Optional, Dict
import pandas as pd

from .types import BarData, Exchange, Interval, bars_to_df, df_to_bars
from .db import BaseDatabase, ParquetDatabase

# 重采样规则映射
RESAMPLE_RULES = {
    Interval.DAILY: "1D",
    Interval.WEEKLY: "1W",
    Interval.MONTHLY: "1MS",
    Interval.HOUR1: "1H",
    Interval.MIN15: "15min",
    Interval.MIN5: "5min",
    Interval.MIN1: "1min",
}


class HistoricalDataService:
    """历史数据服务门面类"""
    
    def __init__(self, db: Optional[BaseDatabase] = None):
        """
        初始化服务
        
        Args:
            db: 数据库实例，默认使用ParquetDatabase
        """
        self.db = db or ParquetDatabase()

    # ========== 持久化 ==========
    def save_bars(self, bars: Iterable[BarData]) -> int:
        """保存K线数据"""
        return self.db.save_bars(list(bars))

    def load_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                  start: Optional[pd.Timestamp] = None,
                  end: Optional[pd.Timestamp] = None) -> list[BarData]:
        """加载K线数据"""
        return self.db.load_bars(symbol, exchange, interval, start, end)

    # ========== 导入数据 ==========
    def import_from_provider(self, provider, symbol: str, exchange: Exchange,
                           interval: Interval, start: pd.Timestamp, end: pd.Timestamp,
                           adjust: str = "none") -> int:
        """
        从数据提供者导入数据
        
        Args:
            provider: 数据提供者实例
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            start: 开始日期
            end: 结束日期
            adjust: 复权类型
            
        Returns:
            导入的记录数
        """
        bars = provider.query_bars(symbol, exchange, interval, start, end, adjust)
        return self.save_bars(bars)

    # ========== 重采样 ==========
    def _resample_ohlcv(self, df: pd.DataFrame, rule: str) -> pd.DataFrame:
        """重采样OHLCV数据"""
        agg_dict = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": lambda x: x.sum(min_count=1),
        }
        
        # 可选字段
        if "turnover" in df.columns:
            agg_dict["turnover"] = lambda x: x.sum(min_count=1)
        else:
            df["turnover"] = df["close"] * df["volume"]
            agg_dict["turnover"] = lambda x: x.sum(min_count=1)
        
        if "open_interest" in df.columns:
            agg_dict["open_interest"] = "last"
        else:
            df["open_interest"] = 0
            agg_dict["open_interest"] = "last"
        
        resampled = df.resample(rule).agg(agg_dict)
        return resampled.dropna(subset=["open", "high", "low", "close"], how="any")

    def resample(self, bars: list[BarData], to: Interval) -> list[BarData]:
        """
        重采样K线数据
        
        Args:
            bars: K线数据列表
            to: 目标周期
            
        Returns:
            重采样后的K线数据
        """
        if not bars:
            return []
        
        df = bars_to_df(bars)
        if df.empty:
            return []
        
        df = df.set_index("datetime").sort_index()
        
        # 获取重采样规则
        rule = RESAMPLE_RULES.get(to)
        if rule is None:
            raise ValueError(f"不支持的重采样周期: {to}")
        
        # 执行重采样
        resampled_df = self._resample_ohlcv(df, rule)
        
        # 获取元数据
        symbol = df.reset_index().iloc[0]["symbol"]
        exchange = df.reset_index().iloc[0]["exchange"]
        
        # 转换回BarData
        result_df = resampled_df.reset_index()
        return df_to_bars(result_df, symbol, exchange, to)

    # ========== 复权 ==========
    def apply_adjust(self, bars: list[BarData],
                    factor_series: Optional[pd.Series] = None) -> list[BarData]:
        """
        应用复权因子
        
        Args:
            bars: K线数据列表
            factor_series: 复权因子序列，index为日期
            
        Returns:
            复权后的K线数据
        """
        if factor_series is None or not bars:
            return bars
        
        df = bars_to_df(bars).set_index("datetime")
        
        # 对齐因子
        factor = factor_series.reindex(df.index).ffill()
        
        # 应用到价格列
        price_columns = ["open", "high", "low", "close"]
        for col in price_columns:
            df[col] = df[col].astype(float) * factor
        
        # 转换回BarData
        return df_to_bars(
            df.reset_index(),
            bars[0].symbol,
            bars[0].exchange,
            bars[0].interval
        )

