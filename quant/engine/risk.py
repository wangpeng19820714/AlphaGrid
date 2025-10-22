
# ========== 风险管理模块 ==========

import pandas as pd
import numpy as np


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