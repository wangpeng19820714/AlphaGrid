# Storage Stores 使用说明

## 📋 概述

Stores 模块提供了 AlphaGrid 数据层的持久化存储功能，负责将 K线数据、财务数据和基本面数据高效地存储到本地文件系统。

**模块路径**: `qp/stores/`

**核心特性**:
- 💾 **高效存储** - 基于 Parquet 格式，支持压缩和列式存储
- 📁 **分区管理** - 按交易所/股票/时间周期智能分区
- 🔄 **增量更新** - 自动合并新旧数据，去重保持最新
- 📊 **快速查询** - DuckDB 加持，支持 SQL 查询和时间范围过滤
- ✅ **原子操作** - 原子性写入，保证数据完整性
- 📝 **索引管理** - Manifest 索引快速定位数据文件

---

## 📁 模块结构

```
qp/stores/
├── __init__.py                  # 统一导出接口
├── base.py                      # 基础类和工具函数
├── bar_store.py                # K线数据存储
├── financial_store.py          # 财务数据存储
├── fundamental_store.py        # 基本面数据存储
└── docs/
    ├── README.md                # 快速参考
    └── USAGE_GUIDE.md           # 详细使用指南（本文件）
```

---

## 🚀 快速开始

### 基本导入

```python
from qp.stores import (
    # 配置
    StoreConfig,
    
    # 存储类
    BarStore,
    FinancialStore,
    FundamentalStore,
    
    # 工具类
    BarReader,
    ManifestIndex,
)
```

### 简单示例

```python
from qp.stores import StoreConfig, BarStore
import pandas as pd

# 1. 创建配置
config = StoreConfig(
    root="data/history",      # 存储根目录
    compression="zstd",       # 压缩算法
    use_dictionary=True       # 使用字典编码
)

# 2. 创建存储实例
store = BarStore(config)

# 3. 准备数据
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=10),
    'open': [10.0 + i * 0.1 for i in range(10)],
    'high': [10.2 + i * 0.1 for i in range(10)],
    'low': [9.9 + i * 0.1 for i in range(10)],
    'close': [10.1 + i * 0.1 for i in range(10)],
    'volume': [1000000] * 10,
})

# 4. 保存数据
count = store.append(
    exchange="SSE",
    symbol="600000",
    interval="1d",
    df=df
)
print(f"保存了 {count} 条数据")

# 5. 加载数据
df_loaded = store.load(
    exchange="SSE",
    symbol="600000",
    interval="1d",
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-01-10")
)
print(f"加载了 {len(df_loaded)} 条数据")
```

---

## 📊 存储类详解

### 1. StoreConfig - 存储配置

**定义**:
```python
@dataclass
class StoreConfig:
    """存储配置"""
    root: str = "~/.quant/history"    # 存储根目录
    compression: str = "zstd"          # 压缩算法（zstd/snappy/gzip）
    use_dictionary: bool = True        # 使用字典编码（节省空间）
```

**使用示例**:

```python
from qp.stores import StoreConfig

# 默认配置
config = StoreConfig()

# 自定义配置
config = StoreConfig(
    root="data/history_db",
    compression="snappy",      # 使用 snappy（速度快）
    use_dictionary=False
)

# 查看配置
print(f"存储路径: {config.root}")
print(f"压缩算法: {config.compression}")
```

**压缩算法对比**:

| 算法 | 压缩率 | 速度 | 推荐场景 |
|------|--------|------|----------|
| `zstd` | 高 | 中 | 默认推荐，平衡性能 |
| `snappy` | 低 | 快 | 重视读写速度 |
| `gzip` | 高 | 慢 | 重视存储空间 |
| `none` | 无 | 最快 | 临时数据 |

---

### 2. BarStore - K线数据存储

**目录结构**:
```
{root}/
  └── {exchange}/           # 交易所（如 SSE）
      └── {symbol}/         # 股票代码（如 600000）
          └── {interval}/   # 时间周期（如 1d）
              ├── 2023.parquet          # 2023年数据
              ├── 2024.parquet          # 2024年数据
              └── manifest_current.json # 索引文件
```

#### 主要方法

##### `append()` - 追加数据

