# quant/datahub/providers/akshare_provider.py
"""AKShare数据提供者"""
from __future__ import annotations
import pandas as pd
import akshare as ak
from .base import BaseProvider
from ..types import BarData, Exchange, Interval, df_to_bars

# 列名映射
COLUMN_MAPPING = {
    "日期": "datetime",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交量": "volume",
    "成交额": "turnover"
}

# 复权类型映射
ADJUST_MAPPING = {
    "none": "",
    "qfq": "qfq",  # 前复权
    "hfq": "hfq"   # 后复权
}


class AkshareProvider(BaseProvider):
    """AKShare数据提供者"""
    
    def __init__(self):
        """初始化"""
        pass

    def _fetch_daily_data(self, symbol: str, start: pd.Timestamp,
                         end: pd.Timestamp, adjust: str) -> pd.DataFrame:
        """获取日线数据"""
        df = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust=ADJUST_MAPPING[adjust]
        )
        
        # 重命名列
        df = df.rename(columns=COLUMN_MAPPING)
        
        # 转换日期
        df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize("UTC")
        
        return df[["datetime", "open", "high", "low", "close", "volume", "turnover"]]

    def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                   start: pd.Timestamp, end: pd.Timestamp, adjust: str = "qfq") -> list[BarData]:
        """
        查询K线数据
        
        Args:
            symbol: 股票代码
            exchange: 交易所
            interval: 时间周期
            start: 开始日期
            end: 结束日期
            adjust: 复权类型 ('none', 'qfq', 'hfq')
            
        Returns:
            K线数据列表
        """
        if interval != Interval.DAILY:
            raise NotImplementedError("AKShare提供者当前仅支持日线数据")
        
        df = self._fetch_daily_data(symbol, start, end, adjust)
        return df_to_bars(df, symbol, exchange, interval)

