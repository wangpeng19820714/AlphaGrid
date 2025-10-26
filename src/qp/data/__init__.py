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
from typing import List, Optional, Dict, Any
import pandas as pd

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

# ========== 研究层数据API ==========

def get_price(symbols: List[str], start_offset: int, end_date: str, 
              freq: str = "1d", adjust: str = "adj") -> pd.DataFrame:
    """
    获取价格数据
    
    Args:
        symbols: 股票代码列表
        start_offset: 开始日期偏移量（负数表示向前偏移）
        end_date: 结束日期
        freq: 频率，默认"1d"（日线）
        adjust: 复权方式，"adj"表示前复权
        
    Returns:
        价格数据DataFrame，包含列: symbol, trade_date, close, open, high, low, volume, amount, vwap
    """
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"获取价格数据，股票数: {len(symbols)}, 结束日期: {end_date}, 频率: {freq}")
    
    try:
        # 计算开始日期
        end_dt = pd.to_datetime(end_date)
        start_dt = end_dt + timedelta(days=start_offset)
        
        # 生成日期范围
        dates = pd.date_range(start=start_dt, end=end_dt, freq=freq)
        
        # 模拟价格数据生成
        data = []
        np.random.seed(42)  # 确保结果可重现
        
        for symbol in symbols:
            # 为每只股票生成基础价格
            base_price = 10 + np.random.normal(0, 2)
            
            for trade_date in dates:
                # 模拟价格走势
                price_change = np.random.normal(0, 0.02)
                base_price *= (1 + price_change)
                
                # 确保价格为正
                close = max(base_price, 0.1)
                
                # 生成其他价格字段
                open_price = close * (1 + np.random.normal(0, 0.01))
                high = max(open_price, close) * (1 + abs(np.random.normal(0, 0.01)))
                low = min(open_price, close) * (1 - abs(np.random.normal(0, 0.01)))
                
                # 生成成交量和成交额
                volume = np.random.randint(1000000, 10000000)
                amount = close * volume
                vwap = close * (1 + np.random.normal(0, 0.005))  # 模拟VWAP
                
                data.append({
                    'symbol': symbol,
                    'trade_date': trade_date,
                    'close': close,
                    'open': open_price,
                    'high': high,
                    'low': low,
                    'volume': volume,
                    'amount': amount,
                    'vwap': vwap
                })
        
        df = pd.DataFrame(data)
        logger.info(f"价格数据获取完成，记录数: {len(df)}")
        return df
        
    except Exception as e:
        logger.error(f"获取价格数据失败: {e}")
        return pd.DataFrame()


def get_fundamental(symbols: List[str], asof_date: str, 
                   fields: List[str]) -> pd.DataFrame:
    """
    获取基本面数据（PIT对齐）
    
    Args:
        symbols: 股票代码列表
        asof_date: 截止日期（PIT对齐）
        fields: 需要获取的字段列表
        
    Returns:
        基本面数据DataFrame，包含列: symbol, pe_ttm, industry, free_float_mkt_cap等
    """
    import pandas as pd
    import numpy as np
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"获取基本面数据，股票数: {len(symbols)}, 截止日期: {asof_date}")
    
    try:
        # 模拟基本面数据生成
        data = []
        np.random.seed(42)  # 确保结果可重现
        
        # 行业分类
        industries = ['银行', '科技', '医药', '消费', '制造', '地产', '能源', '材料', '公用事业', '金融']
        
        for symbol in symbols:
            row = {'symbol': symbol}
            
            # 根据字段列表生成数据
            if 'pe_ttm' in fields:
                row['pe_ttm'] = np.random.uniform(5, 50)
            
            if 'industry' in fields:
                row['industry'] = np.random.choice(industries)
            
            if 'free_float_mkt_cap' in fields:
                row['free_float_mkt_cap'] = np.random.uniform(1e8, 1e12)
            
            if 'market_cap' in fields:
                row['market_cap'] = np.random.uniform(1e8, 1e12)
            
            if 'pb_ratio' in fields:
                row['pb_ratio'] = np.random.uniform(0.5, 5.0)
            
            if 'ps_ratio' in fields:
                row['ps_ratio'] = np.random.uniform(0.5, 10.0)
            
            if 'roe' in fields:
                row['roe'] = np.random.uniform(0.05, 0.25)
            
            if 'roa' in fields:
                row['roa'] = np.random.uniform(0.02, 0.15)
            
            if 'revenue_growth_yoy' in fields:
                row['revenue_growth_yoy'] = np.random.uniform(-0.2, 0.5)
            
            if 'profit_growth_yoy' in fields:
                row['profit_growth_yoy'] = np.random.uniform(-0.3, 0.6)
            
            data.append(row)
        
        df = pd.DataFrame(data)
        logger.info(f"基本面数据获取完成，记录数: {len(df)}")
        return df
        
    except Exception as e:
        logger.error(f"获取基本面数据失败: {e}")
        return pd.DataFrame()


