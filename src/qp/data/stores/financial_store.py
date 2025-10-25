# qp/stores/financial_store.py
"""财务数据存储模块"""
from __future__ import annotations
from pathlib import Path
from typing import Optional
import pandas as pd

from .base import StoreConfig, BaseStore, _normalize_path


class FinancialStore(BaseStore):
    """
    财务数据存储
    
    - 按报表类型分文件存储
    - 按report_date去重
    - 支持增量更新
    """
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
    
    def save(self, symbol: str, exchange: str, 
             report_type: str, df: pd.DataFrame) -> int:
        """
        保存财务数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型（balance_sheet/income/cashflow/indicator）
            df: 财务数据DataFrame
            
        Returns:
            保存的记录数
            
        目录结构: {root}/financials/{exchange}/{symbol}/{report_type}.parquet
        """
        if df.empty:
            return 0
        
        path = self.root / "financials" / exchange / symbol
        path.mkdir(parents=True, exist_ok=True)
        
        file_path = path / f"{report_type}.parquet"
        
        # 与现有数据合并（按 report_date 去重）
        df = self._merge_with_existing(file_path, df, unique_cols=['report_date'])
        
        df.to_parquet(file_path, index=False, compression=self.config.compression)
        return len(df)
    
    def load(self, symbol: str, exchange: str,
             report_type: str,
             start: Optional[pd.Timestamp] = None,
             end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载财务数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型
            start: 开始报告期
            end: 结束报告期
            
        Returns:
            财务数据DataFrame
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
    
    def delete(self, symbol: str, exchange: str, report_type: str) -> bool:
        """
        删除财务数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型
            
        Returns:
            是否成功删除
        """
        file_path = self.root / "financials" / exchange / symbol / f"{report_type}.parquet"
        
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def exists(self, symbol: str, exchange: str, report_type: str) -> bool:
        """
        检查数据是否存在
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            report_type: 报表类型
            
        Returns:
            是否存在
        """
        file_path = self.root / "financials" / exchange / symbol / f"{report_type}.parquet"
        return file_path.exists()


# 向后兼容别名（如果原来有这个函数名的话）
def save_financials(store: FinancialStore, symbol: str, exchange: str,
                   report_type: str, df: pd.DataFrame) -> int:
    """向后兼容的保存函数"""
    return store.save(symbol, exchange, report_type, df)


def load_financials(store: FinancialStore, symbol: str, exchange: str,
                   report_type: str,
                   start: Optional[pd.Timestamp] = None,
                   end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
    """向后兼容的加载函数"""
    return store.load(symbol, exchange, report_type, start, end)

