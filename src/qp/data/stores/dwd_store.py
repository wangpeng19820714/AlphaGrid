# qp/data/stores/dwd_store.py
"""DWD层 - 明细数据存储模块"""
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
class DWDBarData:
    """DWD层规整K线数据"""
    symbol: str
    exchange: Exchange
    interval: Interval
    datetime: pd.Timestamp
    
    # 规整价格数据
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    
    # 规整成交量数据
    volume: float
    turnover: float
    amount: float          # 成交额
    vwap: float           # 成交量加权平均价
    
    # 数据质量信息
    is_valid: bool           # 数据是否有效
    quality_issues: List[str]  # 质量问题列表
    processed_at: datetime   # 处理时间


@dataclass
class DWDFinancialData:
    """DWD层规整财务数据"""
    symbol: str
    exchange: Exchange
    report_date: pd.Timestamp
    report_type: str
    
    # 规整财务指标
    total_revenue: float
    net_profit: float
    total_assets: float
    total_liabilities: float
    shareholders_equity: float
    
    # 计算字段
    revenue_growth: float     # 营收增长率
    profit_growth: float      # 利润增长率
    roe: float               # 净资产收益率
    roa: float               # 总资产收益率
    
    # 数据质量
    is_valid: bool
    quality_issues: List[str]
    processed_at: datetime


@dataclass
class DWDFundamentalData:
    """DWD层规整基本面数据"""
    symbol: str
    exchange: Exchange
    date: pd.Timestamp
    
    # 规整基本面指标
    pe_ratio: float           # 市盈率
    pb_ratio: float           # 市净率
    ps_ratio: float           # 市销率
    market_cap: float         # 市值
    circulating_cap: float    # 流通市值
    
    # 数据质量
    is_valid: bool
    quality_issues: List[str]
    processed_at: datetime


