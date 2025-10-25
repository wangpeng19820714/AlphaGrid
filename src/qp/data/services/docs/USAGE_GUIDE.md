# DataHub Services 使用说明

## 📋 概述

Services 模块提供了数据服务层，负责数据的导入、存储、查询和处理。通过统一的服务接口，可以方便地管理 K线数据、财务数据和基本面数据。

**模块路径**: `qp/data/services/`

**核心特性**:
- 🔄 **数据导入** - 从 Provider 导入数据到本地存储
- 💾 **数据存储** - 持久化存储，支持增量更新
- 🔍 **数据查询** - 灵活的时间范围和条件查询
- ⚙️ **数据处理** - 重采样、复权、分析等功能
- 📊 **便捷方法** - 提供高级查询和分析工具

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

## 🚀 快速开始

### 基本导入

```python
from qp.data.services import (
    BarDataService,
    FinancialDataService,
    FundamentalDataService,
)

# 或使用向后兼容别名
from qp.data.services import HistoricalDataService
```

### 简单示例

```python
from qp.data.services import BarDataService
from qp.data.providers import get_provider
from qp.data.types import Exchange, Interval
import pandas as pd

# 1. 创建服务和数据源
service = BarDataService()
provider = get_provider('akshare')

# 2. 导入数据
count = service.import_from_provider(
    provider=provider,
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31"),
    adjust="qfq"
)

print(f"导入 {count} 条数据")

# 3. 查询数据
bars = service.load_bars("600000", Exchange.SSE, Interval.DAILY)
print(f"加载 {len(bars)} 条数据")
```

---

## 📊 服务类型

### 1. BarDataService - K线数据服务

管理 K线数据的导入、存储和查询。

**主要功能**:
- 数据导入和存储
- 时间范围查询
- 数据重采样（如5分钟→日线）
- 复权处理

**基本用法**:

```python
from qp.data.services import BarDataService

service = BarDataService()

# 保存数据
bars = [...]  # BarData 列表
count = service.save_bars(bars)

# 加载数据
bars = service.load_bars(
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)

# 获取最新K线
latest = service.get_latest_bar("600000", Exchange.SSE, Interval.DAILY)
```

---

### 2. FinancialDataService - 财务数据服务

管理财务报表数据（资产负债表、利润表、现金流量表）。

**主要功能**:
- 财务数据导入和存储
- 按报表类型查询
- 获取年报/季报
- 计算增长率

**基本用法**:

```python
from qp.data.services import FinancialDataService
from qp.data.types import FinancialReportType

service = FinancialDataService()
service.set_store(store)  # 设置存储实例

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
    symbol="600000",
    exchange=Exchange.SSE,
    report_type=FinancialReportType.INCOME
)

# 获取最新财报
latest = service.get_latest_financial_report(
    "600000", Exchange.SSE, FinancialReportType.INCOME
)

# 获取最近3年年报
annual_reports = service.get_annual_reports(
    "600000", Exchange.SSE, FinancialReportType.INCOME, years=3
)
```

---

### 3. FundamentalDataService - 基本面数据服务

管理基本面指标数据（PE、PB、ROE等）。

**主要功能**:
- 基本面数据导入和存储
- 按类别查询（估值/盈利/成长）
- 计算估值百分位
- 历史趋势分析

**基本用法**:

```python
from qp.data.services import FundamentalDataService

service = FundamentalDataService()
service.set_store(store)

# 导入基本面数据
count = service.import_fundamentals(
    provider=provider,
    symbol="600000",
    exchange=Exchange.SSE,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)

# 加载基本面数据
df = service.load_fundamentals(
    symbol="600000",
    exchange=Exchange.SSE
)

# 获取估值指标
valuation = service.get_valuation_metrics(
    "600000", Exchange.SSE
)

# 获取盈利能力指标
profitability = service.get_profitability_metrics(
    "600000", Exchange.SSE
)

# 获取成长性指标
growth = service.get_growth_metrics(
    "600000", Exchange.SSE
)
```

---

## 💡 完整使用示例

### 示例1：完整的数据工作流

