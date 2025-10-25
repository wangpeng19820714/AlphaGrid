# qp/data/services/financial_service.py
"""财务数据服务"""
from __future__ import annotations
from typing import Optional
import pandas as pd

from ..types import FinancialData, Exchange, FinancialReportType, financials_to_df
from .base import BaseDataService


class FinancialDataService(BaseDataService):
    """
    财务数据服务
    
    提供财务报表数据的导入、存储和查询功能
    支持资产负债表、利润表、现金流量表等
    """
    
    def __init__(self, store=None):
        """
        初始化财务数据服务
        
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
    
    # ========== 财务数据导入 ==========
    def import_financials(self, provider, symbol: str, exchange: Exchange,
                         report_type: FinancialReportType,
                         start: pd.Timestamp, end: pd.Timestamp) -> int:
        """
        从Provider导入财务数据
        
        Args:
            provider: 数据提供者实例
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型（资产负债表/利润表/现金流量表）
            start: 开始报告期
            end: 结束报告期
            
        Returns:
            导入的记录数
            
        Raises:
            RuntimeError: 如果store未设置
        """
        if self.store is None:
            raise RuntimeError("Store未设置，请先调用set_store()")
        
        symbol = self._validate_symbol(symbol)
        self._validate_date_range(start, end)
        
        data_list = provider.query_financials(symbol, exchange, report_type, start, end)
        df = financials_to_df(data_list)
        
        return self.store.save_financials(
            symbol, exchange.value, report_type.value, df
        )
    
    # ========== 财务数据查询 ==========
    def load_financials(self, symbol: str, exchange: Exchange,
                       report_type: FinancialReportType,
                       start: Optional[pd.Timestamp] = None,
                       end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载财务数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型
            start: 开始报告期（可选）
            end: 结束报告期（可选）
            
        Returns:
            财务数据DataFrame
            
        Raises:
            RuntimeError: 如果store未设置
        """
        if self.store is None:
            raise RuntimeError("Store未设置，请先调用set_store()")
        
        symbol = self._validate_symbol(symbol)
        self._validate_date_range(start, end)
        
        return self.store.load_financials(
            symbol, exchange.value, report_type.value, start, end
        )
    
    # ========== 便捷方法 ==========
    def get_latest_financial_report(self, symbol: str, exchange: Exchange,
                                    report_type: FinancialReportType) -> pd.Series:
        """
        获取最新财报
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型
            
        Returns:
            最新财报数据（Series格式）
        """
        df = self.load_financials(symbol, exchange, report_type)
        if df.empty:
            return pd.Series()
        return df.iloc[-1]
    
    def get_annual_reports(self, symbol: str, exchange: Exchange,
                          report_type: FinancialReportType,
                          years: int = 3) -> pd.DataFrame:
        """
        获取最近N年的年报
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型
            years: 年数（默认3年）
            
        Returns:
            年报数据DataFrame
        """
        df = self.load_financials(symbol, exchange, report_type)
        if df.empty:
            return pd.DataFrame()
        
        # 筛选年报（假设report_period字段存在）
        if 'report_period' in df.columns:
            annual_df = df[df['report_period'].isin(['annual', 'q4'])]
            return annual_df.tail(years)
        
        return df.tail(years)
    
    def get_quarterly_reports(self, symbol: str, exchange: Exchange,
                            report_type: FinancialReportType,
                            quarters: int = 4) -> pd.DataFrame:
        """
        获取最近N个季度的财报
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型
            quarters: 季度数（默认4个季度）
            
        Returns:
            季报数据DataFrame
        """
        df = self.load_financials(symbol, exchange, report_type)
        if df.empty:
            return pd.DataFrame()
        
        return df.tail(quarters)
    
    def calculate_growth_rate(self, symbol: str, exchange: Exchange,
                            report_type: FinancialReportType,
                            field: str = 'revenue') -> pd.DataFrame:
        """
        计算财务指标增长率
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型
            field: 指标字段名（默认为营收）
            
        Returns:
            包含增长率的DataFrame
        """
        df = self.load_financials(symbol, exchange, report_type)
        if df.empty or field not in df.columns:
            return pd.DataFrame()
        
        result = df.copy()
        result[f'{field}_growth'] = df[field].pct_change() * 100
        return result[['report_date', field, f'{field}_growth']]

