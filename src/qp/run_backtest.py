#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化回测运行脚本
- 加载股票数据
- 生成交易信号和仓位
- 执行向量化回测
- 输出绩效指标
"""

import sys
from pathlib import Path
import pandas as pd

# 设置标准输出编码为 UTF-8（解决 Windows 中文乱码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from engine.data import OHLCVDataset
from engine.backtest import run_vector_bt
from engine.metrics import summary
from strategies.sma_cross import sma_cross
from config_manager import get_config


def load_data(data_path: str) -> pd.DataFrame:
    """加载股票数据"""
    try:
        dataset = OHLCVDataset(data_path)
        return dataset.get()
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        sys.exit(1)


def generate_signals(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """生成交易信号和仓位"""
    config = get_config()
    
    # 生成SMA交叉信号
    signals = sma_cross(
        df, 
        fast=config.strategy.fast_period,
        slow=config.strategy.slow_period,
        mode="regime",
        band_bp=config.strategy.band_bp,
        long_only=config.strategy.long_only,
        delay=config.strategy.delay
    )
    
    # 简单的仓位管理：信号强度 * 固定股数
    shares = signals * config.backtest.position_size
    
    return signals, shares


def run_backtest(df: pd.DataFrame, signals: pd.Series, shares: pd.Series) -> dict:
    """执行回测并返回结果"""
    config = get_config()
    
    try:
        # 执行向量化回测
        daily_pnl, position, fills, trade_price, fees, taxes = run_vector_bt(
            df=df,
            signal=signals,
            sizer_shares=shares,
            fee_bp=config.backtest.fee_bp,
            slip_bp=config.backtest.slip_bp,
            tax_bp_sell=config.backtest.tax_bp_sell
        )
        
        # 计算绩效指标
        results = summary(
            daily_pnl=daily_pnl,
            capital=config.backtest.capital,
            rf_annual=config.backtest.rf_annual,
            trading_days=config.backtest.trading_days
        )
        
        return results
        
    except Exception as e:
        print(f"❌ 回测执行失败: {e}")
        sys.exit(1)


def print_results(results: dict) -> None:
    """格式化输出回测结果"""
    print("\n" + "="*50)
    print("📊 回测绩效报告")
    print("="*50)
    
    # 核心指标
    print(f"💰 总盈亏:     {results['总盈亏']:>12,.2f}")
    print(f"📈 年化收益:   {results['年化收益率']:>12.2%}")
    print(f"📊 夏普比率:   {results['夏普比率']:>12.2f}")
    print(f"📉 年化波动:   {results['年化波动率']:>12.2%}")
    print(f"⬇️  最大回撤:   {results['最大回撤']:>12,.2f}")
    print(f"📊 回撤比例:   {results['最大回撤比例']:>12.2%}")
    
    # 交易统计
    print(f"\n📈 盈利天数:   {results['盈利天数']:>12}")
    print(f"📉 亏损天数:   {results['亏损天数']:>12}")
    print(f"🎯 胜率:       {results['胜率(按天)']:>12.2%}")
    print(f"💵 平均盈利:   {results['平均盈利(按天)']:>12,.2f}")
    print(f"💸 平均亏损:   {results['平均亏损(按天)']:>12,.2f}")
    
    # 回撤期间
    if results['回撤开始日期'] and results['回撤结束日期']:
        print(f"\n📅 最大回撤期间: {results['回撤开始日期']} 至 {results['回撤结束日期']}")
    
    print("="*50)


def main():
    """主函数"""
    # 配置参数
    data_path = "data/stock.csv"
    
    # 检查数据文件是否存在
    if not Path(data_path).exists():
        print(f"❌ 数据文件不存在: {data_path}")
        print("请确保数据文件路径正确")
        sys.exit(1)
    
    print("🚀 开始量化回测...")
    
    # 1. 加载数据
    print("📂 加载股票数据...")
    df = load_data(data_path)
    print(f"✅ 数据加载完成，共 {len(df)} 个交易日")
    
    # 2. 生成信号
    print("🎯 生成交易信号...")
    signals, shares = generate_signals(df)
    signal_count = (signals != 0).sum()
    print(f"✅ 信号生成完成，共 {signal_count} 个交易信号")
    
    # 3. 执行回测
    print("⚡ 执行向量化回测...")
    results = run_backtest(df, signals, shares)
    
    # 4. 输出结果
    print_results(results)
    print("\n🎉 回测完成！")


if __name__ == "__main__":
    main()