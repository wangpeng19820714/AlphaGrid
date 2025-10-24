# quant/storage/stores/minute_store.py
"""分钟线数据存储模块"""
from __future__ import annotations
import os
from pathlib import Path
from typing import List, Optional, Tuple
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb

from .base import (
    StoreConfig, BaseStore, ManifestIndex,
    DEFAULT_COLUMNS, TEMP_SUFFIX,
    _normalize_path, _get_year, _get_partition_dir,
    _get_partition_file
)


class MinuteStore(BaseStore):
    """
    分钟线数据存储
    
    - 按年分桶存储
    - 支持增量更新
    - Manifest索引管理
    - 针对分钟线数据优化
    """
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
    
    def _merge_with_existing_minute(self, dst: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有文件合并（分钟线专用）"""
        if not dst.exists():
            return new_df
        
        old_df = pq.read_table(dst).to_pandas()
        merged = pd.concat([old_df, new_df], axis=0)
        # 分钟线数据按datetime去重
        return merged.drop_duplicates(subset=["datetime"], keep="last").sort_values("datetime")
    
    def _write_year_file(self, part_dir: Path, year: int, df: pd.DataFrame) -> int:
        """写入单个年份文件"""
        dst = _get_partition_file(part_dir, year)
        tmp = part_dir / f"{year}{TEMP_SUFFIX}"
        
        # 与现有数据合并
        final_df = self._merge_with_existing_minute(dst, df)
        
        # 写入临时文件后原子性替换
        table = pa.Table.from_pandas(final_df, preserve_index=False)
        pq.write_table(
            table, tmp,
            compression=self.config.compression,
            use_dictionary=self.config.use_dictionary,
            coerce_timestamps="us"
        )
        os.replace(tmp, dst)
        return len(df)
    
    def append(self, exchange: str, symbol: str, interval: str, df: pd.DataFrame) -> int:
        """
        追加分钟线数据到存储
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            df: 数据框，必须包含 ['datetime','open','high','low','close','volume']
            
        Returns:
            写入的记录数
        """
        if df.empty:
            return 0
        
        df = self._prepare_dataframe(df, date_col="datetime")
        part_dir = _get_partition_dir(self.root, exchange, symbol, interval)
        part_dir.mkdir(parents=True, exist_ok=True)
        
        # 按年分组写入
        count = 0
        for year, group_df in df.groupby(_get_year):
            count += self._write_year_file(part_dir, int(year), group_df)
        
        # 更新 manifest
        manifest_index = ManifestIndex(part_dir)
        manifest = manifest_index.build_from_files()
        manifest_index.save_atomically(manifest)
        
        return count
    
    def load(self, exchange: str, symbol: str, interval: str,
             start: Optional[pd.Timestamp] = None,
             end: Optional[pd.Timestamp] = None,
             columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        加载分钟线数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            start: 开始时间
            end: 结束时间
            columns: 需要的列
            
        Returns:
            DataFrame，按时间升序
        """
        part_dir = _get_partition_dir(self.root, exchange, symbol, interval)
        
        if not part_dir.exists():
            return pd.DataFrame(columns=columns or self._get_minute_columns())
        
        manifest = ManifestIndex(part_dir).load()
        
        if not manifest["files"]:
            return pd.DataFrame(columns=columns or self._get_minute_columns())
        
        # 构建文件列表
        files = [str(part_dir / f["name"]) for f in manifest["files"]]
        
        # 使用DuckDB查询
        reader = MinuteReader(self.config)
        return reader.query(files, start, end, columns)
    
    def _get_minute_columns(self) -> List[str]:
        """获取分钟线数据列名"""
        return ["datetime", "open", "high", "low", "close", "volume", "turnover"]
    
    def get_latest_minute(self, exchange: str, symbol: str, interval: str) -> Optional[pd.Series]:
        """
        获取最新分钟线数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            
        Returns:
            最新分钟线数据Series，如果没有数据则返回None
        """
        df = self.load(exchange, symbol, interval)
        if df.empty:
            return None
        return df.iloc[-1]
    
    def get_minute_count(self, exchange: str, symbol: str, interval: str) -> int:
        """
        获取分钟线数据条数
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            
        Returns:
            数据条数
        """
        df = self.load(exchange, symbol, interval)
        return len(df)
    
    def get_time_range(self, exchange: str, symbol: str, interval: str) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp]]:
        """
        获取时间范围
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            
        Returns:
            (开始时间, 结束时间)
        """
        df = self.load(exchange, symbol, interval)
        if df.empty:
            return None, None
        return df["datetime"].min(), df["datetime"].max()


class MinuteReader:
    """分钟线数据读取器（使用DuckDB）"""
    
    def __init__(self, config: StoreConfig):
        self.config = config
        self.conn = duckdb.connect()
    
    def _build_query(self, files: List[str], columns: Optional[List[str]],
                     start: Optional[pd.Timestamp], end: Optional[pd.Timestamp]) -> Tuple[str, List]:
        """构建SQL查询语句"""
        cols = ", ".join(columns) if columns else "*"
        query = f"SELECT {cols} FROM read_parquet({files})"
        
        where_clauses = []
        params = []
        
        if start is not None:
            where_clauses.append("datetime >= ?")
            params.append(pd.to_datetime(start))
        if end is not None:
            where_clauses.append("datetime <= ?")
            params.append(pd.to_datetime(end))
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY datetime"
        
        return query, params
    
    def query(self, files: List[str],
              start: Optional[pd.Timestamp] = None,
              end: Optional[pd.Timestamp] = None,
              columns: Optional[List[str]] = None) -> pd.DataFrame:
        """执行查询"""
        query, params = self._build_query(files, columns, start, end)
        df = self.conn.execute(query, params).df()
        
        # 标准化时间列
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
        
        return df


def load_multi_minutes(
    store: MinuteStore,
    items: List[Tuple[str, str, str]],
    start: Optional[pd.Timestamp] = None,
    end: Optional[pd.Timestamp] = None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    批量加载多个标的的分钟线数据
    
    Args:
        store: MinuteStore实例
        items: [(exchange, symbol, interval), ...]
        start: 开始时间
        end: 结束时间
        columns: 需要的列
        
    Returns:
        MultiIndex [symbol, datetime] 的 DataFrame
    """
    frames = []
    for exchange, symbol, interval in items:
        df = store.load(exchange, symbol, interval, start, end, columns)
        if df.empty:
            continue
        df["symbol"] = symbol
        frames.append(df.set_index(["symbol", "datetime"]).sort_index())
    
    if not frames:
        return pd.DataFrame(columns=(columns or ["open", "high", "low", "close", "volume"]))
    
    result = pd.concat(frames, axis=0).sort_index()
    
    # 统一列顺序
    wanted_cols = ["open", "high", "low", "close", "volume", "turnover"]
    available_cols = [c for c in wanted_cols if c in result.columns]
    
    return result[available_cols].astype(float)


def get_minute_store(config: Optional[StoreConfig] = None) -> MinuteStore:
    """
    获取分钟线数据存储实例
    
    Args:
        config: 存储配置，如果为None则使用默认配置
        
    Returns:
        MinuteStore实例
    """
    if config is None:
        config = StoreConfig(root="data/history_root/level1_core")
    return MinuteStore(config)


# 向后兼容别名
MinuteDataStore = MinuteStore
MinuteDataReader = MinuteReader
load_multi_minute = load_multi_minutes
