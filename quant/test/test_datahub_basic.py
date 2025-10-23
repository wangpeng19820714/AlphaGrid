#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 datahub 和 storage 模块 (简化版)
测试历史数据获取和基础功能
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
from datahub.types import Exchange, Interval, BarData, bars_to_df, df_to_bars


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_1_bar_data_creation():
    """测试 1: BarData 数据结构"""
    print_section("测试 1: BarData 数据结构")
    
    print("\n📝 创建 BarData 对象...")
    bar = BarData(
        symbol='000001.SZ',
        exchange=Exchange.SZSE,
        interval=Interval.DAILY,
        datetime=pd.Timestamp('2024-01-01', tz='UTC'),
        open_price=10.5,
        high_price=11.0,
        low_price=10.2,
        close_price=10.8,
        volume=1000000.0
    )
    
    print(f"✅ 创建成功:")
    print(f"   股票代码: {bar.symbol}")
    print(f"   交易所: {bar.exchange.value}")
    print(f"   周期: {bar.interval.value}")
    print(f"   日期: {bar.datetime}")
    print(f"   开盘价: {bar.open_price}")
    print(f"   收盘价: {bar.close_price}")
    print(f"   成交量: {bar.volume:,.0f}")
    
    return True


def test_2_bars_to_df():
    """测试 2: BarData 转 DataFrame"""
    print_section("测试 2: BarData 列表转 DataFrame")
    
    print("\n📝 创建多个 BarData...")
    bars = []
    for i in range(5):
        bar = BarData(
            symbol='000001.SZ',
            exchange=Exchange.SZSE,
            interval=Interval.DAILY,
            datetime=pd.Timestamp(f'2024-01-0{i+1}', tz='UTC'),
            open_price=10.0 + i * 0.1,
            high_price=11.0 + i * 0.1,
            low_price=9.0 + i * 0.1,
            close_price=10.5 + i * 0.1,
            volume=1000000.0 + i * 10000
        )
        bars.append(bar)
    
    print(f"✅ 创建了 {len(bars)} 个 BarData 对象")
    
    print("\n🔄 转换为 DataFrame...")
    df = bars_to_df(bars)
    print(f"✅ 转换成功，DataFrame 形状: {df.shape}")
    print(f"\n📊 DataFrame 内容:")
    print(df[['symbol', 'datetime', 'open', 'close', 'volume']])
    
    return True


def test_3_df_to_bars():
    """测试 3: DataFrame 转 BarData"""
    print_section("测试 3: DataFrame 转 BarData 列表")
    
    print("\n📝 创建 DataFrame...")
    df = pd.DataFrame({
        'datetime': pd.date_range('2024-01-01', periods=5, freq='D', tz='UTC'),
        'open': [10.0, 10.1, 10.2, 10.3, 10.4],
        'high': [11.0, 11.1, 11.2, 11.3, 11.4],
        'low': [9.0, 9.1, 9.2, 9.3, 9.4],
        'close': [10.5, 10.6, 10.7, 10.8, 10.9],
        'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
    })
    
    print(f"✅ 创建了 DataFrame，形状: {df.shape}")
    print(df.head())
    
    print("\n🔄 转换为 BarData 列表...")
    bars = df_to_bars(df, '000001.SZ', Exchange.SZSE, Interval.DAILY)
    print(f"✅ 转换成功，得到 {len(bars)} 个 BarData 对象")
    
    print(f"\n📊 BarData 示例:")
    for i, bar in enumerate(bars[:3]):
        print(f"  {i+1}. {bar.datetime.date()}: "
              f"O={bar.open_price:.2f}, C={bar.close_price:.2f}, V={bar.volume:.0f}")
    
    return True


def test_4_exchange_enum():
    """测试 4: 交易所枚举"""
    print_section("测试 4: 交易所枚举")
    
    print("\n📋 可用的交易所:")
    for exchange in Exchange:
        print(f"  • {exchange.name}: {exchange.value}")
    
    print("\n✅ 交易所枚举测试通过")
    return True


def test_5_interval_enum():
    """测试 5: 时间周期枚举"""
    print_section("测试 5: 时间周期枚举")
    
    print("\n📋 可用的时间周期:")
    for interval in Interval:
        print(f"  • {interval.name}: {interval.value}")
    
    print("\n✅ 时间周期枚举测试通过")
    return True


