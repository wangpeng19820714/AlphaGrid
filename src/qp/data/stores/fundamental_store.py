# qp/data/stores/fundamental_store.py
"""基本面数据存储模块"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import pandas as pd

from .base import StoreConfig, BaseStore, _normalize_path


class FundamentalStore(BaseStore):
    """
    基本面数据存储
    
    - 日频数据按日期存储
    - 按date去重
    - 支持增量更新
    """
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
    
    def save(self, symbol: str, exchange: str, df: pd.DataFrame) -> int:
        """
        保存基本面数据（日频）
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            df: 基本面数据DataFrame
            
        Returns:
            保存的记录数
            
        目录结构: {root}/fundamentals/{exchange}/{symbol}/daily.parquet
        """
        if df.empty:
            return 0
        
        path = self.root / "fundamentals" / exchange / symbol
        path.mkdir(parents=True, exist_ok=True)
        
        file_path = path / "daily.parquet"
        
        # 与现有数据合并（按 date 去重）
        df = self._merge_with_existing(file_path, df, unique_cols=['date'])
        
        df.to_parquet(file_path, index=False, compression=self.config.compression)
        return len(df)
    
    def load(self, symbol: str, exchange: str,
             start: Optional[pd.Timestamp] = None,
             end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载基本面数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            start: 开始日期
            end: 结束日期
            
        Returns:
            基本面数据DataFrame
        """
        file_path = self.root / "fundamentals" / exchange / symbol / "daily.parquet"
        
        if not file_path.exists():
            return pd.DataFrame()
        
        df = pd.read_parquet(file_path)
        
        # 日期筛选
        if 'date' in df.columns:
            if start is not None:
                df = df[df['date'] >= start]
            if end is not None:
                df = df[df['date'] <= end]
        
        return df
    
    def delete(self, symbol: str, exchange: str) -> bool:
        """
        删除基本面数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            
        Returns:
            是否成功删除
        """
        file_path = self.root / "fundamentals" / exchange / symbol / "daily.parquet"
        
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def exists(self, symbol: str, exchange: str) -> bool:
        """
        检查数据是否存在
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            
        Returns:
            是否存在
        """
        file_path = self.root / "fundamentals" / exchange / symbol / "daily.parquet"
        return file_path.exists()
    
    # ========== 向后兼容方法（使用原有名称）==========
    def save_fundamentals(self, symbol: str, exchange: str, df: pd.DataFrame) -> int:
        """向后兼容：保存基本面数据"""
        return self.save(symbol, exchange, df)
    
    def load_fundamentals(self, symbol: str, exchange: str,
                         start: Optional[pd.Timestamp] = None,
                         end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """向后兼容：加载基本面数据"""
        return self.load(symbol, exchange, start, end)
    
    def save_financials(self, symbol: str, exchange: str,
                       report_type: str, df: pd.DataFrame) -> int:
        """
        向后兼容：保存财务数据
        
        注意：这是为了保持与旧接口的兼容性
        实际应该使用 FinancialStore
        """
        # 财务数据实际应该使用 FinancialStore
        # 这里只是为了向后兼容
        path = self.root / "financials" / exchange / symbol
        path.mkdir(parents=True, exist_ok=True)
        
        file_path = path / f"{report_type}.parquet"
        
        # 与现有数据合并（按 report_date 去重）
        if file_path.exists():
            old_df = pd.read_parquet(file_path)
            df = pd.concat([old_df, df]).drop_duplicates(
                subset=['report_date'], keep='last'
            ).sort_values('report_date')
        
        df.to_parquet(file_path, index=False, compression=self.config.compression)
        return len(df)
    
    def load_financials(self, symbol: str, exchange: str,
                       report_type: str,
                       start: Optional[pd.Timestamp] = None,
                       end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        向后兼容：加载财务数据
        
        注意：这是为了保持与旧接口的兼容性
        实际应该使用 FinancialStore
        """
        file_path = self.root / "financials" / exchange / symbol / f"{report_type}.parquet"
        
        if not file_path.exists():
            return pd.DataFrame()
        
        df = pd.read_parquet(file_path)
        
        # 日期筛选
        if 'report_date' in df.columns:
            if start is not None:
                df = df[df['report_date'] >= start]
            if end is not None:
                df = df[df['report_date'] <= end]
        
        return df

