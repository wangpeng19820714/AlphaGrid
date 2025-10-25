# qp/data/stores/base.py
"""存储层基础类和工具函数"""
from __future__ import annotations
import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict
from abc import ABC
import pandas as pd
import pyarrow.parquet as pq


# ========== 配置 ==========
@dataclass
class StoreConfig:
    """存储配置"""
    root: str = "~/.quant/history"
    compression: str = "zstd"
    use_dictionary: bool = True


# ========== 常量定义 ==========
DEFAULT_COLUMNS = ["date", "open", "high", "low", "close", "volume"]
MANIFEST_CURRENT = "manifest_current.json"
MANIFEST_TEMPLATE = "manifest_v{}.json"
TEMP_SUFFIX = ".tmp.parquet"


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
            # 尝试读取date列，如果失败则读取datetime列
            try:
                table = pq.read_table(file_path, columns=["date"])
                dates = pd.to_datetime(table.column(0).to_pandas())
            except:
                table = pq.read_table(file_path, columns=["datetime"])
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


# ========== 基础存储类 ==========
class BaseStore(ABC):
    """存储基类"""
    
    def __init__(self, config: StoreConfig):
        """
        初始化存储
        
        Args:
            config: 存储配置
        """
        self.config = config
        self.root = _normalize_path(config.root)
    
    def _prepare_dataframe(self, df: pd.DataFrame, date_col: str = "date") -> pd.DataFrame:
        """
        准备数据框：转换日期、排序、去重
        
        Args:
            df: 原始DataFrame
            date_col: 日期列名
            
        Returns:
            处理后的DataFrame
        """
        df = df.copy()
        df[date_col] = pd.to_datetime(df[date_col])
        return df.sort_values(date_col).drop_duplicates(subset=[date_col], keep="last")
    
    def _merge_with_existing(self, file_path: Path, new_df: pd.DataFrame, 
                            unique_cols: list) -> pd.DataFrame:
        """
        与现有文件合并
        
        Args:
            file_path: 文件路径
            new_df: 新数据
            unique_cols: 唯一性约束列
            
        Returns:
            合并后的DataFrame
        """
        if not file_path.exists():
            return new_df
        
        old_df = pd.read_parquet(file_path)
        merged = pd.concat([old_df, new_df], axis=0)
        return merged.drop_duplicates(subset=unique_cols, keep="last").sort_values(unique_cols[0])

