# quant/storage/parquet_store.py
"""
Parquet 数据存储模块
- 按年分桶存储
- 使用 DuckDB 高效查询
- 支持增量更新
"""
from __future__ import annotations
import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb

# ========== 常量定义 ==========
DEFAULT_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
MANIFEST_CURRENT = "manifest_current.json"
MANIFEST_TEMPLATE = "manifest_v{}.json"
TEMP_SUFFIX = ".tmp.parquet"

# ========== 配置 ==========
@dataclass
class StoreConfig:
    """存储配置"""
    root: str = "~/.quant/history"
    compression: str = "zstd"
    use_dictionary: bool = True

# ========== 工具函数 ==========
def _normalize_path(p: str | Path) -> Path:
    """标准化路径"""
    return Path(os.path.expanduser(str(p))).resolve()

def _get_year(ts: pd.Timestamp) -> int:
    """获取年份"""
    return int(pd.Timestamp(ts).year)

def _get_partition_dir(root: Path, exchange: str, symbol: str, interval: str) -> Path:
    """获取分区目录"""
    return root / exchange / symbol / interval

def _get_partition_file(part_dir: Path, year: int) -> Path:
    """获取分区文件路径"""
    return part_dir / f"{year}.parquet"

def _get_manifest_path(part_dir: Path, version: Optional[int] = None) -> Path:
    """获取manifest文件路径"""
    if version is None:
        return part_dir / MANIFEST_CURRENT
    return part_dir / MANIFEST_TEMPLATE.format(version)

# ========== Manifest 索引 ==========
class ManifestIndex:
    """Manifest索引管理器 - 维护数据文件元信息"""
    
    def __init__(self, part_dir: Path):
        self.part_dir = part_dir
        self.current_path = _get_manifest_path(part_dir)

    def load(self) -> Dict:
        """加载当前manifest"""
        if self.current_path.exists():
            return json.loads(self.current_path.read_text(encoding="utf-8"))
        return {"version": 0, "files": []}

    def _read_file_metadata(self, file_path: Path) -> Optional[Dict]:
        """读取单个parquet文件的元数据"""
        try:
            table = pq.read_table(file_path, columns=["date"])
            dates = pd.to_datetime(table.column(0).to_pandas())
            return {
                "name": file_path.name,
                "start": str(dates.min().date()),
                "end": str(dates.max().date()),
                "rows": len(dates),
                "bytes": file_path.stat().st_size
            }
        except Exception:
            return None

    def build_from_files(self) -> Dict:
        """从实际文件构建manifest"""
        files = []
        for fp in sorted(self.part_dir.glob("*.parquet")):
            metadata = self._read_file_metadata(fp)
            if metadata:
                files.append(metadata)
        return {"version": 1, "files": files}

    def save_atomically(self, manifest: Dict):
        """原子性保存manifest"""
        next_ver = manifest.get("version", 0) + 1
        manifest["version"] = next_ver
        tmp_path = _get_manifest_path(self.part_dir, version=next_ver)
        tmp_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        os.replace(tmp_path, self.current_path)

# ========== 写入器 ==========
class ParquetYearWriter:
    """Parquet按年分桶写入器"""
    
    def __init__(self, cfg: StoreConfig):
        self.cfg = cfg
        self.root = _normalize_path(cfg.root)

    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """准备数据框：转换日期、排序、去重"""
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        return df.sort_values("date").drop_duplicates(subset=["date"], keep="last")

    def _merge_with_existing(self, dst: Path, new_df: pd.DataFrame) -> pd.DataFrame:
        """与现有文件合并"""
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
        final_df = self._merge_with_existing(dst, df)
        
        # 写入临时文件后原子性替换
        table = pa.Table.from_pandas(final_df, preserve_index=False)
        pq.write_table(
            table, tmp,
            compression=self.cfg.compression,
            use_dictionary=self.cfg.use_dictionary,
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

# ========== 读取器 ==========
class DuckDBReader:
    """DuckDB高效读取器"""
    
    def __init__(self, cfg: StoreConfig):
        self.cfg = cfg
        self.root = _normalize_path(cfg.root)
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

    def load(self, exchange: str, symbol: str, interval: str,
             start: Optional[str | pd.Timestamp] = None,
             end: Optional[str | pd.Timestamp] = None,
             columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        加载数据
        
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
        manifest = ManifestIndex(part_dir).load()
        
        if not manifest["files"]:
            return pd.DataFrame(columns=columns or DEFAULT_COLUMNS)
        
        # 构建文件列表
        files = [str(part_dir / f["name"]) for f in manifest["files"]]
        
        # 构建并执行查询
        query, params = self._build_query(files, columns, start, end)
        df = self.conn.execute(query, params).df()
        
        # 标准化日期列
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
        
        return df


# ========== 组合读取 ==========
def load_multi(
    reader: DuckDBReader,
    items: List[Tuple[str, str, str]],
    start=None,
    end=None,
    columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    批量加载多个标的
    
    Args:
        reader: DuckDB读取器
        items: [(exchange, symbol, interval), ...]
        start: 开始日期
        end: 结束日期
        columns: 需要的列
        
    Returns:
        MultiIndex [symbol, date] 的 DataFrame
    """
    frames = []
    for exchange, symbol, interval in items:
        df = reader.load(exchange, symbol, interval, start, end, columns)
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