```python
from qp.stores import StoreConfig, BarStore
import pandas as pd

store = BarStore(StoreConfig(root="data/bars"))

# 准备数据
df = pd.DataFrame({
    'date': pd.date_range('2024-10-01', periods=20),
    'open': [10.0] * 20,
    'high': [10.5] * 20,
    'low': [9.8] * 20,
    'close': [10.2] * 20,
    'volume': [1000000] * 20,
})

# 追加数据（自动按年分桶）
count = store.append("SSE", "600000", "1d", df)
print(f"写入 {count} 条记录")

# 特性：
# - 自动按年份分文件
# - 自动合并重复数据（按 date 去重，保留最新）
# - 原子性写入，不会损坏现有数据
```

##### `load()` - 加载数据

```python
# 加载全部数据
df = store.load("SSE", "600000", "1d")
print(f"共 {len(df)} 条记录")

# 加载指定时间范围
df = store.load(
    exchange="SSE",
    symbol="600000",
    interval="1d",
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)
print(f"2024年数据: {len(df)} 条")

# 特性：
# - 自动读取涉及的年份文件
# - 自动过滤时间范围
# - 返回排序好的 DataFrame
```

##### `query()` - SQL 查询

```python
# 使用 SQL 查询（DuckDB 支持）
query = """
SELECT 
    date,
    close,
    volume,
    close - LAG(close) OVER (ORDER BY date) as price_change
FROM read_parquet(?)
WHERE date >= ? AND date <= ?
ORDER BY date
"""

# 执行查询
result = store.query(
    "SSE", "600000", "1d",
    sql=query,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)

print(result.head())
```

---

### 3. FinancialStore - 财务数据存储

**目录结构**:
```
{root}/
  └── financials/
      └── {exchange}/              # 交易所
          └── {symbol}/            # 股票代码
              ├── balance_sheet.parquet  # 资产负债表
              ├── income.parquet         # 利润表
              ├── cashflow.parquet       # 现金流量表
              └── indicator.parquet      # 财务指标
```

#### 主要方法

##### `save()` - 保存财务数据

```python
from qp.stores import StoreConfig, FinancialStore
import pandas as pd

store = FinancialStore(StoreConfig(root="data/financials"))

# 准备财务数据
df = pd.DataFrame({
    'symbol': ['600000'] * 4,
    'exchange': ['SSE'] * 4,
    'report_date': pd.to_datetime(['2021-12-31', '2022-12-31', '2023-12-31', '2024-12-31']),
    'publish_date': pd.to_datetime(['2022-03-15', '2023-03-15', '2024-03-15', '2025-03-15']),
    'report_type': ['income'] * 4,
    'report_period': ['annual'] * 4,
    'revenue': [90e9, 95e9, 100e9, 110e9],
    'net_profit': [9e9, 9.5e9, 10e9, 11e9],
    'roe': [0.13, 0.14, 0.15, 0.16],
})

# 保存利润表数据
count = store.save(
    symbol="600000",
    exchange="SSE",
    report_type="income",
    df=df
)
print(f"保存 {count} 条财务数据")

# 特性：
# - 按 report_date 自动去重
# - 增量更新，不会重复存储
# - 按报表类型分文件存储
```

##### `load()` - 加载财务数据

```python
# 加载全部财务数据
df = store.load("600000", "SSE", "income")
print(f"共 {len(df)} 条财报")

# 加载指定时间范围
df = store.load(
    symbol="600000",
    exchange="SSE",
    report_type="income",
    start=pd.Timestamp("2020-01-01"),
    end=pd.Timestamp("2024-12-31")
)
print(f"2020-2024年财报: {len(df)} 条")

# 返回数据已按 report_date 排序
print(df[['report_date', 'revenue', 'net_profit', 'roe']])
```

##### 多报表类型保存

```python
# 保存资产负债表
df_balance = pd.DataFrame({...})
store.save("600000", "SSE", "balance_sheet", df_balance)

# 保存利润表
df_income = pd.DataFrame({...})
store.save("600000", "SSE", "income", df_income)

# 保存现金流量表
df_cashflow = pd.DataFrame({...})
store.save("600000", "SSE", "cashflow", df_cashflow)

# 保存财务指标
df_indicator = pd.DataFrame({...})
store.save("600000", "SSE", "indicator", df_indicator)
```

---

### 4. FundamentalStore - 基本面数据存储

