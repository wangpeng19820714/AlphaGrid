# DataHub Types 快速参考

## 📋 类型模块概览

Types 模块定义了 AlphaGrid 数据层的核心数据结构，包括 K线数据、财务数据和基本面数据的类型定义与转换工具。

**模块路径**: `qp/data/types/`

---

## 🚀 快速开始

```python
# 导入类型
from qp.data.types import (
    # 共享枚举
    Exchange, Interval,
    
    # K线数据
    BarData, bars_to_df, df_to_bars,
    
    # 财务数据
    FinancialData, FinancialReportType, ReportPeriod,
    financials_to_df, df_to_financials,
    
    # 基本面数据
    FundamentalData, fundamentals_to_df, df_to_fundamentals
)

# 创建K线数据
import pandas as pd

bar = BarData(
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    datetime=pd.Timestamp("2024-10-24", tz="UTC"),
    open_price=10.50,
    high_price=10.80,
    low_price=10.40,
    close_price=10.75,
    volume=1000000.0
)

print(f"{bar.symbol}: {bar.close_price}")
```

---

## 📊 核心数据类型

### 1️⃣ 共享枚举类型

#### Exchange - 交易所

```python
from qp.data.types import Exchange

Exchange.SSE      # 上海证券交易所
Exchange.SZSE     # 深圳证券交易所
Exchange.HKEX     # 香港交易所
Exchange.NYSE     # 纽约证券交易所
Exchange.NASDAQ   # 纳斯达克
Exchange.OTHER    # 其他
```

#### Interval - 时间周期

```python
from qp.data.types import Interval

Interval.TICK      # Tick
Interval.MIN1      # 1分钟
Interval.MIN5      # 5分钟
Interval.MIN15     # 15分钟
Interval.MIN30     # 30分钟
Interval.HOUR1     # 1小时
Interval.HOUR4     # 4小时
Interval.DAILY     # 日线
Interval.WEEKLY    # 周线
Interval.MONTHLY   # 月线
```

---

### 2️⃣ K线数据（BarData）

**字段**:
- `symbol`: 股票代码
- `exchange`: 交易所（Exchange枚举）
- `interval`: 时间周期（Interval枚举）
- `datetime`: 时间戳（UTC）
- `open_price`: 开盘价
- `high_price`: 最高价
- `low_price`: 最低价
- `close_price`: 收盘价
- `volume`: 成交量
- `turnover`: 成交额
- `open_interest`: 持仓量（期货）

**创建示例**:

```python
from qp.data.types import BarData, Exchange, Interval
import pandas as pd

bar = BarData(
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    datetime=pd.Timestamp("2024-10-24", tz="UTC"),
    open_price=10.50,
    high_price=10.80,
    low_price=10.40,
    close_price=10.75,
    volume=1000000.0,
    turnover=10750000.0
)

print(f"收盘价: {bar.close_price}")
print(f"成交量: {bar.volume}")
```

**转换工具**:

```python
from qp.data.types import bars_to_df, df_to_bars

# 列表 → DataFrame
bars = [bar1, bar2, bar3]
df = bars_to_df(bars)
print(df)

# DataFrame → 列表
bars = df_to_bars(df, "600000", Exchange.SSE, Interval.DAILY)
print(f"转换了 {len(bars)} 条K线")
```

---

### 3️⃣ 财务数据（FinancialData）

#### 报表类型

```python
from qp.data.types import FinancialReportType, ReportPeriod

# 报表类型
FinancialReportType.BALANCE_SHEET  # 资产负债表
FinancialReportType.INCOME         # 利润表
FinancialReportType.CASHFLOW       # 现金流量表
FinancialReportType.INDICATOR      # 财务指标

# 报告期
ReportPeriod.Q1      # 一季报
ReportPeriod.Q2      # 中报/半年报
ReportPeriod.Q3      # 三季报
ReportPeriod.Q4      # 四季报
ReportPeriod.ANNUAL  # 年报
```

