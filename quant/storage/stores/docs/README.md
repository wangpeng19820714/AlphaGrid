# Storage Stores 快速参考

## 📋 存储模块概览

Stores 模块提供高效的本地持久化存储，基于 Parquet 格式管理 K线数据、财务数据和基本面数据。

**模块路径**: `quant/storage/stores/`

---

## 🚀 快速开始

```python
from quant.storage.stores import StoreConfig, BarStore
import pandas as pd

# 1. 创建配置
config = StoreConfig(
    root="data/history",
    compression="zstd"
)

# 2. 创建存储
store = BarStore(config)

# 3. 准备数据
df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=10),
    'open': [10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9],
    'high': [10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 11.0, 11.1],
    'low': [9.9, 10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8],
    'close': [10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 11.0],
    'volume': [1000000] * 10,
})

# 4. 保存数据
count = store.append("SSE", "600000", "1d", df)
print(f"保存 {count} 条数据")

# 5. 加载数据
df_loaded = store.load("SSE", "600000", "1d")
print(f"加载 {len(df_loaded)} 条数据")
```

---

## 📊 三大存储类型

### 1️⃣ BarStore - K线数据存储

管理 OHLCV 数据，按年分桶存储。

**目录结构**:
```
{root}/
  └── {exchange}/
      └── {symbol}/
          └── {interval}/
              ├── 2023.parquet
              ├── 2024.parquet
              └── manifest_current.json
```

**使用示例**:

```python
from quant.storage.stores import StoreConfig, BarStore

store = BarStore(StoreConfig(root="data/bars"))

# 保存数据
count = store.append("SSE", "600000", "1d", df)

# 加载全部数据
df = store.load("SSE", "600000", "1d")

# 加载指定时间范围
df = store.load(
    exchange="SSE",
    symbol="600000",
    interval="1d",
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)

# SQL 查询（DuckDB）
result = store.query(
    "SSE", "600000", "1d",
    sql="SELECT date, close FROM read_parquet(?) WHERE date >= ? AND date <= ?",
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)
```

**主要特性**:
- ✅ 按年自动分桶
- ✅ 自动去重（按 date）
- ✅ 增量更新
- ✅ 原子性写入
- ✅ Manifest 索引
- ✅ DuckDB SQL 查询

---

### 2️⃣ FinancialStore - 财务数据存储

管理财务报表数据，按报表类型分文件。

**目录结构**:
```
{root}/
  └── financials/
      └── {exchange}/
          └── {symbol}/
              ├── balance_sheet.parquet  # 资产负债表
              ├── income.parquet         # 利润表
              ├── cashflow.parquet       # 现金流量表
              └── indicator.parquet      # 财务指标
```

**使用示例**:

```python
from quant.storage.stores import StoreConfig, FinancialStore

store = FinancialStore(StoreConfig(root="data/financials"))

# 保存财务数据
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

count = store.save("600000", "SSE", "income", df)
print(f"保存 {count} 条财务数据")

# 加载财务数据
df = store.load("600000", "SSE", "income")

# 加载指定时间范围
df = store.load(
    symbol="600000",
    exchange="SSE",
    report_type="income",
    start=pd.Timestamp("2020-01-01"),
    end=pd.Timestamp("2024-12-31")
)
```

**报表类型**:
- `balance_sheet` - 资产负债表
- `income` - 利润表
- `cashflow` - 现金流量表
- `indicator` - 财务指标

**主要特性**:
- ✅ 按报表类型分文件
- ✅ 自动去重（按 report_date）
- ✅ 增量更新
- ✅ 原子性写入

---

### 3️⃣ FundamentalStore - 基本面数据存储

管理基本面指标数据（日频）。

**目录结构**:
```
{root}/
  └── fundamentals/
      └── {exchange}/
          └── {symbol}/
              └── daily.parquet
```

**使用示例**:

```python
from quant.storage.stores import StoreConfig, FundamentalStore

store = FundamentalStore(StoreConfig(root="data/fundamentals"))

# 保存基本面数据
df = pd.DataFrame({
    'symbol': ['600000'] * 252,
    'exchange': ['SSE'] * 252,
    'date': pd.date_range('2024-01-01', periods=252),
    'pe_ratio': [5.8] * 252,
    'pb_ratio': [0.6] * 252,
    'market_cap': [200e9] * 252,
    'roe': [0.12] * 252,
    'dividend_yield': [0.045] * 252,
})

count = store.save("600000", "SSE", df)
print(f"保存 {count} 条基本面数据")

# 加载基本面数据
df = store.load("600000", "SSE")

# 加载指定时间范围
df = store.load(
    symbol="600000",
    exchange="SSE",
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)
```

