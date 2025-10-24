# DataHub Types 使用说明

## 📋 概述

Types 模块定义了 AlphaGrid 数据层的核心数据类型，包括 K线数据、财务数据和基本面数据的结构定义、枚举类型和转换工具。

**模块路径**: `quant/datahub/types/`

**核心特性**:
- 📦 **数据类定义** - 使用 dataclass 定义结构化数据
- 🔢 **枚举类型** - 标准化的交易所、时间周期等枚举
- 🔄 **转换工具** - DataFrame ↔ 数据类的双向转换
- ✅ **类型安全** - 不可变数据类，保证数据一致性
- 📊 **字段完整** - 覆盖常用的金融数据字段

---

## 📁 模块结构

```
quant/datahub/types/
├── __init__.py                  # 统一导出接口
├── common.py                    # 共享枚举类型
├── bar.py                       # K线数据类型
├── financial.py                 # 财务数据类型
├── fundamental.py               # 基本面数据类型
└── docs/
    ├── README.md                # 快速参考
    └── USAGE_GUIDE.md           # 详细使用指南（本文件）
```

---

## 🚀 快速开始

### 基本导入

```python
# 共享类型
from quant.datahub.types import Exchange, Interval

# K线相关
from quant.datahub.types import BarData, bars_to_df, df_to_bars

# 财务数据相关
from quant.datahub.types import (
    FinancialData, 
    FinancialReportType, 
    ReportPeriod,
    financials_to_df, 
    df_to_financials
)

# 基本面数据相关
from quant.datahub.types import (
    FundamentalData,
    fundamentals_to_df,
    df_to_fundamentals
)
```

---

## 📊 数据类型详解

### 1. 共享枚举类型（common.py）

#### Exchange - 交易所枚举

```python
from quant.datahub.types import Exchange

# 支持的交易所
Exchange.SSE      # 上海证券交易所
Exchange.SZSE     # 深圳证券交易所
Exchange.HKEX     # 香港交易所
Exchange.NYSE     # 纽约证券交易所
Exchange.NASDAQ   # 纳斯达克
Exchange.OTHER    # 其他交易所

# 使用示例
exchange = Exchange.SSE
print(exchange.value)  # "SSE"

# 字符串转枚举
exchange = Exchange("SSE")
```

#### Interval - 时间周期枚举

```python
from quant.datahub.types import Interval

# 支持的时间周期
Interval.TICK      # Tick 数据
Interval.MIN1      # 1分钟
Interval.MIN5      # 5分钟
Interval.MIN15     # 15分钟
Interval.MIN30     # 30分钟
Interval.HOUR1     # 1小时
Interval.HOUR4     # 4小时
Interval.DAILY     # 日线
Interval.WEEKLY    # 周线
Interval.MONTHLY   # 月线

# 使用示例
interval = Interval.DAILY
print(interval.value)  # "1d"

# 字符串转枚举
interval = Interval("1d")
```

---

### 2. K线数据类型（bar.py）

#### BarData - K线数据类

**定义**:
```python
@dataclass(frozen=True)
class BarData:
    """K线数据类"""
    symbol: str              # 股票代码
    exchange: Exchange       # 交易所
    interval: Interval       # 时间周期
    datetime: pd.Timestamp   # 时间戳
    open_price: float        # 开盘价
    high_price: float        # 最高价
    low_price: float         # 最低价
    close_price: float       # 收盘价
    volume: float = 0.0      # 成交量
    turnover: float = 0.0    # 成交额
    open_interest: float = 0.0  # 持仓量（期货）
```

**使用示例**:

```python
from quant.datahub.types import BarData, Exchange, Interval
import pandas as pd

# 创建K线数据
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

# 访问字段
print(f"股票: {bar.symbol}")
print(f"收盘价: {bar.close_price}")
print(f"成交量: {bar.volume}")

# 不可变性（frozen=True）
# bar.close_price = 11.0  # ❌ 会报错
```

#### bars_to_df - K线列表转DataFrame