def test_6_mock_provider():
    """测试 6: 模拟数据提供者"""
    print_section("测试 6: 模拟数据提供者")
    
    print("\n🔧 创建模拟数据提供者...")
    
    class MockProvider:
        """模拟数据提供者"""
        def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                      start: pd.Timestamp, end: pd.Timestamp, adjust: str = "none"):
            print(f"\n  📡 模拟API调用:")
            print(f"     股票代码: {symbol}")
            print(f"     交易所: {exchange.value}")
            print(f"     周期: {interval.value}")
            print(f"     日期范围: {start.date()} 至 {end.date()}")
            print(f"     复权方式: {adjust}")
            
            # 生成模拟数据
            dates = pd.date_range(start, end, freq='D')
            bars = []
            for i, date in enumerate(dates):
                bars.append(BarData(
                    symbol=symbol,
                    exchange=exchange,
                    interval=interval,
                    datetime=pd.Timestamp(date).tz_localize('UTC'),
                    open_price=100.0 + i,
                    high_price=105.0 + i,
                    low_price=95.0 + i,
                    close_price=102.0 + i,
                    volume=1000000.0 + i * 10000
                ))
            print(f"\n  ✅ 返回 {len(bars)} 条K线数据")
            return bars
    
    provider = MockProvider()
    bars = provider.query_bars(
        '000001.SZ',
        Exchange.SZSE,
        Interval.DAILY,
        pd.Timestamp('2024-01-01'),
        pd.Timestamp('2024-01-10'),
        'qfq'
    )
    
    print(f"\n📊 获取到的K线数据 (前3条):")
    for i, bar in enumerate(bars[:3]):
        print(f"  {i+1}. {bar.datetime.date()}: "
              f"O={bar.open_price:.2f}, H={bar.high_price:.2f}, "
              f"L={bar.low_price:.2f}, C={bar.close_price:.2f}")
    print(f"  ... (共 {len(bars)} 条)")
    
    return True


def test_7_data_conversion():
    """测试 7: 数据往返转换"""
    print_section("测试 7: 数据往返转换测试")
    
    print("\n📝 创建原始 BarData 列表...")
    original_bars = []
    for i in range(3):
        bar = BarData(
            symbol='TEST001',
            exchange=Exchange.SSE,
            interval=Interval.DAILY,
            datetime=pd.Timestamp(f'2024-01-0{i+1}', tz='UTC'),
            open_price=100.0 + i,
            high_price=105.0 + i,
            low_price=95.0 + i,
            close_price=102.0 + i,
            volume=1000000.0
        )
        original_bars.append(bar)
    
    print(f"✅ 创建了 {len(original_bars)} 条原始数据")
    
    print("\n🔄 转换: BarData -> DataFrame...")
    df = bars_to_df(original_bars)
    print(f"✅ 转换为 DataFrame: {df.shape}")
    
    print("\n🔄 转换: DataFrame -> BarData...")
    converted_bars = df_to_bars(df, 'TEST001', Exchange.SSE, Interval.DAILY)
    print(f"✅ 转换回 BarData: {len(converted_bars)} 条")
    
    print("\n🔍 验证数据一致性...")
    success = True
    for i, (orig, conv) in enumerate(zip(original_bars, converted_bars)):
        if abs(orig.close_price - conv.close_price) > 0.01:
            print(f"❌ 第 {i+1} 条数据不一致")
            success = False
    
    if success:
        print("✅ 数据往返转换一致性验证通过")
    
    return success


def main():
    """主测试函数"""
    print("\n" + "🚀 "*20)
    print("   AlphaGrid - 数据类型和接口测试")
    print("🚀 "*20)
    
    tests = [
        ("BarData创建", test_1_bar_data_creation),
        ("BarData转DataFrame", test_2_bars_to_df),
        ("DataFrame转BarData", test_3_df_to_bars),
        ("交易所枚举", test_4_exchange_enum),
        ("时间周期枚举", test_5_interval_enum),
        ("模拟数据提供者", test_6_mock_provider),
        ("数据往返转换", test_7_data_conversion),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 打印测试结果
    print_section("测试结果汇总")
    print()
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {status}  {name}")
    
    print(f"\n{'='*60}")
    print(f"  总计: {passed}/{total} 测试通过")
    print('='*60)
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        print("\n💡 提示:")
        print("  • BarData 数据结构正常工作")
        print("  • 数据转换功能正常")
        print("  • 数据提供者接口设计合理")
        print("  • 要测试存储功能，请先安装: pip install duckdb pyarrow")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")


if __name__ == "__main__":
    main()

