# quant/datahub/services/fundamental_service.py
"""基本面数据服务"""
from __future__ import annotations
from typing import Optional
import pandas as pd

from ..types import FundamentalData, Exchange, fundamentals_to_df
from .base import BaseDataService


class FundamentalDataService(BaseDataService):
    """
    基本面数据服务
    
    提供基本面指标数据的导入、存储和查询功能
    包括估值指标（PE/PB）、财务质量、成长性等
    """
    
    def __init__(self, store=None):
        """
        初始化基本面数据服务
        
        Args:
            store: 存储实例（FundamentalStore），如果为None需要后续设置
        """
        super().__init__()
        self.store = store
    
    def set_store(self, store):
        """
        设置存储实例
        
        Args:
            store: FundamentalStore实例
        """
        self.store = store
    
    # ========== 基本面数据导入 ==========
    def import_fundamentals(self, provider, symbol: str, exchange: Exchange,
                           start: pd.Timestamp, end: pd.Timestamp) -> int:
        """
        从Provider导入基本面数据
        
        Args:
            provider: 数据提供者实例
            symbol: 股票代码
            exchange: 交易所
            start: 开始日期
            end: 结束日期
            
        Returns:
            导入的记录数
            
        Raises:
            RuntimeError: 如果store未设置
        """
        if self.store is None:
            raise RuntimeError("Store未设置，请先调用set_store()")
        
        symbol = self._validate_symbol(symbol)
        self._validate_date_range(start, end)
        
        data_list = provider.query_fundamentals(symbol, exchange, start, end)
        df = fundamentals_to_df(data_list)
        
        return self.store.save_fundamentals(symbol, exchange.value, df)
    
    # ========== 基本面数据查询 ==========
    def load_fundamentals(self, symbol: str, exchange: Exchange,
                         start: Optional[pd.Timestamp] = None,
                         end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载基本面数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            start: 开始日期（可选）
            end: 结束日期（可选）
            
        Returns:
            基本面数据DataFrame
            
        Raises:
            RuntimeError: 如果store未设置
        """
        if self.store is None:
            raise RuntimeError("Store未设置，请先调用set_store()")
        
        symbol = self._validate_symbol(symbol)
        self._validate_date_range(start, end)
        
        return self.store.load_fundamentals(symbol, exchange.value, start, end)
    
    # ========== 便捷方法 ==========
    def get_fundamentals_at_date(self, symbol: str, exchange: Exchange,
                                date: pd.Timestamp) -> pd.Series:
        """
        获取指定日期的基本面数据（向前填充）
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            date: 指定日期
            
        Returns:
            基本面数据（Series格式）
        """
        df = self.load_fundamentals(symbol, exchange, end=date)
        if df.empty:
            return pd.Series()
        return df.iloc[-1]
    
    def get_latest_fundamentals(self, symbol: str, exchange: Exchange) -> pd.Series:
        """
        获取最新的基本面数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            
        Returns:
            最新基本面数据（Series格式）
        """
        df = self.load_fundamentals(symbol, exchange)
        if df.empty:
            return pd.Series()
        return df.iloc[-1]
    
    def get_valuation_metrics(self, symbol: str, exchange: Exchange,
                             start: Optional[pd.Timestamp] = None,
                             end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        获取估值指标（PE/PB/PS等）
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            start: 开始日期（可选）
            end: 结束日期（可选）
            
        Returns:
            估值指标DataFrame
        """
        df = self.load_fundamentals(symbol, exchange, start, end)
        if df.empty:
            return pd.DataFrame()
        
        # 选择估值相关列
        valuation_cols = ['date', 'pe_ratio', 'pe_ttm', 'pb_ratio', 'ps_ratio', 'pcf_ratio']
        available_cols = [col for col in valuation_cols if col in df.columns]
        
        return df[available_cols]
    
    def get_profitability_metrics(self, symbol: str, exchange: Exchange,
                                  start: Optional[pd.Timestamp] = None,
                                  end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        获取盈利能力指标（ROE/ROA等）
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            start: 开始日期（可选）
            end: 结束日期（可选）
            
        Returns:
            盈利能力指标DataFrame
        """
        df = self.load_fundamentals(symbol, exchange, start, end)
        if df.empty:
            return pd.DataFrame()
        
        # 选择盈利能力相关列
        profitability_cols = ['date', 'roe', 'roa', 'roic', 'gross_margin', 'net_margin', 'operating_margin']
        available_cols = [col for col in profitability_cols if col in df.columns]
        
        return df[available_cols]
    
    def get_growth_metrics(self, symbol: str, exchange: Exchange,
                          start: Optional[pd.Timestamp] = None,
                          end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        获取成长性指标
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            start: 开始日期（可选）
            end: 结束日期（可选）
            
        Returns:
            成长性指标DataFrame
        """
        df = self.load_fundamentals(symbol, exchange, start, end)
        if df.empty:
            return pd.DataFrame()
        
        # 选择成长性相关列
        growth_cols = ['date', 'revenue_growth', 'revenue_growth_qoq', 'profit_growth', 'profit_growth_qoq']
        available_cols = [col for col in growth_cols if col in df.columns]
        
        return df[available_cols]
    
    def calculate_valuation_percentile(self, symbol: str, exchange: Exchange,
                                      metric: str = 'pe_ratio',
                                      window: int = 252) -> pd.DataFrame:
        """
        计算估值百分位（相对历史）
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            metric: 估值指标字段名（默认pe_ratio）
            window: 回溯窗口天数（默认252天）
            
        Returns:
            包含百分位的DataFrame
        """
        df = self.load_fundamentals(symbol, exchange)
        if df.empty or metric not in df.columns:
            return pd.DataFrame()
        
        # 计算滚动百分位
        result = df[['date', metric]].copy()
        result[f'{metric}_percentile'] = df[metric].rolling(window=window, min_periods=1).apply(
            lambda x: (x.iloc[-1] <= x).sum() / len(x) * 100
        )
        
        return result

