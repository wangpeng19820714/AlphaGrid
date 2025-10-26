# qp/data/stores/ods_store.py
"""ODS层 - 原始数据存储模块"""
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime

from .base import (
    StoreConfig, BaseStore, ManifestIndex,
    _normalize_path, _get_year, _get_partition_dir,
    _get_partition_file, TEMP_SUFFIX
)
from ..types.bar import BarData
from ..types.common import Exchange, Interval


@dataclass
class ODSBarData:
    """ODS层原始K线数据"""
    symbol: str
    exchange: Exchange
    interval: Interval
    datetime: pd.Timestamp
    
    # 原始价格数据
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    
    # 原始成交量数据
    volume: float
    turnover: float
    
    # 原始数据元信息
    source: str                    # 数据源
    raw_data: Dict[str, Any]      # 原始数据字段
    quality_score: float          # 数据质量分数
    created_at: datetime          # 创建时间
    updated_at: datetime          # 更新时间


@dataclass
class ODSFinancialData:
    """ODS层原始财务数据"""
    symbol: str
    exchange: Exchange
    report_date: pd.Timestamp
    report_type: str              # 年报、中报、季报
    
    # 原始财务数据
    raw_income: Dict[str, float]     # 利润表原始数据
    raw_balance: Dict[str, float]    # 资产负债表原始数据
    raw_cashflow: Dict[str, float]   # 现金流量表原始数据
    
    # 元信息
    source: str
    quality_score: float
    created_at: datetime
    updated_at: datetime


@dataclass
class ODSFundamentalData:
    """ODS层原始基本面数据"""
    symbol: str
    exchange: Exchange
    date: pd.Timestamp
    
    # 原始基本面数据
    raw_data: Dict[str, Any]      # 原始基本面数据字段
    
    # 元信息
    source: str
    quality_score: float
    created_at: datetime
    updated_at: datetime


