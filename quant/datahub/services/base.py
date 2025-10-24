# quant/datahub/services/base.py
"""服务层基础类"""
from __future__ import annotations
from typing import Optional
from abc import ABC


class BaseDataService(ABC):
    """数据服务基类"""
    
    def __init__(self, config: Optional[dict] = None):
        """
        初始化服务
        
        Args:
            config: 服务配置字典
        """
        self.config = config or {}
    
    def _validate_symbol(self, symbol: str) -> str:
        """
        验证股票代码格式
        
        Args:
            symbol: 股票代码
            
        Returns:
            标准化的股票代码
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"无效的股票代码: {symbol}")
        return symbol.strip().upper()
    
    def _validate_date_range(self, start, end):
        """
        验证日期范围
        
        Args:
            start: 开始日期
            end: 结束日期
            
        Raises:
            ValueError: 如果日期范围无效
        """
        if start and end and start > end:
            raise ValueError(f"开始日期 {start} 不能晚于结束日期 {end}")

