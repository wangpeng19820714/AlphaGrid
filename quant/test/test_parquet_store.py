# test_parquet_store.py
"""测试 Parquet 存储模块"""
import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 添加父目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置 UTF-8 输出
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from storage.parquet_store import (
    StoreConfig, ParquetYearWriter, DuckDBReader, 
    ManifestIndex, load_multi
)


def create_test_data(start_date: str, periods: int, symbol: str) -> pd.DataFrame:
    """创建测试数据"""
    dates = pd.date_range(start=start_date, periods=periods, freq='D')
    
    # 生成随机价格数据
    np.random.seed(42)
    base_price = 100
    returns = np.random.normal(0.001, 0.02, periods)
    prices = base_price * np.exp(np.cumsum(returns))
    
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
    
    return pd.DataFrame(data)


def test_write_and_read():
    """测试写入和读取功能"""
    print("=" * 60)
    print("🧪 测试1: 写入和读取数据")
    print("=" * 60)
    
    # 创建测试配置
    test_dir = Path("test_storage_data")
    config = StoreConfig(root=str(test_dir))
    
    # 创建测试数据
    print("\n📝 创建测试数据...")
    df_2023 = create_test_data("2023-01-01", 100, "000001.SZ")
    df_2024 = create_test_data("2024-01-01", 50, "000001.SZ")
    df = pd.concat([df_2023, df_2024])
    
    print(f"   生成 {len(df)} 条记录")
    print(f"   日期范围: {df['date'].min()} 至 {df['date'].max()}")
    
    # 写入数据
    print("\n💾 写入数据...")
    writer = ParquetYearWriter(config)
    count = writer.append("SZSE", "000001", "1d", df)
    print(f"   ✅ 成功写入 {count} 条记录")
    
    # 读取数据
    print("\n📖 读取数据...")
    reader = DuckDBReader(config)
    df_read = reader.load("SZSE", "000001", "1d")
    print(f"   ✅ 成功读取 {len(df_read)} 条记录")
    
    # 验证数据
    print("\n✔️  验证数据...")
    assert len(df_read) == len(df), "记录数不匹配"
    assert set(df_read.columns) == set(['date', 'open', 'high', 'low', 'close', 'volume']), "列名不匹配"
    print("   ✅ 数据验证通过")
    
    return True


def test_date_range_query():
    """测试日期范围查询"""
    print("\n" + "=" * 60)
    print("🧪 测试2: 日期范围查询")
    print("=" * 60)
    
    test_dir = Path("test_storage_data")
    config = StoreConfig(root=str(test_dir))
    reader = DuckDBReader(config)
    
    # 查询2023年的数据
    print("\n📅 查询 2023 年数据...")
    df_2023 = reader.load(
        "SZSE", "000001", "1d",
        start="2023-01-01",
        end="2023-12-31"
    )
    print(f"   ✅ 查询到 {len(df_2023)} 条记录")
    
    # 查询2024年的数据
    print("\n📅 查询 2024 年数据...")
    df_2024 = reader.load(
        "SZSE", "000001", "1d",
        start="2024-01-01",
        end="2024-12-31"
    )
    print(f"   ✅ 查询到 {len(df_2024)} 条记录")
    
    return True


def test_incremental_update():
    """测试增量更新"""
    print("\n" + "=" * 60)
    print("🧪 测试3: 增量更新")
    print("=" * 60)
    
    test_dir = Path("test_storage_data")
    config = StoreConfig(root=str(test_dir))
    writer = ParquetYearWriter(config)
    reader = DuckDBReader(config)
    
    # 读取原始数据
    df_before = reader.load("SZSE", "000001", "1d")
    count_before = len(df_before)
    print(f"\n📊 更新前记录数: {count_before}")
    
    # 添加新数据
    print("\n➕ 添加新数据...")
    df_new = create_test_data("2024-03-01", 30, "000001.SZ")
    count_added = writer.append("SZSE", "000001", "1d", df_new)
    print(f"   ✅ 添加 {count_added} 条记录")
    
    # 读取更新后的数据
    df_after = reader.load("SZSE", "000001", "1d")
    count_after = len(df_after)
    print(f"\n📊 更新后记录数: {count_after}")
    print(f"   增加了 {count_after - count_before} 条记录")
    
    return True


def test_multi_symbol():
    """测试多标的读取"""
    print("\n" + "=" * 60)
    print("🧪 测试4: 多标的读取")
    print("=" * 60)
    
    test_dir = Path("test_storage_data")
    config = StoreConfig(root=str(test_dir))
    writer = ParquetYearWriter(config)
    reader = DuckDBReader(config)
    
    # 写入多个标的的数据
    symbols = ["600000", "510300"]
    print(f"\n📝 写入 {len(symbols)} 个标的数据...")
    
    for symbol in symbols:
        df = create_test_data("2024-01-01", 50, symbol)
        count = writer.append("SSE", symbol, "1d", df)
        print(f"   ✅ {symbol}: 写入 {count} 条记录")
    
    # 使用 load_multi 读取多个标的
    print("\n📖 批量读取多标的数据...")
    items = [
        ("SZSE", "000001", "1d"),
        ("SSE", "600000", "1d"),
        ("SSE", "510300", "1d")
    ]
    
    df_multi = load_multi(reader, items)
    print(f"   ✅ 读取到 {len(df_multi)} 条记录")
    print(f"   标的数量: {len(df_multi.index.get_level_values('symbol').unique())}")
    
    # 显示数据结构
    print("\n📊 数据结构:")
    print(f"   Index: {df_multi.index.names}")
    print(f"   Columns: {list(df_multi.columns)}")
    print(f"   Shape: {df_multi.shape}")
    
    return True


def test_manifest():
    """测试 Manifest 索引"""
    print("\n" + "=" * 60)
    print("🧪 测试5: Manifest 索引管理")
    print("=" * 60)
    
    test_dir = Path("test_storage_data")
    config = StoreConfig(root=str(test_dir))
    
    # 获取 manifest 信息
    part_dir = test_dir / "SZSE" / "000001" / "1d"
    manifest_index = ManifestIndex(part_dir)
    manifest = manifest_index.load()
    
    print(f"\n📋 Manifest 信息:")
    print(f"   版本: {manifest.get('version', 0)}")
    print(f"   文件数: {len(manifest.get('files', []))}")
    
    for file_info in manifest.get('files', []):
        print(f"\n   📄 {file_info['name']}")
        print(f"      日期范围: {file_info['start']} 至 {file_info['end']}")
        print(f"      记录数: {file_info['rows']}")
        print(f"      大小: {file_info['bytes'] / 1024:.2f} KB")
    
    return True


def cleanup():
    """清理测试数据"""
    print("\n" + "=" * 60)
    print("🧹 清理测试数据")
    print("=" * 60)
    
    import shutil
    test_dir = Path("test_storage_data")
    
    if test_dir.exists():
        shutil.rmtree(test_dir)
        print("   ✅ 测试数据已清理")
    else:
        print("   ℹ️  无需清理")


def main():
    """主测试函数"""
    print("\n" + "🚀" * 30)
    print("Parquet Store 模块测试")
    print("🚀" * 30 + "\n")
    
    try:
        # 清理旧的测试数据
        cleanup()
        
        # 运行测试
        tests = [
            ("写入和读取", test_write_and_read),
            ("日期范围查询", test_date_range_query),
            ("增量更新", test_incremental_update),
            ("多标的读取", test_multi_symbol),
            ("Manifest索引", test_manifest),
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