**主要特性**:
- ✅ 日频数据统一存储
- ✅ 自动去重（按 date）
- ✅ 增量更新
- ✅ 原子性写入

---

## ⚙️ 配置说明

### StoreConfig

```python
from quant.storage.stores import StoreConfig

# 默认配置
config = StoreConfig()
# root="~/.quant/history"
# compression="zstd"
# use_dictionary=True

# 自定义配置
config = StoreConfig(
    root="data/my_storage",
    compression="snappy",      # 更快的压缩
    use_dictionary=False
)
```

### 压缩算法对比

| 算法 | 压缩率 | 速度 | 推荐场景 |
|------|--------|------|----------|
| `zstd` | 高（80%） | 中 | 默认推荐 ⭐ |
| `snappy` | 低（50%） | 快 | 重视速度 |
| `gzip` | 高（85%） | 慢 | 重视空间 |
| `none` | 无 | 最快 | 临时数据 |

---

## 💡 常用场景

### 场景1：批量导入K线数据

```python
from quant.storage.stores import StoreConfig, BarStore

store = BarStore(StoreConfig(root="data/history"))

symbols = ["600000", "600036", "601318", "601398"]
for symbol in symbols:
    df = load_data_from_provider(symbol)  # 假设函数
    count = store.append("SSE", symbol, "1d", df)
    print(f"✅ {symbol}: {count} 条")
```

---

### 场景2：财务数据年度对比

```python
from quant.storage.stores import StoreConfig, FinancialStore

store = FinancialStore(StoreConfig(root="data/financials"))

# 加载利润表
income = store.load("600000", "SSE", "income")
income['year'] = income['report_date'].dt.year
income['revenue_growth'] = income['revenue'].pct_change()

print("营收趋势:")
print(income[['year', 'revenue', 'net_profit', 'roe', 'revenue_growth']])
```

---

### 场景3：基本面估值分析

```python
from quant.storage.stores import StoreConfig, FundamentalStore

store = FundamentalStore(StoreConfig(root="data/fundamentals"))

# 加载基本面数据
df = store.load("600000", "SSE")

# 计算PE百分位
df['pe_percentile'] = df['pe_ratio'].rank(pct=True) * 100

# 当前估值
latest = df.iloc[-1]
print(f"PE: {latest['pe_ratio']:.2f}")
print(f"PE百分位: {latest['pe_percentile']:.1f}%")

if latest['pe_percentile'] < 30:
    print("💰 低估区域")
elif latest['pe_percentile'] > 70:
    print("⚠️ 高估区域")
else:
    print("👀 合理区域")
```

---

### 场景4：数据迁移

```python
# 从旧存储迁移到新存储
src = BarStore(StoreConfig(root="data/old"))
dst = BarStore(StoreConfig(root="data/new"))

for symbol in ["600000", "600036"]:
    df = src.load("SSE", symbol, "1d")
    dst.append("SSE", symbol, "1d", df)
    print(f"✅ {symbol} 迁移完成")
```

---

### 场景5：存储空间统计

```python
from pathlib import Path

def get_dir_size(path: Path) -> int:
    total = 0
    for item in path.rglob('*'):
        if item.is_file():
            total += item.stat().st_size
    return total

root = Path("data/history")
total_mb = get_dir_size(root) / 1024 / 1024
print(f"总存储空间: {total_mb:.2f} MB")

# 按交易所统计
for exchange_dir in root.iterdir():
    if exchange_dir.is_dir():
        size_mb = get_dir_size(exchange_dir) / 1024 / 1024
        print(f"{exchange_dir.name}: {size_mb:.2f} MB")
```

---

## 📚 存储对比表

