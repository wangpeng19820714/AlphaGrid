# strategies/sma_cross.py
# -*- coding: utf-8 -*-
"""
双均线交叉策略信号生成器

功能特性：
- 支持SMA/EMA双均线交叉信号
- 两种信号模式：持续状态(regime)或交叉脉冲(on_cross)
- 容忍带机制避免噪音信号
- 支持仅做多模式和信号延迟
"""

from __future__ import annotations
import pandas as pd
import numpy as np

__all__ = ["sma_cross"]

def _calculate_moving_average(series: pd.Series, window: int, ma_type: str = "sma") -> pd.Series:
    """计算移动平均线"""
    if ma_type.lower() == "ema":
        return series.ewm(span=window, adjust=False, min_periods=window).mean()
    return series.rolling(window, min_periods=window).mean()

def _generate_raw_signals(fast_ma: pd.Series, slow_ma: pd.Series, band_bp: float) -> pd.Series:
    """生成原始信号：1(多头), -1(空头), 0(无信号)"""
    diff = fast_ma - slow_ma
    
    if band_bp > 0:
        # 使用容忍带避免噪音
        threshold = (band_bp / 10000.0) * slow_ma.abs().clip(lower=1e-12)
        signals = np.where(diff > threshold, 1, 
                          np.where(diff < -threshold, -1, 0))
    else:
        # 无容忍带，直接比较
        signals = np.where(diff > 0, 1, 
                          np.where(diff < 0, -1, 0))
    
    return pd.Series(signals, index=fast_ma.index, dtype=int)

def _apply_signal_mode(signals: pd.Series, mode: str) -> pd.Series:
    """应用信号模式：regime(持续状态) 或 on_cross(交叉脉冲)"""
    if mode == "regime":
        # 状态型：用前向填充保持信号状态
        return signals.replace(0, pd.NA).ffill().fillna(0).infer_objects(copy=False).astype(int)
    
    elif mode == "on_cross":
        # 脉冲型：仅在交叉时产生信号
        prev_signals = signals.shift(1).fillna(0)
        golden_cross = (prev_signals <= 0) & (signals > 0)  # 金叉
        death_cross = (prev_signals >= 0) & (signals < 0)   # 死叉
        
        pulse_signals = pd.Series(0, index=signals.index, dtype=int)
        pulse_signals[golden_cross] = 1
        pulse_signals[death_cross] = -1
        return pulse_signals
    
    else:
        raise ValueError(f"不支持的信号模式: {mode}。支持的模式: 'regime', 'on_cross'")

def sma_cross(
    df: pd.DataFrame,
    fast: int = 10,
    slow: int = 30,
    price_col: str = "close",
    ma: str = "sma",
    mode: str = "regime",
    band_bp: float = 0.0,
    long_only: bool = False,
    delay: int = 0,
) -> pd.Series:
    """
    双均线交叉策略信号生成器
    
    Parameters:
    -----------
    df : pd.DataFrame
        包含价格数据的DataFrame
    fast : int, default 10
        快均线周期
    slow : int, default 30  
        慢均线周期
    price_col : str, default 'close'
        价格列名
    ma : str, default 'sma'
        均线类型：'sma' 或 'ema'
    mode : str, default 'regime'
        信号模式：'regime'(持续状态) 或 'on_cross'(交叉脉冲)
    band_bp : float, default 0.0
        容忍带(基点)，避免噪音信号
    long_only : bool, default False
        是否仅做多(将-1信号转为0)
    delay : int, default 0
        信号延迟周期数
        
    Returns:
    --------
    pd.Series
        交易信号：1(买入), -1(卖出), 0(持有/无信号)
    """
    # 参数验证
    if price_col not in df.columns:
        raise ValueError(f"DataFrame中缺少价格列: '{price_col}'")
    if fast <= 0 or slow <= 0:
        raise ValueError("均线周期必须为正整数")
    if fast >= slow:
        print(f"警告: 快均线周期({fast}) >= 慢均线周期({slow})，建议 fast < slow")
    
    # 计算均线
    price = df[price_col].astype(float)
    fast_ma = _calculate_moving_average(price, fast, ma)
    slow_ma = _calculate_moving_average(price, slow, ma)
    
    # 生成原始信号
    signals = _generate_raw_signals(fast_ma, slow_ma, band_bp)
    
    # 应用信号模式
    signals = _apply_signal_mode(signals, mode)
    
    # 应用约束条件
    if long_only:
        signals = signals.clip(lower=0)
    
    if delay > 0:
        signals = signals.shift(delay).fillna(0).astype(int)
    
    # 处理均线未成熟期
    first_valid_idx = slow_ma.first_valid_index()
    if first_valid_idx is not None:
        signals.loc[:first_valid_idx] = 0
    
    return signals

# 测试示例
if __name__ == "__main__":
    # 创建测试数据：先上涨后下跌的价格序列
    dates = pd.date_range("2024-01-01", periods=60, freq="B")
    prices = np.concatenate([
        np.linspace(10, 12, 30),  # 上涨阶段
        np.linspace(12, 11, 30)   # 下跌阶段
    ])
    
    test_df = pd.DataFrame({"close": prices}, index=dates)
    
    # 测试不同参数组合
    print("=== 双均线交叉策略测试 ===")
    
    # 基础测试
    signals = sma_cross(test_df, fast=5, slow=20, mode="regime")
    print(f"\n基础信号 (regime模式):\n{signals.tail(10)}")
    
    # 脉冲模式测试
    pulse_signals = sma_cross(test_df, fast=5, slow=20, mode="on_cross")
    print(f"\n脉冲信号 (on_cross模式):\n{pulse_signals.tail(10)}")
    
    # 仅做多模式测试
    long_only_signals = sma_cross(test_df, fast=5, slow=20, long_only=True)
    print(f"\n仅做多信号:\n{long_only_signals.tail(10)}")
    
    print(f"\n信号统计:")
    print(f"总信号数: {len(signals)}")
    print(f"买入信号: {(signals == 1).sum()}")
    print(f"卖出信号: {(signals == -1).sum()}")
    print(f"持有信号: {(signals == 0).sum()}")