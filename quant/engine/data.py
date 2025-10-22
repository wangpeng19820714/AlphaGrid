# engine/data.py
# -*- coding: utf-8 -*-
"""
CSV数据读取与缓存模块
- 支持单文件CSV或目录形式的{symbol}.csv
- 优先使用parquet缓存，回退到pickle
- 自动规范化OHLCV数据格式
"""
from __future__ import annotations
import json
import hashlib
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

import pandas as pd


@dataclass
class DataConfig:
    """数据源配置"""
    path: str = "./data/stock.csv"
    cache_dir: str = "~/.quant/cache"
    date_col: str = "date"
    symbol: Optional[str] = None
    read_csv_kwargs: Dict[str, Any] = field(default_factory=dict)


def _norm_path(p: str | Path) -> Path:
    """标准化路径"""
    return Path(p).expanduser().resolve()


def _file_fingerprint(path: Path) -> str:
    """生成文件指纹用于缓存验证"""
    st = path.stat()
    content = f"{path}|{st.st_size}|{int(st.st_mtime)}"
    return hashlib.md5(content.encode()).hexdigest()


def _get_cache_backend():
    """选择缓存后端：parquet优先，否则pickle"""
    try:
        import pyarrow  # noqa
        return ".parquet", True
    except ImportError:
        try:
            import fastparquet  # noqa
            return ".parquet", True
        except ImportError:
            warnings.warn("未检测到parquet库，使用pickle缓存")
            return ".pkl", False


class CacheStore:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = _norm_path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ext, self.use_parquet = _get_cache_backend()

    def _get_cache_key(self, src_path: Path, symbol: Optional[str]) -> str:
        content = f"{src_path}|{symbol or ''}"
        return hashlib.md5(content.encode()).hexdigest()

    def _get_cache_paths(self, src_path: Path, symbol: Optional[str]) -> tuple[Path, Path]:
        key = self._get_cache_key(src_path, symbol)
        return (
            self.cache_dir / f"{key}{self.ext}",
            self.cache_dir / f"{key}.meta.json"
        )

    def load(self, src_path: Path, symbol: Optional[str]) -> Optional[pd.DataFrame]:
        """加载缓存数据"""
        data_path, meta_path = self._get_cache_paths(src_path, symbol)
        
        if not (data_path.exists() and meta_path.exists()):
            return None

        try:
            with meta_path.open("r", encoding="utf-8") as f:
                meta = json.load(f)
            
            # 验证文件指纹
            if meta.get("fingerprint") != _file_fingerprint(src_path):
                return None

            # 读取数据
            if self.use_parquet:
                return pd.read_parquet(data_path)
            else:
                return pd.read_pickle(data_path)
                
        except Exception as e:
            warnings.warn(f"缓存加载失败: {e}")
            return None

    def save(self, src_path: Path, symbol: Optional[str], df: pd.DataFrame) -> None:
        """保存数据到缓存"""
        data_path, meta_path = self._get_cache_paths(src_path, symbol)
        
        try:
            # 保存数据
            if self.use_parquet:
                df.to_parquet(data_path, index=True)
            else:
                df.to_pickle(data_path)
            
            # 保存元数据
            meta = {
                "fingerprint": _file_fingerprint(src_path),
                "source_path": str(src_path),
                "symbol": symbol,
                "index_name": df.index.name,
                "columns": list(df.columns),
            }
            with meta_path.open("w", encoding="utf-8") as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            warnings.warn(f"缓存保存失败: {e}")