**目录结构**:
```
{root}/
  └── fundamentals/
      └── {exchange}/              # 交易所
          └── {symbol}/            # 股票代码
              └── daily.parquet    # 日频基本面数据
```

#### 主要方法

##### `save()` - 保存基本面数据

```python
from qp.stores import StoreConfig, FundamentalStore
import pandas as pd

store = FundamentalStore(StoreConfig(root="data/fundamentals"))

# 准备基本面数据（日频）
df = pd.DataFrame({
    'symbol': ['600000'] * 252,
    'exchange': ['SSE'] * 252,
    'date': pd.date_range('2024-01-01', periods=252),
    'pe_ratio': [5.8 + i * 0.01 for i in range(252)],
    'pb_ratio': [0.6 + i * 0.001 for i in range(252)],
    'market_cap': [200e9] * 252,
    'roe': [0.12] * 252,
    'roa': [0.08] * 252,
    'dividend_yield': [0.045] * 252,
})

# 保存基本面数据
count = store.save(
    symbol="600000",
    exchange="SSE",
    df=df
)
print(f"保存 {count} 条基本面数据")

# 特性：
# - 按 date 自动去重
# - 增量更新
# - 日频数据统一存储
```

##### `load()` - 加载基本面数据

```python
# 加载全部数据
df = store.load("600000", "SSE")
print(f"共 {len(df)} 条记录")

# 加载指定时间范围
df = store.load(
    symbol="600000",
    exchange="SSE",
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)
print(f"2024年数据: {len(df)} 条")

# 返回数据已按 date 排序
print(df[['date', 'pe_ratio', 'pb_ratio', 'roe']].head())
```

---

## 💡 完整使用示例

### 示例1：K线数据完整工作流

```python
from qp.stores import StoreConfig, BarStore
import pandas as pd
import numpy as np

# ========== 1. 初始化 ==========
config = StoreConfig(
    root="data/history",
    compression="zstd"
)
store = BarStore(config)

# ========== 2. 生成模拟数据 ==========
dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
np.random.seed(42)

df = pd.DataFrame({
    'date': dates,
    'open': 10.0 + np.random.randn(len(dates)).cumsum() * 0.1,
    'high': 10.2 + np.random.randn(len(dates)).cumsum() * 0.1,
    'low': 9.8 + np.random.randn(len(dates)).cumsum() * 0.1,
    'close': 10.1 + np.random.randn(len(dates)).cumsum() * 0.1,
    'volume': np.random.randint(800000, 1200000, len(dates)),
})

# 修正 OHLC 关系
df['high'] = df[['open', 'close']].max(axis=1) + 0.2
df['low'] = df[['open', 'close']].min(axis=1) - 0.2

# ========== 3. 保存数据 ==========
print("=" * 60)
print("保存K线数据")
print("=" * 60)

count = store.append("SSE", "600000", "1d", df)
print(f"✅ 保存了 {count} 条数据")

# ========== 4. 加载并验证 ==========
df_loaded = store.load("SSE", "600000", "1d")
print(f"✅ 加载了 {len(df_loaded)} 条数据")

# 验证数据完整性
assert len(df_loaded) == len(df), "数据量不匹配"
assert df_loaded['date'].is_monotonic_increasing, "日期未排序"
print("✅ 数据验证通过")

# ========== 5. 时间范围查询 ==========
print("\n" + "=" * 60)
print("时间范围查询")
print("=" * 60)

# Q1数据
q1 = store.load("SSE", "600000", "1d",
                start=pd.Timestamp("2024-01-01"),
                end=pd.Timestamp("2024-03-31"))
print(f"Q1数据: {len(q1)} 条")

# Q2数据
q2 = store.load("SSE", "600000", "1d",
                start=pd.Timestamp("2024-04-01"),
                end=pd.Timestamp("2024-06-30"))
print(f"Q2数据: {len(q2)} 条")

# ========== 6. 增量更新 ==========
print("\n" + "=" * 60)
print("增量更新")
print("=" * 60)

# 新增数据
new_df = pd.DataFrame({
    'date': pd.date_range('2025-01-01', periods=10),
    'open': [11.0] * 10,
    'high': [11.5] * 10,
    'low': [10.8] * 10,
    'close': [11.2] * 10,
    'volume': [1000000] * 10,
})

count_new = store.append("SSE", "600000", "1d", new_df)
print(f"✅ 新增 {count_new} 条数据")

# 重新加载验证
df_all = store.load("SSE", "600000", "1d")
print(f"✅ 总数据量: {len(df_all)} 条")

# ========== 7. 数据分析 ==========
print("\n" + "=" * 60)
print("数据分析")
print("=" * 60)

df_all['return'] = df_all['close'].pct_change()
df_all['ma5'] = df_all['close'].rolling(5).mean()
df_all['ma20'] = df_all['close'].rolling(20).mean()

print("最新5条数据:")
print(df_all[['date', 'close', 'return', 'ma5', 'ma20']].tail())

# 统计信息
print(f"\n价格统计:")
print(f"  最高: {df_all['high'].max():.2f}")
print(f"  最低: {df_all['low'].min():.2f}")
print(f"  平均: {df_all['close'].mean():.2f}")
print(f"  波动率: {df_all['return'].std() * np.sqrt(252):.2%}")
```

