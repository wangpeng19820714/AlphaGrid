# qp/data/stores/dws_store.py
"""DWS层 - 汇总数据存储模块"""
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
class DWSAdjustedData:
    """DWS层复权价格数据"""
    symbol: str
    exchange: Exchange
    interval: Interval
    datetime: pd.Timestamp
    
    # 复权价格
    open_qfq: float          # 前复权开盘价
    high_qfq: float          # 前复权最高价
    low_qfq: float           # 前复权最低价
    close_qfq: float         # 前复权收盘价
    
    open_hfq: float          # 后复权开盘价
    high_hfq: float          # 后复权最高价
    low_hfq: float           # 后复权最低价
    close_hfq: float         # 后复权收盘价
    
    # 复权因子
    qfq_factor: float        # 前复权因子
    hfq_factor: float        # 后复权因子
    
    # 元信息
    adjusted_at: datetime
    source_dwd: str


@dataclass
class DWSFactorData:
    """DWS层资金因子数据"""
    symbol: str
    exchange: Exchange
    datetime: pd.Timestamp
    
    # 资金流向因子
    net_inflow: float         # 净流入
    main_inflow: float        # 主力流入
    retail_inflow: float      # 散户流入
    
    # 成交量因子
    volume_ratio: float       # 成交量比
    price_volume_ratio: float # 价量比
    
    # 价格动量因子
    price_momentum_5d: float  # 5日价格动量
    price_momentum_20d: float # 20日价格动量
    
    # 元信息
    calculated_at: datetime
    source_dwd: str


@dataclass
class DWSMergedFinancialData:
    """DWS层财务合并表"""
    symbol: str
    exchange: Exchange
    report_date: pd.Timestamp
    
    # 财务比率
    pe_ratio: float           # 市盈率
    pb_ratio: float           # 市净率
    ps_ratio: float           # 市销率
    pcf_ratio: float          # 市现率
    
    # 成长指标
    revenue_growth_yoy: float # 营收同比增长
    profit_growth_yoy: float  # 利润同比增长
    
    # 盈利能力
    roe: float               # 净资产收益率
    roa: float               # 总资产收益率
    gross_margin: float       # 毛利率
    net_margin: float         # 净利率
    
    # 元信息
    merged_at: datetime
    source_dwd: str


