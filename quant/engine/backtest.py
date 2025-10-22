# engine/backtest.py
# -*- coding: utf-8 -*-
"""
向量化回测引擎 - 收盘成交模式
支持费用、滑点、税费的向量化计算
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import Union, Tuple

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """计算平均真实波幅(ATR)"""
    required_cols = {"high", "low", "close"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"计算ATR需要列: {required_cols}")
    
    prev_close = df["close"].shift(1)
    tr = np.maximum(
        df["high"] - df["low"],
        np.maximum(
            (df["high"] - prev_close).abs(),
            (df["low"] - prev_close).abs()
        )
    )
    return tr.rolling(n, min_periods=n).mean()


def _apply_slippage(close: np.ndarray, fills: np.ndarray, slip_bp: float) -> np.ndarray:
    """应用方向敏感滑点"""
    slip_rate = slip_bp / 10000.0
    buy_price = close * (1.0 + slip_rate)
    sell_price = close * (1.0 - slip_rate)
    return np.where(fills >= 0, buy_price, sell_price)


def _calculate_commission(notional: np.ndarray, fee_bp: float) -> np.ndarray:
    """计算佣金费用"""
    return notional * (fee_bp / 10000.0)


def _calculate_tax(sell_notional: np.ndarray, tax_bp: float) -> np.ndarray:
    """计算卖出税费"""
    return sell_notional * (tax_bp / 10000.0)


def run_close_fill_backtest(
    df: pd.DataFrame,
    orders: Union[pd.Series, np.ndarray],
    fee_bp: float = 10.0,
    slip_bp: float = 2.0,
    tax_bp_sell: float = 0.0,
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    收盘成交的向量化回测
    
    Args:
        df: 包含'close'列的DataFrame，index为日期
        orders: 每日成交股数（正数买入，负数卖出）
        fee_bp: 佣金费率（基点），默认10bp
        slip_bp: 滑点（基点），默认2bp  
        tax_bp_sell: 卖出税费（基点），默认0
        
    Returns:
        (daily_pnl, position, fills, trade_price, fees, taxes)
    """
    # 数据验证和预处理
    if "close" not in df.columns:
        raise ValueError("DataFrame必须包含'close'列")
    
    close = df["close"].astype(float).values
    
    # 处理orders数据
    if isinstance(orders, pd.Series):
        orders = orders.reindex(df.index).fillna(0.0).values
    else:
        orders = np.asarray(orders, dtype=float)
        if len(orders) != len(df):
            raise ValueError("orders长度必须与DataFrame行数一致")
    
    # 计算成交价格（含滑点）
    fills = orders.copy()
    trade_price = _apply_slippage(close, fills, slip_bp)
    
    # 计算费用和税费
    notional = np.abs(fills) * trade_price
    fees = _calculate_commission(notional, fee_bp)
    
    sell_mask = fills < 0
    sell_notional = notional * sell_mask
    taxes = _calculate_tax(sell_notional, tax_bp_sell)
    
    # 计算持仓和收益
    position = np.cumsum(fills)
    prev_close = np.r_[close[0], close[:-1]]
    position_bod = position - fills  # 昨日收盘后仓位
    price_pnl = (close - prev_close) * position_bod
    
    # 计算日度PnL
    daily_pnl = price_pnl - fees - taxes
    
    # 构建返回结果
    index = df.index
    return (
        pd.Series(daily_pnl, index=index, name="daily_pnl"),
        pd.Series(position, index=index, name="position"),
        pd.Series(fills, index=index, name="fills"),
        pd.Series(trade_price, index=index, name="trade_price"),
        pd.Series(fees, index=index, name="fees"),
        pd.Series(taxes, index=index, name="taxes"),
    )


def run_vector_bt(
    df: pd.DataFrame,
    signal: Union[pd.Series, np.ndarray],
    sizer_shares: Union[pd.Series, np.ndarray],
    fee_bp: float = 10.0,
    slip_bp: float = 2.0,
    tax_bp_sell: float = 0.0,
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    兼容旧接口的便捷函数
    
    Args:
        df: 包含'close'列的DataFrame
        signal: 信号（仅保持兼容性，不参与计算）
        sizer_shares: 每日成交股数（正数买入，负数卖出）
        其他参数同run_close_fill_backtest
        
    Returns:
        同run_close_fill_backtest
    """
    return run_close_fill_backtest(
        df=df,
        orders=sizer_shares,
        fee_bp=fee_bp,
        slip_bp=slip_bp,
        tax_bp_sell=tax_bp_sell,
    )