class CSVDataSource:
    """CSV数据源读取器"""
    
    # 列名别名映射
    COLUMN_ALIASES = {
        "date": {"date", "datetime", "trade_date", "time"},
        "open": {"open", "o", "openingprice"},
        "high": {"high", "h", "max", "highprice"},
        "low": {"low", "l", "min", "lowprice"},
        "close": {"close", "c", "price", "adj_close", "closeprice"},
        "volume": {"volume", "vol", "v", "turnovervol", "qty"},
    }

    def __init__(self, cfg: DataConfig):
        self.cfg = cfg
        self.src_path = _norm_path(cfg.path)

    def _resolve_csv_path(self) -> Path:
        """解析CSV文件路径"""
        if self.src_path.is_file():
            return self.src_path
        
        if self.src_path.is_dir():
            if not self.cfg.symbol:
                raise ValueError("目录路径需要指定symbol")
            csv_path = self.src_path / f"{self.cfg.symbol}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"文件不存在: {csv_path}")
            return csv_path
            
        raise FileNotFoundError(f"无效路径: {self.src_path}")

    def _find_column(self, columns: list, target_type: str) -> Optional[str]:
        """查找匹配的列名"""
        lower_map = {col.lower(): col for col in columns}
        for alias in self.COLUMN_ALIASES[target_type]:
            if alias in lower_map:
                return lower_map[alias]
        return None

    def _standardize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        columns = list(df.columns)
        
        # 查找各列
        date_col = self._find_column(columns, "date") or self.cfg.date_col
        ohlcv_cols = {
            "open": self._find_column(columns, "open"),
            "high": self._find_column(columns, "high"),
            "low": self._find_column(columns, "low"),
            "close": self._find_column(columns, "close"),
            "volume": self._find_column(columns, "volume"),
        }
        
        # 检查缺失列
        missing = [name for name, col in ohlcv_cols.items() if col is None]
        if missing:
            raise ValueError(f"缺少必要列: {missing}, 现有列: {columns}")

        # 处理日期列
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        except Exception as e:
            raise ValueError(f"日期解析失败: {e}")
        
        df = df.dropna(subset=[date_col]).set_index(date_col)
        df.index.name = "date"

        # 选择并重命名OHLCV列
        df = df[[ohlcv_cols["open"], ohlcv_cols["high"], ohlcv_cols["low"], 
                 ohlcv_cols["close"], ohlcv_cols["volume"]]]
        df.columns = ["open", "high", "low", "close", "volume"]
        
        # 转换数据类型并清理
        df = df.astype(float)
        df = df[~df.index.duplicated(keep="last")].sort_index()
        
        return df

    def read_csv(self) -> tuple[pd.DataFrame, Path]:
        """读取并标准化CSV数据"""
        csv_path = self._resolve_csv_path()
        
        # 设置读取参数
        kwargs = {
            "encoding": "utf-8",
            "low_memory": False,
            **self.cfg.read_csv_kwargs
        }
        
        try:
            df = pd.read_csv(csv_path, **kwargs)
        except UnicodeDecodeError:
            kwargs["encoding"] = "gbk"
            df = pd.read_csv(csv_path, **kwargs)
        
        df = self._standardize_data(df)
        if df.empty:
            warnings.warn(f"数据为空: {csv_path}")
            
        return df, csv_path


class OHLCVDataset:
    """OHLCV数据集主接口"""
    
    def __init__(self, path: str | Path, cache_dir: str | Path = "~/.quant/cache",
                 symbol: Optional[str] = None, date_col: str = "date",
                 read_csv_kwargs: Optional[Dict[str, Any]] = None):
        self.cfg = DataConfig(
            path=str(path),
            cache_dir=str(cache_dir),
            symbol=symbol,
            date_col=date_col,
            read_csv_kwargs=read_csv_kwargs or {}
        )
        self.cache = CacheStore(self.cfg.cache_dir)
        self.src = CSVDataSource(self.cfg)

    @classmethod
    def from_config(cls, cfg: DataConfig) -> "OHLCVDataset":
        """从配置创建数据集"""
        return cls(
            path=cfg.path,
            cache_dir=cfg.cache_dir,
            symbol=cfg.symbol,
            date_col=cfg.date_col,
            read_csv_kwargs=cfg.read_csv_kwargs
        )

    def get(self) -> pd.DataFrame:
        """获取数据（优先缓存）"""
        source_path = self.src._resolve_csv_path()
        
        # 尝试从缓存加载
        cached = self.cache.load(source_path, self.cfg.symbol)
        if cached is not None and not cached.empty:
            return cached

        # 从源文件读取并缓存
        df, csv_path = self.src.read_csv()
        self.cache.save(csv_path, self.cfg.symbol, df)
        return df


if __name__ == "__main__":
    # 测试单文件CSV
    ds = OHLCVDataset(path="./ data/stock.csv")
    print(ds.get().head())