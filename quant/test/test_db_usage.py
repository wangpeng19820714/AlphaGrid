# test_db_usage.py
"""测试 db.py 的三种使用方式"""
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


def create_sample_bars(symbol: str, exchange: Exchange, count: int = 10) -> list[BarData]:
    """创建示例 BarData 数据"""
    bars = []
    dates = pd.date_range("2024-01-01", periods=count, freq="D")
    
    for i, date in enumerate(dates):
        bar = BarData(
            symbol=symbol,
            exchange=exchange,
            interval=Interval.DAILY,
            datetime=pd.Timestamp(date).tz_localize("UTC"),
            open_price=100.0 + i,
            high_price=102.0 + i,
            low_price=99.0 + i,
            close_price=101.0 + i,
            volume=1000000 + i * 10000
        )
        bars.append(bar)
    
    return bars


def test_method_1_direct_database():
    """方法1: 直接使用 ParquetDatabase"""
    print("=" * 70)
    print("📌 方法1: 直接使用 ParquetDatabase")
    print("=" * 70)
    
    # 创建数据库实例
    print("\n1️⃣ 创建 ParquetDatabase 实例...")
    config = StoreConfig(root="test_db_usage/method1")
    db = ParquetDatabase(config)
    print("   ✅ 数据库实例创建成功")
    
    # 创建测试数据
    print("\n2️⃣ 创建测试数据...")
    bars = create_sample_bars("000001.SZ", Exchange.SZSE, count=15)
    print(f"   ✅ 创建了 {len(bars)} 个 BarData 对象")
    
    # 保存数据
    print("\n3️⃣ 保存数据到数据库...")
    count = db.save_bars(bars)
    print(f"   ✅ 成功保存 {count} 条记录")
    
    # 加载数据
    print("\n4️⃣ 从数据库加载数据...")
    loaded_bars = db.load_bars("000001.SZ", Exchange.SZSE, Interval.DAILY)
    print(f"   ✅ 成功加载 {len(loaded_bars)} 条记录")
    
    # 显示示例数据
    print("\n5️⃣ 显示前3条数据:")
    for i, bar in enumerate(loaded_bars[:3]):
        print(f"   {i+1}. {bar.datetime.date()} - 开:{bar.open_price:.2f} "
              f"高:{bar.high_price:.2f} 低:{bar.low_price:.2f} 收:{bar.close_price:.2f}")
    
    print("\n" + "✅" * 35)
    print("方法1 测试完成\n")
    
    return db


def test_method_2_default_singleton():
    """方法2: 使用默认单例"""
    print("=" * 70)
    print("📌 方法2: 使用默认单例 get_default_db()")
    print("=" * 70)
    
    # 获取默认数据库实例
    print("\n1️⃣ 获取默认数据库实例...")
    db = get_default_db()
    print("   ✅ 获取默认数据库成功（使用单例模式）")
    
    # 验证单例
    print("\n2️⃣ 验证单例模式...")
    db2 = get_default_db()
    is_singleton = db is db2
    print(f"   {'✅' if is_singleton else '❌'} 单例验证: {is_singleton}")
    
    # 创建测试数据
    print("\n3️⃣ 创建测试数据...")
    bars = create_sample_bars("600000.SH", Exchange.SSE, count=12)
    print(f"   ✅ 创建了 {len(bars)} 个 BarData 对象")
    
    # 保存数据
    print("\n4️⃣ 保存数据...")
    count = db.save_bars(bars)
    print(f"   ✅ 成功保存 {count} 条记录")
    
    # 加载数据
    print("\n5️⃣ 加载数据...")
    loaded_bars = db.load_bars("600000.SH", Exchange.SSE, Interval.DAILY)
    print(f"   ✅ 成功加载 {len(loaded_bars)} 条记录")
    
    # 显示日期范围
    if loaded_bars:
        print(f"\n6️⃣ 数据日期范围:")
        print(f"   开始: {loaded_bars[0].datetime.date()}")
        print(f"   结束: {loaded_bars[-1].datetime.date()}")
    
    print("\n" + "✅" * 35)
    print("方法2 测试完成\n")
    
    return db


