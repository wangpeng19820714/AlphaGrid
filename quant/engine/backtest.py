# engine/backtest.py
# -*- coding: utf-8 -*-
"""
量化回测引擎
- 单标的回测：收盘成交 + 费用/滑点
- 组合回测：多标的组合回测
- T+1 再平衡：动态权益 + T+1 再平衡回测
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Tuple, Union

# --------- 常用指标（可选） ---------
def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """简单 ATR（不做复权处理）"""
    if not {"high", "low", "close"}.issubset(df.columns):
        raise ValueError("计算 ATR 需要列：high, low, close")
    prev_close = df["close"].shift(1)
    tr = np.maximum(df["high"] - df["low"],
                    np.maximum((df["high"] - prev_close).abs(),
                               (df["low"] - prev_close).abs()))
    return tr.rolling(n, min_periods=n).mean()


# --------- 滑点与费用 ---------
def _directional_slippage(close: np.ndarray, fills: np.ndarray, slip_bp: float) -> np.ndarray:
    """
    方向敏感滑点：
        买单：成交价 = close * (1 + slip_bp/1e4)
        卖单：成交价 = close * (1 - slip_bp/1e4)
    """
    slip = slip_bp / 10000.0
    buy_px  = close * (1.0 + slip)
    sell_px = close * (1.0 - slip)
    trade_px = np.where(fills >= 0, buy_px, sell_px)
    return trade_px


def _commission(notional_abs: np.ndarray, fee_bp: float) -> np.ndarray:
    """双向收取的佣金/杂费（基点）"""
    return notional_abs * (fee_bp / 10000.0)


def _sell_tax(sell_notional_abs: np.ndarray, tax_bp_sell: float) -> np.ndarray:
    """仅卖出端收取的税费（基点），A股印花税可在此设置"""
    return sell_notional_abs * (tax_bp_sell / 10000.0)


def _align_orders(orders: Union[pd.Series, np.ndarray], index: pd.Index) -> np.ndarray:
    """对齐订单数据"""
    if isinstance(orders, pd.Series):
        return orders.reindex(index).fillna(0.0).values
    else:
        orders = np.asarray(orders, dtype=float)
        if len(orders) != len(index):
            raise ValueError("orders 长度需与 df 行数一致")
        return orders


def _calculate_price_pnl(close: np.ndarray, position: np.ndarray, fills: np.ndarray) -> np.ndarray:
    """计算价格变动收益"""
    prev_close = np.r_[close[0], close[:-1]]
    position_bod = position - fills
    return (close - prev_close) * position_bod


# --------- 主回测函数 ---------
def run_close_fill_backtest(
    df: pd.DataFrame,
    orders: Union[pd.Series, np.ndarray],
    fee_bp: float = 10.0,
    slip_bp: float = 2.0,
    tax_bp_sell: float = 0.0,
) -> BacktestResult:
    """
    收盘成交的向量化回测

    参数:
        df: 价格数据，至少包含 'close' 列
        orders: 每日成交股数（含方向）
        fee_bp: 佣金/杂费（基点）
        slip_bp: 滑点（基点）
        tax_bp_sell: 卖出印花税（基点）

    返回:
        回测结果
    """
    if "close" not in df.columns:
        raise ValueError("df 需要包含列：close")
    
    close = df["close"].astype(float).values
    orders = _align_orders(orders, df.index)
    
    # 计算成交价和费用
    fills = orders.copy()
    trade_price = _directional_slippage(close, fills, slip_bp)
    notional_abs = np.abs(fills) * trade_price
    
    fees = _commission(notional_abs, fee_bp)
    sell_mask = fills < 0
    sell_notional_abs = notional_abs * sell_mask
    taxes = _sell_tax(sell_notional_abs, tax_bp_sell)
    
    # 计算持仓和收益
    position = np.cumsum(fills)
    price_pnl = _calculate_price_pnl(close, position, fills)
    daily_pnl = pd.Series(price_pnl - fees - taxes, index=df.index)
    
    return BacktestResult(
        daily_pnl=daily_pnl,
        position=pd.Series(position, index=df.index, name="position"),
        fills=pd.Series(fills, index=df.index, name="fills"),
        trade_price=pd.Series(trade_price, index=df.index, name="trade_price"),
        fees=pd.Series(fees, index=df.index, name="fees"),
        taxes=pd.Series(taxes, index=df.index, name="taxes"),
    )


# --------- 便捷包装（与之前示例兼容） ---------
def run_vector_bt(
    df: pd.DataFrame,
    signal: Union[pd.Series, np.ndarray],
    sizer_shares: Union[pd.Series, np.ndarray],
    fee_bp: float = 10.0,
    slip_bp: float = 2.0,
    tax_bp_sell: float = 0.0,
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    兼容旧接口的回测函数
    
    参数:
        df: 价格数据
        signal: 信号（仅保持兼容性，不参与计算）
        sizer_shares: 每日成交股数（含方向）
        fee_bp: 手续费（基点）
        slip_bp: 滑点（基点）
        tax_bp_sell: 卖出税费（基点）
        
    返回:
        元组格式的回测结果（向后兼容）
    """
    result = run_close_fill_backtest(
        df=df,
        orders=sizer_shares,
        fee_bp=fee_bp,
        slip_bp=slip_bp,
        tax_bp_sell=tax_bp_sell,
    )
    
    # 返回元组格式以保持向后兼容
    return (
        result.daily_pnl,
        result.position,
        result.fills,
        result.trade_price,
        result.fees,
        result.taxes,
    )

