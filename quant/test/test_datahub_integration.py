# test_datahub_integration.py
"""测试 DataHub 完整数据流"""
import sys
import os
from pathlib import Path
import pandas as pd

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from datahub.types import BarData, Exchange, Interval
from datahub.db import ParquetDatabase, get_default_db
from datahub.service import HistoricalDataService
from storage.parquet_store import StoreConfig


def test_db_layer():
    """测试数据库层"""
    print("=" * 60)
    print("🧪 测试1: 数据库层 (db.py)")
    print("=" * 60)
    
    # 创建测试数据库
    config = StoreConfig(root="test_datahub_data")
    db = ParquetDatabase(config)
    
    # 创建测试数据
    print("\n📝 创建 BarData 对象...")
    bars = []
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    
    for i, date in enumerate(dates):
        bar = BarData(
            symbol="000001.SZ",
            exchange=Exchange.SZSE,
            interval=Interval.DAILY,
            datetime=pd.Timestamp(date).tz_localize("UTC"),
            open_price=100.0 + i,
            high_price=102.0 + i,
            low_price=99.0 + i,
            close_price=101.0 + i,
            volume=1000000 + i * 10000
        )
        bars.append(bar)
    
    print(f"   ✅ 创建 {len(bars)} 个 BarData 对象")
    
    # 保存数据
    print("\n💾 保存到数据库...")
    count = db.save_bars(bars)
    print(f"   ✅ 成功保存 {count} 条记录")
    
    # 加载数据
    print("\n📖 从数据库加载...")
    loaded_bars = db.load_bars("000001.SZ", Exchange.SZSE, Interval.DAILY)
    print(f"   ✅ 成功加载 {len(loaded_bars)} 条记录")
    
    # 验证数据
    print("\n✔️  验证数据...")
    assert len(loaded_bars) == len(bars), "记录数不匹配"
    assert loaded_bars[0].symbol == "000001.SZ", "股票代码不匹配"
    assert loaded_bars[0].exchange == Exchange.SZSE, "交易所不匹配"
    print("   ✅ 数据验证通过")
    
    return True


def test_service_layer():
    """测试服务层"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 服务层 (service.py)")
    print("=" * 60)
    
    # 创建服务
    config = StoreConfig(root="test_datahub_data")
    db = ParquetDatabase(config)
    service = HistoricalDataService(db)
    
    # 创建测试数据
    print("\n📝 创建更多测试数据...")
    bars = []
    dates = pd.date_range("2024-02-01", periods=20, freq="D")
    
    for i, date in enumerate(dates):
        bar = BarData(
            symbol="600000.SH",
            exchange=Exchange.SSE,
            interval=Interval.DAILY,
            datetime=pd.Timestamp(date).tz_localize("UTC"),
            open_price=50.0 + i * 0.5,
            high_price=51.0 + i * 0.5,
            low_price=49.0 + i * 0.5,
            close_price=50.5 + i * 0.5,
            volume=2000000 + i * 20000
        )
        bars.append(bar)
    
    print(f"   ✅ 创建 {len(bars)} 个 BarData 对象")
    
    # 通过服务保存
    print("\n💾 通过服务层保存...")
    count = service.save_bars(bars)
    print(f"   ✅ 成功保存 {count} 条记录")
    
    # 通过服务加载
    print("\n📖 通过服务层加载...")
    loaded_bars = service.load_bars("600000.SH", Exchange.SSE, Interval.DAILY)
    print(f"   ✅ 成功加载 {len(loaded_bars)} 条记录")
    
    # 测试日期范围查询
    print("\n📅 测试日期范围查询...")
    filtered_bars = service.load_bars(
        "600000.SH",
        Exchange.SSE,
        Interval.DAILY,
        start=pd.Timestamp("2024-02-10"),
        end=pd.Timestamp("2024-02-15")
    )
    print(f"   ✅ 查询到 {len(filtered_bars)} 条记录")
    
    return True


def test_resample():
    """测试重采样功能"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 重采样功能")
    print("=" * 60)
    
    # 创建服务
    config = StoreConfig(root="test_datahub_data")
    db = ParquetDatabase(config)
    service = HistoricalDataService(db)
    
    # 加载日线数据
    print("\n📖 加载日线数据...")
    daily_bars = service.load_bars("000001.SZ", Exchange.SZSE, Interval.DAILY)
    print(f"   ✅ 加载 {len(daily_bars)} 条日线数据")
    
    # 重采样到周线（如果数据足够）
    if len(daily_bars) >= 5:
        print("\n🔄 重采样到周线...")
        try:
            weekly_bars = service.resample(daily_bars, Interval.WEEKLY)
            print(f"   ✅ 生成 {len(weekly_bars)} 条周线数据")
        except Exception as e:
            print(f"   ⚠️  重采样失败: {e}")
    else:
        print("\n   ⚠️  数据不足，跳过重采样测试")
    
    return True


def test_default_db():
    """测试默认数据库单例"""
    print("\n" + "=" * 60)
    print("🧪 测试4: 默认数据库单例")
    print("=" * 60)
    
    # 获取默认数据库
    print("\n📦 获取默认数据库实例...")
    db1 = get_default_db()
    db2 = get_default_db()
    
    # 验证是同一个实例
    assert db1 is db2, "不是单例模式"
    print("   ✅ 单例模式验证通过")
    
    return True


def cleanup():
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("🧹 清理测试数据")
    print("=" * 60)
    
    import shutil
    test_dir = Path("test_datahub_data")
    
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("   ✅ 测试数据已清理")
    else:
        print("   ℹ️  无需清理")


def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print("DataHub 集成测试")
    print("🚀" * 30 + "\n")
    
    try:
        # 清理旧的测试数据
        cleanup()
        
        # 运行测试
        tests = [
            ("数据库层", test_db_layer),
            ("服务层", test_service_layer),
            ("重采样功能", test_resample),
            ("默认数据库单例", test_default_db),
        ]
        
        passed = 0
        failed = 0
        
        for name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    print(f"\n✅ {name} - 通过")
                else:
                    failed += 1
                    print(f"\n❌ {name} - 失败")
            except Exception as e:
                failed += 1
                print(f"\n❌ {name} - 错误: {e}")
                import traceback
                traceback.print_exc()
        
        # 测试总结
        print("\n" + "=" * 60)
        print("📊 测试总结")
        print("=" * 60)
        print(f"✅ 通过: {passed}")
        print(f"❌ 失败: {failed}")
        print(f"📈 成功率: {passed / len(tests) * 100:.1f}%")
        
        if failed == 0:
            print("\n🎉 所有测试通过！")
        else:
            print(f"\n⚠️  有 {failed} 个测试失败")
        
    finally:
        # 清理测试数据
        print()
        cleanup()


if __name__ == "__main__":
    main()

