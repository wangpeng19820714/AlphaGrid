"""
数据接口模块

提供数据获取的接口函数，用于选股模块
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import logging

# 导入数据API
try:
    from ..data import get_price, get_fundamental, get_universe_meta
except ImportError:
    # 如果导入失败，使用本地实现
    from .data_interface import get_price, get_fundamental, get_universe_meta

logger = logging.getLogger(__name__)


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
        价格数据DataFrame
    """
    try:
        from ..data import get_price as api_get_price
        return api_get_price(symbols, start_offset, end_date, freq, adjust)
    except ImportError:
        # 本地实现
        logger.warning("使用本地价格数据实现")
        return _local_get_price(symbols, start_offset, end_date, freq, adjust)


def get_fundamental(symbols: List[str], asof_date: str, 
                   fields: List[str]) -> pd.DataFrame:
    """
    获取基本面数据
    
    Args:
        symbols: 股票代码列表
        asof_date: 截止日期
        fields: 需要获取的字段列表
        
    Returns:
        基本面数据DataFrame
    """
    try:
        from ..data import get_fundamental as api_get_fundamental
        return api_get_fundamental(symbols, asof_date, fields)
    except ImportError:
        # 本地实现
        logger.warning("使用本地基本面数据实现")
        return _local_get_fundamental(symbols, asof_date, fields)


def get_universe_meta(universe: str, asof_date: str) -> pd.DataFrame:
    """
    获取股票池元数据
    
    Args:
        universe: 股票池名称
        asof_date: 截止日期
        
    Returns:
        股票池元数据DataFrame
    """
    try:
        from ..data import get_universe_meta as api_get_universe_meta
        return api_get_universe_meta(universe, asof_date)
    except ImportError:
        # 本地实现
        logger.warning("使用本地股票池元数据实现")
        return _local_get_universe_meta(universe, asof_date)


def _local_get_price(symbols: List[str], start_offset: int, end_date: str, 
                     freq: str = "1d", adjust: str = "adj") -> pd.DataFrame:
    """
    本地价格数据实现
    """
    from datetime import datetime, timedelta
    
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
    
    return pd.DataFrame(data)


def _local_get_fundamental(symbols: List[str], asof_date: str, 
                          fields: List[str]) -> pd.DataFrame:
    """
    本地基本面数据实现
    """
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
    
    return pd.DataFrame(data)


def _local_get_universe_meta(universe: str, asof_date: str) -> pd.DataFrame:
    """
    本地股票池元数据实现
    """
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
    
    return pd.DataFrame(data)


def create_data_interface():
    """
    创建数据接口实例
    
    Returns:
        数据接口实例
    """
    class DataInterface:
        """数据接口类"""
        
        def __init__(self):
            self.logger = logging.getLogger(__name__)
        
        def get_price_data(self, symbols: List[str], start_offset: int, end_date: str, 
                          freq: str = "1d", adjust: str = "adj") -> pd.DataFrame:
            """获取价格数据"""
            return get_price(symbols, start_offset, end_date, freq, adjust)
        
        def get_fundamental_data(self, symbols: List[str], asof_date: str, 
                               fields: List[str]) -> pd.DataFrame:
            """获取基本面数据"""
            return get_fundamental(symbols, asof_date, fields)
        
        def get_universe_meta_data(self, universe: str, asof_date: str) -> pd.DataFrame:
            """获取股票池元数据"""
            return get_universe_meta(universe, asof_date)
        
        def get_universe_symbols(self, universe: str) -> List[str]:
            """获取股票池中的股票代码列表"""
            # 使用当前日期作为截止日期
            from datetime import datetime
            asof_date = datetime.now().strftime("%Y-%m-%d")
            meta = get_universe_meta(universe, asof_date)
            return meta['symbol'].tolist()
    
    return DataInterface()