class ODSStore(BaseStore):
    """ODS层数据存储 - 原始数据分区化存储"""
    
    def __init__(self, config: StoreConfig = None):
        if config is None:
            config = StoreConfig(root="data/ods")
        super().__init__(config)
    
    def _prepare_bar_dataframe(self, bars: List[ODSBarData]) -> pd.DataFrame:
        """准备K线数据DataFrame"""
        if not bars:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': bar.symbol,
            'exchange': bar.exchange.value if hasattr(bar.exchange, 'value') else str(bar.exchange),
            'interval': bar.interval.value if hasattr(bar.interval, 'value') else str(bar.interval),
            'datetime': bar.datetime,
            'open': bar.open_price,
            'high': bar.high_price,
            'low': bar.low_price,
            'close': bar.close_price,
            'volume': bar.volume,
            'turnover': bar.turnover,
            'source': bar.source,
            'raw_data': str(bar.raw_data),
            'quality_score': bar.quality_score,
            'created_at': bar.created_at,
            'updated_at': bar.updated_at
        } for bar in bars])
        
        # 按年月分区
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        
        return df.sort_values('datetime')
    
    def _prepare_financial_dataframe(self, financial_data: List[ODSFinancialData]) -> pd.DataFrame:
        """准备财务数据DataFrame"""
        if not financial_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': data.symbol,
            'exchange': data.exchange.value if hasattr(data.exchange, 'value') else str(data.exchange),
            'report_date': data.report_date,
            'report_type': data.report_type,
            'raw_income': str(data.raw_income),
            'raw_balance': str(data.raw_balance),
            'raw_cashflow': str(data.raw_cashflow),
            'source': data.source,
            'quality_score': data.quality_score,
            'created_at': data.created_at,
            'updated_at': data.updated_at
        } for data in financial_data])
        
        # 按年分区
        df['year'] = df['report_date'].dt.year
        
        return df.sort_values('report_date')
    
    def save_bars(self, bars: List[ODSBarData]) -> int:
        """
        保存原始K线数据
        
        Args:
            bars: ODS层K线数据列表
            
        Returns:
            保存的记录数
        """
        if not bars:
            return 0
        
        df = self._prepare_bar_dataframe(bars)
        
        # 按市场/代码/周期分组
        count = 0
        for (exchange, symbol, interval), group_df in df.groupby(['exchange', 'symbol', 'interval']):
            # 构建存储路径: data/ods/bars/{exchange}/{symbol}/{interval}/
            store_path = self.root / "bars" / exchange / symbol / interval
            store_path.mkdir(parents=True, exist_ok=True)
            
            # 按年月分区存储
            for (year, month), month_df in group_df.groupby(['year', 'month']):
                partition_path = store_path / str(year) / f"{year}{month:02d}.parquet"
                partition_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 与现有数据合并
                final_df = self._merge_with_existing_bar(partition_path, month_df.drop(['year', 'month'], axis=1))
                
                # 写入Parquet文件
                table = pa.Table.from_pandas(final_df, preserve_index=False)
                pq.write_table(
                    table, partition_path,
                    compression=self.config.compression,
                    use_dictionary=self.config.use_dictionary
                )
                
                count += len(month_df)
        
        return count
    
    def save_financial(self, financial_data: List[ODSFinancialData]) -> int:
        """
        保存原始财务数据
        
        Args:
            financial_data: ODS层财务数据列表
            
        Returns:
            保存的记录数
        """
        if not financial_data:
            return 0
        
        df = self._prepare_financial_dataframe(financial_data)
        
        # 按市场/代码分组
        count = 0
        for (exchange, symbol), group_df in df.groupby(['exchange', 'symbol']):
            # 构建存储路径: data/ods/financial/{exchange}/{symbol}/
            store_path = self.root / "financial" / exchange / symbol
            store_path.mkdir(parents=True, exist_ok=True)
            
            # 按年分区存储
            for year, year_df in group_df.groupby('year'):
                partition_path = store_path / f"{year}.parquet"
                
                # 与现有数据合并
                final_df = self._merge_with_existing_financial(partition_path, year_df.drop(['year'], axis=1))
                
                # 写入Parquet文件
                table = pa.Table.from_pandas(final_df, preserve_index=False)
                pq.write_table(
                    table, partition_path,
                    compression=self.config.compression,
                    use_dictionary=self.config.use_dictionary
                )
                
                count += len(year_df)
        
        return count
    
    def load_bars(self, exchange: str, symbol: str, interval: str,
                  start_date: Optional[pd.Timestamp] = None,
                  end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载原始K线数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            原始K线数据DataFrame
        """
        store_path = self.root / "bars" / exchange / symbol / interval
        
        if not store_path.exists():
            return pd.DataFrame()
        
        # 读取所有分区文件
        data_files = []
        for year_dir in store_path.iterdir():
            if year_dir.is_dir():
                for month_file in year_dir.glob("*.parquet"):
                    data_files.append(month_file)
        
        if not data_files:
            return pd.DataFrame()
        
        # 合并数据
        dfs = []
        for file_path in data_files:
            df = pd.read_parquet(file_path)
            dfs.append(df)
        
        result_df = pd.concat(dfs, ignore_index=True)
        result_df['datetime'] = pd.to_datetime(result_df['datetime'])
        
        # 时间过滤
        if start_date:
            result_df = result_df[result_df['datetime'] >= start_date]
        if end_date:
            result_df = result_df[result_df['datetime'] <= end_date]
        
        return result_df.sort_values('datetime')
    
    def load_financial(self, exchange: str, symbol: str,
                      start_date: Optional[pd.Timestamp] = None,
                      end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载原始财务数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            原始财务数据DataFrame
        """
        store_path = self.root / "financial" / exchange / symbol
        
        if not store_path.exists():
            return pd.DataFrame()
        
        # 读取所有分区文件
        data_files = list(store_path.glob("*.parquet"))
        
        if not data_files:
            return pd.DataFrame()
        
        # 合并数据
        dfs = []
        for file_path in data_files:
            df = pd.read_parquet(file_path)
            dfs.append(df)
        
        result_df = pd.concat(dfs, ignore_index=True)
        result_df['report_date'] = pd.to_datetime(result_df['report_date'])
        
        # 时间过滤
        if start_date:
            result_df = result_df[result_df['report_date'] >= start_date]
        if end_date:
            result_df = result_df[result_df['report_date'] <= end_date]
        
        return result_df.sort_values('report_date')
    
    def _merge_with_existing_bar(self, file_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有K线文件合并"""
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["datetime"], keep="last").sort_values("datetime")
    
    def save_financial_by_type(self, financial_data: List[ODSFinancialData], 
                              symbol: str, exchange: str, report_type: str) -> int:
        """
        按报表类型保存原始财务数据
        
        Args:
            financial_data: ODS层财务数据列表
            symbol: 股票代码
            exchange: 交易所代码
            report_type: 报表类型（balance_sheet/income/cashflow/indicator）
            
        Returns:
            保存的记录数
        """
        if not financial_data:
            return 0
        
        df = self._prepare_financial_dataframe(financial_data)
        
        # 构建存储路径: data/ods/financial/{exchange}/{symbol}/{report_type}.parquet
        store_path = self.root / "financial" / exchange / symbol
        store_path.mkdir(parents=True, exist_ok=True)
        
        partition_path = store_path / f"{report_type}.parquet"
        
        # 与现有数据合并
        final_df = self._merge_with_existing_financial(partition_path, df)
        
        # 写入Parquet文件
        table = pa.Table.from_pandas(final_df, preserve_index=False)
        pq.write_table(
            table, partition_path,
            compression=self.config.compression,
            use_dictionary=self.config.use_dictionary
        )
        
        return len(df)
    
    def load_financial_by_type(self, exchange: str, symbol: str, report_type: str,
                              start_date: Optional[pd.Timestamp] = None,
                              end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        按报表类型加载原始财务数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            report_type: 报表类型
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            原始财务数据DataFrame
        """
        store_path = self.root / "financial" / exchange / symbol / f"{report_type}.parquet"
        
        if not store_path.exists():
            return pd.DataFrame()
        
        df = pd.read_parquet(store_path)
        df['report_date'] = pd.to_datetime(df['report_date'])
        
        # 时间过滤
        if start_date:
            df = df[df['report_date'] >= start_date]
        if end_date:
            df = df[df['report_date'] <= end_date]
        
        return df.sort_values('report_date')
    
    def save_fundamental(self, fundamental_data: List[ODSFundamentalData], 
                       symbol: str, exchange: str) -> int:
        """
        保存原始基本面数据
        
        Args:
            fundamental_data: ODS层基本面数据列表
            symbol: 股票代码
            exchange: 交易所代码
            
        Returns:
            保存的记录数
        """
        if not fundamental_data:
            return 0
        
        df = self._prepare_fundamental_dataframe(fundamental_data)
        
        # 构建存储路径: data/ods/fundamental/{exchange}/{symbol}/daily.parquet
        store_path = self.root / "fundamental" / exchange / symbol
        store_path.mkdir(parents=True, exist_ok=True)
        
        partition_path = store_path / "daily.parquet"
        
        # 与现有数据合并
        final_df = self._merge_with_existing_fundamental(partition_path, df)
        
        # 写入Parquet文件
        table = pa.Table.from_pandas(final_df, preserve_index=False)
        pq.write_table(
            table, partition_path,
            compression=self.config.compression,
            use_dictionary=self.config.use_dictionary
        )
        
        return len(df)
    
    def load_fundamental(self, exchange: str, symbol: str,
                        start_date: Optional[pd.Timestamp] = None,
                        end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载原始基本面数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            原始基本面数据DataFrame
        """
        store_path = self.root / "fundamental" / exchange / symbol / "daily.parquet"
        
        if not store_path.exists():
            return pd.DataFrame()
        
        df = pd.read_parquet(store_path)
        df['date'] = pd.to_datetime(df['date'])
        
        # 时间过滤
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]
        
        return df.sort_values('date')
    
    def _prepare_financial_dataframe(self, financial_data: List[ODSFinancialData]) -> pd.DataFrame:
        """准备财务数据DataFrame"""
        if not financial_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': data.symbol,
            'exchange': data.exchange.value if hasattr(data.exchange, 'value') else str(data.exchange),
            'report_date': data.report_date,
            'report_type': data.report_type,
            'raw_income': str(data.raw_income),
            'raw_balance': str(data.raw_balance),
            'raw_cashflow': str(data.raw_cashflow),
            'source': data.source,
            'quality_score': data.quality_score,
            'created_at': data.created_at,
            'updated_at': data.updated_at
        } for data in financial_data])
        
        return df.sort_values('report_date')
    
    def _prepare_fundamental_dataframe(self, fundamental_data: List[ODSFundamentalData]) -> pd.DataFrame:
        """准备基本面数据DataFrame"""
        if not fundamental_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': data.symbol,
            'exchange': data.exchange.value if hasattr(data.exchange, 'value') else str(data.exchange),
            'date': data.date,
            'raw_data': str(data.raw_data),
            'source': data.source,
            'quality_score': data.quality_score,
            'created_at': data.created_at,
            'updated_at': data.updated_at
        } for data in fundamental_data])
        
        return df.sort_values('date')
    
    def _merge_with_existing_financial(self, file_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有财务文件合并"""
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["report_date"], keep="last").sort_values("report_date")
    
    def _merge_with_existing_fundamental(self, file_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有基本面文件合并"""
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["date"], keep="last").sort_values("date")


def create_ods_bar_from_bar_data(bar_data: BarData, source: str = "unknown", 
                                quality_score: float = 1.0) -> ODSBarData:
    """从BarData创建ODSBarData"""
    return ODSBarData(
        symbol=bar_data.symbol,
        exchange=bar_data.exchange,
        interval=bar_data.interval,
        datetime=bar_data.datetime,
        open_price=bar_data.open_price,
        high_price=bar_data.high_price,
        low_price=bar_data.low_price,
        close_price=bar_data.close_price,
        volume=bar_data.volume,
        turnover=bar_data.turnover,
        source=source,
        raw_data={},
        quality_score=quality_score,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
