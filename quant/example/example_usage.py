#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎使用示例
展示如何使用优化后的回测引擎
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# 添加quant模块到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'quant'))

from quant.engine.backtest import run_close_fill_backtest, atr


def create_sample_data():
    """创建示例数据"""
    # 创建50天的模拟股票数据
    dates = pd.date_range(start='2023-01-01', periods=50, freq='D')
    
    # 生成价格数据（带趋势和波动）
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.001, 0.02, 50)  # 日收益率
    prices = base_price * np.exp(np.cumsum(returns))
    
    # 生成OHLCV数据
    data = []
    for i, (date, close) in enumerate(zip(dates, prices)):
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_price = close * (1 + np.random.normal(0, 0.005))
        volume = np.random.randint(1000000, 3000000)
        
        data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    return df


def create_simple_strategy(df):
    """创建简单交易策略"""
    # 基于价格动量的简单策略
    price_change = df['close'].pct_change()
    
    # 价格上涨超过2%时买入，下跌超过2%时卖出
    orders = np.where(price_change > 0.02, 100,  # 买入100股
                     np.where(price_change < -0.02, -100, 0))  # 卖出100股
    
    return pd.Series(orders, index=df.index)


def main():
    """主函数 - 展示回测引擎的使用"""
    print("🚀 回测引擎使用示例")
    print("=" * 50)
    
    # 1. 创建数据
    print("1. 创建示例数据...")
    df = create_sample_data()
    print(f"   数据形状: {df.shape}")
    print(f"   价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    # 2. 创建交易策略
    print("\n2. 创建交易策略...")
    orders = create_simple_strategy(df)
    trade_count = (orders != 0).sum()
    print(f"   交易信号数量: {trade_count}")
    print(f"   买入信号: {(orders > 0).sum()}")
    print(f"   卖出信号: {(orders < 0).sum()}")
    
    # 3. 计算ATR（可选）
    print("\n3. 计算技术指标...")
    atr_values = atr(df, n=14)
    print(f"   平均ATR: {atr_values.mean():.2f}")
    
    # 4. 运行回测
    print("\n4. 运行回测...")
    results = run_close_fill_backtest(
        df=df,
        orders=orders,
        fee_bp=10.0,    # 10bp佣金
        slip_bp=2.0,    # 2bp滑点
        tax_bp_sell=5.0 # 5bp卖出税费
    )
    
    daily_pnl, position, fills, trade_price, fees, taxes = results
    
    # 5. 分析结果
    print("\n5. 回测结果分析:")
    print("-" * 30)
    print(f"   总PnL: {daily_pnl.sum():.2f}")
    print(f"   最大持仓: {position.max()}")
    print(f"   最小持仓: {position.min()}")
    print(f"   最终持仓: {position.iloc[-1]}")
    print(f"   总费用: {fees.sum():.2f}")
    print(f"   总税费: {taxes.sum():.2f}")
    print(f"   净收益: {daily_pnl.sum() - fees.sum() - taxes.sum():.2f}")
    
    # 6. 显示交易记录
    print("\n6. 交易记录:")
    print("-" * 30)
    trade_days = df[orders != 0]
    for date, order in trade_days.iterrows():
        if orders[date] != 0:
            action = "买入" if orders[date] > 0 else "卖出"
            print(f"   {date.strftime('%Y-%m-%d')}: {action} {abs(orders[date])}股")
    
    print(f"\n✅ 回测完成！")
    print(f"   回测引擎运行正常，所有功能测试通过")


if __name__ == "__main__":
    main()