---

### 示例2：财务数据管理

```python
from qp.stores import StoreConfig, FinancialStore
import pandas as pd

# ========== 1. 初始化 ==========
config = StoreConfig(root="data/financials")
store = FinancialStore(config)

# ========== 2. 保存多年财报 ==========
print("=" * 60)
print("保存财务数据")
print("=" * 60)

# 准备利润表数据
income_df = pd.DataFrame({
    'symbol': ['600000'] * 5,
    'exchange': ['SSE'] * 5,
    'report_date': pd.to_datetime(['2020-12-31', '2021-12-31', '2022-12-31', 
                                   '2023-12-31', '2024-12-31']),
    'publish_date': pd.to_datetime(['2021-03-15', '2022-03-15', '2023-03-15',
                                    '2024-03-15', '2025-03-15']),
    'report_type': ['income'] * 5,
    'report_period': ['annual'] * 5,
    'revenue': [80e9, 85e9, 90e9, 100e9, 110e9],
    'operating_profit': [12e9, 13e9, 14e9, 16e9, 18e9],
    'net_profit': [8e9, 8.5e9, 9e9, 10e9, 11e9],
    'roe': [0.12, 0.13, 0.14, 0.15, 0.16],
    'net_margin': [0.10, 0.10, 0.10, 0.10, 0.10],
})

count = store.save("600000", "SSE", "income", income_df)
print(f"✅ 保存利润表: {count} 条")

# 准备资产负债表数据
balance_df = pd.DataFrame({
    'symbol': ['600000'] * 5,
    'exchange': ['SSE'] * 5,
    'report_date': pd.to_datetime(['2020-12-31', '2021-12-31', '2022-12-31',
                                   '2023-12-31', '2024-12-31']),
    'publish_date': pd.to_datetime(['2021-03-15', '2022-03-15', '2023-03-15',
                                    '2024-03-15', '2025-03-15']),
    'report_type': ['balance_sheet'] * 5,
    'report_period': ['annual'] * 5,
    'total_assets': [2000e9, 2100e9, 2200e9, 2300e9, 2400e9],
    'total_liabilities': [1800e9, 1880e9, 1960e9, 2040e9, 2120e9],
    'total_equity': [200e9, 220e9, 240e9, 260e9, 280e9],
})

count = store.save("600000", "SSE", "balance_sheet", balance_df)
print(f"✅ 保存资产负债表: {count} 条")

# ========== 3. 加载和分析 ==========
print("\n" + "=" * 60)
print("财务数据分析")
print("=" * 60)

# 加载利润表
income = store.load("600000", "SSE", "income")
income['year'] = income['report_date'].dt.year
income['revenue_growth'] = income['revenue'].pct_change()
income['profit_growth'] = income['net_profit'].pct_change()

print("利润表趋势:")
print(income[['year', 'revenue', 'net_profit', 'roe', 
              'revenue_growth', 'profit_growth']])

# 加载资产负债表
balance = store.load("600000", "SSE", "balance_sheet")
balance['year'] = balance['report_date'].dt.year
balance['debt_ratio'] = balance['total_liabilities'] / balance['total_assets']
balance['asset_growth'] = balance['total_assets'].pct_change()

print("\n资产负债表趋势:")
print(balance[['year', 'total_assets', 'total_equity', 'debt_ratio', 
               'asset_growth']])

# ========== 4. 财务健康度评估 ==========
print("\n" + "=" * 60)
print("财务健康度评估")
print("=" * 60)

latest_income = income.iloc[-1]
latest_balance = balance.iloc[-1]

print(f"最新财报（{latest_income['year']}年）:")
print(f"  营收: {latest_income['revenue']/1e9:.1f}亿")
print(f"  净利润: {latest_income['net_profit']/1e9:.1f}亿")
print(f"  ROE: {latest_income['roe']:.2%}")
print(f"  营收增长: {latest_income['revenue_growth']:.2%}")
print(f"  利润增长: {latest_income['profit_growth']:.2%}")
print(f"\n  总资产: {latest_balance['total_assets']/1e9:.1f}亿")
print(f"  净资产: {latest_balance['total_equity']/1e9:.1f}亿")
print(f"  资产负债率: {latest_balance['debt_ratio']:.2%}")

# 评分
score = 0
if latest_income['roe'] > 0.15:
    score += 1
    print("\n✅ ROE > 15%，盈利能力强")
if latest_income['revenue_growth'] > 0.08:
    score += 1
    print("✅ 营收增长 > 8%，成长性好")
if latest_income['profit_growth'] > 0.10:
    score += 1
    print("✅ 利润增长 > 10%，盈利增长快")
if latest_balance['debt_ratio'] < 0.90:
    score += 1
    print("✅ 资产负债率 < 90%，风险可控")

print(f"\n综合评分: {score}/4")
if score >= 3:
    print("💎 财务状况优秀")
elif score >= 2:
    print("👍 财务状况良好")
else:
    print("⚠️ 财务状况一般")
```