# ========== 数据结构定义 ==========

@dataclass
class BacktestResult:
    """单标的回测结果"""
    daily_pnl: pd.Series
    position: pd.Series
    fills: pd.Series
    trade_price: pd.Series
    fees: pd.Series
    taxes: pd.Series


@dataclass
class PortfolioResult:
    """组合回测结果"""
    portfolio_pnl: pd.Series      # 组合日度 PnL
    per_symbol_pnl: pd.DataFrame  # 分标的日度 PnL
    positions: pd.DataFrame       # 分标的持仓股数
    fills: pd.DataFrame          # 分标的成交股数
    trade_price: pd.DataFrame    # 分标的成交价
    fees: pd.DataFrame           # 分标的费用
    taxes: pd.DataFrame          # 分标的税费


@dataclass
class PortfolioT1Result:
    """T+1 再平衡回测结果"""
    portfolio_pnl: pd.Series      # 组合日度 PnL
    equity: pd.Series             # 组合权益
    per_symbol_pnl: pd.DataFrame  # 分标的日度 PnL
    positions: pd.DataFrame       # 分标的持仓股数
    fills: pd.DataFrame          # 分标的成交股数
    trade_price: pd.DataFrame    # 分标的成交价
    fees: pd.DataFrame           # 分标的费用
    taxes: pd.DataFrame          # 分标的税费


def run_close_fill_portfolio(
    df: pd.DataFrame,
    orders: pd.Series,
    fee_bp: float = 10.0,
    slip_bp: float = 2.0,
    tax_bp_sell: float = 0.0,
) -> PortfolioResult:
    """
    组合层回测
    
    参数:
        df: 价格数据，MultiIndex [symbol, date]，需包含 'close' 列
        orders: 订单数据，MultiIndex [symbol, date]，单位：股
        fee_bp: 手续费（基点）
        slip_bp: 滑点（基点）
        tax_bp_sell: 卖出税费（基点）
        
    返回:
        组合回测结果
    """
    # 验证和预处理数据
    df, orders = _validate_and_prepare_data(df, orders)
    
    # 获取标的和日期列表
    symbols = df.index.get_level_values("symbol").unique().tolist()
    dates = df.index.get_level_values("date").unique()
    
    # 初始化结果容器
    result_containers = _initialize_result_containers(symbols, dates)
    
    # 逐标的执行回测
    for symbol in symbols:
        symbol_data = df.loc[symbol]
        symbol_orders = orders.loc[symbol]
        
        # 执行单标的回测
        symbol_result = run_close_fill_backtest(
            symbol_data, symbol_orders, fee_bp, slip_bp, tax_bp_sell
        )
        
        # 更新结果容器
        _update_result_containers_from_result(result_containers, symbol, symbol_result, dates)
    
    # 计算组合 PnL
    portfolio_pnl = result_containers["pnl"].sum(axis=1)
    
    return PortfolioResult(
        portfolio_pnl=portfolio_pnl,
        per_symbol_pnl=result_containers["pnl"],
        positions=result_containers["positions"],
        fills=result_containers["fills"],
        trade_price=result_containers["trade_price"],
        fees=result_containers["fees"],
        taxes=result_containers["taxes"],
    )


def _validate_and_prepare_data(df: pd.DataFrame, orders: pd.Series) -> tuple:
    """验证和预处理数据"""
    # 验证 DataFrame 索引
    if df.index.nlevels != 2 or df.index.names != ["symbol", "date"]:
        try:
            df = df.copy()
            df.index = df.index.set_names(["symbol", "date"])
        except Exception:
            raise ValueError("df 需要 MultiIndex [symbol, date]")
    
    # 验证 orders 类型
    if not isinstance(orders, pd.Series):
        raise ValueError("orders 需为 pd.Series（MultiIndex）")
    
    # 对齐 orders
    orders = orders.reindex(df.index).fillna(0.0)
    
    return df, orders


