# DataHub Services 快速参考

## 📋 服务模块概览

Services 层提供统一的数据服务接口，管理 K线数据、财务数据和基本面数据的导入、存储和查询。

**模块路径**: `qp/data/services/`

---

## 🚀 快速开始

```python
from qp.data.services import (
    BarDataService,
    FinancialDataService,
    FundamentalDataService,
)
from qp.data.providers import get_provider
from qp.data.types import Exchange, Interval
import pandas as pd

# K线数据服务
bar_service = BarDataService()
provider = get_provider('akshare')

# 导入数据
count = bar_service.import_from_provider(
    provider=provider,
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31"),
    adjust="qfq"
)
print(f"导入 {count} 条数据")

# 查询数据
bars = bar_service.load_bars("600000", Exchange.SSE, Interval.DAILY)
print(f"共 {len(bars)} 条K线")
```

---

## 📊 三大服务类型

### 1️⃣ BarDataService - K线数据服务

管理 OHLCV 数据的完整生命周期。

```python
from qp.data.services import BarDataService

service = BarDataService()

# 保存数据
bars = [...]  # list[BarData]
count = service.save_bars(bars)

# 加载数据（带时间范围）
bars = service.load_bars(
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)

# 获取最新K线
latest = service.get_latest_bar("600000", Exchange.SSE, Interval.DAILY)

# 重采样（5分钟→日线）
bars_daily = service.resample(bars_5min, to=Interval.DAILY)

# 应用复权因子
adjusted = service.apply_adjust(bars, factor_series)
```

**主要方法**:
- `save_bars()` - 保存K线数据
- `load_bars()` - 加载K线数据
- `import_from_provider()` - 从Provider导入
- `resample()` - 重采样
- `apply_adjust()` - 应用复权
- `get_latest_bar()` - 获取最新K线

---

### 2️⃣ FinancialDataService - 财务数据服务

管理三大财务报表（资产负债表、利润表、现金流量表）。

```python
from qp.data.services import FinancialDataService
from qp.data.types import FinancialReportType
from qp.stores import StoreConfig, FundamentalStore

# 初始化存储
config = StoreConfig(root="data/fundamental_root")
store = FundamentalStore(config)

service = FinancialDataService()
service.set_store(store)  # ⚠️ 必须设置存储

# 导入财务数据
count = service.import_financials(
    provider=provider,
    symbol="600000",
    exchange=Exchange.SSE,
    report_type=FinancialReportType.INCOME,
    start=pd.Timestamp("2020-01-01"),
    end=pd.Timestamp("2024-12-31")
)

# 加载财务数据
df = service.load_financials(
    "600000", Exchange.SSE, FinancialReportType.INCOME
)

# 获取最新财报
latest = service.get_latest_financial_report(
    "600000", Exchange.SSE, FinancialReportType.INCOME
)
print(f"营收: {latest['revenue']:,.0f}")
print(f"净利润: {latest['net_profit']:,.0f}")

# 获取最近3年年报
annual = service.get_annual_reports(
    "600000", Exchange.SSE, FinancialReportType.INCOME, years=3
)

# 计算营收增长率
growth = service.calculate_growth_rate(
    "600000", Exchange.SSE, FinancialReportType.INCOME, field='revenue'
)
```

**主要方法**:
- `import_financials()` - 导入财务数据
- `load_financials()` - 加载财务数据
- `get_latest_financial_report()` - 获取最新财报
- `get_annual_reports()` - 获取年报
- `get_quarterly_reports()` - 获取季报
- `calculate_growth_rate()` - 计算增长率

---

### 3️⃣ FundamentalDataService - 基本面数据服务

管理基本面指标（PE、PB、ROE、市值等）。