```python
from quant.datahub.types import bars_to_df

# K线数据列表
bars = [
    BarData(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.DAILY,
        datetime=pd.Timestamp("2024-10-23", tz="UTC"),
        open_price=10.30,
        high_price=10.60,
        low_price=10.20,
        close_price=10.50,
        volume=800000.0,
        turnover=8400000.0
    ),
    BarData(
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
    ),
]

# 转换为 DataFrame
df = bars_to_df(bars)
print(df)

"""
输出:
   symbol exchange interval            datetime   open   high    low  close    volume    turnover  open_interest
0  600000      SSE       1d 2024-10-23 00:00:00  10.30  10.60  10.20  10.50  800000.0   8400000.0           0.0
1  600000      SSE       1d 2024-10-24 00:00:00  10.50  10.80  10.40  10.75 1000000.0  10750000.0           0.0
"""

# 特性：
# - 自动排序（按 datetime）
# - 自动去重（保留最后一条）
# - 标准化列名和数据类型
```

#### df_to_bars - DataFrame转K线列表

```python
from quant.datahub.types import df_to_bars
import pandas as pd

# 准备 DataFrame
df = pd.DataFrame({
    'datetime': ['2024-10-23', '2024-10-24'],
    'open': [10.30, 10.50],
    'high': [10.60, 10.80],
    'low': [10.20, 10.40],
    'close': [10.50, 10.75],
    'volume': [800000, 1000000],
    'turnover': [8400000, 10750000]
})

# 转换为 K线列表
bars = df_to_bars(
    df,
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY
)

print(f"转换了 {len(bars)} 条K线")
for bar in bars[:2]:
    print(f"{bar.datetime.date()}: {bar.close_price}")
```

---

### 3. 财务数据类型（financial.py）

#### FinancialReportType - 财务报表类型

```python
from quant.datahub.types import FinancialReportType

# 支持的报表类型
FinancialReportType.BALANCE_SHEET  # 资产负债表
FinancialReportType.INCOME         # 利润表
FinancialReportType.CASHFLOW       # 现金流量表
FinancialReportType.INDICATOR      # 财务指标

# 使用示例
report_type = FinancialReportType.INCOME
print(report_type.value)  # "income"
```

#### ReportPeriod - 报告期类型

```python
from quant.datahub.types import ReportPeriod

# 支持的报告期
ReportPeriod.Q1      # 一季报
ReportPeriod.Q2      # 中报/半年报
ReportPeriod.Q3      # 三季报
ReportPeriod.Q4      # 四季报
ReportPeriod.ANNUAL  # 年报（与Q4等同）

# 使用示例
period = ReportPeriod.ANNUAL
print(period.value)  # "annual"
```

#### FinancialData - 财务数据类

**定义**:
```python
@dataclass(frozen=True)
class FinancialData:
    """财务报表数据"""
    symbol: str                          # 股票代码
    exchange: Exchange                   # 交易所
    report_date: pd.Timestamp           # 报告期（如 2024-12-31）
    publish_date: pd.Timestamp          # 公告日期
    report_type: FinancialReportType    # 报表类型
    report_period: ReportPeriod         # 报告期类型
    
    # === 资产负债表字段 ===
    total_assets: Optional[float] = None              # 资产总计
    total_liabilities: Optional[float] = None         # 负债合计
    total_equity: Optional[float] = None              # 股东权益合计
    current_assets: Optional[float] = None            # 流动资产
    current_liabilities: Optional[float] = None       # 流动负债
    fixed_assets: Optional[float] = None              # 固定资产
    intangible_assets: Optional[float] = None         # 无形资产
    
    # === 利润表字段 ===
    revenue: Optional[float] = None                   # 营业总收入
    operating_revenue: Optional[float] = None         # 营业收入
    operating_cost: Optional[float] = None            # 营业成本
    operating_profit: Optional[float] = None          # 营业利润
    total_profit: Optional[float] = None              # 利润总额
    net_profit: Optional[float] = None                # 净利润
    net_profit_parent: Optional[float] = None         # 归属母公司净利润
    basic_eps: Optional[float] = None                 # 基本每股收益
    
    # === 现金流量表字段 ===
    cash_flow_operating: Optional[float] = None       # 经营活动现金流
    cash_flow_investing: Optional[float] = None       # 投资活动现金流
    cash_flow_financing: Optional[float] = None       # 筹资活动现金流
    cash_equivalent_increase: Optional[float] = None  # 现金及现金等价物净增加
    
    # === 财务指标 ===
    roe: Optional[float] = None                       # 净资产收益率
    roa: Optional[float] = None                       # 总资产收益率
    gross_margin: Optional[float] = None              # 毛利率
    net_margin: Optional[float] = None                # 净利率
    debt_to_asset_ratio: Optional[float] = None       # 资产负债率
    current_ratio: Optional[float] = None             # 流动比率
    
    # 扩展字段（存储其他指标）
    extra_fields: Optional[Dict[str, Any]] = None
```

