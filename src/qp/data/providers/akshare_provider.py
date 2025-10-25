# qp/data/providers/akshare_provider.py
"""AKShare数据提供者"""
from __future__ import annotations
import pandas as pd
import akshare as ak
from .base import BaseProvider
from ..types import (
    FinancialData, FundamentalData, FinancialReportType, 
    ReportPeriod, Exchange, Interval, BarData, df_to_bars
)

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

    def query_financials(self, symbol: str, exchange: Exchange,
                         report_type: FinancialReportType,
                         start: pd.Timestamp, end: pd.Timestamp) -> list[FinancialData]:
        """查询财务数据"""
        
        # 根据报表类型选择AKShare接口
        if report_type == FinancialReportType.BALANCE_SHEET:
            df = ak.stock_financial_report_sina(
                stock=symbol, 
                symbol="资产负债表"
            )
        elif report_type == FinancialReportType.INCOME:
            df = ak.stock_financial_report_sina(
                stock=symbol, 
                symbol="利润表"
            )
        elif report_type == FinancialReportType.CASHFLOW:
            df = ak.stock_financial_report_sina(
                stock=symbol, 
                symbol="现金流量表"
            )
        
        # 标准化并转换为 FinancialData 对象
        return self._parse_financial_df(df, symbol, exchange, report_type)
    
    def query_fundamentals(self, symbol: str, exchange: Exchange,
                          start: pd.Timestamp, end: pd.Timestamp) -> list[FundamentalData]:
        """查询基本面数据"""
        
        # AKShare 获取估值数据
        df = ak.stock_a_lg_indicator(symbol=symbol)
        
        # 筛选日期范围
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        df = df[(df['trade_date'] >= start) & (df['trade_date'] <= end)]
        
        # 转换为 FundamentalData 对象
        result = []
        for _, row in df.iterrows():
            result.append(FundamentalData(
                symbol=symbol,
                exchange=exchange,
                date=pd.Timestamp(row['trade_date']).tz_localize("UTC"),
                pe_ratio=float(row.get('pe', 0)),
                pb_ratio=float(row.get('pb', 0)),
                market_cap=float(row.get('total_mv', 0)),
                # ... 其他字段映射
            ))
        
        return result
    
    def _parse_financial_df(self, df: pd.DataFrame, symbol: str, 
                           exchange: Exchange, 
                           report_type: FinancialReportType) -> list[FinancialData]:
        """解析财务报表DataFrame"""
        result = []
        for _, row in df.iterrows():
            result.append(FinancialData(
                symbol=symbol,
                exchange=exchange,
                report_date=pd.Timestamp(row['报告期']).tz_localize("UTC"),
                publish_date=pd.Timestamp(row.get('公告日期', row['报告期'])).tz_localize("UTC"),
                report_type=report_type,
                report_period=self._infer_period(row['报告期']),
                total_assets=float(row.get('资产总计', 0)),
                revenue=float(row.get('营业总收入', 0)),
                net_profit=float(row.get('净利润', 0)),
                # ... 更多字段映射
            ))
        return result
    
    @staticmethod
    def _infer_period(date_str: str) -> ReportPeriod:
        """推断报告期类型"""
        month = pd.Timestamp(date_str).month
        if month == 3:
            return ReportPeriod.Q1
        elif month == 6:
            return ReportPeriod.Q2
        elif month == 9:
            return ReportPeriod.Q3
        else:
            return ReportPeriod.ANNUAL