```python
from qp.data.services import (
    BarDataService,
    FinancialDataService,
    FundamentalDataService,
)
from qp.data.providers import get_provider
from qp.data.types import Exchange, Interval, FinancialReportType
from qp.data.stores import StoreConfig, FundamentalStore
import pandas as pd

# ========== 准备工作 ==========
symbol = "600000"
exchange = Exchange.SSE
provider = get_provider('akshare')

# ========== 1. K线数据工作流 ==========
print("=" * 60)
print("1. K线数据服务")
print("=" * 60)

bar_service = BarDataService()

# 导入数据
count = bar_service.import_from_provider(
    provider=provider,
    symbol=symbol,
    exchange=exchange,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31"),
    adjust="qfq"
)
print(f"导入 {count} 条K线数据")

# 查询数据
bars = bar_service.load_bars(symbol, exchange, Interval.DAILY)
print(f"加载 {len(bars)} 条K线数据")

# 获取最新数据
latest = bar_service.get_latest_bar(symbol, exchange, Interval.DAILY)
if latest:
    print(f"最新: {latest.datetime.date()} 收盘={latest.close_price:.2f}")

# ========== 2. 财务数据工作流 ==========
print("\n" + "=" * 60)
print("2. 财务数据服务")
print("=" * 60)

# 初始化存储和服务
config = StoreConfig(root="data/fundamental_root")
store = FundamentalStore(config)
financial_service = FinancialDataService()
financial_service.set_store(store)

# 导入财务数据
count = financial_service.import_financials(
    provider=provider,
    symbol=symbol,
    exchange=exchange,
    report_type=FinancialReportType.INCOME,
    start=pd.Timestamp("2023-01-01"),
    end=pd.Timestamp("2024-12-31")
)
print(f"导入 {count} 条财务数据")

# 查询财务数据
df = financial_service.load_financials(
    symbol, exchange, FinancialReportType.INCOME
)
print(f"加载 {len(df)} 条财务记录")

# 获取最新财报
latest = financial_service.get_latest_financial_report(
    symbol, exchange, FinancialReportType.INCOME
)
if not latest.empty:
    print(f"最新财报: {latest['report_date']}")
    print(f"  营收: {latest['revenue']:,.0f}")
    print(f"  净利润: {latest['net_profit']:,.0f}")

# 获取年报
annual = financial_service.get_annual_reports(
    symbol, exchange, FinancialReportType.INCOME, years=3
)
print(f"\n最近3年年报: {len(annual)} 条")

# 计算增长率
growth = financial_service.calculate_growth_rate(
    symbol, exchange, FinancialReportType.INCOME, field='revenue'
)
print(f"\n营收增长率分析:\n{growth}")

# ========== 3. 基本面数据工作流 ==========
print("\n" + "=" * 60)
print("3. 基本面数据服务")
print("=" * 60)

fundamental_service = FundamentalDataService()
fundamental_service.set_store(store)

# 导入基本面数据
count = fundamental_service.import_fundamentals(
    provider=provider,
    symbol=symbol,
    exchange=exchange,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)
print(f"导入 {count} 条基本面数据")

# 获取估值指标
valuation = fundamental_service.get_valuation_metrics(
    symbol, exchange
)
print(f"\n估值指标:\n{valuation.tail()}")

# 获取盈利能力
profitability = fundamental_service.get_profitability_metrics(
    symbol, exchange
)
print(f"\n盈利能力:\n{profitability.tail()}")

# 计算估值百分位
pe_percentile = fundamental_service.calculate_valuation_percentile(
    symbol, exchange, metric='pe_ratio', window=252
)
print(f"\nPE百分位:\n{pe_percentile.tail()}")
```

---

### 示例2：K线数据重采样

```python
from qp.data.services import BarDataService
from qp.data.types import Exchange, Interval

service = BarDataService()

# 加载分钟数据
bars_5m = service.load_bars(
    "600000", Exchange.SSE, Interval.MIN5,
    start=pd.Timestamp("2024-12-01"),
    end=pd.Timestamp("2024-12-31")
)

print(f"原始数据: {len(bars_5m)} 条5分钟K线")

# 重采样为小时线
bars_1h = service.resample(bars_5m, to=Interval.HOUR1)
print(f"重采样后: {len(bars_1h)} 条1小时K线")

# 重采样为日线
bars_1d = service.resample(bars_5m, to=Interval.DAILY)
print(f"重采样后: {len(bars_1d)} 条日线")
```

---

### 示例3：复权处理

```python
from qp.data.services import BarDataService
import pandas as pd

service = BarDataService()

# 加载未复权数据
bars = service.load_bars("600000", Exchange.SSE, Interval.DAILY)

# 准备复权因子（示例）
factor_series = pd.Series({
    pd.Timestamp("2024-01-01"): 1.0,
    pd.Timestamp("2024-06-15"): 1.1,  # 除权除息日
    pd.Timestamp("2024-12-31"): 1.1,
})

# 应用复权
adjusted_bars = service.apply_adjust(bars, factor_series)

print(f"原始数据: {bars[0].close_price:.2f}")
print(f"复权后: {adjusted_bars[0].close_price:.2f}")
```

