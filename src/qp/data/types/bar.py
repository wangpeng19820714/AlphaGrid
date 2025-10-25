# qp/data/types/bar.py
"""K线数据相关类型定义"""
from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

from .common import Exchange, Interval, _to_utc, _get_enum_value


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


# ========== 常量定义 ==========
BAR_COLUMNS = [
    "symbol", "exchange", "interval", "datetime",
    "open", "high", "low", "close", "volume", "turnover", "open_interest"
]

BAR_DTYPES = {
    "symbol": str,
    "exchange": str,
    "interval": str,
    "datetime": "datetime64[ns, UTC]",
    "open": float,
    "high": float,
    "low": float,
    "close": float,
    "volume": float,
    "turnover": float,
    "open_interest": float
}


# ========== 转换函数 ==========
def bars_to_df(bars: list[BarData]) -> pd.DataFrame:
    """将K线数据列表转换为DataFrame"""
    if not bars:
        return pd.DataFrame(columns=BAR_COLUMNS).astype(BAR_DTYPES)

    recs = [{
        "symbol": b.symbol,
        "exchange": _get_enum_value(b.exchange, Exchange),
        "interval": _get_enum_value(b.interval, Interval),
        "datetime": _to_utc(pd.Timestamp(b.datetime)),
        "open": b.open_price,
        "high": b.high_price,
        "low": b.low_price,
        "close": b.close_price,
        "volume": b.volume,
        "turnover": b.turnover,
        "open_interest": b.open_interest
    } for b in bars]

    return (pd.DataFrame.from_records(recs)
            .sort_values("datetime")
            .drop_duplicates(subset=["datetime"], keep="last"))


def df_to_bars(df: pd.DataFrame, symbol: str,
               exchange: Exchange, interval: Interval) -> list[BarData]:
    """将DataFrame转换为K线数据列表"""
    if "datetime" not in df.columns:
        raise ValueError("df 缺少 datetime 列")

    return [BarData(
        symbol=symbol,
        exchange=exchange,
        interval=interval,
        datetime=pd.Timestamp(getattr(r, "datetime")),
        open_price=float(getattr(r, "open")),
        high_price=float(getattr(r, "high")),
        low_price=float(getattr(r, "low")),
        close_price=float(getattr(r, "close")),
        volume=float(getattr(r, "volume", 0.0)),
        turnover=float(getattr(r, "turnover", 0.0)),
        open_interest=float(getattr(r, "open_interest", 0.0)),
    ) for r in df.itertuples(index=False)]

