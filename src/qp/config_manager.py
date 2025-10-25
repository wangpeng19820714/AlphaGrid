# quant/config_manager.py
# -*- coding: utf-8 -*-
"""
统一配置管理模块
集中管理回测参数、路径配置等
"""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import sys

@dataclass
class BacktestConfig:
    """回测配置"""
    # 初始资金
    capital: float = 1_000_000.0
    # 费用设置（基点）
    fee_bp: float = 10.0
    slip_bp: float = 2.0
    tax_bp_sell: float = 0.0
    # 风险参数
    rf_annual: float = 0.02  # 年化无风险利率
    trading_days: int = 252
    # 仓位管理
    position_size: int = 1000  # 每次交易股数
    lot_size: int = 1  # 最小交易单位

@dataclass
class PathConfig:
    """路径配置"""
    data_dir: str = "data"
    cache_dir: str = "cache"
    reports_dir: str = "reports"
    
    def __post_init__(self):
        """确保目录存在"""
        for dir_attr in ['data_dir', 'cache_dir', 'reports_dir']:
            dir_path = Path(getattr(self, dir_attr))
            dir_path.mkdir(parents=True, exist_ok=True)

@dataclass
class DisplayConfig:
    """显示配置"""
    use_emoji: bool = True
    decimal_places: int = 2
    column_width: int = 12
    
    @staticmethod
    def setup_utf8_output():
        """设置 UTF-8 输出（Windows）"""
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

@dataclass
class StrategyConfig:
    """策略配置"""
    # SMA 双均线参数
    fast_period: int = 10
    slow_period: int = 30
    band_bp: float = 5.0  # 容忍带
    long_only: bool = False
    delay: int = 1  # 信号滞后

@dataclass
class GlobalConfig:
    """全局配置"""
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    path: PathConfig = field(default_factory=PathConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    strategy: StrategyConfig = field(default_factory=StrategyConfig)
    
    @classmethod
    def default(cls) -> GlobalConfig:
        """获取默认配置"""
        return cls()

# 全局配置实例
_config: Optional[GlobalConfig] = None

def get_config() -> GlobalConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = GlobalConfig.default()
    return _config

def set_config(config: GlobalConfig):
    """设置全局配置"""
    global _config
    _config = config