#### 主要字段

**基本信息**:
- `symbol`, `exchange`, `report_date`, `publish_date`
- `report_type`, `report_period`

**资产负债表**:
- `total_assets`, `total_liabilities`, `total_equity`
- `current_assets`, `current_liabilities`, `fixed_assets`

**利润表**:
- `revenue`, `operating_revenue`, `operating_cost`
- `operating_profit`, `total_profit`, `net_profit`
- `net_profit_parent`, `basic_eps`

**现金流量表**:
- `cash_flow_operating`, `cash_flow_investing`, `cash_flow_financing`

**财务指标**:
- `roe`, `roa`, `gross_margin`, `net_margin`
- `debt_to_asset_ratio`, `current_ratio`

**创建示例**:

```python
from quan.types import (
    FinancialData, FinancialReportType, ReportPeriod, Exchange
)
import pandas as pd

financial = FinancialData(
    symbol="600000",
    exchange=Exchange.SSE,
    report_date=pd.Timestamp("2024-12-31", tz="UTC"),
    publish_date=pd.Timestamp("2025-03-15", tz="UTC"),
    report_type=FinancialReportType.INCOME,
    report_period=ReportPeriod.ANNUAL,
    revenue=100_000_000_000.0,      # 1000亿
    net_profit=10_000_000_000.0,    # 100亿
    operating_profit=15_000_000_000.0,
    roe=0.15,                        # 15%
    net_margin=0.10,                 # 10%
    extra_fields={"industry": "银行业"}
)

print(f"营收: {financial.revenue:,.0f}")
print(f"净利润: {financial.net_profit:,.0f}")
print(f"ROE: {financial.roe:.2%}")
```

**转换工具**:

```python
from qp.data.types import financials_to_df, df_to_financials

# 列表 → DataFrame
financials = [financial1, financial2, financial3]
df = financials_to_df(financials)
print(df[['symbol', 'report_date', 'revenue', 'net_profit']])

# DataFrame → 列表
financials = df_to_financials(df)
```

---

### 4️⃣ 基本面数据（FundamentalData）

#### 主要字段

**估值指标**:
- `pe_ratio`, `pe_ttm`, `pb_ratio`, `ps_ratio`, `pcf_ratio`

**市值相关**:
- `market_cap`, `circulating_market_cap`
- `total_shares`, `circulating_shares`

**财务质量**:
- `roe`, `roa`, `roic`
- `debt_to_asset_ratio`, `debt_to_equity_ratio`
- `current_ratio`, `quick_ratio`

**成长性**:
- `revenue_growth`, `revenue_growth_qoq`
- `profit_growth`, `profit_growth_qoq`

**盈利能力**:
- `gross_margin`, `net_margin`, `operating_margin`

**每股指标**:
- `eps`, `bps`, `ocfps`

**分红**:
- `dividend_yield`, `payout_ratio`

**创建示例**:

```python
from qp.data.types import FundamentalData, Exchange
import pandas as pd

fundamental = FundamentalData(
    symbol="600000",
    exchange=Exchange.SSE,
    date=pd.Timestamp("2024-10-24", tz="UTC"),
    pe_ratio=5.8,
    pb_ratio=0.6,
    market_cap=200_000_000_000.0,    # 2000亿
    roe=0.12,                         # 12%
    roa=0.08,                         # 8%
    revenue_growth=0.08,              # 8%
    profit_growth=0.10,               # 10%
    eps=2.50,
    dividend_yield=0.045,             # 4.5%
)

print(f"PE: {fundamental.pe_ratio:.2f}")
print(f"PB: {fundamental.pb_ratio:.2f}")
print(f"ROE: {fundamental.roe:.2%}")
print(f"股息率: {fundamental.dividend_yield:.2%}")
```

**转换工具**:

```python
from qp.data.types import fundamentals_to_df, df_to_fundamentals

# 列表 → DataFrame
fundamentals = [fundamental1, fundamental2, fundamental3]
df = fundamentals_to_df(fundamentals)
print(df[['symbol', 'date', 'pe_ratio', 'pb_ratio', 'roe']])

# DataFrame → 列表
fundamentals = df_to_fundamentals(df)
```

---

## 💡 常用场景

### 场景1：K线数据处理

```python
from qp.data.types import BarData, bars_to_df, Exchange, Interval
import pandas as pd

# 创建K线数据
bars = [
    BarData(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.DAILY,
        datetime=pd.Timestamp(f"2024-10-{20+i}", tz="UTC"),
        open_price=10.0 + i * 0.1,
        high_price=10.2 + i * 0.1,
        low_price=9.9 + i * 0.1,
        close_price=10.1 + i * 0.1,
        volume=1000000.0
    )
    for i in range(5)
]

# 转为 DataFrame 分析
df = bars_to_df(bars)

# 计算收益率
df['return'] = df['close'].pct_change()

# 计算均线
df['ma5'] = df['close'].rolling(5).mean()

print(df[['datetime', 'close', 'return', 'ma5']])
```

---

### 场景2：财务数据对比

```python
from qp.data.types import (
    FinancialData, FinancialReportType, ReportPeriod,
    Exchange, financials_to_df
)
import pandas as pd

# 创建多年财务数据
financials = []
for year in range(2022, 2025):
    financials.append(FinancialData(
        symbol="600000",
        exchange=Exchange.SSE,
        report_date=pd.Timestamp(f"{year}-12-31", tz="UTC"),
        publish_date=pd.Timestamp(f"{year+1}-03-15", tz="UTC"),
        report_type=FinancialReportType.INCOME,
        report_period=ReportPeriod.ANNUAL,
        revenue=90_000_000_000 * (1.1 ** (year - 2022)),
        net_profit=9_000_000_000 * (1.12 ** (year - 2022)),
        roe=0.13 + (year - 2022) * 0.01
    ))

# 转为 DataFrame 并分析
df = financials_to_df(financials)
df['year'] = df['report_date'].dt.year
df['revenue_growth'] = df['revenue'].pct_change()

print("年度对比:")
print(df[['year', 'revenue', 'net_profit', 'roe', 'revenue_growth']])
```

---

### 场景3：估值分析

```python
from qp.data.types import FundamentalData, fundamentals_to_df, Exchange
import pandas as pd

# 创建时间序列基本面数据
fundamentals = [
    FundamentalData(
        symbol="600000",
        exchange=Exchange.SSE,
        date=pd.Timestamp(f"2024-10-{20+i}", tz="UTC"),
        pe_ratio=5.8 + i * 0.05,
        pb_ratio=0.6 + i * 0.01,
        market_cap=200_000_000_000,
        roe=0.12
    )
    for i in range(5)
]

# 转为 DataFrame 并分析
df = fundamentals_to_df(fundamentals)

# 计算估值百分位
df['pe_percentile'] = df['pe_ratio'].rank(pct=True) * 100

# 估值判断
latest = df.iloc[-1]
if latest['pe_percentile'] < 30:
    print("估值较低，可能被低估")
elif latest['pe_percentile'] > 70:
    print("估值较高，可能被高估")
else:
    print("估值合理")

print(f"当前PE: {latest['pe_ratio']:.2f}")
print(f"PE百分位: {latest['pe_percentile']:.1f}%")
```

---

### 场景4：数据导出

```python
from qp.data.types import bars_to_df

# 转为 DataFrame
df = bars_to_df(bars)

# 导出到不同格式
df.to_csv("bars.csv", index=False)           # CSV
df.to_excel("bars.xlsx", index=False)        # Excel
df.to_parquet("bars.parquet", index=False)   # Parquet（推荐）

print("数据已导出")
```

