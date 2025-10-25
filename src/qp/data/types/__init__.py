# qp/data/types/__init__.py
"""
Data 类型定义统一导出

用法：
    from qp.data.types import BarData, Exchange, Interval
    from qp.data.types import FinancialData, FinancialReportType
    from qp.data.types import FundamentalData
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

# ========== 衍生数据相关 ==========
from .derivative import (
    # 枚举类型
    AnnouncementType, NewsSentiment, ReportType, ReportRating,
    FlowType, FlowDirection, ThemeType, DragonTigerType, DragonTigerReason,
    
    # 数据类
    AnnouncementData, NewsSentimentData, ResearchReportData,
    CapitalFlowData, ThemeData, DragonTigerData,
    
    # 转换函数
    announcements_to_df, df_to_announcements,
    news_sentiments_to_df, df_to_news_sentiments,
    research_reports_to_df, df_to_research_reports,
    capital_flows_to_df, df_to_capital_flows,
    themes_to_df, df_to_themes,
    dragon_tigers_to_df, df_to_dragon_tigers,
    
    # 常量
    ANNOUNCEMENT_COLUMNS, NEWS_SENTIMENT_COLUMNS, RESEARCH_REPORT_COLUMNS,
    CAPITAL_FLOW_COLUMNS, THEME_COLUMNS, DRAGON_TIGER_COLUMNS,
    DERIVATIVE_DTYPES,
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
    
    # 衍生数据 - 枚举类型
    "AnnouncementType", "NewsSentiment", "ReportType", "ReportRating",
    "FlowType", "FlowDirection", "ThemeType", "DragonTigerType", "DragonTigerReason",
    
    # 衍生数据 - 数据类
    "AnnouncementData", "NewsSentimentData", "ResearchReportData",
    "CapitalFlowData", "ThemeData", "DragonTigerData",
    
    # 衍生数据 - 转换函数
    "announcements_to_df", "df_to_announcements",
    "news_sentiments_to_df", "df_to_news_sentiments",
    "research_reports_to_df", "df_to_research_reports",
    "capital_flows_to_df", "df_to_capital_flows",
    "themes_to_df", "df_to_themes",
    "dragon_tigers_to_df", "df_to_dragon_tigers",
    
    # 衍生数据 - 常量
    "ANNOUNCEMENT_COLUMNS", "NEWS_SENTIMENT_COLUMNS", "RESEARCH_REPORT_COLUMNS",
    "CAPITAL_FLOW_COLUMNS", "THEME_COLUMNS", "DRAGON_TIGER_COLUMNS",
    "DERIVATIVE_DTYPES",
]

