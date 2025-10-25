# qp/data/types/financial.py
"""财务数据相关类型定义"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import pandas as pd

from .common import Exchange, _to_utc


class FinancialReportType(Enum):
    """财务报表类型"""
    BALANCE_SHEET = "balance_sheet"   # 资产负债表
    INCOME = "income"                 # 利润表
    CASHFLOW = "cashflow"             # 现金流量表
    INDICATOR = "indicator"           # 财务指标


class ReportPeriod(Enum):
    """报告期类型"""
    Q1 = "q1"           # 一季报
    Q2 = "q2"           # 中报/半年报
    Q3 = "q3"           # 三季报
    Q4 = "q4"           # 年报
    ANNUAL = "annual"   # 年度（与Q4等同）


@dataclass(frozen=True)
class FinancialData:
    """财务报表数据"""
    symbol: str
    exchange: Exchange
    report_date: pd.Timestamp       # 报告期（如 2024-12-31）
    publish_date: pd.Timestamp      # 公告日期
    report_type: FinancialReportType
    report_period: ReportPeriod

    # ===== 资产负债表字段 =====
    total_assets: Optional[float] = None              # 资产总计
    total_liabilities: Optional[float] = None         # 负债合计
    total_equity: Optional[float] = None              # 股东权益合计
    current_assets: Optional[float] = None            # 流动资产
    current_liabilities: Optional[float] = None       # 流动负债
    fixed_assets: Optional[float] = None              # 固定资产
    intangible_assets: Optional[float] = None         # 无形资产

    # ===== 利润表字段 =====
    revenue: Optional[float] = None                   # 营业总收入
    operating_revenue: Optional[float] = None         # 营业收入
    operating_cost: Optional[float] = None            # 营业成本
    operating_profit: Optional[float] = None          # 营业利润
    total_profit: Optional[float] = None              # 利润总额
    net_profit: Optional[float] = None                # 净利润
    net_profit_parent: Optional[float] = None         # 归属母公司净利润
    basic_eps: Optional[float] = None                 # 基本每股收益

    # ===== 现金流量表字段 =====
    cash_flow_operating: Optional[float] = None       # 经营活动现金流
    cash_flow_investing: Optional[float] = None       # 投资活动现金流
    cash_flow_financing: Optional[float] = None       # 筹资活动现金流
    cash_equivalent_increase: Optional[float] = None  # 现金及现金等价物净增加

    # ===== 财务指标 =====
    roe: Optional[float] = None                       # 净资产收益率
    roa: Optional[float] = None                       # 总资产收益率
    gross_margin: Optional[float] = None              # 毛利率
    net_margin: Optional[float] = None                # 净利率
    debt_to_asset_ratio: Optional[float] = None       # 资产负债率
    current_ratio: Optional[float] = None             # 流动比率

    # 扩展字段（JSON存储其他指标）
    extra_fields: Optional[Dict[str, Any]] = None


# ========== 常量定义 ==========
FINANCIAL_COLUMNS = [
    "symbol", "exchange", "report_date", "publish_date",
    "report_type", "report_period",
    "total_assets", "total_liabilities", "total_equity",
    "revenue", "net_profit", "operating_profit",
    "cash_flow_operating", "roe", "roa"
]


# ========== 转换函数 ==========
def financials_to_df(data_list: list[FinancialData]) -> pd.DataFrame:
    """将财务数据列表转为DataFrame"""
    if not data_list:
        return pd.DataFrame(columns=FINANCIAL_COLUMNS)

    records = []
    for d in data_list:
        record = {
            "symbol": d.symbol,
            "exchange": d.exchange.value if isinstance(d.exchange, Exchange) else d.exchange,
            "report_date": _to_utc(d.report_date),
            "publish_date": _to_utc(d.publish_date),
            "report_type": d.report_type.value if isinstance(d.report_type, FinancialReportType) else d.report_type,
            "report_period": d.report_period.value if isinstance(d.report_period, ReportPeriod) else d.report_period,
            "total_assets": d.total_assets,
            "total_liabilities": d.total_liabilities,
            "total_equity": d.total_equity,
            "revenue": d.revenue,
            "net_profit": d.net_profit,
            "operating_profit": d.operating_profit,
            "cash_flow_operating": d.cash_flow_operating,
            "roe": d.roe,
            "roa": d.roa,
        }

        # 添加扩展字段
        if d.extra_fields:
            record.update(d.extra_fields)

        records.append(record)

    return pd.DataFrame(records).sort_values("report_date")


def df_to_financials(df: pd.DataFrame) -> list[FinancialData]:
    """将DataFrame转换为财务数据列表"""
    if df.empty:
        return []

    result = []
    for _, row in df.iterrows():
        result.append(FinancialData(
            symbol=str(row.get("symbol", "")),
            exchange=Exchange(row.get("exchange", "OTHER")),
            report_date=pd.Timestamp(row["report_date"]),
            publish_date=pd.Timestamp(row["publish_date"]),
            report_type=FinancialReportType(row.get("report_type", "income")),
            report_period=ReportPeriod(row.get("report_period", "q4")),
            total_assets=float(row.get("total_assets", 0)) if pd.notna(row.get("total_assets")) else None,
            revenue=float(row.get("revenue", 0)) if pd.notna(row.get("revenue")) else None,
            net_profit=float(row.get("net_profit", 0)) if pd.notna(row.get("net_profit")) else None,
            # 可以根据需要添加更多字段
        ))

    return result