```python
from qp.data.services import FundamentalDataService

service = FundamentalDataService()
service.set_store(store)  # ⚠️ 必须设置存储

# 导入基本面数据
count = service.import_fundamentals(
    provider=provider,
    symbol="600000",
    exchange=Exchange.SSE,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)

# 加载基本面数据
df = service.load_fundamentals("600000", Exchange.SSE)

# 获取最新数据
latest = service.get_latest_fundamentals("600000", Exchange.SSE)
print(f"PE: {latest['pe_ratio']:.2f}")
print(f"PB: {latest['pb_ratio']:.2f}")
print(f"ROE: {latest['roe']:.2%}")

# 获取指定日期数据
data = service.get_fundamentals_at_date(
    "600000", Exchange.SSE, pd.Timestamp("2024-10-15")
)

# 获取估值指标趋势
valuation = service.get_valuation_metrics("600000", Exchange.SSE)

# 获取盈利能力指标
profitability = service.get_profitability_metrics("600000", Exchange.SSE)

# 获取成长性指标
growth = service.get_growth_metrics("600000", Exchange.SSE)

# 计算估值百分位（判断高估/低估）
percentile = service.calculate_valuation_percentile(
    "600000", Exchange.SSE, metric='pe_ratio', window=252
)
```

**主要方法**:
- `import_fundamentals()` - 导入基本面数据
- `load_fundamentals()` - 加载基本面数据
- `get_latest_fundamentals()` - 获取最新数据
- `get_fundamentals_at_date()` - 获取指定日期数据
- `get_valuation_metrics()` - 获取估值指标（PE/PB/PS）
- `get_profitability_metrics()` - 获取盈利能力（ROE/ROA/利润率）
- `get_growth_metrics()` - 获取成长性（营收/利润增长）
- `calculate_valuation_percentile()` - 计算估值百分位

---

## 📚 服务对比表

| 服务 | 数据类型 | 频率 | 存储方式 | 主要用途 |
|------|----------|------|----------|----------|
| **BarDataService** | K线数据 | 分钟/日线等 | 数据库(自动) | 技术分析、回测 |
| **FinancialDataService** | 财务报表 | 季度/年度 | Parquet(需配置) | 财务分析、基本面筛选 |
| **FundamentalDataService** | 基本面指标 | 日频 | Parquet(需配置) | 估值分析、投资决策 |

---

## 💡 常用场景

### 场景1：完整数据工作流

```python
# 1. 导入K线数据
bar_service = BarDataService()
bar_service.import_from_provider(provider, "600000", Exchange.SSE, ...)

# 2. 导入财务数据
financial_service = FinancialDataService()
financial_service.set_store(store)
financial_service.import_financials(provider, "600000", Exchange.SSE, ...)

# 3. 导入基本面数据
fundamental_service = FundamentalDataService()
fundamental_service.set_store(store)
fundamental_service.import_fundamentals(provider, "600000", Exchange.SSE, ...)

# 4. 综合分析
bars = bar_service.load_bars("600000", Exchange.SSE, Interval.DAILY)
financials = financial_service.load_financials("600000", Exchange.SSE, ...)
fundamentals = fundamental_service.load_fundamentals("600000", Exchange.SSE)
```

---

### 场景2：批量导入数据

```python
symbols = ["600000", "600036", "601318", "601398"]

for symbol in symbols:
    try:
        count = bar_service.import_from_provider(
            provider, symbol, Exchange.SSE, Interval.DAILY,
            start=pd.Timestamp("2024-01-01"),
            end=pd.Timestamp("2024-12-31")
        )
        print(f"✅ {symbol}: {count} 条")
    except Exception as e:
        print(f"❌ {symbol}: {e}")
```

---

### 场景3：估值分析

```python
# 获取估值指标
valuation = fundamental_service.get_valuation_metrics("600000", Exchange.SSE)

# 计算PE历史百分位
pe_percentile = fundamental_service.calculate_valuation_percentile(
    "600000", Exchange.SSE, metric='pe_ratio', window=252
)

# 判断估值水平
latest = pe_percentile.iloc[-1]['pe_ratio_percentile']
if latest < 30:
    print("估值较低，可能被低估")
elif latest > 70:
    print("估值较高，可能被高估")
else:
    print("估值合理")
```

---

### 场景4：财务增长分析

