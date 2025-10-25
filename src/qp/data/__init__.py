# qp/data/__init__.py
"""
AlphaGrid 数据模块统一接口

提供数据获取、存储、查询的完整解决方案

主要功能：
- 数据提供者：支持多种数据源 (AKShare, TuShare, YFinance)
- 数据服务：提供业务逻辑层的数据操作
- 数据存储：支持 Parquet + DuckDB 的高性能存储
- 数据类型：统一的数据模型和类型定义

快速开始：
    # 获取数据
    from qp.data import get_bars, get_minute_bars, get_financials
    
    # 存储数据
    from qp.data import save_bars, save_minute_bars, save_financials
    
    # 查询数据
    from qp.data import query_bars, query_minute_bars, query_financials

完整示例：
    # 1. 获取K线数据
    bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31', 'daily')
    
    # 2. 存储数据
    save_bars(bars)
    
    # 3. 查询数据
    result = query_bars('000001.SZ', '2023-01-01', '2023-12-31')
    
    # 4. 获取分钟线数据
    minute_bars = get_minute_bars('000001.SZ', '2023-01-01', '1m')
    
    # 5. 获取财务数据
    financials = get_financials('000001.SZ', '2023-01-01', '2023-12-31')
"""

# ========== 导入所有子模块 ==========

# 数据类型
from .types import (
    # 基础类型
    Exchange,
    Interval,
    BarData,
    FinancialData,
    FundamentalData,
    FinancialReportType,
    ReportPeriod,
    
    # 工具函数
    bars_to_df,
    df_to_bars,
    financials_to_df,
    df_to_financials,
    fundamentals_to_df,
    df_to_fundamentals,
)

# 数据提供者
from .providers import (
    BaseProvider,
    AkshareProvider,
    TuShareProvider,
    YFProvider,
    MinuteProvider,
    get_provider,
    PROVIDERS,
)

# 数据服务
from .services import (
    BaseDataService,
    BarDataService,
    FinancialDataService,
    FundamentalDataService,
    MinuteDataService,
    HistoricalDataService,  # 向后兼容
    RESAMPLE_RULES,
)

# 数据存储
from .stores import (
    # 基础类
    StoreConfig,
    BaseStore,
    ManifestIndex,
    
    # K线存储
    BarStore,
    BarReader,
    load_multi_bars,
    
    # 财务存储
    FinancialStore,
    save_financials,
    load_financials,
    
    # 基本面存储
    FundamentalStore,
    
    # 分钟线存储
    MinuteStore,
    MinuteReader,
    load_multi_minutes,
    get_minute_store,
)

# 数据库
from .db import DataHub

# ========== 统一接口函数 ==========

def get_bars(symbol: str, start_date: str, end_date: str, 
             interval: str = 'daily', provider: str = 'akshare', **kwargs):
    """
    获取K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        interval: 时间间隔 ('daily', 'weekly', 'monthly')
        provider: 数据提供者 ('akshare', 'tushare', 'yfinance')
        **kwargs: 其他参数
        
    Returns:
        List[BarData]: K线数据列表
        
    Example:
        >>> bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31')
        >>> bars = get_bars('AAPL', '2023-01-01', '2023-12-31', provider='yfinance')
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_bars(symbol, start_date, end_date, interval)

def get_minute_bars(symbol: str, start_date: str, 
                   interval: str = '1m', provider: str = 'akshare', **kwargs):
    """
    获取分钟线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        interval: 时间间隔 ('1m', '5m', '15m', '30m', '1h')
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[BarData]: 分钟线数据列表
        
    Example:
        >>> minute_bars = get_minute_bars('000001.SZ', '2023-01-01', '1m')
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_minute_bars(symbol, start_date, interval)

