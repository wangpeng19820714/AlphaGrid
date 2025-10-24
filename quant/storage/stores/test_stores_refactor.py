#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Storage Stores 模块测试
验证存储层拆分后的功能
"""
import sys
import io
from pathlib import Path

# Windows UTF-8 输出设置
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目路径
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))


def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_imports():
    """测试1：导入测试"""
    print_section("测试1：存储层导入")
    
    try:
        # 测试统一接口导入
        from quant.storage.stores import (
            StoreConfig,
            BaseStore,
            BarStore,
            FinancialStore,
            FundamentalStore,
            ManifestIndex,
            # 向后兼容
            ParquetYearWriter,
            DuckDBReader,
        )
        
        print("✅ 统一接口导入成功:")
        print(f"   - StoreConfig: {StoreConfig}")
        print(f"   - BaseStore: {BaseStore}")
        print(f"   - BarStore: {BarStore}")
        print(f"   - FinancialStore: {FinancialStore}")
        print(f"   - FundamentalStore: {FundamentalStore}")
        print(f"   - ManifestIndex: {ManifestIndex}")
        
        # 验证向后兼容
        assert ParquetYearWriter is BarStore
        assert DuckDBReader.__name__ == 'BarReader'
        print("\n✅ 向后兼容别名验证通过")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bar_store():
    """测试2：K线存储"""
    print_section("测试2：K线存储 (BarStore)")
    
    try:
        from quant.storage.stores import BarStore, StoreConfig
        
        # 创建存储实例
        print("\n📍 创建BarStore实例:")
        config = StoreConfig(root="test_data/bar_store")
        store = BarStore(config)
        print(f"   Store: {store}")
        print(f"   Root: {store.root}")
        print(f"   Compression: {config.compression}")
        
        # 测试方法存在性
        print("\n📍 检查存储方法:")
        methods = ['append', 'load']
        for method in methods:
            has_method = hasattr(store, method)
            status = "✓" if has_method else "✗"
            print(f"   {status} {method}")
        
        print("\n✅ K线存储测试通过")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_financial_store():
    """测试3：财务数据存储"""
    print_section("测试3：财务数据存储 (FinancialStore)")
    
    try:
        from quant.storage.stores import FinancialStore, StoreConfig
        
        # 创建存储实例
        print("\n📍 创建FinancialStore实例:")
        config = StoreConfig(root="test_data/financial_store")
        store = FinancialStore(config)
        print(f"   Store: {store}")
        print(f"   Root: {store.root}")
        
        # 测试方法存在性
        print("\n📍 检查存储方法:")
        methods = ['save', 'load', 'delete', 'exists']
        for method in methods:
            has_method = hasattr(store, method)
            status = "✓" if has_method else "✗"
            print(f"   {status} {method}")
        
        print("\n✅ 财务数据存储测试通过")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_fundamental_store():
    """测试4：基本面数据存储"""
    print_section("测试4：基本面数据存储 (FundamentalStore)")
    
    try:
        from quant.storage.stores import FundamentalStore, StoreConfig
        
        # 创建存储实例
        print("\n📍 创建FundamentalStore实例:")
        config = StoreConfig(root="test_data/fundamental_store")
        store = FundamentalStore(config)
        print(f"   Store: {store}")
        print(f"   Root: {store.root}")
        
        # 测试方法存在性
        print("\n📍 检查存储方法:")
        methods = [
            'save', 'load', 'delete', 'exists',
            'save_fundamentals', 'load_fundamentals',  # 向后兼容
            'save_financials', 'load_financials',  # 向后兼容
        ]
        for method in methods:
            has_method = hasattr(store, method)
            status = "✓" if has_method else "✗"
            print(f"   {status} {method}")
        
        print("\n✅ 基本面数据存储测试通过")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_multiple_imports():
    """测试5：多种导入方式"""
    print_section("测试5：多种导入方式")
    
    try:
        # 方式1：从统一接口导入
        print("\n📍 方式1：从统一接口导入")
        from quant.storage.stores import BarStore as BS1
        print("   ✅ from quant.storage.stores import BarStore")
        
        # 方式2：从具体模块导入
        print("\n📍 方式2：从具体模块导入")
        from quant.storage.stores.bar_store import BarStore as BS2
        print("   ✅ from quant.storage.stores.bar_store import BarStore")
        
        # 验证是同一个类
        assert BS1 is BS2
        print("\n📍 验证：两种导入方式得到相同的类")
        
        # 方式3：导入整个模块
        print("\n📍 方式3：导入整个模块")
        from quant.storage import stores
        assert hasattr(stores, 'BarStore')
        assert hasattr(stores, 'FinancialStore')
        assert hasattr(stores, 'FundamentalStore')
        print("   ✅ from quant.storage import stores")
        
        print("\n✅ 所有导入方式测试通过")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """测试6：向后兼容性"""
    print_section("测试6：向后兼容性")
    
    try:
        # 测试原有的导入方式
        print("\n📍 测试原有导入方式:")
        from quant.storage.stores import ParquetYearWriter, DuckDBReader
        print(f"   ParquetYearWriter: {ParquetYearWriter}")
        print(f"   DuckDBReader: {DuckDBReader}")
        
        # 验证别名
        from quant.storage.stores import BarStore, BarReader
        assert ParquetYearWriter is BarStore
        print("\n📍 ParquetYearWriter = BarStore ✓")
        
        # 创建实例测试
        from quant.storage.stores import StoreConfig
        config = StoreConfig(root="test_data")
        store = ParquetYearWriter(config)
        print(f"   实例创建成功: {store}")
        
        # 测试方法存在性
        print("\n📍 检查原有方法:")
        methods = ['append', '_write_year_file', '_prepare_dataframe']
        for method in methods:
            has_method = hasattr(store, method)
            status = "✓" if has_method else "✗"
            print(f"   {status} {method}")
        
        print("\n✅ 向后兼容性测试通过")
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("  Storage Stores 模块测试")
    print("="*60)
    
    tests = [
        ("存储层导入", test_imports),
        ("K线存储", test_bar_store),
        ("财务数据存储", test_financial_store),
        ("基本面数据存储", test_fundamental_store),
        ("多种导入方式", test_multiple_imports),
        ("向后兼容性", test_backward_compatibility),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 发生异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 汇总结果
    print_section("测试结果汇总")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status}  {name}")
    
    print(f"\n{'='*60}")
    print(f"  总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print(f"  🎉 所有测试通过！存储层拆分成功！")
    else:
        print(f"  ⚠️  有 {total - passed} 个测试失败，请检查")
    
    print(f"{'='*60}\n")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

