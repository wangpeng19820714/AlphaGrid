# qp/data/stores/__init__.py
"""
Storage Stores 统一导出

用法：
    # 注意：以下导入已迁移到数据分层架构
# from qp.data import BarStore, FinancialStore, FundamentalStore
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
# 注意：财务数据存储已迁移到数据分层架构中
# 请使用 ODSStore.save_financial() 和 DWDStore.save_financial() 等方法

# ========== 基本面数据存储 ==========
# 注意：基本面数据存储已迁移到数据分层架构中
# 请使用 ODSStore.save_fundamental() 和 DWDStore.save_fundamental() 等方法

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

# ========== 数据分层存储 ==========
from .ods_store import (
    ODSStore,
    ODSBarData,
    ODSFinancialData,
    ODSFundamentalData,
    create_ods_bar_from_bar_data,
)

from .dwd_store import (
    DWDStore,
    DWDBarData,
    DWDFinancialData,
    DWDFundamentalData,
    DWDProcessor,
    create_dwd_bar_from_ods_bar,
)

from .dws_store import (
    DWSStore,
    DWSAdjustedData,
    DWSFactorData,
    DWSMergedFinancialData,
    DWSProcessor,
)

from .data_layers_models import (
    DataLayerConfig,
    DataQualityChecker,
    ods_bar_to_dwd_bar,
    ods_financial_to_dwd_financial,
    ods_fundamental_to_dwd_fundamental,
    dwd_bar_to_dws_adjusted,
    dwd_bar_to_dws_factor,
    dwd_financial_to_dws_merged,
)

from .config_loader import (
    DataLayerConfigLoader,
    load_data_layer_config,
    load_legacy_config,
)

from .data_layers_pipeline import (
    DataLayersPipeline,
    create_data_layers_pipeline,
    process_bar_data_to_layers,
    get_symbol_data_summary,
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
    
    # 财务存储 - 已迁移到数据分层架构
    # "FinancialStore", "save_financials", "load_financials",
    
    # 基本面存储 - 已迁移到数据分层架构
    # "FundamentalStore",
    
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
    
    # 数据分层存储 - ODS层
    "ODSStore",
    "ODSBarData",
    "ODSFinancialData",
    "ODSFundamentalData",
    "create_ods_bar_from_bar_data",
    
    # 数据分层存储 - DWD层
    "DWDStore",
    "DWDBarData",
    "DWDFinancialData",
    "DWDFundamentalData",
    "DWDProcessor",
    "create_dwd_bar_from_ods_bar",
    
    # 数据分层存储 - DWS层
    "DWSStore",
    "DWSAdjustedData",
    "DWSFactorData",
    "DWSMergedFinancialData",
    "DWSProcessor",
    
    # 数据分层模型和工具
    "DataLayerConfig",
    "DataQualityChecker",
    "ods_bar_to_dwd_bar",
    "ods_financial_to_dwd_financial",
    "ods_fundamental_to_dwd_fundamental",
    "dwd_bar_to_dws_adjusted",
    "dwd_bar_to_dws_factor",
    "dwd_financial_to_dws_merged",
    
    # 数据分层管道
    "DataLayersPipeline",
    "create_data_layers_pipeline",
    "process_bar_data_to_layers",
    "get_symbol_data_summary",
    
    # 配置加载器
    "DataLayerConfigLoader",
    "load_data_layer_config",
    "load_legacy_config",
]

