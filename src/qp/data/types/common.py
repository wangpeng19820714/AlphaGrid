# qp/data/types/common.py
"""共享的枚举类型和基础定义"""
from enum import Enum
import pandas as pd


class Exchange(Enum):
    """交易所枚举"""
    SSE = "SSE"         # 上交所
    SZSE = "SZSE"       # 深交所
    HKEX = "HKEX"       # 港交所
    NYSE = "NYSE"       # 纽交所
    NASDAQ = "NASDAQ"   # 纳斯达克
    OTHER = "OTHER"


class Interval(Enum):
    """时间周期枚举"""
    TICK = "tick"
    MIN1 = "1m"
    MIN5 = "5m"
    MIN15 = "15m"
    MIN30 = "30m"
    HOUR1 = "1h"
    HOUR4 = "4h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1mo"


# ========== 工具函数 ==========
def _to_utc(dt: pd.Timestamp) -> pd.Timestamp:
    """转换为UTC时区"""
    return dt.tz_convert("UTC") if dt.tzinfo else dt.tz_localize("UTC")


def _get_enum_value(obj, enum_type):
    """获取枚举值"""
    return obj.value if isinstance(obj, enum_type) else str(obj)

