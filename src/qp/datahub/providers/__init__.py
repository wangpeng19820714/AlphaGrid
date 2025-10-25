# quant/datahub/providers/__init__.py
"""
数据提供者模块
统一管理不同数据源的接口
"""
from .base import BaseProvider
from .akshare_provider import AkshareProvider
from .tushare_provider import TuShareProvider
from .yfinance_provider import YFProvider
from .minute_provider import MinuteProvider

# 提供者注册表
PROVIDERS = {
    "akshare": AkshareProvider,
    "tushare": TuShareProvider,
    "yfinance": YFProvider,
    "minute": MinuteProvider,
}

def get_provider(name: str, **kwargs) -> BaseProvider:
    """
    获取数据提供者实例
    
    Args:
        name: 提供者名称 ('akshare', 'tushare', 'yfinance')
        **kwargs: 提供者初始化参数
        
    Returns:
        数据提供者实例
        
    Example:
        >>> provider = get_provider('tushare', token='your_token')
        >>> provider = get_provider('akshare')
    """
    if name not in PROVIDERS:
        raise ValueError(f"未知的数据提供者: {name}. 可选: {list(PROVIDERS.keys())}")
    return PROVIDERS[name](**kwargs)

__all__ = [
    'BaseProvider',
    'AkshareProvider',
    'TuShareProvider',
    'YFProvider',
    'MinuteProvider',
    'get_provider',
    'PROVIDERS',
]