---

### 示例4：财务数据分析

```python
from qp.data.services import FinancialDataService
from qp.data.types import FinancialReportType

service = FinancialDataService()
service.set_store(store)

symbol = "600000"

# 获取季报数据
quarterly = service.get_quarterly_reports(
    symbol, Exchange.SSE, 
    FinancialReportType.INCOME,
    quarters=8  # 最近8个季度
)

print("季度财报趋势:")
print(quarterly[['report_date', 'revenue', 'net_profit']])

# 计算营收增长率
revenue_growth = service.calculate_growth_rate(
    symbol, Exchange.SSE,
    FinancialReportType.INCOME,
    field='revenue'
)

print("\n营收增长率:")
print(revenue_growth)

# 计算利润增长率
profit_growth = service.calculate_growth_rate(
    symbol, Exchange.SSE,
    FinancialReportType.INCOME,
    field='net_profit'
)

print("\n净利润增长率:")
print(profit_growth)
```

---

### 示例5：基本面指标分析

```python
from qp.data.services import FundamentalDataService

service = FundamentalDataService()
service.set_store(store)

symbol = "600000"

# 获取最新基本面数据
latest = service.get_latest_fundamentals(symbol, Exchange.SSE)
print("最新基本面指标:")
print(f"  PE: {latest['pe_ratio']:.2f}")
print(f"  PB: {latest['pb_ratio']:.2f}")
print(f"  ROE: {latest['roe']:.2%}")
print(f"  市值: {latest['market_cap']:,.0f}")

# 获取估值趋势
valuation = service.get_valuation_metrics(
    symbol, Exchange.SSE,
    start=pd.Timestamp("2024-01-01")
)

print("\n估值指标趋势:")
print(valuation[['date', 'pe_ratio', 'pb_ratio']].tail())

# 计算PE历史百分位
pe_percentile = service.calculate_valuation_percentile(
    symbol, Exchange.SSE,
    metric='pe_ratio',
    window=252  # 一年
)

latest_percentile = pe_percentile.iloc[-1]
print(f"\nPE当前处于过去一年的 {latest_percentile['pe_ratio_percentile']:.1f}% 分位")

# 判断估值水平
if latest_percentile['pe_ratio_percentile'] < 30:
    print("估值较低，可能被低估")
elif latest_percentile['pe_ratio_percentile'] > 70:
    print("估值较高，可能被高估")
else:
    print("估值处于合理区间")
```

---

## 🔧 高级功能

### 1. 批量数据导入

```python
from qp.data.services import BarDataService
from qp.data.providers import get_provider

service = BarDataService()
provider = get_provider('akshare')

# 批量导入多只股票
symbols = ["600000", "600036", "601318", "601398"]
exchange = Exchange.SSE

for symbol in symbols:
    try:
        count = service.import_from_provider(
            provider=provider,
            symbol=symbol,
            exchange=exchange,
            interval=Interval.DAILY,
            start=pd.Timestamp("2024-01-01"),
            end=pd.Timestamp("2024-12-31"),
            adjust="qfq"
        )
        print(f"✅ {symbol}: 导入 {count} 条数据")
    except Exception as e:
        print(f"❌ {symbol}: {e}")
```

---

### 2. 数据验证和清洗

```python
from qp.data.services import BarDataService

service = BarDataService()

# 加载数据
bars = service.load_bars("600000", Exchange.SSE, Interval.DAILY)

# 验证数据完整性
if bars:
    # 检查时间序列连续性
    dates = [bar.datetime for bar in bars]
    gaps = []
    for i in range(1, len(dates)):
        diff = (dates[i] - dates[i-1]).days
        if diff > 3:  # 周末+节假日
            gaps.append((dates[i-1].date(), dates[i].date()))
    
    if gaps:
        print(f"发现 {len(gaps)} 个数据缺口:")
        for start, end in gaps[:5]:
            print(f"  {start} -> {end}")
    else:
        print("✅ 数据连续，无缺口")
    
    # 检查异常值
    prices = [bar.close_price for bar in bars]
    volumes = [bar.volume for bar in bars]
    
    # 简单的异常检测
    price_changes = [(prices[i]/prices[i-1] - 1) * 100 
                     for i in range(1, len(prices))]
    
    large_moves = [(i, change) for i, change in enumerate(price_changes) 
                   if abs(change) > 10]
    
    if large_moves:
        print(f"\n发现 {len(large_moves)} 个大幅波动:")
        for i, change in large_moves[:5]:
            print(f"  {dates[i+1].date()}: {change:+.2f}%")
```

