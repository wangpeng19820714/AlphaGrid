# quant/datahub/types/__init__.py
"""
DataHub 类型定义统一导出

用法：
    from quant.datahub.types import BarData, Exchange, Interval
    from quant.datahub.types import FinancialData, FinancialReportType
    from quant.datahub.types import FundamentalData
"""

# ========== 共享类型 ==========
from .common import (
    Exchange,
    Interval,
    _to_utc,
    _get_enum_value,
)

# ========== K线相关 ==========
from .bar import (
    BarData,
    BAR_COLUMNS,
    BAR_DTYPES,
    bars_to_df,
    df_to_bars,
)

# ========== 财务数据相关 ==========
from .financial import (
    FinancialData,
    FinancialReportType,
    ReportPeriod,
    FINANCIAL_COLUMNS,
    financials_to_df,
    df_to_financials,
)

# ========== 基本面数据相关 ==========
from .fundamental import (
    FundamentalData,
    FUNDAMENTAL_COLUMNS,
    fundamentals_to_df,
    df_to_fundamentals,
)

# ========== 导出清单 ==========
__all__ = [
    # 共享类型
    "Exchange",
    "Interval",
    "_to_utc",
    "_get_enum_value",
    
    # K线
    "BarData",
    "BAR_COLUMNS",
    "BAR_DTYPES",
    "bars_to_df",
    "df_to_bars",
    
    # 财务数据
    "FinancialData",
    "FinancialReportType",
    "ReportPeriod",
    "FINANCIAL_COLUMNS",
    "financials_to_df",
    "df_to_financials",
    
    # 基本面数据
    "FundamentalData",
    "FUNDAMENTAL_COLUMNS",
    "fundamentals_to_df",
    "df_to_fundamentals",
]