**使用示例**:

```python
from quant.datahub.types import (
    FinancialData, 
    FinancialReportType, 
    ReportPeriod,
    Exchange
)
import pandas as pd

# 创建财务数据
financial = FinancialData(
    symbol="600000",
    exchange=Exchange.SSE,
    report_date=pd.Timestamp("2024-12-31", tz="UTC"),
    publish_date=pd.Timestamp("2025-03-15", tz="UTC"),
    report_type=FinancialReportType.INCOME,
    report_period=ReportPeriod.ANNUAL,
    revenue=100_000_000_000.0,           # 1000亿营收
    operating_profit=15_000_000_000.0,   # 150亿营业利润
    net_profit=10_000_000_000.0,         # 100亿净利润
    basic_eps=2.50,                       # 每股收益2.5元
    roe=0.15,                             # ROE 15%
    net_margin=0.10,                      # 净利率 10%
    extra_fields={"industry": "银行业"}
)

# 访问字段
print(f"股票: {financial.symbol}")
print(f"报告期: {financial.report_date.date()}")
print(f"营收: {financial.revenue:,.0f}")
print(f"净利润: {financial.net_profit:,.0f}")
print(f"ROE: {financial.roe:.2%}")
print(f"扩展字段: {financial.extra_fields}")
```

#### financials_to_df - 财务数据转DataFrame

```python
from quant.datahub.types import financials_to_df

# 财务数据列表
financials = [
    FinancialData(
        symbol="600000",
        exchange=Exchange.SSE,
        report_date=pd.Timestamp("2023-12-31", tz="UTC"),
        publish_date=pd.Timestamp("2024-03-15", tz="UTC"),
        report_type=FinancialReportType.INCOME,
        report_period=ReportPeriod.ANNUAL,
        revenue=90_000_000_000.0,
        net_profit=9_000_000_000.0,
        roe=0.14
    ),
    FinancialData(
        symbol="600000",
        exchange=Exchange.SSE,
        report_date=pd.Timestamp("2024-12-31", tz="UTC"),
        publish_date=pd.Timestamp("2025-03-15", tz="UTC"),
        report_type=FinancialReportType.INCOME,
        report_period=ReportPeriod.ANNUAL,
        revenue=100_000_000_000.0,
        net_profit=10_000_000_000.0,
        roe=0.15
    ),
]

# 转换为 DataFrame
df = financials_to_df(financials)
print(df[['symbol', 'report_date', 'revenue', 'net_profit', 'roe']])

"""
输出:
   symbol report_date      revenue    net_profit   roe
0  600000  2023-12-31  9.0e+10      9.0e+09      0.14
1  600000  2024-12-31  1.0e+11      1.0e+10      0.15
"""
```

---

### 4. 基本面数据类型（fundamental.py）

#### FundamentalData - 基本面数据类

