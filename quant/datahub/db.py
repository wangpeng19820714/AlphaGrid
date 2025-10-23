# quant/datahub/db.py
"""数据库接口定义"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List
import pandas as pd

from .types import BarData, Exchange, Interval


class BaseDatabase(ABC):
    """数据库基类接口"""
    
    @abstractmethod
    def save_bars(self, bars: List[BarData]) -> int:
        """保存K线数据"""
        pass
    
    @abstractmethod
    def load_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                  start: Optional[pd.Timestamp] = None,
                  end: Optional[pd.Timestamp] = None) -> List[BarData]:
        """加载K线数据"""
        pass


class ParquetDatabase(BaseDatabase):
    """Parquet数据库实现"""
    
    def __init__(self, root: str = "~/.quant/history"):
        from storage.parquet_store import ParquetYearWriter, DuckDBReader, StoreConfig
        self.config = StoreConfig(root=root)
        self.writer = ParquetYearWriter(self.config)
        self.reader = DuckDBReader(self.config)
    
    def save_bars(self, bars: List[BarData]) -> int:
        """保存K线数据"""
        if not bars:
            return 0
        
        from .types import bars_to_df
        
        # 按 (exchange, symbol, interval) 分组
        groups = {}
        for bar in bars:
            key = (bar.exchange.value, bar.symbol, bar.interval.value)
            if key not in groups:
                groups[key] = []
            groups[key].append(bar)
        
        # 分组写入
        total = 0
        for (exchange, symbol, interval), group_bars in groups.items():
            df = bars_to_df(group_bars)
            df = df.rename(columns={"datetime": "date"})
            count = self.writer.append(exchange, symbol, interval, df)
            total += count
        
        return total
    
    def load_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                  start: Optional[pd.Timestamp] = None,
                  end: Optional[pd.Timestamp] = None) -> List[BarData]:
        """加载K线数据"""
        from .types import df_to_bars
        
        df = self.reader.load(
            exchange.value, symbol, interval.value,
            start, end
        )
        
        if df.empty:
            return []
        
        # 重命名列
        df = df.rename(columns={"date": "datetime"})
        
        return df_to_bars(df, symbol, exchange, interval)