def get_financials(symbol: str, start_date: str, end_date: str, 
                  provider: str = 'akshare', **kwargs):
    """
    获取财务数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[FinancialData]: 财务数据列表
        
    Example:
        >>> financials = get_financials('000001.SZ', '2023-01-01', '2023-12-31')
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_financials(symbol, start_date, end_date)

def get_fundamentals(symbol: str, start_date: str, end_date: str, 
                    provider: str = 'akshare', **kwargs):
    """
    获取基本面数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[FundamentalData]: 基本面数据列表
        
    Example:
        >>> fundamentals = get_fundamentals('000001.SZ', '2023-01-01', '2023-12-31')
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_fundamentals(symbol, start_date, end_date)

def save_bars(bars, store_config: StoreConfig = None):
    """
    保存K线数据
    
    Args:
        bars: K线数据列表
        store_config: 存储配置
        
    Returns:
        int: 保存的记录数
        
    Example:
        >>> bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31')
        >>> save_bars(bars)
    """
    if store_config is None:
        store_config = StoreConfig()
    
    store = BarStore(store_config)
    return store.save_bars(bars)

def save_minute_bars(bars, store_config: StoreConfig = None):
    """
    保存分钟线数据
    
    Args:
        bars: 分钟线数据列表
        store_config: 存储配置
        
    Returns:
        int: 保存的记录数
        
    Example:
        >>> minute_bars = get_minute_bars('000001.SZ', '2023-01-01', '1m')
        >>> save_minute_bars(minute_bars)
    """
    if store_config is None:
        store_config = StoreConfig()
    
    store = MinuteStore(store_config)
    return store.save_bars(bars)

def save_financials(financials, store_config: StoreConfig = None):
    """
    保存财务数据
    
    Args:
        financials: 财务数据列表
        store_config: 存储配置
        
    Returns:
        int: 保存的记录数
        
    Example:
        >>> financials = get_financials('000001.SZ', '2023-01-01', '2023-12-31')
        >>> save_financials(financials)
    """
    if store_config is None:
        store_config = StoreConfig()
    
    store = FinancialStore(store_config)
    return store.save_financials(financials)

def save_fundamentals(fundamentals, store_config: StoreConfig = None):
    """
    保存基本面数据
    
    Args:
        fundamentals: 基本面数据列表
        store_config: 存储配置
        
    Returns:
        int: 保存的记录数
        
    Example:
        >>> fundamentals = get_fundamentals('000001.SZ', '2023-01-01', '2023-12-31')
        >>> save_fundamentals(fundamentals)
    """
    if store_config is None:
        store_config = StoreConfig()
    
    store = FundamentalStore(store_config)
    return store.save_fundamentals(fundamentals)

def query_bars(symbol: str, start_date: str, end_date: str, 
               store_config: StoreConfig = None):
    """
    查询K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        store_config: 存储配置
        
    Returns:
        List[BarData]: K线数据列表
        
    Example:
        >>> bars = query_bars('000001.SZ', '2023-01-01', '2023-12-31')
    """
    if store_config is None:
        store_config = StoreConfig()
    
    store = BarStore(store_config)
    return store.query_bars(symbol, start_date, end_date)

def query_minute_bars(symbol: str, start_date: str, end_date: str, 
                     store_config: StoreConfig = None):
    """
    查询分钟线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        store_config: 存储配置
        
    Returns:
        List[BarData]: 分钟线数据列表
        
    Example:
        >>> minute_bars = query_minute_bars('000001.SZ', '2023-01-01', '2023-12-31')
    """
    if store_config is None:
        store_config = StoreConfig()
    
    store = MinuteStore(store_config)
    return store.query_bars(symbol, start_date, end_date)

def query_financials(symbol: str, start_date: str, end_date: str, 
                    store_config: StoreConfig = None):
    """
    查询财务数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        store_config: 存储配置
        
    Returns:
        List[FinancialData]: 财务数据列表
        
    Example:
        >>> financials = query_financials('000001.SZ', '2023-01-01', '2023-12-31')
    """
    if store_config is None:
        store_config = StoreConfig()
    
    store = FinancialStore(store_config)
    return store.query_financials(symbol, start_date, end_date)

