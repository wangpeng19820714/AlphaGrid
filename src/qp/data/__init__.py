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

# ========== 导入类型注解 ==========
from typing import List, Optional

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
    
    # 衍生数据类型
    AnnouncementData, NewsSentimentData, ResearchReportData,
    CapitalFlowData, ThemeData, DragonTigerData,
    AnnouncementType, NewsSentiment, ReportType, ReportRating,
    FlowType, FlowDirection, ThemeType, DragonTigerType, DragonTigerReason,
    
    # 第三方数据类型
    IndexComponentData, IndustryClassificationData, MacroData,
    IndexType, IndustryLevel, IndustryStandard, MacroDataType, DataFrequency,
    
    # 工具函数
    bars_to_df,
    df_to_bars,
    financials_to_df,
    df_to_financials,
    fundamentals_to_df,
    df_to_fundamentals,
    announcements_to_df, df_to_announcements,
    news_sentiments_to_df, df_to_news_sentiments,
    research_reports_to_df, df_to_research_reports,
    capital_flows_to_df, df_to_capital_flows,
    themes_to_df, df_to_themes,
    dragon_tigers_to_df, df_to_dragon_tigers,
    index_components_to_df, df_to_index_components,
    industry_classifications_to_df, df_to_industry_classifications,
    macro_data_to_df, df_to_macro_data,
)

