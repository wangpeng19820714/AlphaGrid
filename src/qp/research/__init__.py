# qp/research/__init__.py
"""
量化研究模块

提供量化研究相关的功能，包括选股、因子计算、策略研究等。
"""

from .selector import (
    StockSelector,
    FactorCalculator,
    StockScreener,
    create_stock_selector,
    run_stock_selection,
)

__all__ = [
    "StockSelector",
    "FactorCalculator", 
    "StockScreener",
    "create_stock_selector",
    "run_stock_selection",
]
