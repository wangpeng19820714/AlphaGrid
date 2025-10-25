# qp/data/services/minute_service.py
"""分钟线数据服务"""
from __future__ import annotations
from typing import Iterable, Optional, List
import pandas as pd

from ..types import BarData, Exchange, Interval, bars_to_df, df_to_bars
from ..db import BaseDatabase, ParquetDatabase
from ..providers import MinuteProvider
from .base import BaseDataService


class MinuteDataService(BaseDataService):
    """
    分钟线数据服务
    
    专门处理分钟线数据的导入、存储、查询和实时更新
    """
    
    def __init__(self, db: Optional[BaseDatabase] = None, provider: Optional[MinuteProvider] = None):
        """
        初始化分钟线数据服务
        
        Args:
            db: 数据库实例，默认使用ParquetDatabase
            provider: 数据提供者实例，默认使用MinuteProvider
        """
        super().__init__()
        self.db = db or ParquetDatabase()
        self.provider = provider or MinuteProvider()
    
    # ========== 数据持久化 ==========
    def save_bars(self, bars: Iterable[BarData]) -> int:
        """
        保存K线数据
        
        Args:
            bars: K线数据列表
            
        Returns:
            保存的记录数
        """
        return self.db.save_bars(list(bars))
    
    # ========== 数据导入 ==========
    def import_minute_data(self, symbol: str, exchange: Exchange,
                          interval: Interval, start: pd.Timestamp, 
                          end: pd.Timestamp, adjust: str = "qfq") -> int:
        """
        导入分钟线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            start: 开始时间
            end: 结束时间
            adjust: 复权类型
            
        Returns:
            导入的记录数
        """
        symbol = self._validate_symbol(symbol)
        self._validate_date_range(start, end)
        
        # 检查是否支持分钟线
        if interval not in [Interval.MIN1, Interval.MIN5, Interval.MIN15, 
                           Interval.MIN30, Interval.HOUR1]:
            raise ValueError(f"不支持的分钟线周期: {interval}")
        
        # 从提供商获取数据
        bars = self.provider.query_bars(symbol, exchange, interval, start, end, adjust)
        
        # 保存到数据库
        return self.db.save_bars(bars)
    
    def import_today_minutes(self, symbol: str, exchange: Exchange,
                           interval: Interval = Interval.MIN1) -> int:
        """
        导入今日分钟线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            
        Returns:
            导入的记录数
        """
        today = pd.Timestamp.now(tz="UTC").normalize()
        tomorrow = today + pd.Timedelta(days=1)
        
        return self.import_minute_data(symbol, exchange, interval, today, tomorrow)
    
    def import_latest_minutes(self, symbol: str, exchange: Exchange,
                            interval: Interval, n: int = 100) -> int:
        """
        导入最新N条分钟线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            n: 数据条数
            
        Returns:
            导入的记录数
        """
        bars = self.provider.get_latest_n_minutes(symbol, exchange, interval, n)
        return self.db.save_bars(bars)
    
    # ========== 数据查询 ==========
    def load_minute_data(self, symbol: str, exchange: Exchange, interval: Interval,
                        start: Optional[pd.Timestamp] = None,
                        end: Optional[pd.Timestamp] = None) -> List[BarData]:
        """
        加载分钟线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            start: 开始时间（可选）
            end: 结束时间（可选）
            
        Returns:
            分钟线数据列表
        """
        symbol = self._validate_symbol(symbol)
        self._validate_date_range(start, end)
        
        return self.db.load_bars(symbol, exchange, interval, start, end)
    
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
        return self.provider.get_realtime_minute(symbol, exchange, interval)
    
    def get_today_minutes(self, symbol: str, exchange: Exchange,
                         interval: Interval = Interval.MIN1) -> List[BarData]:
        """
        获取今日分钟线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            
        Returns:
            今日分钟线数据列表
        """
        return self.provider.get_today_minutes(symbol, exchange, interval)
    
    def get_latest_n_minutes(self, symbol: str, exchange: Exchange,
                            interval: Interval, n: int = 100) -> List[BarData]:
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
        return self.provider.get_latest_n_minutes(symbol, exchange, interval, n)
    
    # ========== 数据更新 ==========
    def update_minute_data(self, symbol: str, exchange: Exchange,
                          interval: Interval) -> int:
        """
        更新分钟线数据（增量更新）
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            
        Returns:
            更新的记录数
        """
        # 获取最新数据
        latest_bar = self.get_latest_bar(symbol, exchange, interval)
        
        if latest_bar is None:
            # 如果没有历史数据，导入最近100条
            return self.import_latest_minutes(symbol, exchange, interval, 100)
        
        # 从最新数据时间开始更新
        start_time = latest_bar.datetime
        end_time = pd.Timestamp.now(tz="UTC")
        
        # 如果时间差小于1分钟，不需要更新
        if (end_time - start_time).total_seconds() < 60:
            return 0
        
        # 导入新数据
        return self.import_minute_data(symbol, exchange, interval, start_time, end_time)
    
    def sync_minute_data(self, symbol: str, exchange: Exchange,
                        interval: Interval, days: int = 7) -> int:
        """
        同步分钟线数据（全量同步）
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            days: 同步天数
            
        Returns:
            同步的记录数
        """
        end_time = pd.Timestamp.now(tz="UTC")
        start_time = end_time - pd.Timedelta(days=days)
        
        return self.import_minute_data(symbol, exchange, interval, start_time, end_time)
    
    # ========== 数据统计 ==========
    def get_minute_stats(self, symbol: str, exchange: Exchange,
                        interval: Interval) -> dict:
        """
        获取分钟线数据统计信息
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            
        Returns:
            统计信息字典
        """
        bars = self.load_minute_data(symbol, exchange, interval)
        
        if not bars:
            return {
                "count": 0,
                "start_time": None,
                "end_time": None,
                "latest_price": None,
                "volume_total": 0.0
            }
        
        df = bars_to_df(bars)
        
        if df.empty:
            return {
                "count": 0,
                "start_time": None,
                "end_time": None,
                "latest_price": None,
                "volume_total": 0.0,
                "price_range": {"min": 0.0, "max": 0.0}
            }
        
        # 使用更安全的方式获取统计信息
        start_time = df["datetime"].iloc[0] if len(df) > 0 else None
        end_time = df["datetime"].iloc[-1] if len(df) > 0 else None
        latest_price = df["close"].iloc[-1] if len(df) > 0 else None
        volume_total = df["volume"].sum() if len(df) > 0 else 0.0
        
        # 手动计算最小值和最大值
        low_values = df["low"].tolist() if len(df) > 0 else [0.0]
        high_values = df["high"].tolist() if len(df) > 0 else [0.0]
        
        return {
            "count": len(bars),
            "start_time": start_time,
            "end_time": end_time,
            "latest_price": latest_price,
            "volume_total": float(volume_total),
            "price_range": {
                "min": float(min(low_values)),
                "max": float(max(high_values))
            }
        }
    
    # ========== 便捷方法 ==========
    def get_latest_bar(self, symbol: str, exchange: Exchange, 
                      interval: Interval) -> Optional[BarData]:
        """
        获取最新分钟线
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            
        Returns:
            最新的分钟线数据，如果不存在则返回None
        """
        bars = self.load_minute_data(symbol, exchange, interval)
        return bars[-1] if bars else None
    
    def is_market_open(self, symbol: str, exchange: Exchange) -> bool:
        """
        判断市场是否开盘
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            
        Returns:
            是否开盘
        """
        # 获取最新数据
        latest_bar = self.get_latest_bar(symbol, exchange, Interval.MIN1)
        
        if latest_bar is None:
            return False
        
        # 检查数据时间是否在最近5分钟内
        now = pd.Timestamp.now(tz="UTC")
        time_diff = (now - latest_bar.datetime).total_seconds()
        
        return time_diff < 300  # 5分钟内认为市场开盘
