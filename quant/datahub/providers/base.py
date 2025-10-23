# quant/datahub/providers/base.py
from __future__ import annotations
from typing import Iterable, Optional
import pandas as pd
from ..types import Exchange, Interval, BarData

class BaseProvider:
    """
    统一拉取接口：返回 list[BarData]
    """
    def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                   start: pd.Timestamp, end: pd.Timestamp, adjust: str="none") -> list[BarData]:
        raise NotImplementedError