---

### 示例3：基本面数据趋势分析

```python
from qp.stores import StoreConfig, FundamentalStore
import pandas as pd
import numpy as np

# ========== 1. 初始化 ==========
config = StoreConfig(root="data/fundamentals")
store = FundamentalStore(config)

# ========== 2. 生成模拟基本面数据 ==========
print("=" * 60)
print("保存基本面数据")
print("=" * 60)

dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
np.random.seed(42)

# 模拟PE/PB波动
pe_base = 6.0
pb_base = 0.6

df = pd.DataFrame({
    'symbol': ['600000'] * len(dates),
    'exchange': ['SSE'] * len(dates),
    'date': dates,
    'pe_ratio': pe_base + np.sin(np.arange(len(dates)) / 50) * 0.5,
    'pb_ratio': pb_base + np.sin(np.arange(len(dates)) / 50) * 0.1,
    'pe_ttm': (pe_base + np.sin(np.arange(len(dates)) / 50) * 0.5) * 0.95,
    'market_cap': 200e9 * (1 + np.sin(np.arange(len(dates)) / 50) * 0.05),
    'circulating_market_cap': 180e9 * (1 + np.sin(np.arange(len(dates)) / 50) * 0.05),
    'roe': 0.12 + np.random.normal(0, 0.005, len(dates)),
    'roa': 0.08 + np.random.normal(0, 0.003, len(dates)),
    'dividend_yield': 0.045 + np.random.normal(0, 0.002, len(dates)),
    'revenue_growth': 0.08 + np.random.normal(0, 0.01, len(dates)),
    'profit_growth': 0.10 + np.random.normal(0, 0.015, len(dates)),
    'gross_margin': 0.45 + np.random.normal(0, 0.01, len(dates)),
    'net_margin': 0.30 + np.random.normal(0, 0.005, len(dates)),
})

count = store.save("600000", "SSE", df)
print(f"✅ 保存 {count} 条基本面数据")

# ========== 3. 加载和分析 ==========
print("\n" + "=" * 60)
print("估值趋势分析")
print("=" * 60)

df_loaded = store.load("600000", "SSE")

# 计算百分位
df_loaded['pe_percentile'] = df_loaded['pe_ratio'].rank(pct=True) * 100
df_loaded['pb_percentile'] = df_loaded['pb_ratio'].rank(pct=True) * 100

# 估值判断
def valuation_level(percentile):
    if percentile < 30:
        return "低估"
    elif percentile > 70:
        return "高估"
    else:
        return "合理"

df_loaded['pe_valuation'] = df_loaded['pe_percentile'].apply(valuation_level)
df_loaded['pb_valuation'] = df_loaded['pb_percentile'].apply(valuation_level)

# 统计
print("估值分布:")
print(df_loaded['pe_valuation'].value_counts())

# 最新估值
latest = df_loaded.iloc[-1]
print(f"\n当前估值（{latest['date'].date()}）:")
print(f"  PE: {latest['pe_ratio']:.2f} (百分位: {latest['pe_percentile']:.1f}%)")
print(f"  PB: {latest['pb_ratio']:.2f} (百分位: {latest['pb_percentile']:.1f}%)")
print(f"  市值: {latest['market_cap']/1e9:.1f}亿")
print(f"  ROE: {latest['roe']:.2%}")
print(f"  股息率: {latest['dividend_yield']:.2%}")
print(f"\n  估值水平: {latest['pe_valuation']}")

# 历史统计
print(f"\n历史统计:")
print(f"  PE范围: {df_loaded['pe_ratio'].min():.2f} ~ {df_loaded['pe_ratio'].max():.2f}")
print(f"  PE均值: {df_loaded['pe_ratio'].mean():.2f}")
print(f"  PE中位数: {df_loaded['pe_ratio'].median():.2f}")
print(f"  PB范围: {df_loaded['pb_ratio'].min():.2f} ~ {df_loaded['pb_ratio'].max():.2f}")

# 投资建议
if latest['pe_percentile'] < 30 and latest['pb_percentile'] < 30:
    print("\n💰 投资建议: 低估区域，可以考虑买入")
elif latest['pe_percentile'] > 70 and latest['pb_percentile'] > 70:
    print("\n⚠️ 投资建议: 高估区域，建议观望")
else:
    print("\n👀 投资建议: 估值合理，持续关注")
```

