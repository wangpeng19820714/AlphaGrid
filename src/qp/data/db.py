# qp/data/db.py
"""数据库抽象层 - 提供统一的数据存储接口"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, List
import pandas as pd
import yaml
from pathlib import Path

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


class DataHub:
    """数据中心 - 统一的数据管理接口"""
    
    def __init__(self, config_path: str = None):
        """
        初始化数据中心
        
        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config = self._load_config(config_path)
        self._init_providers()
        self._init_stores()
    
    def _load_config(self, config_path: str = None) -> dict:
        """加载配置文件"""
        if config_path is None:
            # 使用默认配置
            return {
                "root": "data/history_root",
                "provider": "akshare",
                "adjust": "qfq",
                "interval": "1d"
            }
        
        # 处理配置文件路径
        if not Path(config_path).is_absolute():
            # 相对路径，从项目根目录开始
            config_path = Path.cwd() / config_path
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _init_providers(self):
        """初始化数据提供者"""
        from .providers import get_provider
        
        provider_name = self.config.get('provider', 'akshare')
        self.provider = get_provider(provider_name)
    
    def _init_stores(self):
        """初始化数据存储"""
        from .stores import StoreConfig, BarStore, MinuteStore, FinancialStore, FundamentalStore
        
        store_config = StoreConfig(
            root=self.config.get('root', 'data/history_root')
        )
        
        self.bar_store = BarStore(store_config)
        self.minute_store = MinuteStore(store_config)
        self.financial_store = FinancialStore(store_config)
        self.fundamental_store = FundamentalStore(store_config)
    
    def get_bars(self, symbol: str, start_date: str, end_date: str, 
                 interval: str = 'daily') -> List[BarData]:
        """获取K线数据"""
        return self.provider.get_bars(symbol, start_date, end_date, interval)
    
    def get_minute_bars(self, symbol: str, start_date: str, 
                       interval: str = '1m') -> List[BarData]:
        """获取分钟线数据"""
        return self.provider.get_minute_bars(symbol, start_date, interval)
    
    def get_financials(self, symbol: str, start_date: str, end_date: str) -> List:
        """获取财务数据"""
        return self.provider.get_financials(symbol, start_date, end_date)
    
    def get_fundamentals(self, symbol: str, start_date: str, end_date: str) -> List:
        """获取基本面数据"""
        return self.provider.get_fundamentals(symbol, start_date, end_date)
    
    def save_bars(self, bars: List[BarData]) -> int:
        """保存K线数据"""
        return self.bar_store.save_bars(bars)
    
    def save_minute_bars(self, bars: List[BarData]) -> int:
        """保存分钟线数据"""
        return self.minute_store.save_bars(bars)
    
    def save_financials(self, financials: List) -> int:
        """保存财务数据"""
        return self.financial_store.save_financials(financials)
    
    def save_fundamentals(self, fundamentals: List) -> int:
        """保存基本面数据"""
        return self.fundamental_store.save_fundamentals(fundamentals)
    
    def query_bars(self, symbol: str, start_date: str, end_date: str) -> List[BarData]:
        """查询K线数据"""
        return self.bar_store.query_bars(symbol, start_date, end_date)
    
    def query_minute_bars(self, symbol: str, start_date: str, end_date: str) -> List[BarData]:
        """查询分钟线数据"""
        return self.minute_store.query_bars(symbol, start_date, end_date)
    
    def query_financials(self, symbol: str, start_date: str, end_date: str) -> List:
        """查询财务数据"""
        return self.financial_store.query_financials(symbol, start_date, end_date)
    
    def query_fundamentals(self, symbol: str, start_date: str, end_date: str) -> List:
        """查询基本面数据"""
        return self.fundamental_store.query_fundamentals(symbol, start_date, end_date)


def get_default_db() -> BaseDatabase:
    """获取默认数据库实例"""
    return ParquetDatabase()

