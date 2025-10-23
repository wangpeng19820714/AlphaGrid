# quant/datahub/types.py
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import pandas as pd

class Exchange(Enum):
    """交易所枚举"""
    SSE = "SSE"     # 上交所
    SZSE = "SZSE"   # 深交所
    HKEX = "HKEX"   # 港交所
    NYSE = "NYSE"   # 纽交所
    NASDAQ = "NASDAQ"  # 纳斯达克
    OTHER = "OTHER"

class Interval(Enum):
    """时间周期枚举"""
    TICK = "tick"
    MIN1 = "1m"
    MIN5 = "5m"
    MIN15 = "15m"
    MIN30 = "30m"
    HOUR1 = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1mo"

@dataclass(frozen=True)
class BarData:
    """K线数据类"""
    symbol: str
    exchange: Exchange
    interval: Interval
    datetime: pd.Timestamp
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    volume: float = 0.0
    turnover: float = 0.0
    open_interest: float = 0.0

# --------- 常量定义 ----------
BAR_COLUMNS = [
    "symbol", "exchange", "interval", "datetime",
    "open", "high", "low", "close", "volume", "turnover", "open_interest"
]

BAR_DTYPES = {
    "symbol": str, "exchange": str, "interval": str,
    "datetime": "datetime64[ns, UTC]",
    "open": float, "high": float, "low": float, "close": float,
    "volume": float, "turnover": float, "open_interest": float
}

# --------- 工具函数 ----------
def _to_utc(dt: pd.Timestamp) -> pd.Timestamp:
    """转换为UTC时区"""
    return dt.tz_convert("UTC") if dt.tzinfo else dt.tz_localize("UTC")

def _get_enum_value(obj, enum_type):
    """获取枚举值"""
    return obj.value if isinstance(obj, enum_type) else str(obj)

def bars_to_df(bars: list[BarData]) -> pd.DataFrame:
    """将K线数据列表转换为DataFrame"""
    if not bars:
        return pd.DataFrame(columns=BAR_COLUMNS).astype(BAR_DTYPES)
    
    recs = [{
        "symbol": b.symbol,
        "exchange": _get_enum_value(b.exchange, Exchange),
        "interval": _get_enum_value(b.interval, Interval),
        "datetime": _to_utc(pd.Timestamp(b.datetime)),
        "open": b.open_price, "high": b.high_price,
        "low": b.low_price, "close": b.close_price,
        "volume": b.volume, "turnover": b.turnover,
        "open_interest": b.open_interest
    } for b in bars]
    
    return (pd.DataFrame.from_records(recs)
            .sort_values("datetime")
            .drop_duplicates(subset=["datetime"], keep="last"))

def df_to_bars(df: pd.DataFrame, symbol: str, exchange: Exchange, interval: Interval) -> list[BarData]:
    """将DataFrame转换为K线数据列表"""
    if "datetime" not in df.columns:
        raise ValueError("df 缺少 datetime 列")
    
    return [BarData(
        symbol=symbol, exchange=exchange, interval=interval,
        datetime=pd.Timestamp(getattr(r, "datetime")),
        open_price=float(getattr(r, "open")),
        high_price=float(getattr(r, "high")),
        low_price=float(getattr(r, "low")),
        close_price=float(getattr(r, "close")),
        volume=float(getattr(r, "volume", 0.0)),
        turnover=float(getattr(r, "turnover", 0.0)),
        open_interest=float(getattr(r, "open_interest", 0.0)),
    ) for r in df.itertuples(index=False)]