def _initialize_result_containers(symbols: List[str], dates: pd.DatetimeIndex) -> Dict:
    """初始化结果容器"""
    return {
        "pnl": pd.DataFrame(0.0, index=dates, columns=symbols),
        "positions": pd.DataFrame(0.0, index=dates, columns=symbols),
        "fills": pd.DataFrame(0.0, index=dates, columns=symbols),
        "trade_price": pd.DataFrame(np.nan, index=dates, columns=symbols),
        "fees": pd.DataFrame(0.0, index=dates, columns=symbols),
        "taxes": pd.DataFrame(0.0, index=dates, columns=symbols),
    }


def _update_result_containers_from_result(
    containers: Dict,
    symbol: str,
    result: BacktestResult,
    dates: pd.DatetimeIndex,
) -> None:
    """从回测结果更新结果容器"""
    containers["pnl"][symbol] = result.daily_pnl.reindex(dates).fillna(0.0)
    containers["positions"][symbol] = result.position.reindex(dates).fillna(0.0)
    containers["fills"][symbol] = result.fills.reindex(dates).fillna(0.0)
    containers["trade_price"][symbol] = result.trade_price.reindex(dates)
    containers["fees"][symbol] = result.fees.reindex(dates).fillna(0.0)
    containers["taxes"][symbol] = result.taxes.reindex(dates).fillna(0.0)

# ========== T+1 再平衡回测 ==========


def run_portfolio_t1_rebalance(
    df: pd.DataFrame,
    target_weights: pd.DataFrame,
    capital0: float = 1_000_000.0,
    fee_bp: float = 10.0,
    slip_bp: float = 2.0,
    tax_bp_sell: float = 0.0,
    lot_size: int = 1,
) -> PortfolioT1Result:
    """
    T+1 再平衡回测
    
    参数:
        df: 价格数据，MultiIndex [symbol, date]，需包含 'close' 列
        target_weights: 目标权重，DataFrame(index=date, columns=symbol)
        capital0: 初始资金
        fee_bp: 手续费（基点）
        slip_bp: 滑点（基点）
        tax_bp_sell: 卖出税费（基点）
        lot_size: 最小交易单位
        
    返回:
        T+1 再平衡回测结果
    """
    # 验证和预处理数据
    df = _validate_t1_data(df)
    prices, dates, symbols = _prepare_t1_data(df, target_weights)
    
    # 初始化回测状态
    state = _initialize_t1_state(dates, symbols, capital0)
    results = _initialize_t1_results(dates, symbols)
    
    # 执行 T+1 再平衡回测
    for i, date in enumerate(dates):
        _process_t1_day(i, date, prices, target_weights, state, results, 
                       fee_bp, slip_bp, tax_bp_sell, lot_size)
    
    # 计算组合 PnL
    portfolio_pnl = results["pnl"].sum(axis=1)
    
    return PortfolioT1Result(
        portfolio_pnl=portfolio_pnl,
        equity=state["equity"],
        per_symbol_pnl=results["pnl"],
        positions=results["positions"],
        fills=results["fills"],
        trade_price=results["trade_price"],
        fees=results["fees"],
        taxes=results["taxes"],
    )


def _validate_t1_data(df: pd.DataFrame) -> pd.DataFrame:
    """验证 T+1 回测数据"""
    if "close" not in df.columns:
        raise ValueError("df 需要包含 'close' 列")
    if df.index.nlevels != 2:
        raise ValueError("df 需要 MultiIndex [symbol, date]")
    
    if df.index.names != ["symbol", "date"]:
        df = df.copy()
        df.index = df.index.set_names(["symbol", "date"])
    
    return df


def _prepare_t1_data(df: pd.DataFrame, target_weights: pd.DataFrame) -> tuple:
    """准备 T+1 回测数据"""
    # 转换价格数据为宽表格式
    prices = df["close"].unstack(level="symbol").sort_index()
    dates = prices.index
    symbols = list(prices.columns)
    
    # 对齐权重矩阵
    weights = target_weights.reindex(index=dates, columns=symbols).fillna(0.0)
    
    return prices, dates, symbols


def _initialize_t1_state(dates: pd.DatetimeIndex, symbols: List[str], capital0: float) -> Dict:
    """初始化 T+1 回测状态"""
    return {
        "equity": pd.Series(0.0, index=dates),
        "prev_position": pd.Series(0.0, index=symbols),
        "pending_orders": pd.Series(0.0, index=symbols),
        "prev_close": None,
        "capital0": capital0,
    }


def _initialize_t1_results(dates: pd.DatetimeIndex, symbols: List[str]) -> Dict:
    """初始化 T+1 回测结果容器"""
    return {
        "pnl": pd.DataFrame(0.0, index=dates, columns=symbols),
        "positions": pd.DataFrame(0.0, index=dates, columns=symbols),
        "fills": pd.DataFrame(0.0, index=dates, columns=symbols),
        "trade_price": pd.DataFrame(np.nan, index=dates, columns=symbols),
        "fees": pd.DataFrame(0.0, index=dates, columns=symbols),
        "taxes": pd.DataFrame(0.0, index=dates, columns=symbols),
    }