**定义**:
```python
@dataclass(frozen=True)
class FundamentalData:
    """基本面数据（日频或定期更新）"""
    symbol: str              # 股票代码
    exchange: Exchange       # 交易所
    date: pd.Timestamp       # 日期
    
    # === 估值指标 ===
    pe_ratio: Optional[float] = None            # 市盈率 PE
    pe_ttm: Optional[float] = None              # 市盈率TTM
    pb_ratio: Optional[float] = None            # 市净率 PB
    ps_ratio: Optional[float] = None            # 市销率 PS
    pcf_ratio: Optional[float] = None           # 市现率 PCF
    
    # === 市值相关 ===
    market_cap: Optional[float] = None              # 总市值
    circulating_market_cap: Optional[float] = None  # 流通市值
    total_shares: Optional[float] = None            # 总股本
    circulating_shares: Optional[float] = None      # 流通股本
    
    # === 财务质量指标 ===
    roe: Optional[float] = None                     # 净资产收益率
    roa: Optional[float] = None                     # 总资产收益率
    roic: Optional[float] = None                    # 投入资本回报率
    debt_to_asset_ratio: Optional[float] = None     # 资产负债率
    debt_to_equity_ratio: Optional[float] = None    # 产权比率
    current_ratio: Optional[float] = None           # 流动比率
    quick_ratio: Optional[float] = None             # 速动比率
    
    # === 成长性指标 ===
    revenue_growth: Optional[float] = None          # 营收增长率（同比）
    revenue_growth_qoq: Optional[float] = None      # 营收增长率（环比）
    profit_growth: Optional[float] = None           # 净利润增长率（同比）
    profit_growth_qoq: Optional[float] = None       # 净利润增长率（环比）
    
    # === 盈利能力 ===
    gross_margin: Optional[float] = None            # 毛利率
    net_margin: Optional[float] = None              # 净利率
    operating_margin: Optional[float] = None        # 营业利润率
    
    # === 每股指标 ===
    eps: Optional[float] = None                     # 每股收益
    bps: Optional[float] = None                     # 每股净资产
    ocfps: Optional[float] = None                   # 每股经营现金流
    
    # === 分红相关 ===
    dividend_yield: Optional[float] = None          # 股息率
    payout_ratio: Optional[float] = None            # 分红率
    
    # 扩展字段
    extra_fields: Optional[Dict[str, Any]] = None
```

**使用示例**:

```python
from quant.datahub.types import FundamentalData, Exchange
import pandas as pd

# 创建基本面数据
fundamental = FundamentalData(
    symbol="600000",
    exchange=Exchange.SSE,
    date=pd.Timestamp("2024-10-24", tz="UTC"),
    pe_ratio=5.8,
    pe_ttm=5.5,
    pb_ratio=0.6,
    ps_ratio=1.2,
    market_cap=200_000_000_000.0,     # 2000亿市值
    circulating_market_cap=180_000_000_000.0,
    roe=0.12,                          # ROE 12%
    roa=0.08,                          # ROA 8%
    debt_to_asset_ratio=0.92,          # 银行业负债率高
    revenue_growth=0.08,               # 营收同比增长8%
    profit_growth=0.10,                # 利润同比增长10%
    gross_margin=0.45,                 # 毛利率45%
    net_margin=0.30,                   # 净利率30%
    eps=2.50,                          # 每股收益2.5元
    bps=18.50,                         # 每股净资产18.5元
    dividend_yield=0.045,              # 股息率4.5%
)

# 访问字段
print(f"股票: {fundamental.symbol}")
print(f"日期: {fundamental.date.date()}")
print(f"PE: {fundamental.pe_ratio:.2f}")
print(f"PB: {fundamental.pb_ratio:.2f}")
print(f"ROE: {fundamental.roe:.2%}")
print(f"股息率: {fundamental.dividend_yield:.2%}")

# 估值判断
if fundamental.pe_ratio < 10:
    print("PE较低，可能被低估")
if fundamental.pb_ratio < 1:
    print("PB小于1，股价低于净资产")
if fundamental.dividend_yield > 0.03:
    print("股息率>3%，分红稳定")
```

#### fundamentals_to_df - 基本面数据转DataFrame

