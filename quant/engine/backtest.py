# engine/backtest.py
# -*- coding: utf-8 -*-
"""
向量化回测（收盘成交 + 费用/滑点）
- 输入：
    df:            必备列 ['close']（如有 ['open','high','low','volume'] 也可，无强制）
    orders:        每日下单“股数”（含方向，买>0 卖<0）；通常来自仓位/风控模块的 sizing 输出
    fee_bp:        佣金/杂费，基点（bps），默认 10bp = 0.10%，买卖均收
    slip_bp:       滑点，基点（bps），买入 +slip，卖出 -slip
    tax_bp_sell:   卖出印花税，基点（仅卖出收取；A股默认为 0 或 5bp/10bp 等）
- 假设：
    1) 当日收盘下单并成交（close fill）
    2) 持仓以“收盘后”的仓位记为当日仓位；价格变动收益按“昨日收盘后仓位”计算
- 输出：
    daily_pnl:     Series，日度 PnL（价格变动收益 - 费用 - 税费）
    position:      Series，日终持仓股数
    fills:         Series，当日成交股数（与 orders 相同，若需要撮合约束可在外部处理）
    trade_price:   Series，方向敏感的成交价（含滑点）
    fees:          Series，当日佣金/杂费
    taxes:         Series，当日卖出税费
"""
from __future__ import annotations

import numpy as np
import pandas as pd

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


# --------- 主回测函数 ---------
def run_close_fill_backtest(
    df: pd.DataFrame,
    orders: pd.Series | np.ndarray,
    fee_bp: float = 10.0,
    slip_bp: float = 2.0,
    tax_bp_sell: float = 0.0,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series, pd.Series, pd.Series]:
    """
    收盘成交的向量化回测。

    参数
    ----
    df: DataFrame
        至少包含 'close' 列，index 为日期（升序）。
    orders: Series/ndarray
        每日成交“股数”（含方向）。若传入 Series，index 应与 df 对齐。
    fee_bp: float
        佣金/杂费（基点，买卖均收），默认 10bp = 0.10%。
    slip_bp: float
        滑点（基点），买单加价、卖单减价，默认 2bp。
    tax_bp_sell: float
        卖出印花税（基点，仅卖出端收取），默认 0。

    返回
    ----
    daily_pnl, position, fills, trade_price, fees, taxes
    """
    if "close" not in df.columns:
        raise ValueError("df 需要包含列：close")
    close = df["close"].astype(float).values

    # 对齐 orders
    if isinstance(orders, pd.Series):
        # 允许 orders 缺失索引，尝试对齐 df.index
        orders = orders.reindex(df.index).fillna(0.0).values
    else:
        orders = np.asarray(orders, dtype=float)
        if len(orders) != len(df):
            raise ValueError("orders 长度需与 df 行数一致")

    n = len(df)
    fills = orders.copy()  # 本模型中 orders 即为当日成交股数（如需约束在外部处理）

    # 成交价（方向敏感滑点）
    trade_price = _directional_slippage(close, fills, slip_bp)  # 成交价
    notional_abs = np.abs(fills) * trade_price

    # 费用与税费
    fees = _commission(notional_abs, fee_bp)
    sell_mask = fills < 0
    sell_notional_abs = notional_abs * sell_mask
    taxes = _sell_tax(sell_notional_abs, tax_bp_sell)

    # 持仓路径（当日收盘后仓位 = 昨日 + 今日成交）
    position = np.cumsum(fills)

    # 价格变动收益：昨收仓位 * 当日 close-to-close 变动
    prev_close = np.r_[close[0], close[:-1]]
    # 昨日收盘后仓位 = 当日仓位 - 当日成交
    position_bod = position - fills
    price_pnl = (close - prev_close) * position_bod

    # 现金流（仅用于理解）：买入现金流为负，卖出为正；这里不额外返回
    # cash_flow = -(fills * trade_price) - fees - taxes
    # NAV 变化 = price_pnl + 当日已实现盈亏（体现在成交价相对收盘价的差异） - 费用 - 税费
    # 在“以收盘价为记账价”的框架中，方向性滑点已通过成交价体现为即时成本/损耗，
    # 这里直接从当日 PnL 中扣除费用与税费即可。
    daily_pnl = pd.Series(price_pnl - fees - taxes, index=df.index)

    return (
        daily_pnl,
        pd.Series(position, index=df.index, name="position"),
        pd.Series(fills, index=df.index, name="fills"),
        pd.Series(trade_price, index=df.index, name="trade_price"),
        pd.Series(fees, index=df.index, name="fees"),
        pd.Series(taxes, index=df.index, name="taxes"),
    )


# --------- 便捷包装（与之前示例兼容） ---------
def run_vector_bt(
    df: pd.DataFrame,
    signal: pd.Series | np.ndarray,
    sizer_shares: pd.Series | np.ndarray,
    fee_bp: float = 10.0,
    slip_bp: float = 2.0,
    tax_bp_sell: float = 0.0,
):
    """
    兼容旧接口：
    - signal: {-1,0,1}（此参数只为保持签名兼容，不参与内部计算）
    - sizer_shares: 每日成交股数（含方向），会直接作为 orders 使用
    """
    orders = sizer_shares
    return run_close_fill_backtest(
        df=df,
        orders=orders,
        fee_bp=fee_bp,
        slip_bp=slip_bp,
        tax_bp_sell=tax_bp_sell,
    )

# ========== 组合回测 ==========

from collections import namedtuple
from dataclasses import dataclass
from typing import Dict, List


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
        symbol_results = _run_single_symbol_backtest(
            symbol_data, symbol_orders, fee_bp, slip_bp, tax_bp_sell
        )
        
        # 更新结果容器
        _update_result_containers(result_containers, symbol, symbol_results, dates)
    
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


def _run_single_symbol_backtest(
    symbol_data: pd.DataFrame,
    symbol_orders: pd.Series,
    fee_bp: float,
    slip_bp: float,
    tax_bp_sell: float,
) -> tuple:
    """执行单标的回测"""
    return run_close_fill_backtest(
        df=symbol_data,
        orders=symbol_orders,
        fee_bp=fee_bp,
        slip_bp=slip_bp,
        tax_bp_sell=tax_bp_sell,
    )


def _update_result_containers(
    containers: Dict,
    symbol: str,
    results: tuple,
    dates: pd.DatetimeIndex,
) -> None:
    """更新结果容器"""
    daily_pnl, position, fills, trade_price, fees, taxes = results
    
    containers["pnl"][symbol] = daily_pnl.reindex(dates).fillna(0.0)
    containers["positions"][symbol] = position.reindex(dates).fillna(0.0)
    containers["fills"][symbol] = fills.reindex(dates).fillna(0.0)
    containers["trade_price"][symbol] = trade_price.reindex(dates)
    containers["fees"][symbol] = fees.reindex(dates).fillna(0.0)
    containers["taxes"][symbol] = taxes.reindex(dates).fillna(0.0)