def _process_t1_day(
    day_index: int,
    date: pd.Timestamp,
    prices: pd.DataFrame,
    target_weights: pd.DataFrame,
    state: Dict,
    results: Dict,
    fee_bp: float,
    slip_bp: float,
    tax_bp_sell: float,
    lot_size: int,
) -> None:
    """处理 T+1 回测的单个交易日"""
    close_today = prices.loc[date]
    
    # 1. 执行昨日订单
    fills_today = state["pending_orders"].copy()
    trade_px_today, fees_today, taxes_today = _execute_orders(
        fills_today, close_today, fee_bp, slip_bp, tax_bp_sell
    )
    
    # 2. 更新持仓
    position_eod = state["prev_position"] + fills_today
    
    # 3. 计算价格变动收益
    price_pnl = _calculate_price_pnl(close_today, state["prev_close"], state["prev_position"])
    pnl_today = price_pnl - fees_today - taxes_today
    
    # 4. 更新权益
    equity_today = _update_equity(day_index, state, pnl_today.sum())
    state["equity"].iloc[day_index] = equity_today
    
    # 5. 记录当日结果
    _record_daily_results(date, results, pnl_today, position_eod, fills_today, 
                         trade_px_today, fees_today, taxes_today)
    
    # 6. 生成下一日订单
    target_weights_today = target_weights.loc[date].clip(lower=0.0).fillna(0.0)
    state["pending_orders"] = _generate_next_day_orders(
        target_weights_today, position_eod, close_today, equity_today, lot_size
    )
    
    # 7. 更新状态
    state["prev_position"] = position_eod
    state["prev_close"] = close_today


def _execute_orders(
    fills: pd.Series, 
    close_prices: pd.Series, 
    fee_bp: float, 
    slip_bp: float, 
    tax_bp_sell: float
) -> tuple:
    """执行订单并计算费用"""
    # 计算成交价（含滑点）
    trade_prices = _directional_slippage(close_prices.values, fills.values, slip_bp)
    trade_prices = pd.Series(trade_prices, index=fills.index)
    
    # 计算费用
    notional_abs = (fills.abs() * trade_prices).fillna(0.0)
    fees = _commission(notional_abs.values, fee_bp)
    fees = pd.Series(fees, index=fills.index)
    
    # 计算税费
    sell_mask = fills < 0
    sell_notional_abs = (notional_abs * sell_mask).fillna(0.0)
    taxes = _sell_tax(sell_notional_abs.values, tax_bp_sell)
    taxes = pd.Series(taxes, index=fills.index)
    
    return trade_prices, fees, taxes


def _calculate_price_pnl(close_today: pd.Series, prev_close: pd.Series, prev_position: pd.Series) -> pd.Series:
    """计算价格变动收益"""
    if prev_close is None:
        return pd.Series(0.0, index=close_today.index)
    return (close_today - prev_close) * prev_position


def _update_equity(day_index: int, state: Dict, pnl_today: float) -> float:
    """更新权益"""
    if day_index == 0:
        return state["capital0"] + pnl_today
    else:
        return state["equity"].iloc[day_index - 1] + pnl_today


def _record_daily_results(
    date: pd.Timestamp,
    results: Dict,
    pnl_today: pd.Series,
    position_eod: pd.Series,
    fills_today: pd.Series,
    trade_px_today: pd.Series,
    fees_today: pd.Series,
    taxes_today: pd.Series,
) -> None:
    """记录当日结果"""
    symbols = results["pnl"].columns
    
    results["pnl"].loc[date] = pnl_today.reindex(symbols).fillna(0.0)
    results["positions"].loc[date] = position_eod.reindex(symbols).fillna(0.0)
    results["fills"].loc[date] = fills_today.reindex(symbols).fillna(0.0)
    results["trade_price"].loc[date] = trade_px_today.reindex(symbols)
    results["fees"].loc[date] = fees_today.reindex(symbols).fillna(0.0)
    results["taxes"].loc[date] = taxes_today.reindex(symbols).fillna(0.0)


def _generate_next_day_orders(
    target_weights: pd.Series,
    current_position: pd.Series,
    close_prices: pd.Series,
    equity: float,
    lot_size: int,
) -> pd.Series:
    """生成下一日订单"""
    # 计算目标股数
    target_shares = (target_weights * equity / close_prices)
    target_shares = target_shares.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    
    # 取整到最小交易单位
    if lot_size > 1:
        target_shares = np.floor(target_shares / lot_size) * lot_size
    else:
        target_shares = np.floor(target_shares)
    
    # 计算调仓订单
    orders = (target_shares - current_position).astype(float)
    
    return orders