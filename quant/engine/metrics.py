# engine/metrics.py
# -*- coding: utf-8 -*-
"""
绩效指标：CAGR / Sharpe / Max Drawdown（含辅助函数与汇总）
- 输入：日度 PnL（Series，index 为日期），或日度收益率（Series）
- 约定：默认一年 252 个交易日；风险自由率按“年化”传入
"""
from __future__ import annotations
from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd


# -----------------------
# 基础工具
# -----------------------
def _to_series(x) -> pd.Series:
    """把输入转成 Series 并丢弃 NaN。"""
    if isinstance(x, pd.Series):
        s = x.copy()
    else:
        s = pd.Series(x)
    return s.dropna()


def _annualize_rf_daily(rf_annual: float, trading_days: int) -> float:
    """把年化无风险利率转换为“日度无风险收益率”"""
    if rf_annual <= -0.9999:  # 避免数学错误
        return 0.0
    return (1.0 + rf_annual) ** (1.0 / trading_days) - 1.0


# -----------------------
# 收益曲线与衍生
# -----------------------
def equity_curve(daily_pnl: pd.Series) -> pd.Series:
    """
    资金曲线（以 PnL 的累计和表示；若想要权益=初始资金+累计PnL，外层再相加即可）
    """
    s = _to_series(daily_pnl).astype(float)
    return s.cumsum().rename("equity")


def daily_return_from_pnl(daily_pnl: pd.Series, capital: float) -> pd.Series:
    """
    将日度 PnL 转换为日度收益率（相对初始资金 capital）。
    若你使用随净值变化的资本基数，请在外部提供更准确的分母。
    """
    if capital <= 0:
        raise ValueError("capital 必须为正。")
    s = _to_series(daily_pnl).astype(float)
    return (s / float(capital)).rename("ret")


# -----------------------
# 核心指标
# -----------------------
def max_drawdown(curve: pd.Series) -> Tuple[float, Optional[pd.Timestamp], Optional[pd.Timestamp]]:
    """
    最大回撤（基于资金曲线或净值曲线）
    返回：
    - mdd: 最大回撤（绝对数值，若传入的是净值则为净值差；若想要比例请自行除以峰值）
    - start: 回撤开始日期
    - end: 回撤触底日期
    """
    s = _to_series(curve).astype(float)
    if s.empty:
        return 0.0, None, None

    roll_max = s.cummax()
    dd = s - roll_max
    end = dd.idxmin()
    mdd = float(dd.loc[end])
    start = s.loc[:end].idxmax() if end is not None else None
    return mdd, start, end


def annual_return(daily_ret: pd.Series, trading_days: int = 252) -> float:
    """
    CAGR：复利年化收益率
    """
    r = _to_series(daily_ret).astype(float)
    n = len(r)
    if n == 0:
        return 0.0
    gross = float((1.0 + r).prod())
    if gross <= 0:
        # 若出现极端亏损至净值<=0，CAGR 设为 -100%
        return -1.0
    return gross ** (trading_days / n) - 1.0


def annual_volatility(daily_ret: pd.Series, trading_days: int = 252) -> float:
    """
    年化波动率（标准差 × sqrt(交易日)）
    """
    r = _to_series(daily_ret).astype(float)
    if r.empty:
        return 0.0
    vol = float(r.std(ddof=0))  # 与多数量化库一致，使用总体标准差
    return vol * (trading_days ** 0.5)


def sharpe(daily_ret: pd.Series, rf_annual: float = 0.0, trading_days: int = 252) -> float:
    """
    年化 Sharpe Ratio（超额收益率 / 年化波动率）
    - rf_annual：年化无风险利率（如 2% -> 0.02）
    """
    r = _to_series(daily_ret).astype(float)
    if r.empty:
        return 0.0

    rf_daily = _annualize_rf_daily(rf_annual, trading_days)
    ex = r - rf_daily
    ex_mean = float(ex.mean())
    ex_vol = float(ex.std(ddof=0))
    if ex_vol == 0.0 or np.isnan(ex_vol):
        return 0.0
    return (ex_mean / ex_vol) * (trading_days ** 0.5)


# -----------------------
# 汇总入口
# -----------------------
def summary(
    daily_pnl: pd.Series,
    capital: float = 1_000_000.0,
    rf_annual: float = 0.0,
    trading_days: int = 252,
) -> Dict[str, object]:
    """
    传入日度 PnL，输出一组常用指标。
    - capital: 初始资金，用于把 PnL 转成日收益率
    - rf_annual: 年化无风险利率（例如 0.02 表示 2%）
    """
    pnl = _to_series(daily_pnl).astype(float)
    ret = daily_return_from_pnl(pnl, capital)
    eq = equity_curve(pnl)

    # 核心指标
    cagr = annual_return(ret, trading_days=trading_days)
    vol = annual_volatility(ret, trading_days=trading_days)
    sr = sharpe(ret, rf_annual=rf_annual, trading_days=trading_days)
    mdd_abs, dd_start, dd_end = max_drawdown(eq)
    # 回撤百分比（相对峰值）
    if dd_end is not None:
        peak = float(eq.loc[:dd_end].max())
        mdd_pct = (mdd_abs / peak) if peak != 0 else 0.0
    else:
        mdd_pct = 0.0

    # 胜率等简单统计（按“日”为单位）
    wins = int((pnl > 0).sum())
    losses = int((pnl < 0).sum())
    trades_like = int((pnl != 0).sum())  # 注意：这里并非真实“笔数”，仅为日度非零计数
    win_rate = (wins / trades_like) if trades_like > 0 else 0.0
    avg_win = float(pnl[pnl > 0].mean()) if wins > 0 else 0.0
    avg_loss = float(pnl[pnl < 0].mean()) if losses > 0 else 0.0

    return {
        "总盈亏": float(pnl.sum()),
        "年化收益率": float(cagr),
        "夏普比率": float(sr),
        "年化波动率": float(vol),
        "最大回撤": float(mdd_abs),
        "最大回撤比例": float(mdd_pct),
        "回撤开始日期": str(dd_start) if dd_start is not None else None,
        "回撤结束日期": str(dd_end) if dd_end is not None else None,
        "盈利天数": wins,
        "亏损天数": losses,
        "胜率(按天)": float(win_rate),
        "平均盈利(按天)": float(avg_win),
        "平均亏损(按天)": float(avg_loss),
    }