---

## 🔧 高级功能

### 1. Manifest 索引管理

Manifest 是元数据索引，记录每个数据文件的时间范围和统计信息。

```python
from qp.stores import ManifestIndex
from pathlib import Path

# 创建 Manifest 管理器
part_dir = Path("data/history/SSE/600000/1d")
manifest = ManifestIndex(part_dir)

# 加载现有索引
index = manifest.load()
print("当前索引:")
print(f"  版本: {index['version']}")
print(f"  文件数: {len(index['files'])}")

for file_info in index['files']:
    print(f"    {file_info['name']}: "
          f"{file_info['start']} ~ {file_info['end']} "
          f"({file_info['rows']} 行, {file_info['bytes']/1024:.1f} KB)")

# 从文件重建索引
new_index = manifest.build_from_files()
print(f"\n重建索引: {len(new_index['files'])} 个文件")

# 保存索引
manifest.save_atomically(new_index)
print("✅ 索引已保存")
```

---

### 2. 批量数据导入

```python
from qp.stores import StoreConfig, BarStore
import pandas as pd

store = BarStore(StoreConfig(root="data/history"))

# 批量导入多只股票
symbols = ["600000", "600036", "601318", "601398"]
exchange = "SSE"
interval = "1d"

for symbol in symbols:
    # 生成模拟数据
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=252),
        'open': [10.0] * 252,
        'high': [10.5] * 252,
        'low': [9.8] * 252,
        'close': [10.2] * 252,
        'volume': [1000000] * 252,
    })
    
    try:
        count = store.append(exchange, symbol, interval, df)
        print(f"✅ {symbol}: 导入 {count} 条数据")
    except Exception as e:
        print(f"❌ {symbol}: {e}")

print("\n批量导入完成！")
```

---

### 3. 数据迁移

```python
from qp.stores import StoreConfig, BarStore

# 源存储
src_store = BarStore(StoreConfig(root="data/old_history"))

# 目标存储
dst_store = BarStore(StoreConfig(root="data/new_history"))

# 迁移数据
symbols = ["600000", "600036"]
for symbol in symbols:
    df = src_store.load("SSE", symbol, "1d")
    if not df.empty:
        count = dst_store.append("SSE", symbol, "1d", df)
        print(f"✅ {symbol}: 迁移 {count} 条数据")

print("\n数据迁移完成！")
```

---

### 4. 数据备份

```python
import shutil
from pathlib import Path

# 备份整个存储目录
src = Path("data/history")
dst = Path("backup/history_20241024")

shutil.copytree(src, dst)
print(f"✅ 备份完成: {dst}")

# 或仅备份特定股票
src_symbol = Path("data/history/SSE/600000")
dst_symbol = Path("backup/600000_20241024")

shutil.copytree(src_symbol, dst_symbol)
print(f"✅ 备份 600000: {dst_symbol}")
```