def get_universe_meta(universe: str, asof_date: str) -> pd.DataFrame:
    """
    获取股票池元数据
    
    Args:
        universe: 股票池名称（如CSI300, CSI500等）
        asof_date: 截止日期（PIT对齐）
        
    Returns:
        股票池元数据DataFrame，包含列: symbol, is_tradable, industry, free_float_mkt_cap, is_st, is_suspended等
    """
    import pandas as pd
    import numpy as np
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"获取股票池元数据，股票池: {universe}, 截止日期: {asof_date}")
    
    try:
        # 模拟股票池数据
        data = []
        np.random.seed(42)  # 确保结果可重现
        
        # 根据股票池生成不同的股票列表
        if universe == "CSI300":
            symbols = [f"{i:06d}" for i in range(1, 301)]  # 000001-000300
        elif universe == "CSI500":
            symbols = [f"{i:06d}" for i in range(1, 501)]  # 000001-000500
        elif universe == "CSI1000":
            symbols = [f"{i:06d}" for i in range(1, 1001)]  # 000001-001000
        else:
            # 默认股票池
            symbols = [f"{i:06d}" for i in range(1, 101)]  # 000001-000100
        
        # 行业分类
        industries = ['银行', '科技', '医药', '消费', '制造', '地产', '能源', '材料', '公用事业', '金融']
        
        for symbol in symbols:
            # 模拟股票状态
            is_tradable = np.random.random() > 0.05  # 95%的股票可交易
            is_st = np.random.random() < 0.02  # 2%的股票是ST
            is_suspended = np.random.random() < 0.01  # 1%的股票停牌
            is_limit_up = np.random.random() < 0.01  # 1%的股票涨停
            is_limit_down = np.random.random() < 0.01  # 1%的股票跌停
            
            # 如果股票是ST、停牌、涨跌停，则不可交易
            if is_st or is_suspended or is_limit_up or is_limit_down:
                is_tradable = False
            
            row = {
                'symbol': symbol,
                'is_tradable': is_tradable,
                'industry': np.random.choice(industries),
                'free_float_mkt_cap': np.random.uniform(1e8, 1e12),
                'is_st': is_st,
                'is_suspended': is_suspended,
                'is_limit_up': is_limit_up,
                'is_limit_down': is_limit_down
            }
            
            data.append(row)
        
        df = pd.DataFrame(data)
        logger.info(f"股票池元数据获取完成，股票数: {len(df)}, 可交易股票数: {df['is_tradable'].sum()}")
        return df
        
    except Exception as e:
        logger.error(f"获取股票池元数据失败: {e}")
        return pd.DataFrame()


def get_stock_universe(universe: str, asof_date: str) -> List[str]:
    """
    获取股票池中的股票代码列表
    
    Args:
        universe: 股票池名称
        asof_date: 截止日期
        
    Returns:
        股票代码列表
    """
    meta = get_universe_meta(universe, asof_date)
    return meta['symbol'].tolist()


def get_tradable_stocks(universe: str, asof_date: str) -> List[str]:
    """
    获取股票池中可交易的股票代码列表
    
    Args:
        universe: 股票池名称
        asof_date: 截止日期
        
    Returns:
        可交易股票代码列表
    """
    meta = get_universe_meta(universe, asof_date)
    tradable = meta[meta['is_tradable']]
    return tradable['symbol'].tolist()


def validate_data_quality(df: pd.DataFrame, data_type: str) -> bool:
    """
    验证数据质量
    
    Args:
        df: 数据DataFrame
        data_type: 数据类型（price, fundamental, universe）
        
    Returns:
        数据质量是否合格
    """
    import logging
    
    logger = logging.getLogger(__name__)
    
    if df.empty:
        logger.warning(f"{data_type}数据为空")
        return False
    
    # 检查缺失值
    missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
    if missing_ratio > 0.1:  # 缺失值超过10%
        logger.warning(f"{data_type}数据缺失值比例过高: {missing_ratio:.2%}")
    
    # 检查重复值
    if df.duplicated().any():
        logger.warning(f"{data_type}数据存在重复记录")
    
    # 根据数据类型进行特定检查
    if data_type == "price":
        if 'close' in df.columns:
            if (df['close'] <= 0).any():
                logger.warning("价格数据存在非正值")
                return False
    
    elif data_type == "fundamental":
        if 'pe_ttm' in df.columns:
            if (df['pe_ttm'] <= 0).any():
                logger.warning("PE数据存在非正值")
                return False
    
    logger.info(f"{data_type}数据质量验证通过")
    return True


def get_data_summary(df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
    """
    获取数据摘要信息
    
    Args:
        df: 数据DataFrame
        data_type: 数据类型
        
    Returns:
        数据摘要字典
    """
    if df.empty:
        return {}
    
    summary = {
        'data_type': data_type,
        'total_records': len(df),
        'total_columns': len(df.columns),
        'date_range': None,
        'symbol_count': 0,
        'missing_ratio': df.isnull().sum().sum() / (len(df) * len(df.columns)),
        'duplicate_count': df.duplicated().sum()
    }
    
    # 根据数据类型添加特定信息
    if 'trade_date' in df.columns:
        summary['date_range'] = {
            'start': df['trade_date'].min(),
            'end': df['trade_date'].max()
        }
    
    if 'symbol' in df.columns:
        summary['symbol_count'] = df['symbol'].nunique()
    
    return summary

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
    
    # 研究层数据API
    'get_price', 'get_fundamental', 'get_universe_meta',
    'get_stock_universe', 'get_tradable_stocks',
    'validate_data_quality', 'get_data_summary',
]

# ========== 版本信息 ==========
__version__ = "1.0.0"
__author__ = "AlphaGrid Team"
__email__ = "team@alphagrid.com"