# 数据提供者
from .providers import (
    BaseProvider,
    AkshareProvider,
    TuShareProvider,
    YFProvider,
    MinuteProvider,
    DerivativeProvider,
    MockDerivativeProvider,
    AkshareDerivativeProvider,
    ThirdPartyProvider,
    MockThirdPartyProvider,
    AkshareThirdPartyProvider,
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
    DerivativeDataService,
    ThirdPartyDataService,
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
    
    # 财务存储 - 已迁移到数据分层架构
    # FinancialStore, save_financials, load_financials,
    
    # 基本面存储 - 已迁移到数据分层架构
    # FundamentalStore,
    
    # 分钟线存储
    MinuteStore,
    MinuteReader,
    load_multi_minutes,
    get_minute_store,
    
    # 衍生数据存储
    DerivativeDataStore,
    AnnouncementStore,
    NewsSentimentStore,
    ResearchReportStore,
    CapitalFlowStore,
    ThemeStore,
    DragonTigerStore,
    get_derivative_store,
    
    # 第三方数据存储
    ThirdPartyStore,
    IndexComponentStore,
    IndustryClassificationStore,
    MacroDataStore,
    get_third_party_store,
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
    保存财务数据（已迁移到数据分层架构）
    
    注意：此函数已废弃，请使用新的数据分层架构
    """
    raise DeprecationWarning(
        "save_financials 已废弃，请使用 DataLayersPipeline.process_financial_data() "
        "或 ODSStore.save_financial_by_type()"
    )

def save_fundamentals(fundamentals, store_config: StoreConfig = None):
    """
    保存基本面数据（已迁移到数据分层架构）
    
    注意：此函数已废弃，请使用新的数据分层架构
    """
    raise DeprecationWarning(
        "save_fundamentals 已废弃，请使用 DataLayersPipeline.process_fundamental_data() "
        "或 ODSStore.save_fundamental()"
    )

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
    查询财务数据（已迁移到数据分层架构）
    
    注意：此函数已废弃，请使用新的数据分层架构
    """
    raise DeprecationWarning(
        "query_financials 已废弃，请使用 ODSStore.load_financial_by_type() "
        "或 DWDStore.load_financial()"
    )

def query_fundamentals(symbol: str, start_date: str, end_date: str, 
                      store_config: StoreConfig = None):
    """
    查询基本面数据（已迁移到数据分层架构）
    
    注意：此函数已废弃，请使用新的数据分层架构
    """
    raise DeprecationWarning(
        "query_fundamentals 已废弃，请使用 ODSStore.load_fundamental() "
        "或 DWDStore.load_fundamental()"
    )

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

# ========== 衍生数据统一接口函数 ==========

def get_announcements(symbol: str, start_date: str, end_date: str, 
                     announcement_type: str = None, provider: str = 'derivative', **kwargs):
    """
    获取公告数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        announcement_type: 公告类型过滤
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[AnnouncementData]: 公告数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_announcements(symbol, start_date, end_date, announcement_type)

def get_news_sentiments(symbol: str, start_date: str, end_date: str,
                       sentiment: str = None, provider: str = 'derivative', **kwargs):
    """
    获取新闻情绪数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        sentiment: 情绪类型过滤
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[NewsSentimentData]: 新闻情绪数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_news_sentiments(symbol, start_date, end_date, sentiment)

def get_research_reports(symbol: str, start_date: str, end_date: str,
                        report_type: str = None, rating: str = None, 
                        provider: str = 'derivative', **kwargs):
    """
    获取研报数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        report_type: 研报类型过滤
        rating: 评级过滤
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[ResearchReportData]: 研报数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_research_reports(symbol, start_date, end_date, report_type, rating)

def get_capital_flows(symbol: str, start_date: str, end_date: str,
                     flow_type: str = None, provider: str = 'derivative', **kwargs):
    """
    获取资金流数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        flow_type: 资金流类型过滤
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[CapitalFlowData]: 资金流数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_capital_flows(symbol, start_date, end_date, flow_type)

def get_themes(symbol: str, theme_type: str = None, provider: str = 'derivative', **kwargs):
    """
    获取板块/主题数据
    
    Args:
        symbol: 股票代码
        theme_type: 主题类型过滤
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[ThemeData]: 主题数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_themes(symbol, theme_type)

def get_dragon_tigers(symbol: str, start_date: str, end_date: str,
                     dragon_tiger_type: str = None, provider: str = 'derivative', **kwargs):
    """
    获取龙虎榜数据
    
    Args:
        symbol: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        dragon_tiger_type: 龙虎榜类型过滤
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[DragonTigerData]: 龙虎榜数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_dragon_tigers(symbol, start_date, end_date, dragon_tiger_type)

# ========== 第三方数据统一接口函数 ==========

def get_index_components(index_code: str, date: str = None, 
                        provider: str = 'third_party', **kwargs):
    """
    获取指数成分数据
    
    Args:
        index_code: 指数代码
        date: 查询日期，如果为None则获取最新数据
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[IndexComponentData]: 指数成分数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_index_components(index_code, date)

def get_industry_classifications(symbol: str, industry_standard: str = None,
                               industry_level: str = None, provider: str = 'third_party', **kwargs):
    """
    获取行业分类数据
    
    Args:
        symbol: 股票代码
        industry_standard: 行业分类标准
        industry_level: 行业分类级别
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[IndustryClassificationData]: 行业分类数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_industry_classifications(symbol, industry_standard, industry_level)

def get_macro_data(data_code: str, start_date: str, end_date: str,
                  data_type: str = None, provider: str = 'third_party', **kwargs):
    """
    获取宏观数据
    
    Args:
        data_code: 数据代码
        start_date: 开始日期
        end_date: 结束日期
        data_type: 数据类型过滤
        provider: 数据提供者
        **kwargs: 其他参数
        
    Returns:
        List[MacroData]: 宏观数据列表
    """
    provider_instance = get_provider(provider, **kwargs)
    return provider_instance.get_macro_data(data_code, start_date, end_date, data_type)

def save_index_components(components: List[IndexComponentData], 
                         store_config: StoreConfig = None) -> int:
    """
    保存指数成分数据
    
    Args:
        components: 指数成分数据列表
        store_config: 存储配置
        
    Returns:
        int: 保存的记录数
    """
    if store_config is None:
        store_config = StoreConfig(root="data/third_party")
    
    store = IndexComponentStore(store_config)
    return store.save_index_components(components)

def save_industry_classifications(classifications: List[IndustryClassificationData],
                                 store_config: StoreConfig = None) -> int:
    """
    保存行业分类数据
    
    Args:
        classifications: 行业分类数据列表
        store_config: 存储配置
        
    Returns:
        int: 保存的记录数
    """
    if store_config is None:
        store_config = StoreConfig(root="data/third_party")
    
    store = IndustryClassificationStore(store_config)
    return store.save_industry_classifications(classifications)

def save_macro_data(macro_data: List[MacroData], 
                   store_config: StoreConfig = None) -> int:
    """
    保存宏观数据
    
    Args:
        macro_data: 宏观数据列表
        store_config: 存储配置
        
    Returns:
        int: 保存的记录数
    """
    if store_config is None:
        store_config = StoreConfig(root="data/third_party")
    
    store = MacroDataStore(store_config)
    return store.save_macro_data(macro_data)

def query_index_components(index_code: str, effective_date: str = None,
                          store_config: StoreConfig = None) -> List[IndexComponentData]:
    """
    查询指数成分数据
    
    Args:
        index_code: 指数代码
        effective_date: 生效日期
        store_config: 存储配置
        
    Returns:
        List[IndexComponentData]: 指数成分数据列表
    """
    if store_config is None:
        store_config = StoreConfig(root="data/third_party")
    
    store = IndexComponentStore(store_config)
    return store.load_index_components(index_code, effective_date)

def query_industry_classifications(symbol: str, industry_standard: str = None,
                                 industry_level: str = None,
                                 store_config: StoreConfig = None) -> List[IndustryClassificationData]:
    """
    查询行业分类数据
    
    Args:
        symbol: 股票代码
        industry_standard: 行业分类标准
        industry_level: 行业分类级别
        store_config: 存储配置
        
    Returns:
        List[IndustryClassificationData]: 行业分类数据列表
    """
    if store_config is None:
        store_config = StoreConfig(root="data/third_party")
    
    store = IndustryClassificationStore(store_config)
    return store.load_industry_classifications(symbol, industry_standard, industry_level)

def query_macro_data(data_code: str, start_date: str = None, end_date: str = None,
                    data_type: str = None, store_config: StoreConfig = None) -> List[MacroData]:
    """
    查询宏观数据
    
    Args:
        data_code: 数据代码
        start_date: 开始日期
        end_date: 结束日期
        data_type: 数据类型过滤
        store_config: 存储配置
        
    Returns:
        List[MacroData]: 宏观数据列表
    """
    if store_config is None:
        store_config = StoreConfig(root="data/third_party")
    
    store = MacroDataStore(store_config)
    return store.load_macro_data(data_code, start_date, end_date, data_type)

# ========== 导出清单 ==========

__all__ = [
    # 数据类型
    'Exchange', 'Interval', 'BarData', 'FinancialData', 'FundamentalData',
    'FinancialReportType', 'ReportPeriod',
    'bars_to_df', 'df_to_bars', 'financials_to_df', 'df_to_financials',
    'fundamentals_to_df', 'df_to_fundamentals',
    
    # 衍生数据类型
    'AnnouncementData', 'NewsSentimentData', 'ResearchReportData',
    'CapitalFlowData', 'ThemeData', 'DragonTigerData',
    'AnnouncementType', 'NewsSentiment', 'ReportType', 'ReportRating',
    'FlowType', 'FlowDirection', 'ThemeType', 'DragonTigerType', 'DragonTigerReason',
    'announcements_to_df', 'df_to_announcements',
    'news_sentiments_to_df', 'df_to_news_sentiments',
    'research_reports_to_df', 'df_to_research_reports',
    'capital_flows_to_df', 'df_to_capital_flows',
    'themes_to_df', 'df_to_themes',
    'dragon_tigers_to_df', 'df_to_dragon_tigers',
    
    # 第三方数据类型
    'IndexComponentData', 'IndustryClassificationData', 'MacroData',
    'IndexType', 'IndustryLevel', 'IndustryStandard', 'MacroDataType', 'DataFrequency',
    'index_components_to_df', 'df_to_index_components',
    'industry_classifications_to_df', 'df_to_industry_classifications',
    'macro_data_to_df', 'df_to_macro_data',
    
    # 数据提供者
    'BaseProvider', 'AkshareProvider', 'TuShareProvider', 'YFProvider', 
    'MinuteProvider', 'DerivativeProvider', 'MockDerivativeProvider', 'AkshareDerivativeProvider',
    'ThirdPartyProvider', 'MockThirdPartyProvider', 'AkshareThirdPartyProvider',
    'get_provider', 'PROVIDERS',
    
    # 数据服务
    'BaseDataService', 'BarDataService', 'FinancialDataService', 
    'FundamentalDataService', 'MinuteDataService', 'DerivativeDataService',
    'ThirdPartyDataService', 'HistoricalDataService', 'RESAMPLE_RULES',
    
    # 数据存储
    'StoreConfig', 'BaseStore', 'ManifestIndex',
    'BarStore', 'BarReader', 'load_multi_bars',
    'FinancialStore', 'save_financials', 'load_financials',
    'FundamentalStore',
    'MinuteStore', 'MinuteReader', 'load_multi_minutes', 'get_minute_store',
    'DerivativeDataStore', 'AnnouncementStore', 'NewsSentimentStore',
    'ResearchReportStore', 'CapitalFlowStore', 'ThemeStore', 'DragonTigerStore',
    'get_derivative_store',
    'ThirdPartyStore', 'IndexComponentStore', 'IndustryClassificationStore',
    'MacroDataStore', 'get_third_party_store',
    
    # 数据库
    'DataHub', 'get_data_hub',
    
    # 统一接口
    'get_bars', 'get_minute_bars', 'get_financials', 'get_fundamentals',
    'save_bars', 'save_minute_bars', 'save_financials', 'save_fundamentals',
    'query_bars', 'query_minute_bars', 'query_financials', 'query_fundamentals',
    
    # 衍生数据接口
    'get_announcements', 'get_news_sentiments', 'get_research_reports',
    'get_capital_flows', 'get_themes', 'get_dragon_tigers',
    
    # 第三方数据接口
    'get_index_components', 'get_industry_classifications', 'get_macro_data',
    'save_index_components', 'save_industry_classifications', 'save_macro_data',
    'query_index_components', 'query_industry_classifications', 'query_macro_data',
    
    # 便捷函数
    'quick_bars', 'quick_minute_bars',
]

# ========== 版本信息 ==========
__version__ = "1.0.0"
__author__ = "AlphaGrid Team"
__email__ = "team@alphagrid.com"