class DWDStore(BaseStore):
    """DWD层数据存储 - 规整K线数据存储"""
    
    def __init__(self, config: StoreConfig = None):
        if config is None:
            config = StoreConfig(root="data/dwd")
        super().__init__(config)
    
    def _prepare_bar_dataframe(self, bars: List[DWDBarData]) -> pd.DataFrame:
        """准备规整K线数据DataFrame"""
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
            'amount': bar.amount,
            'vwap': bar.vwap,
            'is_valid': bar.is_valid,
            'quality_issues': str(bar.quality_issues),
            'processed_at': bar.processed_at
        } for bar in bars])
        
        # 按年月分区
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        
        return df.sort_values('datetime')
    
    def _prepare_financial_dataframe(self, financial_data: List[DWDFinancialData]) -> pd.DataFrame:
        """准备规整财务数据DataFrame"""
        if not financial_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': data.symbol,
            'exchange': data.exchange.value if hasattr(data.exchange, 'value') else str(data.exchange),
            'report_date': data.report_date,
            'report_type': data.report_type,
            'total_revenue': data.total_revenue,
            'net_profit': data.net_profit,
            'total_assets': data.total_assets,
            'total_liabilities': data.total_liabilities,
            'shareholders_equity': data.shareholders_equity,
            'revenue_growth': data.revenue_growth,
            'profit_growth': data.profit_growth,
            'roe': data.roe,
            'roa': data.roa,
            'is_valid': data.is_valid,
            'quality_issues': str(data.quality_issues),
            'processed_at': data.processed_at
        } for data in financial_data])
        
        # 按年分区
        df['year'] = df['report_date'].dt.year
        
        return df.sort_values('report_date')
    
    def load_fundamental(self, exchange: str, symbol: str,
                        start_date: Optional[pd.Timestamp] = None,
                        end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载规整基本面数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            规整基本面数据DataFrame
        """
        store_path = self.root / "fundamental" / exchange / f"{symbol}.parquet"
        
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
    
    def _prepare_fundamental_dataframe(self, fundamental_data: List[DWDFundamentalData]) -> pd.DataFrame:
        """准备基本面数据DataFrame"""
        if not fundamental_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': data.symbol,
            'exchange': data.exchange.value if hasattr(data.exchange, 'value') else str(data.exchange),
            'date': data.date,
            'pe_ratio': data.pe_ratio,
            'pb_ratio': data.pb_ratio,
            'ps_ratio': data.ps_ratio,
            'market_cap': data.market_cap,
            'circulating_cap': data.circulating_cap,
            'is_valid': data.is_valid,
            'quality_issues': str(data.quality_issues),
            'processed_at': data.processed_at
        } for data in fundamental_data])
        
        return df.sort_values('date')
    
    def _merge_with_existing_fundamental(self, file_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有基本面文件合并"""
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["date"], keep="last").sort_values("date")
    
    def save_bars(self, bars: List[DWDBarData]) -> int:
        """
        保存规整K线数据
        
        Args:
            bars: DWD层K线数据列表
            
        Returns:
            保存的记录数
        """
        if not bars:
            return 0
        
        df = self._prepare_bar_dataframe(bars)
        
        # 按市场/代码/周期分组
        count = 0
        for (exchange, symbol, interval), group_df in df.groupby(['exchange', 'symbol', 'interval']):
            # 构建存储路径: data/dwd/bars/{exchange}/{symbol}/{interval}/
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
    
    def save_financial(self, financial_data: List[DWDFinancialData]) -> int:
        """
        保存规整财务数据
        
        Args:
            financial_data: DWD层财务数据列表
            
        Returns:
            保存的记录数
        """
        if not financial_data:
            return 0
        
        df = self._prepare_financial_dataframe(financial_data)
        
        # 按市场/代码分组
        count = 0
        for (exchange, symbol), group_df in df.groupby(['exchange', 'symbol']):
            # 构建存储路径: data/dwd/financial/{exchange}/{symbol}/
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
    
    def save_financial_by_symbol(self, financial_data: List[DWDFinancialData], symbol: str, exchange: str) -> int:
        """
        按股票代码保存规整财务数据
        
        Args:
            financial_data: DWD层财务数据列表
            symbol: 股票代码
            exchange: 交易所代码
            
        Returns:
            保存的记录数
        """
        if not financial_data:
            return 0
        
        df = self._prepare_financial_dataframe(financial_data)
        
        # 构建存储路径: data/dwd/financial/{exchange}/{symbol}.parquet
        store_path = self.root / "financial" / exchange
        store_path.mkdir(parents=True, exist_ok=True)
        
        partition_path = store_path / f"{symbol}.parquet"
        
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
    
    def save_fundamental_by_symbol(self, fundamental_data: List[DWDFundamentalData], symbol: str, exchange: str) -> int:
        """
        按股票代码保存规整基本面数据
        
        Args:
            fundamental_data: DWD层基本面数据列表
            symbol: 股票代码
            exchange: 交易所代码
            
        Returns:
            保存的记录数
        """
        if not fundamental_data:
            return 0
        
        df = self._prepare_fundamental_dataframe(fundamental_data)
        
        # 构建存储路径: data/dwd/fundamental/{exchange}/{symbol}.parquet
        store_path = self.root / "fundamental" / exchange
        store_path.mkdir(parents=True, exist_ok=True)
        
        partition_path = store_path / f"{symbol}.parquet"
        
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
    
    def load_bars(self, exchange: str, symbol: str, interval: str,
                  start_date: Optional[pd.Timestamp] = None,
                  end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载规整K线数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            规整K线数据DataFrame
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
        加载规整财务数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            规整财务数据DataFrame
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
    
    def _merge_with_existing_financial(self, file_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有财务文件合并"""
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["report_date"], keep="last").sort_values("report_date")


class DWDProcessor:
    """DWD层数据处理器"""
    
    def __init__(self, dwd_store: DWDStore):
        self.dwd_store = dwd_store
    
    def process_bars_from_ods(self, ods_df: pd.DataFrame) -> List[DWDBarData]:
        """
        从ODS层数据处理规整K线数据
        
        Args:
            ods_df: ODS层原始K线数据
            
        Returns:
            规整K线数据列表
        """
        processed_bars = []
        
        for _, row in ods_df.iterrows():
            # 数据验证
            quality_issues = self._validate_bar_data(row)
            
            # 计算VWAP
            vwap = self._calculate_vwap(row)
            
            # 计算成交额
            amount = self._calculate_amount(row)
            
            # 创建规整数据
            dwd_bar = DWDBarData(
                symbol=row['symbol'],
                exchange=Exchange(row['exchange']),
                interval=Interval(row['interval']),
                datetime=row['datetime'],
                open_price=row['open'],
                high_price=row['high'],
                low_price=row['low'],
                close_price=row['close'],
                volume=row['volume'],
                turnover=row['turnover'],
                amount=amount,
                vwap=vwap,
                is_valid=len(quality_issues) == 0,
                quality_issues=quality_issues,
                processed_at=datetime.now()
            )
            
            processed_bars.append(dwd_bar)
        
        return processed_bars
    
    def _validate_bar_data(self, row: pd.Series) -> List[str]:
        """验证K线数据质量"""
        issues = []
        
        # 价格关系检查
        if not (row['low'] <= row['open'] <= row['high']):
            issues.append("价格关系异常")
        
        if not (row['low'] <= row['close'] <= row['high']):
            issues.append("价格关系异常")
        
        # 成交量检查
        if row['volume'] < 0:
            issues.append("成交量异常")
        
        # 成交额检查
        if row['turnover'] < 0:
            issues.append("成交额异常")
        
        return issues
    
    def _calculate_vwap(self, row: pd.Series) -> float:
        """计算成交量加权平均价"""
        if row['volume'] == 0:
            return row['close']
        
        # 简化计算：使用OHLC平均价
        avg_price = (row['open'] + row['high'] + row['low'] + row['close']) / 4
        return avg_price
    
    def _calculate_amount(self, row: pd.Series) -> float:
        """计算成交额"""
        return row['volume'] * row['close']


def create_dwd_bar_from_ods_bar(ods_bar: 'ODSBarData') -> DWDBarData:
    """从ODSBarData创建DWDBarData"""
    processor = DWDProcessor(None)
    
    # 创建临时DataFrame进行处理
    temp_df = pd.DataFrame([{
        'symbol': ods_bar.symbol,
        'exchange': ods_bar.exchange.value if hasattr(ods_bar.exchange, 'value') else str(ods_bar.exchange),
        'interval': ods_bar.interval.value if hasattr(ods_bar.interval, 'value') else str(ods_bar.interval),
        'datetime': ods_bar.datetime,
        'open': ods_bar.open_price,
        'high': ods_bar.high_price,
        'low': ods_bar.low_price,
        'close': ods_bar.close_price,
        'volume': ods_bar.volume,
        'turnover': ods_bar.turnover
    }])
    
    processed_bars = processor.process_bars_from_ods(temp_df)
    return processed_bars[0] if processed_bars else None
