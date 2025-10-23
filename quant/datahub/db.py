# quant/datahub/db.py
"""
数据库抽象层
提供统一的数据存储接口
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List
import pandas as pd
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from datahub.types import BarData, Exchange, Interval, bars_to_df, df_to_bars
from storage.parquet_store import (
    ParquetYearWriter, DuckDBReader, StoreConfig
)


class BaseDatabase(ABC):
    """数据库抽象基类"""
    
    @abstractmethod
    def save_bars(self, bars: List[BarData]) -> int:
        """
        保存K线数据
        
        Args:
            bars: K线数据列表
            
        Returns:
            保存的记录数
        """
        pass
    
    @abstractmethod
    def load_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                  start: Optional[pd.Timestamp] = None,
                  end: Optional[pd.Timestamp] = None) -> List[BarData]:
        """
        加载K线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            start: 开始日期
            end: 结束日期
            
        Returns:
            K线数据列表
        """
        pass


class ParquetDatabase(BaseDatabase):
    """
    Parquet数据库实现
    使用 parquet 格式存储，DuckDB 查询
    """
    
    def __init__(self, config: Optional[StoreConfig] = None):
        """
        初始化Parquet数据库
        
        Args:
            config: 存储配置，默认使用默认配置
        """
        self.config = config or StoreConfig()
        self.writer = ParquetYearWriter(self.config)
        self.reader = DuckDBReader(self.config)
    
    def save_bars(self, bars: List[BarData]) -> int:
        """
        保存K线数据到Parquet文件
        
        Args:
            bars: K线数据列表
            
        Returns:
            保存的记录数
        """
        if not bars:
            return 0
        
        # 按 (exchange, symbol, interval) 分组
        grouped = {}
        for bar in bars:
            key = (bar.exchange.value, bar.symbol, bar.interval.value)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(bar)
        
        # 逐组保存
        total_count = 0
        for (exchange, symbol, interval), bar_list in grouped.items():
            df = bars_to_df(bar_list)
            # 重命名 datetime 列为 date
            df = df.rename(columns={"datetime": "date"})
            count = self.writer.append(exchange, symbol, interval, df)
            total_count += count
        
        return total_count
    
    def load_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                  start: Optional[pd.Timestamp] = None,
                  end: Optional[pd.Timestamp] = None) -> List[BarData]:
        """
        从Parquet文件加载K线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            start: 开始日期
            end: 结束日期
            
        Returns:
            K线数据列表
        """
        # 从存储读取数据
        df = self.reader.load(
            exchange.value,
            symbol,
            interval.value,
            start,
            end
        )
        
        if df.empty:
            return []
        
        # 重命名 date 列为 datetime
        df = df.rename(columns={"date": "datetime"})
        
        # 转换为 BarData 列表
        return df_to_bars(df, symbol, exchange, interval)


# 便捷函数：获取默认数据库实例
_default_db: Optional[ParquetDatabase] = None

def get_default_db() -> ParquetDatabase:
    """获取默认数据库实例（单例模式）"""
    global _default_db
    if _default_db is None:
        _default_db = ParquetDatabase()
    return _default_db

