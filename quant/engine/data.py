# engine/data.py
# -*- coding: utf-8 -*-
"""
读取 csv + 本地缓存抽象（离线优先）
- 支持：单文件 csv；或目录形式的 {symbol}.csv
- 缓存：优先 parquet（pyarrow/fastparquet），缺失时回退 pickle
- 规范化列：open, high, low, close, volume；index=date（升序、去重）
"""
from __future__ import annotations
import os
import json
import hashlib
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

import pandas as pd


# ========== 配置 ==========
@dataclass
class DataConfig:
    source: str = "csv"                 # 目前仅实现 csv
    path: str = "./data/stock.csv"      # 文件路径；或目录路径（需配合 symbol）
    cache_dir: str = "~/.quant/cache"   # 缓存目录
    date_col: str = "date"              # 日期列名（大小写不敏感）
    freq: str = "D"                     # 频率（预留；当前用于校验/提示）
    symbol: Optional[str] = None        # 当 path 是目录时，需要指定 symbol
    # 额外传参给 pandas.read_csv（如 sep、encoding 等）
    read_csv_kwargs: Optional[Dict[str, Any]] = None


# ========== 工具 ==========
def _norm_path(p: str | Path) -> Path:
    return Path(os.path.expanduser(str(p))).resolve()


def _file_fingerprint(path: Path) -> str:
    """
    使用 (path, size, mtime) 生成稳定签名；无需读取完整文件，避免大文件开销。
    """
    st = path.stat()
    base = f"{str(path)}|{st.st_size}|{int(st.st_mtime)}"
    return hashlib.md5(base.encode("utf-8")).hexdigest()


def _choose_cache_backend() -> Tuple[str, bool]:
    """
    选择缓存后端：parquet 优先；否则退化到 pickle
    返回：(ext, use_parquet)
    """
    try:
        # 优先尝试 pyarrow / fastparquet
        import pyarrow  # noqa
        return ".parquet", True
    except Exception:
        try:
            import fastparquet  # noqa
            return ".parquet", True
        except Exception:
            warnings.warn("未检测到 pyarrow/fastparquet，将使用 pickle 作为缓存格式。")
            return ".pkl", False


# ========== 缓存层 ==========
class CacheStore:
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = _norm_path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ext, self.use_parquet = _choose_cache_backend()

    def _cache_key(self, *, src_path: Path, symbol: Optional[str]) -> str:
        raw = f"{str(src_path)}|{symbol or ''}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def cache_paths(self, *, src_path: Path, symbol: Optional[str]) -> Tuple[Path, Path]:
        key = self._cache_key(src_path=src_path, symbol=symbol)
        data_path = self.cache_dir / f"{key}{self.ext}"
        meta_path = self.cache_dir / f"{key}.meta.json"
        return data_path, meta_path

    def load(self, *, src_path: Path, symbol: Optional[str]) -> Optional[pd.DataFrame]:
        data_path, meta_path = self.cache_paths(src_path=src_path, symbol=symbol)
        if not data_path.exists() or not meta_path.exists():
            return None

        # 校验签名
        try:
            with meta_path.open("r", encoding="utf-8") as f:
                meta = json.load(f)
        except Exception:
            return None

        cur_fp = _file_fingerprint(src_path)
        if meta.get("fingerprint") != cur_fp:
            # 源文件有变动，缓存失效
            return None

        try:
            if self.use_parquet:
                df = pd.read_parquet(data_path)
            else:
                df = pd.read_pickle(data_path)
            return df
        except Exception as e:
            warnings.warn(f"加载缓存失败，将重建缓存：{e}")
            return None

    def save(self, *, src_path: Path, symbol: Optional[str], df: pd.DataFrame) -> None:
        data_path, meta_path = self.cache_paths(src_path=src_path, symbol=symbol)
        try:
            if self.use_parquet:
                df.to_parquet(data_path, index=True)
            else:
                df.to_pickle(data_path)
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
            warnings.warn(f"写入缓存失败（不影响回测）：{e}")


