# engine/metrics.py
# -*- coding: utf-8 -*-
"""
绩效指标计算模块：CAGR / Sharpe / Max Drawdown
- 输入：日度 PnL（Series，index 为日期），或日度收益率（Series）
- 约定：默认一年 252 个交易日；风险自由率按"年化"传入
"""
from __future__ import annotations
from typing import Dict, Tuple, Optional, Union
import numpy as np
import pandas as pd


def _clean_series(data: Union[pd.Series, list, np.ndarray]) -> pd.Series:
    """清理并标准化输入数据为 Series"""
    if isinstance(data, pd.Series):
        return data.dropna().astype(float)
    return pd.Series(data).dropna().astype(float)


def _daily_rf_rate(rf_annual: float, trading_days: int = 252) -> float:
    """年化无风险利率转日度利率"""
    if rf_annual <= -0.9999:
        return 0.0
    return (1.0 + rf_annual) ** (1.0 / trading_days) - 1.0


def equity_curve(pnl: pd.Series) -> pd.Series:
    """资金曲线（累计PnL）"""
    return _clean_series(pnl).cumsum().rename("equity")


def daily_returns(pnl: pd.Series, capital: float) -> pd.Series:
    """PnL转日度收益率"""
    if capital <= 0:
        raise ValueError("初始资金必须为正")
    return (_clean_series(pnl) / capital).rename("returns")


def max_drawdown(curve: pd.Series) -> Tuple[float, Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """最大回撤计算"""
    s = _clean_series(curve)
    if s.empty:
        return 0.0, None, None

    peak = s.cummax()
    drawdown = s - peak
    end_idx = drawdown.idxmin()
    mdd = float(drawdown.loc[end_idx])
    start_idx = s.loc[:end_idx].idxmax() if end_idx is not None else None
    
    return mdd, start_idx, end_idx


def cagr(returns: pd.Series, trading_days: int = 252) -> float:
    """年化复合收益率"""
    r = _clean_series(returns)
    if r.empty:
        return 0.0
    
    total_return = (1 + r).prod()
    if total_return <= 0:
        return -1.0
    
    years = len(r) / trading_days
    return total_return ** (1 / years) - 1.0


def annual_volatility(returns: pd.Series, trading_days: int = 252) -> float:
    """年化波动率"""
    r = _clean_series(returns)
    if r.empty:
        return 0.0
    return float(r.std(ddof=0)) * np.sqrt(trading_days)


def sharpe_ratio(returns: pd.Series, rf_annual: float = 0.0, trading_days: int = 252) -> float:
    """夏普比率"""
    r = _clean_series(returns)
    if r.empty:
        return 0.0

    rf_daily = _daily_rf_rate(rf_annual, trading_days)
    excess_returns = r - rf_daily
    
    if excess_returns.std() == 0 or np.isnan(excess_returns.std()):
        return 0.0
    
    return (excess_returns.mean() / excess_returns.std()) * np.sqrt(trading_days)


def summary(
    daily_pnl: pd.Series,
    capital: float = 1_000_000.0,
    rf_annual: float = 0.0,
    trading_days: int = 252,
) -> Dict[str, Union[float, int, str, None]]:
    """
    计算完整的绩效指标汇总
    
    Args:
        daily_pnl: 日度PnL序列
        capital: 初始资金
        rf_annual: 年化无风险利率
        trading_days: 年交易日数
    
    Returns:
        包含各项绩效指标的字典
    """
    pnl = _clean_series(daily_pnl)
    returns = daily_returns(pnl, capital)
    equity = equity_curve(pnl)
    
    # 核心指标
    cagr_val = cagr(returns, trading_days)
    volatility = annual_volatility(returns, trading_days)
    sharpe_val = sharpe_ratio(returns, rf_annual, trading_days)
    mdd_abs, dd_start, dd_end = max_drawdown(equity)
    
    # 最大回撤百分比
    mdd_pct = 0.0
    if dd_end is not None:
        peak = float(equity.loc[:dd_end].max())
        mdd_pct = (mdd_abs / peak) if peak != 0 else 0.0
    
    # 交易统计
    wins = (pnl > 0).sum()
    losses = (pnl < 0).sum()
    total_trades = (pnl != 0).sum()
    win_rate = (wins / total_trades) if total_trades > 0 else 0.0
    avg_win = float(pnl[pnl > 0].mean()) if wins > 0 else 0.0
    avg_loss = float(pnl[pnl < 0].mean()) if losses > 0 else 0.0

    return {
        # 收益指标
        "TotalPnL": float(pnl.sum()),                   # 总盈亏
        "CAGR": cagr_val,                               # 年化复合收益率
        "Sharpe": sharpe_val,                           # 夏普比率
        "AnnVol": volatility,                           # 年化波动率
        
        # 风险指标
        "MaxDD": mdd_abs,                                               # 最大回撤（绝对值）
        "MaxDDPct": mdd_pct,                                            # 最大回撤百分比
        "DD_Start": str(dd_start) if dd_start is not None else None,    # 回撤开始日期
        "DD_End": str(dd_end) if dd_end is not None else None,          # 回撤结束日期
        
        # 交易统计
        "Days>0": int(wins),                                            # 盈利天数
        "Days<0": int(losses),                                          # 亏损天数
        "WinRate(Day)": win_rate,                                       # 日胜率
        "AvgWin(Day)": avg_win,                                         # 平均日盈利
        "AvgLoss(Day)": avg_loss,                                       # 平均日亏损
    }