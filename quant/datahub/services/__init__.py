# quant/datahub/services/__init__.py
"""
DataHub Services 统一导出

用法：
    from quant.datahub.services import BarDataService
    from quant.datahub.services import FinancialDataService, FundamentalDataService
"""

# ========== 基础类 ==========
from .base import BaseDataService

# ========== K线数据服务 ==========
from .bar_service import (
    BarDataService,
    HistoricalDataService,  # 向后兼容别名
    RESAMPLE_RULES,
)

# ========== 财务数据服务 ==========
from .financial_service import FinancialDataService

# ========== 基本面数据服务 ==========
from .fundamental_service import FundamentalDataService

# ========== 分钟线数据服务 ==========
from .minute_service import MinuteDataService


# ========== 导出清单 ==========
__all__ = [
    # 基础类
    "BaseDataService",
    
    # K线服务
    "BarDataService",
    "HistoricalDataService",  # 向后兼容
    "RESAMPLE_RULES",
    
    # 财务服务
    "FinancialDataService",
    
    # 基本面服务
    "FundamentalDataService",
    
    # 分钟线服务
    "MinuteDataService",
]