```python
from quant.datahub.types import fundamentals_to_df

# 基本面数据列表（时间序列）
fundamentals = [
    FundamentalData(
        symbol="600000",
        exchange=Exchange.SSE,
        date=pd.Timestamp("2024-10-23", tz="UTC"),
        pe_ratio=5.9,
        pb_ratio=0.61,
        market_cap=198_000_000_000.0,
        roe=0.12,
        dividend_yield=0.045
    ),
    FundamentalData(
        symbol="600000",
        exchange=Exchange.SSE,
        date=pd.Timestamp("2024-10-24", tz="UTC"),
        pe_ratio=5.8,
        pb_ratio=0.60,
        market_cap=200_000_000_000.0,
        roe=0.12,
        dividend_yield=0.045
    ),
]

# 转换为 DataFrame
df = fundamentals_to_df(fundamentals)
print(df[['symbol', 'date', 'pe_ratio', 'pb_ratio', 'market_cap', 'roe']])

"""
输出:
   symbol       date  pe_ratio  pb_ratio       market_cap   roe
0  600000 2024-10-23      5.9      0.61  1.98e+11         0.12
1  600000 2024-10-24      5.8      0.60  2.00e+11         0.12
"""
```

---

## 💡 完整使用示例

### 示例1：K线数据处理流程

```python
from quant.datahub.types import (
    BarData, Exchange, Interval,
    bars_to_df, df_to_bars
)
import pandas as pd

# ========== 1. 创建K线数据 ==========
bars = []
for i in range(5):
    bar = BarData(
        symbol="600000",
        exchange=Exchange.SSE,
        interval=Interval.DAILY,
        datetime=pd.Timestamp(f"2024-10-{20+i}", tz="UTC"),
        open_price=10.0 + i * 0.1,
        high_price=10.2 + i * 0.1,
        low_price=9.9 + i * 0.1,
        close_price=10.1 + i * 0.1,
        volume=1000000 * (1 + i * 0.1),
        turnover=10000000 * (1 + i * 0.1)
    )
    bars.append(bar)

print(f"创建了 {len(bars)} 条K线数据")

# ========== 2. 转换为 DataFrame ==========
df = bars_to_df(bars)
print("\nDataFrame 格式:")
print(df)

# ========== 3. 数据分析 ==========
# 计算收益率
df['return'] = df['close'].pct_change()
print("\n收益率:")
print(df[['datetime', 'close', 'return']])

# 计算均线
df['ma5'] = df['close'].rolling(5).mean()
print("\n5日均线:")
print(df[['datetime', 'close', 'ma5']])

# ========== 4. 导出到文件 ==========
df.to_csv("bars.csv", index=False)
df.to_parquet("bars.parquet", index=False)
print("\n已导出到 CSV 和 Parquet 文件")

# ========== 5. 从文件加载并转回 BarData ==========
df_loaded = pd.read_parquet("bars.parquet")
bars_loaded = df_to_bars(df_loaded, "600000", Exchange.SSE, Interval.DAILY)
print(f"\n从文件加载了 {len(bars_loaded)} 条K线")
```

---

### 示例2：财务数据年度对比

```python
from quant.datahub.types import (
    FinancialData, FinancialReportType, ReportPeriod,
    Exchange, financials_to_df
)
import pandas as pd

# 创建3年财务数据
financials = []
for year in range(2022, 2025):
    financial = FinancialData(
        symbol="600000",
        exchange=Exchange.SSE,
        report_date=pd.Timestamp(f"{year}-12-31", tz="UTC"),
        publish_date=pd.Timestamp(f"{year+1}-03-15", tz="UTC"),
        report_type=FinancialReportType.INCOME,
        report_period=ReportPeriod.ANNUAL,
        revenue=90_000_000_000 * (1.1 ** (year - 2022)),  # 每年增长10%
        net_profit=9_000_000_000 * (1.12 ** (year - 2022)),  # 每年增长12%
        operating_profit=12_000_000_000 * (1.11 ** (year - 2022)),
        roe=0.13 + (year - 2022) * 0.01,  # ROE逐年提升
        net_margin=0.10 + (year - 2022) * 0.005,
        extra_fields={"year": year}
    )
    financials.append(financial)

# 转换为 DataFrame
df = financials_to_df(financials)

# 添加年份列
df['year'] = df['report_date'].dt.year

# 计算增长率
df['revenue_growth'] = df['revenue'].pct_change()
df['profit_growth'] = df['net_profit'].pct_change()

print("财务数据年度对比:")
print(df[['year', 'revenue', 'net_profit', 'roe', 'net_margin']])

print("\n增长率分析:")
print(df[['year', 'revenue_growth', 'profit_growth']])

# 可视化
import matplotlib.pyplot as plt

fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 营收趋势
axes[0, 0].plot(df['year'], df['revenue'] / 1e9)
axes[0, 0].set_title('营收趋势（十亿元）')
axes[0, 0].set_xlabel('年份')
axes[0, 0].set_ylabel('营收')

# 净利润趋势
axes[0, 1].plot(df['year'], df['net_profit'] / 1e9)
axes[0, 1].set_title('净利润趋势（十亿元）')
axes[0, 1].set_xlabel('年份')
axes[0, 1].set_ylabel('净利润')

# ROE趋势
axes[1, 0].plot(df['year'], df['roe'] * 100)
axes[1, 0].set_title('ROE趋势（%）')
axes[1, 0].set_xlabel('年份')
axes[1, 0].set_ylabel('ROE (%)')

# 净利率趋势
axes[1, 1].plot(df['year'], df['net_margin'] * 100)
axes[1, 1].set_title('净利率趋势（%）')
axes[1, 1].set_xlabel('年份')
axes[1, 1].set_ylabel('净利率 (%)')

plt.tight_layout()
plt.savefig('financial_analysis.png')
print("\n已生成财务分析图表: financial_analysis.png")
```