---

## 📚 数据类型对比表

| 类型 | 用途 | 频率 | 主要字段 | 转换函数 |
|------|------|------|----------|----------|
| **BarData** | K线数据 | 分钟/日线等 | OHLCV | `bars_to_df`, `df_to_bars` |
| **FinancialData** | 财务报表 | 季度/年度 | 资产/营收/利润 | `financials_to_df`, `df_to_financials` |
| **FundamentalData** | 基本面指标 | 日频 | PE/PB/ROE/市值 | `fundamentals_to_df`, `df_to_fundamentals` |

---

## ⚠️ 重要提示

### 1. 数据不可变性

所有数据类都是 **不可变的**（`frozen=True`）：

```python
# ❌ 错误：不能直接修改
bar.close_price = 11.0  # 会报错

# ✅ 正确：使用 replace 创建新对象
from dataclasses import replace
bar_new = replace(bar, close_price=11.0)
```

---

### 2. 时区处理

所有时间戳应使用 **UTC 时区**：

```python
# ✅ 推荐
datetime = pd.Timestamp("2024-10-24", tz="UTC")

# ⚠️ 不推荐（会自动转换）
datetime = pd.Timestamp("2024-10-24")
```

---

### 3. Optional 字段

财务和基本面数据的大部分字段是 `Optional`，使用前检查：

```python
if fundamental.pe_ratio is not None:
    print(f"PE: {fundamental.pe_ratio:.2f}")
else:
    print("PE数据缺失")
```

---

### 4. 扩展字段

使用 `extra_fields` 存储自定义数据：

```python
financial = FinancialData(
    ...,
    extra_fields={
        "industry": "银行业",
        "custom_metric": 123.45
    }
)

# 访问
industry = financial.extra_fields.get("industry")
```

---

## 🔄 转换工具总览

| 函数 | 输入 | 输出 | 说明 |
|------|------|------|------|
| `bars_to_df(bars)` | list[BarData] | DataFrame | K线列表→表格 |
| `df_to_bars(df, symbol, exchange, interval)` | DataFrame | list[BarData] | 表格→K线列表 |
| `financials_to_df(financials)` | list[FinancialData] | DataFrame | 财务列表→表格 |
| `df_to_financials(df)` | DataFrame | list[FinancialData] | 表格→财务列表 |
| `fundamentals_to_df(fundamentals)` | list[FundamentalData] | DataFrame | 基本面列表→表格 |
| `df_to_fundamentals(df)` | DataFrame | list[FundamentalData] | 表格→基本面列表 |

---

## 📖 完整文档

- **[详细使用指南](./USAGE_GUIDE.md)** - 完整的字段说明、使用示例和高级功能
- **[Services 模块](../../services/docs/README.md)** - 数据服务层
- **[Providers 模块](../../providers/docs/README.md)** - 数据提供者
- **[Stores 模块](../../../storage/stores/README.md)** - 存储层接口

---

## 📁 模块结构

```
qp/data/types/
├── __init__.py                  # 统一导出接口
├── common.py                    # 共享枚举（Exchange, Interval）
├── bar.py                       # K线数据类型
├── financial.py                 # 财务数据类型
├── fundamental.py               # 基本面数据类型
└── docs/
    ├── README.md                # 快速参考（本文件）
    └── USAGE_GUIDE.md           # 详细使用指南
```

---

## 🎯 设计特性

- ✅ **类型安全** - 使用 dataclass 和类型注解
- ✅ **不可变** - frozen=True 保证数据一致性
- ✅ **可扩展** - extra_fields 支持自定义字段
- ✅ **标准化** - 统一的枚举和字段命名
- ✅ **易转换** - DataFrame 双向转换工具
- ✅ **文档完整** - 每个字段都有注释说明

---

**维护者**: AlphaGrid Team  
**最后更新**: 2024-10-24  
**版本**: 1.0.0

