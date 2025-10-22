
# engine/risk.py
# -*- coding: utf-8 -*-
"""
风险管理模块
- 权重调仓：根据目标权重生成调仓订单
- POV 约束：按成交量比例限制交易
- 风险控制：各种风险管理工具
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Optional, Union


def rebalance_to_weights_orders(
    df_prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    capital: float = 1_000_000.0,
    lot_size: int = 1,
) -> pd.Series:
    """
    根据目标权重生成调仓订单
    
    参数:
        df_prices: 价格数据，MultiIndex [symbol, date]，需包含 'close' 列
        target_weights: 目标权重，DataFrame(index=date, columns=symbol)
        capital: 初始资金
        lot_size: 最小交易单位
        
    返回:
        调仓订单，MultiIndex [symbol, date]，单位：股
    """
    if "close" not in df_prices.columns:
        raise ValueError("df_prices 需要包含 'close' 列")
    
    # 转换价格数据为宽表格式
    prices = df_prices["close"].unstack(level=0)
    prices = prices.reindex(index=target_weights.index, columns=target_weights.columns)
    
    # 计算目标股数
    target_shares = _calculate_target_shares(target_weights, prices, capital, lot_size)
    
    # 生成调仓订单
    orders = _generate_rebalance_orders(target_shares, lot_size)
    
    return orders


def _calculate_target_shares(
    weights: pd.DataFrame, 
    prices: pd.DataFrame, 
    capital: float, 
    lot_size: int
) -> pd.DataFrame:
    """计算目标股数"""
    # 目标市值 = 权重 × 资金
    target_value = weights * capital
    
    # 目标股数 = 目标市值 / 价格
    target_shares = target_value / prices
    
    # 向下取整到最小交易单位
    target_shares = np.floor(target_shares / lot_size) * lot_size
    
    return target_shares.fillna(0.0)


def _generate_rebalance_orders(target_shares: pd.DataFrame, lot_size: int) -> pd.Series:
    """生成调仓订单"""
    orders_records = []
    prev_position = pd.Series(0.0, index=target_shares.columns)
    
    for date, target_row in target_shares.iterrows():
        target = target_row.fillna(0.0)
        
        # 计算调仓量 = 目标 - 当前
        rebalance = target - prev_position
        
        # 处理最小交易单位
        if lot_size > 1:
            rebalance = np.round(rebalance / lot_size) * lot_size
        
        # 记录非零订单
        for symbol, quantity in rebalance.items():
            if quantity != 0 and not np.isnan(quantity):
                orders_records.append((symbol, date, quantity))
        
        prev_position = target
    
    # 构建结果
    if not orders_records:
        return _create_empty_orders(target_shares)
    
    symbols, dates, quantities = zip(*orders_records)
    index = pd.MultiIndex.from_tuples(
        list(zip(symbols, dates)), 
        names=["symbol", "date"]
    )
    
    return pd.Series(quantities, index=index, dtype=float)


def _create_empty_orders(target_shares: pd.DataFrame) -> pd.Series:
    """创建空的订单序列"""
    index = pd.MultiIndex.from_product(
        [target_shares.columns, target_shares.index], 
        names=["symbol", "date"]
    )
    return pd.Series(0.0, index=index)


# ========== POV 约束 ==========

def apply_pov_constraints(
    df: pd.DataFrame,
    raw_orders: pd.Series,
    pov: float = 0.1,
    min_clip: int = 1,
) -> pd.Series:
    """
    按 POV 约束订单并滚动未成交部分
    
    参数:
        df: 价格数据，MultiIndex [symbol, date]，需包含 'volume' 列
        raw_orders: 原始订单，MultiIndex [symbol, date]
        pov: 参与率限制 (0-1)
        min_clip: 最小交易单位
        
    返回:
        约束后的可执行订单
    """
    # 验证数据
    if "volume" not in df.columns:
        raise ValueError("需要 'volume' 列")
    
    if df.index.names != ["symbol", "date"]:
        df = df.copy()
        df.index = df.index.set_names(["symbol", "date"])
    
    if not isinstance(raw_orders, pd.Series):
        raise ValueError("raw_orders 必须是 MultiIndex Series")
    
    # 准备数据
    volume_wide = df["volume"].unstack(level="symbol").fillna(0.0)
    orders_wide = raw_orders.unstack(level="symbol").reindex(
        index=volume_wide.index, 
        columns=volume_wide.columns
    ).fillna(0.0)
    
    # 执行 POV 约束
    executed_orders = _apply_pov_daily(volume_wide, orders_wide, pov, min_clip)
    
    return executed_orders


def _apply_pov_daily(
    volume_wide: pd.DataFrame,
    orders_wide: pd.DataFrame,
    pov: float,
    min_clip: int
) -> pd.Series:
    """逐日应用 POV 约束"""
    symbols = volume_wide.columns
    dates = volume_wide.index
    
    # 初始化状态
    backlogs = pd.Series(0.0, index=symbols)
    executed_wide = pd.DataFrame(0.0, index=dates, columns=symbols)
    
    for date in dates:
        # 当日意向订单（含 backlog）
        want_today = orders_wide.loc[date] + backlogs
        
        # 计算当日容量
        capacity = volume_wide.loc[date] * pov
        
        # 应用 POV 约束
        filled_today = _apply_pov_single_day(want_today, capacity, min_clip)
        
        # 记录执行结果
        executed_wide.loc[date] = filled_today
        
        # 更新 backlog
        backlogs = want_today - filled_today
    
    # 转换回 MultiIndex Series
    executed = executed_wide.stack()
    executed.index = executed.index.set_names(["date", "symbol"])
    executed = executed.reorder_levels(["symbol", "date"]).sort_index()
    
    return executed


def _apply_pov_single_day(
    want_orders: pd.Series,
    capacity: pd.Series,
    min_clip: int
) -> pd.Series:
    """单日 POV 约束"""
    min_clip = max(min_clip, 1)
    
    # 分别处理买单和卖单
    buy_orders = want_orders.clip(lower=0.0)
    sell_orders = want_orders.clip(upper=0.0)
    
    # 计算可执行量
    buy_exec = np.minimum(buy_orders, np.floor(capacity / min_clip) * min_clip)
    sell_exec = np.maximum(sell_orders, -np.floor(capacity / min_clip) * min_clip)
    
    return buy_exec + sell_exec


# ========== 风险控制工具 ==========

def calculate_position_limits(
    df_prices: pd.DataFrame,
    max_weight: float = 0.1,
    max_position_value: Optional[float] = None,
    capital: float = 1_000_000.0,
) -> pd.DataFrame:
    """
    计算持仓限制
    
    参数:
        df_prices: 价格数据，MultiIndex [symbol, date]
        max_weight: 最大权重限制
        max_position_value: 最大持仓金额限制
        capital: 总资金
        
    返回:
        持仓限制 DataFrame
    """
    if "close" not in df_prices.columns:
        raise ValueError("需要 'close' 列")
    
    # 转换价格数据
    prices = df_prices["close"].unstack(level=0)
    
    # 计算权重限制
    weight_limits = pd.DataFrame(max_weight, index=prices.index, columns=prices.columns)
    
    # 计算金额限制
    if max_position_value is not None:
        value_limits = pd.DataFrame(
            max_position_value / capital, 
            index=prices.index, 
            columns=prices.columns
        )
        # 取更严格的限制
        weight_limits = np.minimum(weight_limits, value_limits)
    
    return weight_limits


def apply_position_limits(
    target_weights: pd.DataFrame,
    position_limits: pd.DataFrame,
    normalize: bool = True,
) -> pd.DataFrame:
    """
    应用持仓限制
    
    参数:
        target_weights: 目标权重
        position_limits: 持仓限制
        normalize: 是否重新归一化
        
    返回:
        限制后的权重
    """
    # 对齐数据
    aligned_weights = target_weights.reindex(
        index=position_limits.index,
        columns=position_limits.columns
    ).fillna(0.0)
    
    # 应用限制
    limited_weights = np.minimum(aligned_weights, position_limits)
    
    # 重新归一化（如果启用）
    if normalize:
        row_sums = limited_weights.sum(axis=1)
        # 只对非零行进行归一化
        non_zero_rows = row_sums > 0
        if non_zero_rows.any():
            limited_weights.loc[non_zero_rows] = limited_weights.loc[non_zero_rows].div(
                row_sums[non_zero_rows], axis=0
            )
    
    return limited_weights


def calculate_risk_metrics(
    returns: pd.Series,
    window: int = 252,
) -> dict:
    """
    计算风险指标
    
    参数:
        returns: 收益率序列
        window: 滚动窗口
        
    返回:
        风险指标字典
    """
    if returns.empty:
        return {}
    
    # 基础统计
    mean_return = returns.mean()
    volatility = returns.std()
    
    # 滚动统计
    rolling_vol = returns.rolling(window).std()
    
    # 最大回撤
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.rolling(window).max()
    drawdown = (cumulative - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    
    # VaR (95% 置信度)
    var_95 = returns.quantile(0.05)
    
    # 夏普比率（假设无风险利率为 0）
    sharpe_ratio = mean_return / volatility if volatility > 0 else 0
    
    return {
        "mean_return": mean_return,
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "var_95": var_95,
        "sharpe_ratio": sharpe_ratio,
        "rolling_volatility": rolling_vol,
        "drawdown": drawdown,
    }


def rebalance_with_risk_limits(
    df_prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    capital: float = 1_000_000.0,
    max_weight: float = 0.1,
    lot_size: int = 1,
    pov: Optional[float] = None,
) -> pd.Series:
    """
    带风险限制的调仓
    
    参数:
        df_prices: 价格数据，MultiIndex [symbol, date]
        target_weights: 目标权重
        capital: 初始资金
        max_weight: 最大权重限制
        lot_size: 最小交易单位
        pov: POV 限制（可选）
        
    返回:
        调仓订单
    """
    # 计算持仓限制
    position_limits = calculate_position_limits(
        df_prices, max_weight=max_weight, capital=capital
    )
    
    # 应用持仓限制
    limited_weights = apply_position_limits(target_weights, position_limits)
    
    # 生成调仓订单
    orders = rebalance_to_weights_orders(
        df_prices, limited_weights, capital, lot_size
    )
    
    # 应用 POV 约束（如果指定）
    if pov is not None:
        orders = apply_pov_constraints(df_prices, orders, pov=pov, min_clip=lot_size)
    
    return orders