# qp/stores/bar_store.py
"""K线数据存储模块"""
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


class BarStore(BaseStore):
    """
    K线数据存储
    
    - 按年分桶存储
    - 支持增量更新
    - Manifest索引管理
    """
    
    def __init__(self, config: StoreConfig):
        super().__init__(config)
    
    def _merge_with_existing_bar(self, dst: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有文件合并（K线专用）"""
        if not dst.exists():
            return new_df
        
        old_df = pq.read_table(dst).to_pandas()
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=["date"], keep="last").sort_values("date")
    
    def _write_year_file(self, part_dir: Path, year: int, df: pd.DataFrame) -> int:
        """写入单个年份文件"""
        dst = _get_partition_file(part_dir, year)
        tmp = part_dir / f"{year}{TEMP_SUFFIX}"
        
        # 与现有数据合并
        final_df = self._merge_with_existing_bar(dst, df)
        
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
        追加数据到存储
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            df: 数据框，必须包含 ['date','open','high','low','close','volume']
            
        Returns:
            写入的记录数
        """
        if df.empty:
            return 0
        
        df = self._prepare_dataframe(df)
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
        加载K线数据
        
        Args:
            exchange: 交易所代码
            symbol: 股票代码
            interval: 时间周期
            start: 开始日期
            end: 结束日期
            columns: 需要的列
            
        Returns:
            DataFrame，按日期升序
        """
        part_dir = _get_partition_dir(self.root, exchange, symbol, interval)
        
        if not part_dir.exists():
            return pd.DataFrame(columns=columns or DEFAULT_COLUMNS)
        
        manifest = ManifestIndex(part_dir).load()
        
        if not manifest["files"]:
            return pd.DataFrame(columns=columns or DEFAULT_COLUMNS)
        
        # 构建文件列表
        files = [str(part_dir / f["name"]) for f in manifest["files"]]
        
        # 使用DuckDB查询
        reader = BarReader(self.config)
        return reader.query(files, start, end, columns)


class BarReader:
    """K线数据读取器（使用DuckDB）"""
    
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
            where_clauses.append("date >= ?")
            params.append(pd.to_datetime(start))
        if end is not None:
            where_clauses.append("date <= ?")
            params.append(pd.to_datetime(end))
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY date"
        
        return query, params
    
    def query(self, files: List[str],
              start: Optional[pd.Timestamp] = None,
              end: Optional[pd.Timestamp] = None,
              columns: Optional[List[str]] = None) -> pd.DataFrame:
        """执行查询"""
        query, params = self._build_query(files, columns, start, end)
        df = self.conn.execute(query, params).df()
        
        # 标准化日期列
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        
        return df


def load_multi_bars(
    store: BarStore,
    items: List[Tuple[str, str, str]],
    start=None,
    end=None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    批量加载多个标的
    
    Args:
        store: BarStore实例
        items: [(exchange, symbol, interval), ...]
        start: 开始日期
        end: 结束日期
        columns: 需要的列
        
    Returns:
        MultiIndex [symbol, date] 的 DataFrame
    """
    frames = []
    for exchange, symbol, interval in items:
        df = store.load(exchange, symbol, interval, start, end, columns)
        if df.empty:
            continue
        df["symbol"] = symbol
        frames.append(df.set_index(["symbol", "date"]).sort_index())
    
    if not frames:
        return pd.DataFrame(columns=(columns or ["open", "high", "low", "close", "volume"]))
    
    result = pd.concat(frames, axis=0).sort_index()
    
    # 统一列顺序
    wanted_cols = ["open", "high", "low", "close", "volume"]
    available_cols = [c for c in wanted_cols if c in result.columns]
    
    return result[available_cols].astype(float)


# 向后兼容别名
ParquetYearWriter = BarStore
DuckDBReader = BarReader
load_multi = load_multi_bars