| 存储 | 数据类型 | 分区方式 | 去重字段 | 目录结构 |
|------|----------|----------|----------|----------|
| **BarStore** | K线数据 | 按年分桶 | `date` | `{exchange}/{symbol}/{interval}/{year}.parquet` |
| **FinancialStore** | 财务报表 | 按报表类型 | `report_date` | `financials/{exchange}/{symbol}/{report_type}.parquet` |
| **FundamentalStore** | 基本面指标 | 单文件 | `date` | `fundamentals/{exchange}/{symbol}/daily.parquet` |

---

## 📖 API 参考

### StoreConfig

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `root` | str | `"~/.quant/history"` | 存储根目录 |
| `compression` | str | `"zstd"` | 压缩算法 |
| `use_dictionary` | bool | `True` | 字典编码 |

### BarStore

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `append(exchange, symbol, interval, df)` | 追加K线数据 | int |
| `load(exchange, symbol, interval, start, end)` | 加载K线数据 | DataFrame |
| `query(exchange, symbol, interval, sql, start, end)` | SQL查询 | DataFrame |

### FinancialStore

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `save(symbol, exchange, report_type, df)` | 保存财务数据 | int |
| `load(symbol, exchange, report_type, start, end)` | 加载财务数据 | DataFrame |

### FundamentalStore

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `save(symbol, exchange, df)` | 保存基本面数据 | int |
| `load(symbol, exchange, start, end)` | 加载基本面数据 | DataFrame |

---

## ⚠️ 重要提示

### 1. 数据格式

**K线数据**必须包含列：
```python
['date', 'open', 'high', 'low', 'close', 'volume']
```

**财务数据**至少包含：
```python
['report_date', 'publish_date', 'report_type', 'report_period']
```

**基本面数据**至少包含：
```python
['date']
```

---

### 2. 时间格式

所有时间字段必须是 `pd.Timestamp`：

```python
# ✅ 正确
df['date'] = pd.to_datetime(df['date'])

# ❌ 错误
df['date'] = ['2024-01-01', '2024-01-02', ...]  # 字符串
```

---

### 3. 数据去重

- **K线**: 按 `date` 去重，保留最新
- **财务**: 按 `report_date` 去重，保留最新
- **基本面**: 按 `date` 去重，保留最新

---

### 4. 并发写入

⚠️ **不支持并发写入**，需要在应用层加锁：

```python
import threading

lock = threading.Lock()

def safe_append(store, exchange, symbol, interval, df):
    with lock:
        return store.append(exchange, symbol, interval, df)
```

---

### 5. 存储空间

典型数据量（使用 zstd 压缩）：

| 数据类型 | 原始大小 | 压缩后 | 压缩率 |
|----------|----------|--------|--------|
| K线（1年日线） | ~500 KB | ~100 KB | 80% |
| 财务（10年） | ~200 KB | ~40 KB | 80% |
| 基本面（1年日频） | ~2 MB | ~400 KB | 80% |

---

## 🔗 相关文档

- **[详细使用指南](./USAGE_GUIDE.md)** - 完整的API文档和高级功能
- **[Types 模块](../../datahub/types/docs/README.md)** - 数据类型定义
- **[Services 模块](../../datahub/services/docs/README.md)** - 数据服务层
- **[Providers 模块](../../datahub/providers/docs/README.md)** - 数据提供者

---

## 📁 模块结构

```
quant/storage/stores/
├── __init__.py                  # 统一导出接口
├── base.py                      # 基础类和工具
├── bar_store.py                # K线存储
├── financial_store.py          # 财务存储
├── fundamental_store.py        # 基本面存储
└── docs/
    ├── README.md                # 快速参考（本文件）
    └── USAGE_GUIDE.md           # 详细使用指南
```

---

## 🎯 核心特性

- ✅ **高效存储** - Parquet + zstd 压缩
- ✅ **智能分区** - 按年/类型/股票分区
- ✅ **增量更新** - 自动合并去重
- ✅ **快速查询** - DuckDB SQL 支持
- ✅ **原子操作** - 写入安全可靠
- ✅ **索引管理** - Manifest 快速定位

---

## 🔄 向后兼容

保留了原有别名：

```python
# 新接口（推荐）
from quant.storage.stores import BarStore
store = BarStore(config)

# 旧接口（仍然可用）
from quant.storage.stores import ParquetYearWriter
writer = ParquetYearWriter(config)  # 等同于 BarStore
```

---

**维护者**: AlphaGrid Team  
**最后更新**: 2024-10-24  
**版本**: 1.0.0