class DWSStore(BaseStore):
    """DWS层数据存储 - 复权价、资金因子、财务合并表"""
    
    def __init__(self, config: StoreConfig = None):
        if config is None:
            config = StoreConfig(root="data/dws")
        super().__init__(config)
    
    def save_adjusted_data(self, adjusted_data: List[DWSAdjustedData]) -> int:
        """
        保存复权价格数据
        
        Args:
            adjusted_data: DWS层复权价格数据列表
            
        Returns:
            保存的记录数
        """
        if not adjusted_data:
            return 0
        
        df = self._prepare_adjusted_dataframe(adjusted_data)
        
        # 按市场/代码/周期分组
        count = 0
        for (exchange, symbol, interval), group_df in df.groupby(['exchange', 'symbol', 'interval']):
            # 构建存储路径: data/dws/adjusted/{exchange}/{symbol}/{interval}/
            store_path = self.root / "adjusted" / exchange / symbol / interval
            store_path.mkdir(parents=True, exist_ok=True)
            
            # 按年月分区存储
            for (year, month), month_df in group_df.groupby(['year', 'month']):
                partition_path = store_path / str(year) / f"{year}{month:02d}.parquet"
                partition_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 与现有数据合并
                final_df = self._merge_with_existing_adjusted(partition_path, month_df.drop(['year', 'month'], axis=1))
                
                # 写入Parquet文件
                table = pa.Table.from_pandas(final_df, preserve_index=False)
                pq.write_table(
                    table, partition_path,
                    compression=self.config.compression,
                    use_dictionary=self.config.use_dictionary
                )
                
                count += len(month_df)
        
        return count
    
    def save_factor_data(self, factor_data: List[DWSFactorData]) -> int:
        """
        保存资金因子数据
        
        Args:
            factor_data: DWS层资金因子数据列表
            
        Returns:
            保存的记录数
        """
        if not factor_data:
            return 0
        
        df = self._prepare_factor_dataframe(factor_data)
        
        # 按市场/代码分组
        count = 0
        for (exchange, symbol), group_df in df.groupby(['exchange', 'symbol']):
            # 构建存储路径: data/dws/factors/{exchange}/{symbol}/
            store_path = self.root / "factors" / exchange / symbol
            store_path.mkdir(parents=True, exist_ok=True)
            
            # 按年月分区存储
            for (year, month), month_df in group_df.groupby(['year', 'month']):
                partition_path = store_path / str(year) / f"{year}{month:02d}.parquet"
                partition_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 与现有数据合并
                final_df = self._merge_with_existing_factor(partition_path, month_df.drop(['year', 'month'], axis=1))
                
                # 写入Parquet文件
                table = pa.Table.from_pandas(final_df, preserve_index=False)
                pq.write_table(
                    table, partition_path,
                    compression=self.config.compression,
                    use_dictionary=self.config.use_dictionary
                )
                
                count += len(month_df)
        
        return count
    
    def save_merged_financial_data(self, merged_data: List[DWSMergedFinancialData]) -> int:
        """
        保存财务合并表数据
        
        Args:
            merged_data: DWS层财务合并表数据列表
            
        Returns:
            保存的记录数
        """
        if not merged_data:
            return 0
        
        df = self._prepare_merged_financial_dataframe(merged_data)
        
        # 按市场/代码分组
        count = 0
        for (exchange, symbol), group_df in df.groupby(['exchange', 'symbol']):
            # 构建存储路径: data/dws/merged/{exchange}/{symbol}/
            store_path = self.root / "merged" / exchange / symbol
            store_path.mkdir(parents=True, exist_ok=True)
            
            # 按年分区存储
            for year, year_df in group_df.groupby('year'):
                partition_path = store_path / f"{year}.parquet"
                
                # 与现有数据合并
                final_df = self._merge_with_existing_merged_financial(partition_path, year_df.drop(['year'], axis=1))
                
                # 写入Parquet文件
                table = pa.Table.from_pandas(final_df, preserve_index=False)
                pq.write_table(
                    table, partition_path,
                    compression=self.config.compression,
                    use_dictionary=self.config.use_dictionary
                )
                
                count += len(year_df)
        
        return count
    
    def load_adjusted_data(self, exchange: str, symbol: str, interval: str,
                          adjustment_type: str = 'qfq',
                          start_date: Optional[pd.Timestamp] = None,
                          end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载复权价格数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            adjustment_type: 复权类型 ('qfq' 或 'hfq')
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            复权价格数据DataFrame
        """
        store_path = self.root / "adjusted" / exchange / symbol / interval
        
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
    
    def load_factor_data(self, exchange: str, symbol: str,
                        start_date: Optional[pd.Timestamp] = None,
                        end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载资金因子数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            资金因子数据DataFrame
        """
        store_path = self.root / "factors" / exchange / symbol
        
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
    
    def load_merged_financial_data(self, exchange: str, symbol: str,
                                  start_date: Optional[pd.Timestamp] = None,
                                  end_date: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """
        加载财务合并表数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            财务合并表数据DataFrame
        """
        store_path = self.root / "merged" / exchange / symbol
        
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
    
    def _prepare_adjusted_dataframe(self, adjusted_data: List[DWSAdjustedData]) -> pd.DataFrame:
        """准备复权价格数据DataFrame"""
        if not adjusted_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': data.symbol,
            'exchange': data.exchange.value if hasattr(data.exchange, 'value') else str(data.exchange),
            'interval': data.interval.value if hasattr(data.interval, 'value') else str(data.interval),
            'datetime': data.datetime,
            'open_qfq': data.open_qfq,
            'high_qfq': data.high_qfq,
            'low_qfq': data.low_qfq,
            'close_qfq': data.close_qfq,
            'open_hfq': data.open_hfq,
            'high_hfq': data.high_hfq,
            'low_hfq': data.low_hfq,
            'close_hfq': data.close_hfq,
            'qfq_factor': data.qfq_factor,
            'hfq_factor': data.hfq_factor,
            'adjusted_at': data.adjusted_at,
            'source_dwd': data.source_dwd
        } for data in adjusted_data])
        
        # 按年月分区
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        
        return df.sort_values('datetime')
    
    def _prepare_factor_dataframe(self, factor_data: List[DWSFactorData]) -> pd.DataFrame:
        """准备资金因子数据DataFrame"""
        if not factor_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': data.symbol,
            'exchange': data.exchange.value if hasattr(data.exchange, 'value') else str(data.exchange),
            'datetime': data.datetime,
            'net_inflow': data.net_inflow,
            'main_inflow': data.main_inflow,
            'retail_inflow': data.retail_inflow,
            'volume_ratio': data.volume_ratio,
            'price_volume_ratio': data.price_volume_ratio,
            'price_momentum_5d': data.price_momentum_5d,
            'price_momentum_20d': data.price_momentum_20d,
            'calculated_at': data.calculated_at,
            'source_dwd': data.source_dwd
        } for data in factor_data])
        
        # 按年月分区
        df['year'] = df['datetime'].dt.year
        df['month'] = df['datetime'].dt.month
        
        return df.sort_values('datetime')
    
    def _prepare_merged_financial_dataframe(self, merged_data: List[DWSMergedFinancialData]) -> pd.DataFrame:
        """准备财务合并表数据DataFrame"""
        if not merged_data:
            return pd.DataFrame()
        
        df = pd.DataFrame([{
            'symbol': data.symbol,
            'exchange': data.exchange.value if hasattr(data.exchange, 'value') else str(data.exchange),
            'report_date': data.report_date,
            'pe_ratio': data.pe_ratio,
            'pb_ratio': data.pb_ratio,
            'ps_ratio': data.ps_ratio,
            'pcf_ratio': data.pcf_ratio,
            'revenue_growth_yoy': data.revenue_growth_yoy,
            'profit_growth_yoy': data.profit_growth_yoy,
            'roe': data.roe,
            'roa': data.roa,
            'gross_margin': data.gross_margin,
            'net_margin': data.net_margin,
            'merged_at': data.merged_at,
            'source_dwd': data.source_dwd
        } for data in merged_data])
        
        # 按年分区
        df['year'] = df['report_date'].dt.year
        
        return df.sort_values('report_date')
    
    def _merge_with_existing_adjusted(self, file_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有复权文件合并"""
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["datetime"], keep="last").sort_values("datetime")
    
    def _merge_with_existing_factor(self, file_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有因子文件合并"""
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["datetime"], keep="last").sort_values("datetime")
    
    def _merge_with_existing_merged_financial(self, file_path: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有财务合并文件合并"""
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["report_date"], keep="last").sort_values("report_date")


class DWSProcessor:
    """DWS层数据处理器"""
    
    def __init__(self, dws_store: DWSStore):
        self.dws_store = dws_store
    
    def calculate_adjusted_prices(self, dwd_df: pd.DataFrame, 
                                adjustment_type: str = 'qfq') -> List[DWSAdjustedData]:
        """
        计算复权价格
        
        Args:
            dwd_df: DWD层规整K线数据
            adjustment_type: 复权类型 ('qfq' 或 'hfq')
            
        Returns:
            复权价格数据列表
        """
        if dwd_df.empty:
            return []
        
        adjusted_data = []
        
        for _, row in dwd_df.iterrows():
            # 计算复权因子（简化实现）
            qfq_factor, hfq_factor = self._calculate_adjustment_factors(row['datetime'])
            
            # 计算复权价格
            adjusted_bar = DWSAdjustedData(
                symbol=row['symbol'],
                exchange=Exchange(row['exchange']),
                interval=Interval(row['interval']),
                datetime=row['datetime'],
                open_qfq=row['open'] * qfq_factor,
                high_qfq=row['high'] * qfq_factor,
                low_qfq=row['low'] * qfq_factor,
                close_qfq=row['close'] * qfq_factor,
                open_hfq=row['open'] * hfq_factor,
                high_hfq=row['high'] * hfq_factor,
                low_hfq=row['low'] * hfq_factor,
                close_hfq=row['close'] * hfq_factor,
                qfq_factor=qfq_factor,
                hfq_factor=hfq_factor,
                adjusted_at=datetime.now(),
                source_dwd=f"dwd_bars_{row['symbol']}_{row['exchange']}_{row['interval']}"
            )
            
            adjusted_data.append(adjusted_bar)
        
        return adjusted_data
    
    def calculate_money_flow_factors(self, dwd_df: pd.DataFrame) -> List[DWSFactorData]:
        """
        计算资金流向因子
        
        Args:
            dwd_df: DWD层规整K线数据
            
        Returns:
            资金因子数据列表
        """
        if dwd_df.empty:
            return []
        
        factor_data = []
        
        for i, (_, row) in enumerate(dwd_df.iterrows()):
            # 计算净流入（简化计算）
            net_inflow = self._calculate_net_inflow(row, dwd_df, i)
            
            # 计算成交量比
            volume_ratio = self._calculate_volume_ratio(row, dwd_df, i)
            
            # 计算价格动量
            momentum_5d = self._calculate_price_momentum(row, dwd_df, i, 5)
            momentum_20d = self._calculate_price_momentum(row, dwd_df, i, 20)
            
            factor_bar = DWSFactorData(
                symbol=row['symbol'],
                exchange=Exchange(row['exchange']),
                datetime=row['datetime'],
                net_inflow=net_inflow,
                main_inflow=net_inflow * 0.7,  # 简化：主力占70%
                retail_inflow=net_inflow * 0.3,  # 简化：散户占30%
                volume_ratio=volume_ratio,
                price_volume_ratio=volume_ratio * momentum_5d,
                price_momentum_5d=momentum_5d,
                price_momentum_20d=momentum_20d,
                calculated_at=datetime.now(),
                source_dwd=f"dwd_bars_{row['symbol']}_{row['exchange']}_{row['interval']}"
            )
            
            factor_data.append(factor_bar)
        
        return factor_data
    
    def merge_financial_data(self, dwd_financial_df: pd.DataFrame) -> List[DWSMergedFinancialData]:
        """
        合并财务数据
        
        Args:
            dwd_financial_df: DWD层规整财务数据
            
        Returns:
            财务合并表数据列表
        """
        if dwd_financial_df.empty:
            return []
        
        merged_data = []
        
        for _, row in dwd_financial_df.iterrows():
            # 计算财务比率和指标
            merged_bar = DWSMergedFinancialData(
                symbol=row['symbol'],
                exchange=Exchange(row['exchange']),
                report_date=row['report_date'],
                pe_ratio=0.0,  # 需要市值数据
                pb_ratio=0.0,  # 需要市值数据
                ps_ratio=0.0,  # 需要市值数据
                pcf_ratio=0.0,  # 需要市值数据
                revenue_growth_yoy=row.get('revenue_growth', 0.0),
                profit_growth_yoy=row.get('profit_growth', 0.0),
                roe=row.get('roe', 0.0),
                roa=row.get('roa', 0.0),
                gross_margin=0.0,  # 需要毛利率计算
                net_margin=0.0,    # 需要净利率计算
                merged_at=datetime.now(),
                source_dwd=f"dwd_financial_{row['symbol']}_{row['exchange']}"
            )
            
            merged_data.append(merged_bar)
        
        return merged_data
    
    def _calculate_adjustment_factors(self, date: pd.Timestamp) -> tuple:
        """计算复权因子"""
        # 简化实现，返回1.0
        # 实际实现中需要从除权除息数据中获取
        return 1.0, 1.0
    
    def _calculate_net_inflow(self, row: pd.Series, df: pd.DataFrame, index: int) -> float:
        """计算净流入"""
        # 简化计算：基于价格变化和成交量
        if index > 0:
            price_change = row['close'] - df.iloc[index-1]['close']
            return price_change * row['volume'] / 1000000  # 转换为万元
        return 0.0
    
    def _calculate_volume_ratio(self, row: pd.Series, df: pd.DataFrame, index: int) -> float:
        """计算成交量比"""
        if index >= 20:
            avg_volume = df.iloc[index-20:index]['volume'].mean()
            return row['volume'] / avg_volume if avg_volume > 0 else 1.0
        return 1.0
    
    def _calculate_price_momentum(self, row: pd.Series, df: pd.DataFrame, 
                                 index: int, period: int) -> float:
        """计算价格动量"""
        if index >= period:
            start_price = df.iloc[index-period]['close']
            return (row['close'] - start_price) / start_price
        return 0.0
