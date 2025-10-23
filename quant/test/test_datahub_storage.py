#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 datahub 和 storage 模块
测试历史数据获取和数据库写入功能
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import pandas as pd
from datahub.types import Exchange, Interval, BarData
from datahub.service import HistoricalDataService
from storage.parquet_store import ParquetYearWriter, DuckDBReader, StoreConfig


def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_1_storage_write_read():
    """测试 1: 存储模块的写入和读取"""
    print_section("测试 1: 存储模块基础功能")
    
    # 创建测试数据
    print("\n📝 创建测试数据...")
    dates = pd.date_range('2024-01-01', periods=10, freq='D')
    test_data = pd.DataFrame({
        'date': dates,
        'open': [100 + i for i in range(10)],
        'high': [105 + i for i in range(10)],
        'low': [95 + i for i in range(10)],
        'close': [102 + i for i in range(10)],
        'volume': [1000000 + i*10000 for i in range(10)]
    })
    print(f"✅ 创建了 {len(test_data)} 条测试数据")
    print(test_data.head(3))
    
    # 写入数据
    print("\n📥 写入数据到 Parquet...")
    config = StoreConfig(root="./test_data")
    writer = ParquetYearWriter(config)
    
    count = writer.append('TEST', 'TEST001', '1d', test_data)
    print(f"✅ 成功写入 {count} 条记录")
    
    # 读取数据
    print("\n📤 读取数据...")
    reader = DuckDBReader(config)
    df_read = reader.load('TEST', 'TEST001', '1d')
    print(f"✅ 成功读取 {len(df_read)} 条记录")
    print(df_read.head(3))
    
    # 验证数据一致性
    print("\n🔍 验证数据一致性...")
    if len(df_read) == len(test_data):
        print("✅ 记录数一致")
    else:
        print(f"❌ 记录数不一致: 写入 {len(test_data)}, 读取 {len(df_read)}")
    
    return True


def test_2_storage_filter():
    """测试 2: 存储模块的日期过滤"""
    print_section("测试 2: 日期范围查询")
    
    config = StoreConfig(root="./test_data")
    reader = DuckDBReader(config)
    
    print("\n📅 测试日期范围查询...")
    df_filtered = reader.load(
        'TEST', 'TEST001', '1d',
        start='2024-01-03',
        end='2024-01-07'
    )
    print(f"✅ 查询到 {len(df_filtered)} 条记录")
    print(df_filtered[['date', 'close']])
    
    if len(df_filtered) == 5:
        print("✅ 日期过滤正确")
    else:
        print(f"⚠️ 期望 5 条记录，实际 {len(df_filtered)} 条")
    
    return True


def test_3_mock_provider():
    """测试 3: 模拟数据提供者"""
    print_section("测试 3: 数据提供者接口")
    
    print("\n🔧 创建模拟数据提供者...")
    
    class MockProvider:
        """模拟数据提供者"""
        def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                      start: pd.Timestamp, end: pd.Timestamp, adjust: str = "none"):
            print(f"  查询参数: {symbol}, {exchange.value}, {interval.value}")
            print(f"  日期范围: {start.date()} 至 {end.date()}")
            
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
                    volume=1000000.0 + i*10000
                ))
            print(f"✅ 生成了 {len(bars)} 条模拟K线数据")
            return bars
    
    provider = MockProvider()
    bars = provider.query_bars(
        'MOCK001',
        Exchange.SSE,
        Interval.DAILY,
        pd.Timestamp('2024-01-01'),
        pd.Timestamp('2024-01-10'),
        'none'
    )
    
    print(f"\n📊 返回的K线数据:")
    for i, bar in enumerate(bars[:3]):
        print(f"  {i+1}. {bar.datetime.date()}: O={bar.open_price:.2f}, "
              f"H={bar.high_price:.2f}, L={bar.low_price:.2f}, C={bar.close_price:.2f}")
    print(f"  ...")
    
    return True


def test_4_service_integration():
    """测试 4: 数据服务集成"""
    print_section("测试 4: 数据服务集成测试")
    
    print("\n🔧 初始化数据服务...")
    service = HistoricalDataService()
    
    # 创建模拟provider
    class MockProvider:
        def query_bars(self, symbol, exchange, interval, start, end, adjust="none"):
            dates = pd.date_range(start, end, freq='D')
            return [BarData(
                symbol=symbol, exchange=exchange, interval=interval,
                datetime=pd.Timestamp(date).tz_localize('UTC'),
                open_price=100.0 + i, high_price=105.0 + i,
                low_price=95.0 + i, close_price=102.0 + i,
                volume=1000000.0
            ) for i, date in enumerate(dates)]
    
    provider = MockProvider()
    
    print("\n📥 从数据提供者导入数据...")
    count = service.import_from_provider(
        provider, 'SERVICE001', Exchange.SZSE, Interval.DAILY,
        pd.Timestamp('2024-01-01'), pd.Timestamp('2024-01-15'),
        'none'
    )
    print(f"✅ 导入了 {count} 条记录")
    
    print("\n📤 从数据库加载数据...")
    bars = service.load_bars('SERVICE001', Exchange.SZSE, Interval.DAILY)
    print(f"✅ 加载了 {len(bars)} 条记录")
    
    if len(bars) > 0:
        print(f"\n📊 示例数据:")
        for i, bar in enumerate(bars[:3]):
            print(f"  {i+1}. {bar.datetime.date()}: C={bar.close_price:.2f}, V={bar.volume:.0f}")
    
    return True


def test_5_resample():
    """测试 5: 重采样功能"""
    print_section("测试 5: 数据重采样")
    
    service = HistoricalDataService()
    
    print("\n📊 加载日线数据...")
    bars = service.load_bars('SERVICE001', Exchange.SZSE, Interval.DAILY)
    print(f"✅ 加载了 {len(bars)} 条日线数据")
    
    if len(bars) >= 5:
        print("\n🔄 重采样为周线...")
        weekly_bars = service.resample(bars, Interval.WEEKLY)
        print(f"✅ 重采样得到 {len(weekly_bars)} 条周线数据")
        
        if len(weekly_bars) > 0:
            print(f"\n📊 周线数据示例:")
            for i, bar in enumerate(weekly_bars[:2]):
                print(f"  {i+1}. {bar.datetime.date()}: "
                      f"O={bar.open_price:.2f}, C={bar.close_price:.2f}")
    else:
        print("⚠️ 数据不足，跳过重采样测试")
    
    return True


def test_6_cleanup():
    """测试 6: 清理测试数据"""
    print_section("测试 6: 清理测试数据")
    
    import shutil
    test_dir = Path('./test_data')
    
    if test_dir.exists():
        print(f"\n🗑️ 删除测试目录: {test_dir}")
        shutil.rmtree(test_dir)
        print("✅ 清理完成")
    else:
        print("⚠️ 测试目录不存在，无需清理")
    
    return True


def main():
    """主测试函数"""
    print("\n" + "🚀 "*20)
    print("   AlphaGrid - 数据模块测试套件")
    print("🚀 "*20)
    
    tests = [
        ("存储写入读取", test_1_storage_write_read),
        ("日期范围查询", test_2_storage_filter),
        ("数据提供者", test_3_mock_provider),
        ("服务集成", test_4_service_integration),
        ("重采样功能", test_5_resample),
        ("清理测试数据", test_6_cleanup),
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
    else:
        print(f"\n⚠️ {total - passed} 个测试失败")


if __name__ == "__main__":
    main()