```python
# 获取季报趋势
quarterly = financial_service.get_quarterly_reports(
    "600000", Exchange.SSE, FinancialReportType.INCOME, quarters=8
)

# 计算增长率
revenue_growth = financial_service.calculate_growth_rate(
    "600000", Exchange.SSE, FinancialReportType.INCOME, field='revenue'
)

profit_growth = financial_service.calculate_growth_rate(
    "600000", Exchange.SSE, FinancialReportType.INCOME, field='net_profit'
)

print("营收增长率:")
print(revenue_growth)
print("\n净利润增长率:")
print(profit_growth)
```

---

### 场景5：数据重采样

```python
# 加载5分钟数据
bars_5m = bar_service.load_bars(
    "600000", Exchange.SSE, Interval.MIN5
)

# 重采样为小时线
bars_1h = bar_service.resample(bars_5m, to=Interval.HOUR1)

# 重采样为日线
bars_1d = bar_service.resample(bars_5m, to=Interval.DAILY)

print(f"5分钟: {len(bars_5m)} 条")
print(f"1小时: {len(bars_1h)} 条")
print(f"日线: {len(bars_1d)} 条")
```

---

## ⚙️ 配置说明

### K线数据服务（自动配置）

```python
# BarDataService 使用默认数据库，无需额外配置
bar_service = BarDataService()
```

---

### 财务/基本面服务（需要配置存储）

```python
from qp.stores import StoreConfig, FundamentalStore

# 1. 创建存储配置
config = StoreConfig(root="data/fundamental_root")

# 2. 创建存储实例
store = FundamentalStore(config)

# 3. 设置到服务
financial_service = FinancialDataService()
financial_service.set_store(store)

fundamental_service = FundamentalDataService()
fundamental_service.set_store(store)
```

---

## ⚠️ 重要提示

### 1. 存储初始化

❗ **财务和基本面服务必须先调用 `set_store()`**：

```python
# ❌ 错误：未设置存储
service = FinancialDataService()
service.load_financials(...)  # 会报错

# ✅ 正确：先设置存储
service = FinancialDataService()
service.set_store(store)
service.load_financials(...)  # 正常工作
```

---

### 2. 时间范围查询

建议指定时间范围，避免加载全部数据：

```python
# ✅ 推荐：指定时间范围
bars = service.load_bars(
    symbol, exchange, interval,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)

# ⚠️ 不推荐：加载全部数据（可能很慢）
bars = service.load_bars(symbol, exchange, interval)
```

---

### 3. 异常处理

```python
try:
    bars = service.load_bars(symbol, exchange, interval)
except FileNotFoundError:
    print("数据不存在，需要先导入")
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"查询失败: {e}")
```

---

### 4. 数据持久化

- **K线数据**: 自动持久化到数据库 ✅
- **财务数据**: 需要配置存储路径 ⚙️
- **基本面数据**: 需要配置存储路径 ⚙️
- 所有服务都支持增量更新，不会重复存储 🔄

---

## 📖 完整文档

- **[详细使用指南](./USAGE_GUIDE.md)** - 完整的API文档、使用示例和高级功能
- **[Providers 模块](../../providers/docs/README.md)** - 数据提供者接口
- **[Types 模块](../../types/)** - 数据类型定义
- **[Stores 模块](../../../storage/stores/)** - 存储层接口

---

## 📁 模块结构

```
qp/data/services/
├── __init__.py                  # 统一导出接口
├── base.py                      # 基础服务类
├── bar_service.py              # K线数据服务
├── financial_service.py        # 财务数据服务
├── fundamental_service.py      # 基本面数据服务
└── docs/
    ├── README.md                # 快速参考（本文件）
    └── USAGE_GUIDE.md           # 详细使用指南
```

---

## 🔄 向后兼容

保留了原有的 `HistoricalDataService` 别名：

```python
# 新接口（推荐）
from qp.data.services import BarDataService
service = BarDataService()

# 旧接口（仍然可用）
from qp.data.services import HistoricalDataService
service = HistoricalDataService()  # 等同于 BarDataService
```

---

**维护者**: AlphaGrid Team  
**最后更新**: 2024-10-24  
**版本**: 1.0.0