---

### 3. 数据导出

```python
from qp.data.services import BarDataService
from qp.data.types import bars_to_df
import pandas as pd

service = BarDataService()

# 加载数据
bars = service.load_bars("600000", Exchange.SSE, Interval.DAILY)

# 转换为 DataFrame
df = bars_to_df(bars)

# 导出为 CSV
df.to_csv("600000_daily.csv", index=False)
print(f"导出 {len(df)} 条数据到 CSV")

# 导出为 Excel
df.to_excel("600000_daily.xlsx", index=False)
print(f"导出 {len(df)} 条数据到 Excel")

# 导出为 Parquet（高效压缩）
df.to_parquet("600000_daily.parquet", index=False)
print(f"导出 {len(df)} 条数据到 Parquet")
```

---

## 📚 API 参考

### BarDataService

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `save_bars(bars)` | 保存K线数据 | int (保存数量) |
| `load_bars(symbol, exchange, interval, start, end)` | 加载K线数据 | list[BarData] |
| `import_from_provider(provider, ...)` | 从Provider导入 | int |
| `resample(bars, to)` | 重采样 | list[BarData] |
| `apply_adjust(bars, factor_series)` | 应用复权 | list[BarData] |
| `get_latest_bar(symbol, exchange, interval)` | 获取最新K线 | BarData 或 None |
| `get_bars_between(symbol, exchange, interval, start, end)` | 时间范围查询 | list[BarData] |

### FinancialDataService

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `import_financials(provider, ...)` | 导入财务数据 | int |
| `load_financials(symbol, exchange, report_type, ...)` | 加载财务数据 | DataFrame |
| `get_latest_financial_report(...)` | 获取最新财报 | Series |
| `get_annual_reports(symbol, exchange, report_type, years)` | 获取年报 | DataFrame |
| `get_quarterly_reports(symbol, exchange, report_type, quarters)` | 获取季报 | DataFrame |
| `calculate_growth_rate(symbol, exchange, report_type, field)` | 计算增长率 | DataFrame |

### FundamentalDataService

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `import_fundamentals(provider, ...)` | 导入基本面数据 | int |
| `load_fundamentals(symbol, exchange, ...)` | 加载基本面数据 | DataFrame |
| `get_latest_fundamentals(symbol, exchange)` | 获取最新数据 | Series |
| `get_fundamentals_at_date(symbol, exchange, date)` | 获取指定日期数据 | Series |
| `get_valuation_metrics(symbol, exchange, ...)` | 获取估值指标 | DataFrame |
| `get_profitability_metrics(symbol, exchange, ...)` | 获取盈利能力 | DataFrame |
| `get_growth_metrics(symbol, exchange, ...)` | 获取成长性 | DataFrame |
| `calculate_valuation_percentile(symbol, exchange, metric, window)` | 计算估值百分位 | DataFrame |

---

## ⚠️ 注意事项

### 1. 存储初始化

财务和基本面服务需要设置存储实例：

```python
from qp.data.stores import StoreConfig, FundamentalStore

# 初始化存储
config = StoreConfig(root="data/fundamental_root")
store = FundamentalStore(config)

# 设置到服务
financial_service.set_store(store)
fundamental_service.set_store(store)
```

### 2. 数据持久化

- K线数据自动持久化到数据库
- 财务和基本面数据需要配置存储路径
- 支持增量更新，不会重复存储

### 3. 性能优化

```python
# 使用时间范围查询，避免加载全部数据
bars = service.load_bars(
    symbol, exchange, interval,
    start=pd.Timestamp("2024-01-01"),  # 指定开始时间
    end=pd.Timestamp("2024-12-31")     # 指定结束时间
)

# 使用列筛选（如果支持）
df = service.load_fundamentals(
    symbol, exchange,
    start=pd.Timestamp("2024-01-01")
)
```

### 4. 异常处理

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

## 🔗 相关文档

- [Providers 模块文档](../../providers/docs/USAGE_GUIDE.md) - 数据提供者
- [Types 模块文档](../../types/README.md) - 数据类型定义
- [Stores 模块文档](../../../storage/stores/README.md) - 存储层接口

---

## 📝 更新日志

- **2024-10-24**: 初始版本
  - 实现 BarDataService, FinancialDataService, FundamentalDataService
  - 支持数据导入、存储、查询
  - 提供重采样、复权、分析功能
  - 30+ 便捷方法

---

**维护者**: AlphaGrid Team  
**最后更新**: 2024-10-24

