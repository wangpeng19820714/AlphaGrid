# qp/data/stores/__init__.py
"""
Storage Stores 统一导出

用法：
    from qp.data import BarStore, FinancialStore, FundamentalStore
"""

# ========== 基础类和配置 ==========
from .base import (
    StoreConfig,
    BaseStore,
    ManifestIndex,
    DEFAULT_COLUMNS,
    MANIFEST_CURRENT,
    MANIFEST_TEMPLATE,
    TEMP_SUFFIX,
    _normalize_path,
    _get_year,
    _get_partition_dir,
    _get_partition_file,
    _get_manifest_path,
)

# ========== K线存储 ==========
from .bar_store import (
    BarStore,
    BarReader,
    load_multi_bars,
    # 向后兼容别名
    ParquetYearWriter,
    DuckDBReader,
    load_multi,
)

# ========== 财务数据存储 ==========
from .financial_store import (
    FinancialStore,
    save_financials,
    load_financials,
)

# ========== 基本面数据存储 ==========
from .fundamental_store import (
    FundamentalStore,
)

# ========== 分钟线数据存储 ==========
from .minute_store import (
    MinuteStore,
    MinuteReader,
    load_multi_minutes,
    get_minute_store,
    # 向后兼容别名
    MinuteDataStore,
    MinuteDataReader,
    load_multi_minute,
)

# ========== 衍生数据存储 ==========
from .derivative_store import (
    DerivativeDataStore,
    AnnouncementStore,
    NewsSentimentStore,
    ResearchReportStore,
    CapitalFlowStore,
    ThemeStore,
    DragonTigerStore,
    get_derivative_store,
)

# ========== 第三方数据存储 ==========
from .third_party_store import (
    ThirdPartyStore,
    IndexComponentStore,
    IndustryClassificationStore,
    MacroDataStore,
    get_third_party_store,
)

# ========== 导出清单 ==========
__all__ = [
    # 配置和基础类
    "StoreConfig",
    "BaseStore",
    "ManifestIndex",
    
    # 常量
    "DEFAULT_COLUMNS",
    "MANIFEST_CURRENT",
    "MANIFEST_TEMPLATE",
    "TEMP_SUFFIX",
    
    # 工具函数
    "_normalize_path",
    "_get_year",
    "_get_partition_dir",
    "_get_partition_file",
    "_get_manifest_path",
    
    # K线存储
    "BarStore",
    "BarReader",
    "load_multi_bars",
    # 向后兼容
    "ParquetYearWriter",
    "DuckDBReader",
    "load_multi",
    
    # 财务存储
    "FinancialStore",
    "save_financials",
    "load_financials",
    
    # 基本面存储
    "FundamentalStore",
    
    # 分钟线存储
    "MinuteStore",
    "MinuteReader",
    "load_multi_minutes",
    "get_minute_store",
    
    # 向后兼容
    "MinuteDataStore",
    "MinuteDataReader",
    "load_multi_minute",
    
    # 衍生数据存储
    "DerivativeDataStore",
    "AnnouncementStore",
    "NewsSentimentStore",
    "ResearchReportStore",
    "CapitalFlowStore",
    "ThemeStore",
    "DragonTigerStore",
    "get_derivative_store",
    
    # 第三方数据存储
    "ThirdPartyStore",
    "IndexComponentStore",
    "IndustryClassificationStore",
    "MacroDataStore",
    "get_third_party_store",
]