def test_method_3_service_layer():
    """方法3: 通过服务层"""
    print("=" * 70)
    print("📌 方法3: 通过服务层 HistoricalDataService")
    print("=" * 70)
    
    # 创建服务实例
    print("\n1️⃣ 创建 HistoricalDataService 实例...")
    service = HistoricalDataService()
    print("   ✅ 服务实例创建成功")
    
    # 创建测试数据
    print("\n2️⃣ 创建测试数据...")
    bars = create_sample_bars("510300.SH", Exchange.SSE, count=20)
    print(f"   ✅ 创建了 {len(bars)} 个 BarData 对象")
    
    # 通过服务保存数据
    print("\n3️⃣ 通过服务层保存数据...")
    count = service.save_bars(bars)
    print(f"   ✅ 成功保存 {count} 条记录")
    
    # 通过服务加载数据
    print("\n4️⃣ 通过服务层加载全部数据...")
    all_bars = service.load_bars("510300.SH", Exchange.SSE, Interval.DAILY)
    print(f"   ✅ 成功加载 {len(all_bars)} 条记录")
    
    # 测试日期范围查询
    print("\n5️⃣ 测试日期范围查询...")
    start_date = pd.Timestamp("2024-01-05")
    end_date = pd.Timestamp("2024-01-10")
    filtered_bars = service.load_bars(
        "510300.SH",
        Exchange.SSE,
        Interval.DAILY,
        start=start_date,
        end=end_date
    )
    print(f"   ✅ 查询 {start_date.date()} 至 {end_date.date()}")
    print(f"   ✅ 查询到 {len(filtered_bars)} 条记录")
    
    # 显示查询结果
    if filtered_bars:
        print(f"\n6️⃣ 查询结果明细:")
        for bar in filtered_bars:
            print(f"   📅 {bar.datetime.date()}: 收盘 {bar.close_price:.2f}, "
                  f"成交量 {bar.volume:,}")
    
    print("\n" + "✅" * 35)
    print("方法3 测试完成\n")
    
    return service


def compare_methods():
    """对比三种方法"""
    print("=" * 70)
    print("📊 三种方法对比总结")
    print("=" * 70)
    
    print("""
┌─────────────────────┬──────────────────────────────────────────┐
│      方法           │              特点与适用场景              │
├─────────────────────┼──────────────────────────────────────────┤
│ 1. ParquetDatabase  │ • 直接操作，最灵活                       │
│                     │ • 可自定义存储路径                       │
│                     │ • 适合需要细粒度控制的场景               │
├─────────────────────┼──────────────────────────────────────────┤
│ 2. get_default_db() │ • 单例模式，全局唯一实例                 │
│                     │ • 简单快捷，无需手动创建                 │
│                     │ • 适合快速原型和简单应用                 │
├─────────────────────┼──────────────────────────────────────────┤
│ 3. Service Layer    │ • 最高层抽象，功能最丰富                 │
│                     │ • 支持重采样、复权等高级功能             │
│                     │ • 推荐用于生产环境                       │
└─────────────────────┴──────────────────────────────────────────┘
    """)
    
    print("\n💡 使用建议:")
    print("   • 快速测试/脚本 → 使用 get_default_db()")
    print("   • 需要自定义配置 → 使用 ParquetDatabase(config)")
    print("   • 完整应用开发 → 使用 HistoricalDataService")


def cleanup():
    """清理测试数据"""
    print("\n" + "=" * 70)
    print("🧹 清理测试数据")
    print("=" * 70)
    
    import shutil
    test_dir = Path("test_db_usage")
    
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("   ✅ 测试数据已清理")
    else:
        print("   ℹ️  无需清理")


def main():
    """主函数"""
    print("\n" + "🚀" * 35)
    print("DataHub DB 使用方法测试")
    print("🚀" * 35 + "\n")
    
    try:
        # 清理旧数据
        cleanup()
        
        # 测试三种方法
        print("\n")
        test_method_1_direct_database()
        
        print("\n")
        test_method_2_default_singleton()
        
        print("\n")
        test_method_3_service_layer()
        
        # 对比总结
        print("\n")
        compare_methods()
        
        # 最终总结
        print("\n" + "=" * 70)
        print("🎉 所有测试完成！")
        print("=" * 70)
        print("""
📚 代码示例已保存，你可以在项目中这样使用：

# 示例1: 快速使用
from datahub.db import get_default_db
db = get_default_db()
db.save_bars(bars)

# 示例2: 自定义配置
from datahub.db import ParquetDatabase
from storage.parquet_store import StoreConfig
config = StoreConfig(root="my_data")
db = ParquetDatabase(config)
db.save_bars(bars)

# 示例3: 完整功能
from datahub.service import HistoricalDataService
service = HistoricalDataService()
service.save_bars(bars)
loaded = service.load_bars(symbol, exchange, interval, start, end)
        """)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理测试数据
        cleanup()


if __name__ == "__main__":
    main()