---

### 示例3：基本面估值分析

```python
from quant.datahub.types import (
    FundamentalData, Exchange,
    fundamentals_to_df
)
import pandas as pd
import numpy as np

# 创建一年的基本面数据（每日）
start_date = pd.Timestamp("2024-01-01", tz="UTC")
fundamentals = []

for i in range(252):  # 252个交易日
    date = start_date + pd.Timedelta(days=i)
    
    # 模拟数据波动
    pe_base = 6.0
    pe_ratio = pe_base + np.sin(i / 50) * 0.5  # 周期性波动
    
    fundamental = FundamentalData(
        symbol="600000",
        exchange=Exchange.SSE,
        date=date,
        pe_ratio=pe_ratio,
        pe_ttm=pe_ratio * 0.95,
        pb_ratio=0.6 + np.sin(i / 50) * 0.1,
        market_cap=200_000_000_000 * (1 + np.sin(i / 50) * 0.05),
        roe=0.12 + np.random.normal(0, 0.005),
        roa=0.08 + np.random.normal(0, 0.003),
        dividend_yield=0.045 + np.random.normal(0, 0.002),
        revenue_growth=0.08 + np.random.normal(0, 0.01),
        profit_growth=0.10 + np.random.normal(0, 0.015),
    )
    fundamentals.append(fundamental)

# 转换为 DataFrame
df = fundamentals_to_df(fundamentals)

# ========== 估值分析 ==========

# 1. 计算PE百分位
df['pe_percentile'] = df['pe_ratio'].rank(pct=True) * 100

# 2. 计算PB百分位
df['pb_percentile'] = df['pb_ratio'].rank(pct=True) * 100

# 3. 估值判断
def valuation_level(row):
    if row['pe_percentile'] < 30:
        return "低估"
    elif row['pe_percentile'] > 70:
        return "高估"
    else:
        return "合理"

df['valuation'] = df.apply(valuation_level, axis=1)

# 4. 统计估值分布
print("估值分布:")
print(df['valuation'].value_counts())

# 5. 当前估值
latest = df.iloc[-1]
print(f"\n当前估值状态:")
print(f"  PE: {latest['pe_ratio']:.2f}")
print(f"  PE百分位: {latest['pe_percentile']:.1f}%")
print(f"  PB: {latest['pb_ratio']:.2f}")
print(f"  PB百分位: {latest['pb_percentile']:.1f}%")
print(f"  估值水平: {latest['valuation']}")
print(f"  ROE: {latest['roe']:.2%}")
print(f"  股息率: {latest['dividend_yield']:.2%}")

# 6. 可视化
import matplotlib.pyplot as plt

fig, axes = plt.subplots(3, 1, figsize=(14, 10))

# PE趋势和百分位
axes[0].plot(df['date'], df['pe_ratio'], label='PE', color='blue')
axes[0].axhline(y=df['pe_ratio'].quantile(0.3), color='green', 
                linestyle='--', label='30分位')
axes[0].axhline(y=df['pe_ratio'].quantile(0.7), color='red', 
                linestyle='--', label='70分位')
axes[0].set_title('PE趋势与估值区间')
axes[0].legend()
axes[0].grid(True)

# PB趋势
axes[1].plot(df['date'], df['pb_ratio'], label='PB', color='orange')
axes[1].axhline(y=1.0, color='red', linestyle='--', label='破净线')
axes[1].set_title('PB趋势')
axes[1].legend()
axes[1].grid(True)

# ROE和股息率
ax2 = axes[2].twinx()
axes[2].plot(df['date'], df['roe'] * 100, label='ROE', color='green')
ax2.plot(df['date'], df['dividend_yield'] * 100, label='股息率', 
         color='purple', linestyle='--')
axes[2].set_title('盈利能力和分红')
axes[2].set_ylabel('ROE (%)', color='green')
ax2.set_ylabel('股息率 (%)', color='purple')
axes[2].legend(loc='upper left')
ax2.legend(loc='upper right')
axes[2].grid(True)

plt.tight_layout()
plt.savefig('fundamental_analysis.png')
print("\n已生成基本面分析图表: fundamental_analysis.png")
```

