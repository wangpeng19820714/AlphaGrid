# strategies/sma_cross.py
# -*- coding: utf-8 -*-
"""
SMA/EMA 双均线择时（-1/0/1）
- 默认：状态型信号（regime），金叉后持续为 +1，死叉后持续为 -1
- 可选：仅在发生交叉当日给脉冲信号（on_cross）
- 支持：长多/禁做空、容忍带(band)避免噪音、信号滞后一根（delay）
"""

from __future__ import annotations
import pandas as pd

__all__ = ["sma_cross"]

def _ma(series: pd.Series, window: int, kind: str = "sma") -> pd.Series:
    if kind.lower() == "ema":
        return series.ewm(span=window, adjust=False, min_periods=window).mean()
    # 默认 SMA
    return series.rolling(window, min_periods=window).mean()

def sma_cross(
    df: pd.DataFrame,
    fast: int = 10,
    slow: int = 30,
    price_col: str = "close",
    ma: str = "sma",                 # "sma" | "ema"
    mode: str = "regime",            # "regime"（持有状态）| "on_cross"（仅交叉日脉冲）
    band_bp: float = 0.0,            # 容忍带（基点），例如 5 表示 5bp，避免“假穿越”
    long_only: bool = False,         # 禁做空时将 -1 裁剪为 0
    delay: int = 0,                  # 信号滞后 N 根（避免前视；常用 1）
) -> pd.Series:
    """
    返回：pd.Series，取值 ∈ {-1, 0, 1}，index 与 df 对齐
    """
    if price_col not in df.columns:
        raise ValueError(f"df 需要包含列 '{price_col}'")
    if fast <= 0 or slow <= 0:
        raise ValueError("fast/slow 必须为正整数")
    if fast >= slow:
        # 常见约定：快均线 < 慢均线；若相等或反了，仍允许但会提示
        pass

    px = df[price_col].astype(float)
    ma_fast = _ma(px, fast, ma)
    ma_slow = _ma(px, slow, ma)

    # 计算差异与容忍带（以慢均线为基准的相对差）
    # diff_ratio > +th 视为多头；< -th 视为空头；否则视为无明确趋势
    diff = ma_fast - ma_slow
    th = (band_bp / 10000.0) * ma_slow.abs().clip(lower=1e-12)
    regime = pd.Series(0, index=df.index, dtype=int)
    regime = regime.where(diff.abs() <= th, other=0)  # 先置 0，下面再赋方向
    regime = regime.mask(diff > th, 1)
    regime = regime.mask(diff < -th, -1)

    if mode == "regime":
        # 状态型：用最后一个非零值前向填充；起始NaN/未成熟区间仍为0
        regime = regime.replace(0, pd.NA).ffill().fillna(0).astype(int)
    elif mode == "on_cross":
        # 脉冲型：仅在穿越当日给信号（从 <=0 到 >0 记 +1；从 >=0 到 <0 记 -1）
        sign_now = regime
        sign_prev = sign_now.shift(1).fillna(0)
        up_cross = (sign_prev <= 0) & (sign_now > 0)
        dn_cross = (sign_prev >= 0) & (sign_now < 0)
        regime = pd.Series(0, index=df.index, dtype=int)
        regime[up_cross] = 1
        regime[dn_cross] = -1
    else:
        raise ValueError("mode 仅支持 'regime' 或 'on_cross'")

    if long_only:
        regime = regime.clip(lower=0)

    if delay > 0:
        regime = regime.shift(delay).fillna(0).astype(int)

    # 均线未成熟的前 slow 根强制为 0（避免 warmup 噪声）
    regime.loc[: ma_slow.index[ma_slow.first_valid_index()]] = 0

    return regime

# 简单自测
if __name__ == "__main__":
    import numpy as np
    idx = pd.date_range("2024-01-01", periods=60, freq="B")
    # 构造一个上升+回落的价格序列
    px = pd.Series(np.r_[np.linspace(10, 12, 30), np.linspace(12, 11, 30)], index=idx)
    df = pd.DataFrame({"close": px})
    sig = sma_cross(df, fast=5, slow=20, ma="sma", mode="regime", band_bp=3, long_only=False, delay=1)
    print(sig.tail(10))