---

### 5. 存储空间统计

```python
from qp.stores import StoreConfig, BarStore
from pathlib import Path
import os

def get_dir_size(path: Path) -> int:
    """计算目录大小（字节）"""
    total = 0
    for item in path.rglob('*'):
        if item.is_file():
            total += item.stat().st_size
    return total

# 统计各交易所数据量
root = Path("data/history")
for exchange_dir in root.iterdir():
    if exchange_dir.is_dir():
        size = get_dir_size(exchange_dir)
        print(f"{exchange_dir.name}: {size / 1024 / 1024:.2f} MB")

# 统计总大小
total_size = get_dir_size(root)
print(f"\n总存储空间: {total_size / 1024 / 1024:.2f} MB")
```

---

## 📚 API 参考

### StoreConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `root` | str | `"~/.quant/history"` | 存储根目录 |
| `compression` | str | `"zstd"` | 压缩算法 |
| `use_dictionary` | bool | `True` | 使用字典编码 |

### BarStore

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `append(exchange, symbol, interval, df)` | DataFrame | int | 追加K线数据 |
| `load(exchange, symbol, interval, start, end)` | - | DataFrame | 加载K线数据 |
| `query(exchange, symbol, interval, sql, start, end)` | SQL字符串 | DataFrame | SQL查询 |

### FinancialStore

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `save(symbol, exchange, report_type, df)` | DataFrame | int | 保存财务数据 |
| `load(symbol, exchange, report_type, start, end)` | - | DataFrame | 加载财务数据 |

### FundamentalStore

| 方法 | 参数 | 返回值 | 说明 |
|------|------|--------|------|
| `save(symbol, exchange, df)` | DataFrame | int | 保存基本面数据 |
| `load(symbol, exchange, start, end)` | - | DataFrame | 加载基本面数据 |

---

## ⚠️ 注意事项

### 1. 数据格式要求

**K线数据** 必须包含以下列：
```python
required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
```

**财务数据** 至少包含：
```python
required_columns = ['report_date', 'publish_date', 'report_type', 'report_period']
```

**基本面数据** 至少包含：
```python
required_columns = ['date']
```

---

### 2. 时间格式

所有时间字段必须是 `pd.Timestamp` 或可转换为时间戳的格式：

```python
# ✅ 正确
df['date'] = pd.to_datetime(df['date'])

# ✅ 正确
df['date'] = pd.date_range('2024-01-01', periods=10)

# ❌ 错误
df['date'] = ['2024-01-01', '2024-01-02', ...]  # 字符串
```

---

### 3. 数据去重

- **K线数据**: 按 `date` 去重，保留最新
- **财务数据**: 按 `report_date` 去重，保留最新
- **基本面数据**: 按 `date` 去重，保留最新

---

### 4. 存储空间

使用压缩可大幅减少存储空间：

| 数据类型 | 未压缩 | zstd压缩 | 压缩率 |
|----------|--------|----------|--------|
| K线（1年日线） | ~500 KB | ~100 KB | 80% |
| 财务（10年） | ~200 KB | ~40 KB | 80% |
| 基本面（1年日频） | ~2 MB | ~400 KB | 80% |

---

### 5. 并发安全

目前存储层 **不支持并发写入**，需要在应用层控制：

```python
import threading

lock = threading.Lock()

def safe_append(store, exchange, symbol, interval, df):
    with lock:
        return store.append(exchange, symbol, interval, df)
```

---

## 🔗 相关文档

- **[Types 模块文档](../../datahub/types/docs/USAGE_GUIDE.md)** - 数据类型定义
- **[Services 模块文档](../../datahub/services/docs/USAGE_GUIDE.md)** - 数据服务层
- **[Providers 模块文档](../../datahub/providers/docs/USAGE_GUIDE.md)** - 数据提供者

---

## 📝 更新日志

- **2024-10-24**: 初始版本
  - 实现 BarStore, FinancialStore, FundamentalStore
  - 支持 Parquet 格式和 zstd 压缩
  - Manifest 索引管理
  - 原子性写入和增量更新

---

**维护者**: AlphaGrid Team  
**最后更新**: 2024-10-24