---

### 示例4：多股票数据管理

```python
from quant.datahub.types import (
    BarData, Exchange, Interval, bars_to_df
)
import pandas as pd

# 创建多只股票的K线数据
symbols = ["600000", "600036", "601318", "601398"]
all_bars = []

for symbol in symbols:
    for i in range(5):
        bar = BarData(
            symbol=symbol,
            exchange=Exchange.SSE,
            interval=Interval.DAILY,
            datetime=pd.Timestamp(f"2024-10-{20+i}", tz="UTC"),
            open_price=10.0 + hash(symbol) % 10,
            high_price=10.5 + hash(symbol) % 10,
            low_price=9.8 + hash(symbol) % 10,
            close_price=10.2 + hash(symbol) % 10,
            volume=1000000,
            turnover=10000000
        )
        all_bars.append(bar)

# 转换为 DataFrame
df = bars_to_df(all_bars)

# 按股票分组
print("各股票数据量:")
print(df.groupby('symbol').size())

# 计算各股票平均价格
print("\n各股票平均收盘价:")
print(df.groupby('symbol')['close'].mean())

# 透视表：日期 vs 股票
pivot = df.pivot_table(
    index='datetime',
    columns='symbol',
    values='close'
)
print("\n价格透视表:")
print(pivot)

# 导出
pivot.to_csv("multi_stock_prices.csv")
print("\n已导出到 multi_stock_prices.csv")
```

---

## 🔧 高级功能

### 1. 数据验证

```python
from quant.datahub.types import BarData, Exchange, Interval
import pandas as pd

def validate_bar_data(bar: BarData) -> bool:
    """验证K线数据有效性"""
    # 检查价格关系
    if not (bar.low_price <= bar.open_price <= bar.high_price):
        return False
    if not (bar.low_price <= bar.close_price <= bar.high_price):
        return False
    
    # 检查成交量
    if bar.volume < 0:
        return False
    
    # 检查时间
    if bar.datetime > pd.Timestamp.now(tz="UTC"):
        return False
    
    return True

# 使用示例
bar = BarData(
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    datetime=pd.Timestamp("2024-10-24", tz="UTC"),
    open_price=10.5,
    high_price=10.8,
    low_price=10.4,
    close_price=10.75,
    volume=1000000
)

if validate_bar_data(bar):
    print("✅ 数据有效")
else:
    print("❌ 数据无效")
```

---

### 2. 数据过滤

