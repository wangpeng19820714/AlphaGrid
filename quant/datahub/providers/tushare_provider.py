# quant/datahub/providers/tushare_provider.py
"""TuShare数据提供者"""
from __future__ import annotations
import os
import pandas as pd
import tushare as ts
from .base import BaseProvider
from ..types import BarData, Exchange, Interval, df_to_bars

# 列名映射
COLUMN_MAPPING = {
    "trade_date": "datetime",
    "vol": "volume"
}


class TuShareProvider(BaseProvider):
    """TuShare数据提供者"""
    
    def __init__(self, token: str | None = None):
        """
        初始化TuShare
        
        Args:
            token: TuShare token，如果为None则从环境变量TUSHARE_TOKEN读取
        """
        token = token or os.getenv("TUSHARE_TOKEN")
        if not token:
            raise ValueError("请提供TuShare token或设置环境变量TUSHARE_TOKEN")
        ts.set_token(token)
        self.pro = ts.pro_api()

    def _fetch_daily_data(self, symbol: str, start: pd.Timestamp,
                         end: pd.Timestamp) -> pd.DataFrame:
        """获取日线数据"""
        raw = self.pro.daily(
            ts_code=symbol,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d")
        )
        
        # 重命名列
        df = raw.rename(columns=COLUMN_MAPPING)
        
        # 转换日期
        df["datetime"] = pd.to_datetime(df["datetime"]).dt.tz_localize("UTC")
        df = df.sort_values("datetime")
        
        return df[["datetime", "open", "high", "low", "close", "volume"]]

    def _apply_adjust_factor(self, df: pd.DataFrame, symbol: str,
                            start: pd.Timestamp, end: pd.Timestamp, adjust: str) -> pd.DataFrame:
        """应用复权因子"""
        if adjust == "none":
            return df
        
        # 获取复权因子
        factor_df = self.pro.adj_factor(
            ts_code=symbol,
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d")
        )
        
        factor_df = factor_df.rename(columns={"trade_date": "datetime"})
        factor_df["datetime"] = pd.to_datetime(factor_df["datetime"]).dt.tz_localize("UTC")
        factor_df = factor_df[["datetime", "adj_factor"]].sort_values("datetime")
        
        # 合并因子
        df = df.merge(factor_df, on="datetime", how="left").ffill()
        
        # 计算复权价格
        base_factor = df["adj_factor"].iloc[-1]
        ratio = (df["adj_factor"] / base_factor) if adjust == "qfq" else (base_factor / df["adj_factor"])
        
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col].astype(float) * ratio
        
        return df[["datetime", "open", "high", "low", "close", "volume"]]

    def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                   start: pd.Timestamp, end: pd.Timestamp, adjust: str = "qfq") -> list[BarData]:
        """
        查询K线数据
        
        Args:
            symbol: 股票代码 (如: '000001.SZ')
            exchange: 交易所
            interval: 时间周期
            start: 开始日期
            end: 结束日期
            adjust: 复权类型 ('none', 'qfq', 'hfq')
            
        Returns:
            K线数据列表
        """
        if interval != Interval.DAILY:
            raise NotImplementedError("TuShare提供者当前仅支持日线数据")
        
        df = self._fetch_daily_data(symbol, start, end)
        df = self._apply_adjust_factor(df, symbol, start, end, adjust)
        
        return df_to_bars(df, symbol, exchange, interval)