def query_fundamentals(symbol: str, start_date: str, end_date: str, 
                      store_config: StoreConfig = None):
    """
    查询基本面数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        store_config: 存储配置
        
    Returns:
        List[FundamentalData]: 基本面数据列表
        
    Example:
        >>> fundamentals = query_fundamentals('000001.SZ', '2023-01-01', '2023-12-31')
    """
    if store_config is None:
        store_config = StoreConfig()
    
    store = FundamentalStore(store_config)
    return store.query_fundamentals(symbol, start_date, end_date)

def get_data_hub(config_path: str = None):
    """
    获取数据中心实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        DataHub: 数据中心实例
        
    Example:
        >>> hub = get_data_hub()
        >>> bars = hub.get_bars('000001.SZ', '2023-01-01', '2023-12-31')
    """
    return DataHub(config_path)

# ========== 便捷函数 ==========

def quick_bars(symbol: str, start_date: str, end_date: str, 
               interval: str = 'daily', provider: str = 'akshare', 
               save: bool = True, **kwargs):
    """
    快速获取并保存K线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        interval: 时间间隔
        provider: 数据提供者
        save: 是否保存到本地
        **kwargs: 其他参数
        
    Returns:
        List[BarData]: K线数据列表
        
    Example:
        >>> bars = quick_bars('000001.SZ', '2023-01-01', '2023-12-31')
    """
    bars = get_bars(symbol, start_date, end_date, interval, provider, **kwargs)
    if save:
        save_bars(bars)
    return bars

def quick_minute_bars(symbol: str, start_date: str, 
                     interval: str = '1m', provider: str = 'akshare', 
                     save: bool = True, **kwargs):
    """
    快速获取并保存分钟线数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        interval: 时间间隔
        provider: 数据提供者
        save: 是否保存到本地
        **kwargs: 其他参数
        
    Returns:
        List[BarData]: 分钟线数据列表
        
    Example:
        >>> minute_bars = quick_minute_bars('000001.SZ', '2023-01-01', '1m')
    """
    bars = get_minute_bars(symbol, start_date, interval, provider, **kwargs)
    if save:
        save_minute_bars(bars)
    return bars

# ========== 导出清单 ==========

__all__ = [
    # 数据类型
    'Exchange', 'Interval', 'BarData', 'FinancialData', 'FundamentalData',
    'FinancialReportType', 'ReportPeriod',
    'bars_to_df', 'df_to_bars', 'financials_to_df', 'df_to_financials',
    'fundamentals_to_df', 'df_to_fundamentals',
    
    # 数据提供者
    'BaseProvider', 'AkshareProvider', 'TuShareProvider', 'YFProvider', 
    'MinuteProvider', 'get_provider', 'PROVIDERS',
    
    # 数据服务
    'BaseDataService', 'BarDataService', 'FinancialDataService', 
    'FundamentalDataService', 'MinuteDataService', 'HistoricalDataService',
    'RESAMPLE_RULES',
    
    # 数据存储
    'StoreConfig', 'BaseStore', 'ManifestIndex',
    'BarStore', 'BarReader', 'load_multi_bars',
    'FinancialStore', 'save_financials', 'load_financials',
    'FundamentalStore',
    'MinuteStore', 'MinuteReader', 'load_multi_minutes', 'get_minute_store',
    
    # 数据库
    'DataHub', 'get_data_hub',
    
    # 统一接口
    'get_bars', 'get_minute_bars', 'get_financials', 'get_fundamentals',
    'save_bars', 'save_minute_bars', 'save_financials', 'save_fundamentals',
    'query_bars', 'query_minute_bars', 'query_financials', 'query_fundamentals',
    
    # 便捷函数
    'quick_bars', 'quick_minute_bars',
]

# ========== 版本信息 ==========
__version__ = "1.0.0"
__author__ = "AlphaGrid Team"
__email__ = "team@alphagrid.com"