```python
from quant.datahub.types import bars_to_df
import pandas as pd

# 假设已有K线数据
df = bars_to_df(bars)

# 按时间范围过滤
start = pd.Timestamp("2024-10-01", tz="UTC")
end = pd.Timestamp("2024-10-31", tz="UTC")
df_filtered = df[(df['datetime'] >= start) & (df['datetime'] <= end)]

# 按成交量过滤（去除异常小成交量）
df_filtered = df[df['volume'] > df['volume'].quantile(0.1)]

# 按涨跌幅过滤
df['change'] = df['close'].pct_change()
df_up = df[df['change'] > 0]  # 上涨日
df_down = df[df['change'] < 0]  # 下跌日

print(f"上涨日: {len(df_up)}, 下跌日: {len(df_down)}")
```

---

### 3. 数据聚合

```python
from quant.datahub.types import bars_to_df
import pandas as pd

# 转换为 DataFrame
df = bars_to_df(bars)

# 按周聚合
df_weekly = df.resample('W', on='datetime').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum',
    'turnover': 'sum'
})

print("周线数据:")
print(df_weekly)

# 按月聚合
df_monthly = df.resample('M', on='datetime').agg({
    'open': 'first',
    'high': 'max',
    'low': 'min',
    'close': 'last',
    'volume': 'sum'
})

print("\n月线数据:")
print(df_monthly)
```

---

## 📚 常量参考

### BAR_COLUMNS

K线数据的标准列名：
```python
BAR_COLUMNS = [
    "symbol", "exchange", "interval", "datetime",
    "open", "high", "low", "close", 
    "volume", "turnover", "open_interest"
]
```

### BAR_DTYPES

K线数据的标准数据类型：
```python
BAR_DTYPES = {
    "symbol": str,
    "exchange": str,
    "interval": str,
    "datetime": "datetime64[ns, UTC]",
    "open": float,
    "high": float,
    "low": float,
    "close": float,
    "volume": float,
    "turnover": float,
    "open_interest": float
}
```

### FINANCIAL_COLUMNS

财务数据的核心列名：
```python
FINANCIAL_COLUMNS = [
    "symbol", "exchange", "report_date", "publish_date",
    "report_type", "report_period",
    "total_assets", "total_liabilities", "total_equity",
    "revenue", "net_profit", "operating_profit",
    "cash_flow_operating", "roe", "roa"
]
```

### FUNDAMENTAL_COLUMNS

基本面数据的核心列名：
```python
FUNDAMENTAL_COLUMNS = [
    "symbol", "exchange", "date",
    "pe_ratio", "pb_ratio", "ps_ratio",
    "market_cap", "circulating_market_cap",
    "roe", "roa", "debt_to_asset_ratio",
    "revenue_growth", "profit_growth",
    "gross_margin", "net_margin"
]
```

---

## ⚠️ 注意事项

### 1. 数据不可变性

所有数据类都使用 `frozen=True`，确保数据不可变：

```python
# ❌ 错误：不能修改
bar.close_price = 11.0  # 会抛出异常

# ✅ 正确：创建新对象
from dataclasses import replace
bar_new = replace(bar, close_price=11.0)
```

---

### 2. 时区处理

所有时间戳都应使用 UTC 时区：

```python
# ✅ 推荐：明确指定 UTC
datetime = pd.Timestamp("2024-10-24", tz="UTC")

# ⚠️ 不推荐：无时区
datetime = pd.Timestamp("2024-10-24")  # 会自动转为 UTC
```

---

### 3. Optional 字段

财务和基本面数据很多字段是 `Optional`，使用前检查：

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

# 访问扩展字段
industry = financial.extra_fields.get("industry")
```

---

## 🔗 相关文档

- **[Services 模块文档](../../services/docs/USAGE_GUIDE.md)** - 数据服务层
- **[Providers 模块文档](../../providers/docs/USAGE_GUIDE.md)** - 数据提供者
- **[Stores 模块文档](../../../storage/stores/README.md)** - 存储层接口

---

## 📝 更新日志

- **2024-10-24**: 初始版本
  - 实现 BarData, FinancialData, FundamentalData
  - 支持 Exchange, Interval, FinancialReportType, ReportPeriod 枚举
  - 提供 DataFrame 双向转换工具
  - 30+ 数据字段，覆盖常用金融指标

---

**维护者**: AlphaGrid Team  
**最后更新**: 2024-10-24

