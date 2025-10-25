# quant/datahub/db.py
"""数据库抽象层 - 提供统一的数据存储接口"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List
import pandas as pd

from .types import BarData, Exchange, Interval


class BaseDatabase(ABC):
    """数据库基类"""
    
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
    """Parquet数据库实现（占位）"""
    
    def __init__(self, root: str = "data/history_root"):
        self.root = root
    
    def save_bars(self, bars: List[BarData]) -> int:
        """保存K线数据"""
        # TODO: 实现实际的存储逻辑
        return len(bars)
    
    def load_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                  start: Optional[pd.Timestamp] = None,
                  end: Optional[pd.Timestamp] = None) -> List[BarData]:
        """加载K线数据"""
        # TODO: 实现实际的加载逻辑
        return []


def get_default_db() -> BaseDatabase:
    """获取默认数据库实例"""
    return ParquetDatabase()