# ========== CSV 读取与标准化 ==========
class CSVDataSource:
    """
    读取 CSV，并规范化为标准 OHLCV：
    - index: DatetimeIndex（升序、去重）
    - columns: open, high, low, close, volume（float）
    """

    # 允许的别名（大小写不敏感）
    ALIASES = {
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
        """
        - 若 path 是文件：直接返回
        - 若 path 是目录：需要 symbol，对应 {dir}/{symbol}.csv
        """
        if self.src_path.is_file():
            return self.src_path
        if self.src_path.is_dir():
            if not self.cfg.symbol:
                raise ValueError("path 为目录时必须提供 symbol（如 DataConfig.symbol='600000.SH'）。")
            candidate = self.src_path / f"{self.cfg.symbol}.csv"
            if not candidate.exists():
                raise FileNotFoundError(f"未找到 {candidate}")
            return candidate
        raise FileNotFoundError(f"无效的 CSV 路径：{self.src_path}")

    @staticmethod
    def _match_col(cols, targets) -> Optional[str]:
        lower = {c.lower(): c for c in cols}
        for t in targets:
            if t in lower:
                return lower[t]
        return None

    def _standardize(self, raw: pd.DataFrame) -> pd.DataFrame:
        cols = list(raw.columns)
        # 定位列名（大小写不敏感）
        date_col = self._match_col(cols, self.ALIASES["date"]) or self.cfg.date_col
        o = self._match_col(cols, self.ALIASES["open"])
        h = self._match_col(cols, self.ALIASES["high"])
        l = self._match_col(cols, self.ALIASES["low"])
        c = self._match_col(cols, self.ALIASES["close"])
        v = self._match_col(cols, self.ALIASES["volume"])

        miss = [name for name, real in
                [("open", o), ("high", h), ("low", l), ("close", c), ("volume", v)]
                if real is None]
        if miss:
            raise ValueError(f"CSV 列缺失或未识别：{miss}，现有列：{cols}")

        df = raw.copy()

        # 解析日期，设置索引
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce", utc=False)
        except Exception as e:
            raise ValueError(f"日期列解析失败：{date_col}, error={e}")

        df = df.dropna(subset=[date_col])
        df = df.set_index(date_col)
        df.index.name = "date"

        # 选择并重命名列
        df = df[[o, h, l, c, v]]
        df.columns = ["open", "high", "low", "close", "volume"]

        # 类型统一为 float（volume 也转 float，必要时你可自行改为 int64）
        df = df.astype(float)

        # 去重、升序
        df = df[~df.index.duplicated(keep="last")]
        df = df.sort_index()

        # 校验频率（提示而不强制）
        if self.cfg.freq.upper() == "D":
            # 简单检查：日期是否单调递增；是否有逆序已处理
            pass

        return df

    def read_csv(self) -> pd.DataFrame:
        csv_path = self._resolve_csv_path()
        kwargs = dict(self.cfg.read_csv_kwargs or {})
        if "encoding" not in kwargs:
            kwargs["encoding"] = "utf-8"
        if "low_memory" not in kwargs:
            kwargs["low_memory"] = False

        try:
            raw = pd.read_csv(csv_path, **kwargs)
        except UnicodeDecodeError:
            # 若编码错误，尝试 gbk
            kwargs["encoding"] = "gbk"
            raw = pd.read_csv(csv_path, **kwargs)

        df = self._standardize(raw)
        if df.empty:
            warnings.warn(f"CSV 数据为空：{csv_path}")
        return df, csv_path


# ========== 数据集 API ==========
class OHLCVDataset:
    """
    与之前示例兼容：
        ds = OHLCVDataset("data/stock.csv")
        df = ds.get()
    同时支持配置化：
        ds = OHLCVDataset.from_config(DataConfig(path="data", symbol="000001.SZ"))
    """

    def __init__(self, path: str | Path, cache_dir: str | Path = "~/.quant/cache",
                 symbol: Optional[str] = None, date_col: str = "date",
                 freq: str = "D", read_csv_kwargs: Optional[Dict[str, Any]] = None):
        cfg = DataConfig(
            path=str(path),
            cache_dir=str(cache_dir),
            symbol=symbol,
            date_col=date_col,
            freq=freq,
            read_csv_kwargs=read_csv_kwargs,
        )
        self.cfg = cfg
        self.cache = CacheStore(cfg.cache_dir)
        self.src = CSVDataSource(cfg)

    @classmethod
    def from_config(cls, cfg: DataConfig) -> "OHLCVDataset":
        return cls(
            path=cfg.path,
            cache_dir=cfg.cache_dir,
            symbol=cfg.symbol,
            date_col=cfg.date_col,
            freq=cfg.freq,
            read_csv_kwargs=cfg.read_csv_kwargs,
        )

    def get(self) -> pd.DataFrame:
        """
        优先读缓存；若源文件有更新则重建缓存。
        """
        # 尝试缓存
        source_path = self.src._resolve_csv_path()
        cached = self.cache.load(src_path=source_path, symbol=self.cfg.symbol)
        if cached is not None and not cached.empty:
            return cached

        # 重建缓存
        df, csv_path = self.src.read_csv()
        self.cache.save(src_path=csv_path, symbol=self.cfg.symbol, df=df)
        return df

# ========== 多标的数据集 ==========
class MultiOHLCVDataset:
    """
    多标的 OHLCV 数据集
    - 支持目录下多个 CSV 文件
    - 返回 MultiIndex (symbol, date) 的 DataFrame
    - 复用单标的缓存机制
    """

    def __init__(
        self,
        dir_path: str | Path,
        symbols: Optional[List[str]] = None,
        cache_dir: str | Path = "~/.quant/cache",
        **kwargs
    ):
        self.dir_path = _norm_path(dir_path)
        if not self.dir_path.is_dir():
            raise FileNotFoundError(f"目录不存在：{self.dir_path}")
        
        self.cache = CacheStore(cache_dir)
        self.symbols = self._resolve_symbols(symbols)
        self.config = {**kwargs}

    def _resolve_symbols(self, symbols: Optional[List[str]]) -> List[str]:
        """解析标的列表"""
        if symbols is None:
            symbols = [p.stem for p in sorted(self.dir_path.glob("*.csv"))]
        
        if not symbols:
            raise ValueError("未发现任何 CSV 文件")
        
        return symbols

    def _load_symbol(self, symbol: str) -> pd.DataFrame:
        """加载单个标的的数据"""
        # 创建单标的配置
        cfg = DataConfig(
            source="csv",
            path=str(self.dir_path),
            cache_dir=str(self.cache.cache_dir),
            symbol=symbol,
            **self.config
        )
        
        # 尝试从缓存加载
        src = CSVDataSource(cfg)
        src_path = src._resolve_csv_path()
        cached = self.cache.load(src_path=src_path, symbol=symbol)
        
        if cached is not None:
            return cached
        
        # 缓存未命中，重新加载并保存
        df, csv_path = src.read_csv()
        self.cache.save(src_path=csv_path, symbol=symbol, df=df)
        return df

    def get(self) -> pd.DataFrame:
        """获取多标的数据"""
        frames = []
        
        for symbol in self.symbols:
            df = self._load_symbol(symbol)
            df = df.copy()
            df["symbol"] = symbol
            frames.append(df.reset_index().set_index(["symbol", "date"]))
        
        # 合并所有数据
        result = pd.concat(frames, axis=0).sort_index()
        
        # 标准化列顺序和类型
        columns = ["open", "high", "low", "close", "volume"]
        return result[columns].astype(float)

# ========== 简单自测 ==========
if __name__ == "__main__":
    # 1) 单文件 csv
    ds = OHLCVDataset(path="./data/stock.csv")
    print(ds.get().head())

    # 2) 目录 + symbol
    # ds2 = OHLCVDataset(path="./data", symbol="000001.SZ")
    # print(ds2.get().tail())