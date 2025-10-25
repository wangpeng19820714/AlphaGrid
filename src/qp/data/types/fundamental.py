# qp/data/types/fundamental.py
"""基本面数据相关类型定义"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd

from .common import Exchange, _to_utc


@dataclass(frozen=True)
class FundamentalData:
    """基本面数据（日频或定期更新）"""
    symbol: str
    exchange: Exchange
    date: pd.Timestamp

    # ===== 估值指标 =====
    pe_ratio: Optional[float] = None            # 市盈率 PE
    pe_ttm: Optional[float] = None              # 市盈率TTM
    pb_ratio: Optional[float] = None            # 市净率 PB
    ps_ratio: Optional[float] = None            # 市销率 PS
    pcf_ratio: Optional[float] = None           # 市现率 PCF

    # ===== 市值相关 =====
    market_cap: Optional[float] = None              # 总市值
    circulating_market_cap: Optional[float] = None  # 流通市值
    total_shares: Optional[float] = None            # 总股本
    circulating_shares: Optional[float] = None      # 流通股本

    # ===== 财务质量指标 =====
    roe: Optional[float] = None                     # 净资产收益率
    roa: Optional[float] = None                     # 总资产收益率
    roic: Optional[float] = None                    # 投入资本回报率
    debt_to_asset_ratio: Optional[float] = None     # 资产负债率
    debt_to_equity_ratio: Optional[float] = None    # 产权比率
    current_ratio: Optional[float] = None           # 流动比率
    quick_ratio: Optional[float] = None             # 速动比率

    # ===== 成长性指标 =====
    revenue_growth: Optional[float] = None          # 营收增长率（同比）
    revenue_growth_qoq: Optional[float] = None      # 营收增长率（环比）
    profit_growth: Optional[float] = None           # 净利润增长率（同比）
    profit_growth_qoq: Optional[float] = None       # 净利润增长率（环比）

    # ===== 盈利能力 =====
    gross_margin: Optional[float] = None            # 毛利率
    net_margin: Optional[float] = None              # 净利率
    operating_margin: Optional[float] = None        # 营业利润率

    # ===== 每股指标 =====
    eps: Optional[float] = None                     # 每股收益
    bps: Optional[float] = None                     # 每股净资产
    ocfps: Optional[float] = None                   # 每股经营现金流

    # ===== 分红相关 =====
    dividend_yield: Optional[float] = None          # 股息率
    payout_ratio: Optional[float] = None            # 分红率

    # 扩展字段
    extra_fields: Optional[Dict[str, Any]] = None


# ========== 常量定义 ==========
FUNDAMENTAL_COLUMNS = [
    "symbol", "exchange", "date",
    "pe_ratio", "pb_ratio", "ps_ratio",
    "market_cap", "circulating_market_cap",
    "roe", "roa", "debt_to_asset_ratio",
    "revenue_growth", "profit_growth",
    "gross_margin", "net_margin"
]


# ========== 转换函数 ==========
def fundamentals_to_df(data_list: list[FundamentalData]) -> pd.DataFrame:
    """将基本面数据列表转为DataFrame"""
    if not data_list:
        return pd.DataFrame(columns=FUNDAMENTAL_COLUMNS)

    records = []
    for d in data_list:
        record = {
            "symbol": d.symbol,
            "exchange": d.exchange.value if isinstance(d.exchange, Exchange) else d.exchange,
            "date": _to_utc(d.date),
            "pe_ratio": d.pe_ratio,
            "pe_ttm": d.pe_ttm,
            "pb_ratio": d.pb_ratio,
            "ps_ratio": d.ps_ratio,
            "market_cap": d.market_cap,
            "circulating_market_cap": d.circulating_market_cap,
            "roe": d.roe,
            "roa": d.roa,
            "debt_to_asset_ratio": d.debt_to_asset_ratio,
            "revenue_growth": d.revenue_growth,
            "profit_growth": d.profit_growth,
            "gross_margin": d.gross_margin,
            "net_margin": d.net_margin,
        }

        if d.extra_fields:
            record.update(d.extra_fields)

        records.append(record)

    return pd.DataFrame(records).sort_values("date")


def df_to_fundamentals(df: pd.DataFrame) -> list[FundamentalData]:
    """将DataFrame转换为基本面数据列表"""
    if df.empty:
        return []

    result = []
    for _, row in df.iterrows():
        result.append(FundamentalData(
            symbol=str(row.get("symbol", "")),
            exchange=Exchange(row.get("exchange", "OTHER")),
            date=pd.Timestamp(row["date"]),
            pe_ratio=float(row.get("pe_ratio")) if pd.notna(row.get("pe_ratio")) else None,
            pb_ratio=float(row.get("pb_ratio")) if pd.notna(row.get("pb_ratio")) else None,
            market_cap=float(row.get("market_cap")) if pd.notna(row.get("market_cap")) else None,
            roe=float(row.get("roe")) if pd.notna(row.get("roe")) else None,
            # 可以根据需要添加更多字段
        ))

    return result

