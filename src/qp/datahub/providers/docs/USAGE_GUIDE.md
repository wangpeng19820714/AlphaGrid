# DataHub Providers 使用说明

## 📋 概述

Providers 模块提供了统一的数据源接口，支持从多个数据提供商（AKShare、TuShare、YFinance）获取金融市场数据，包括 K线数据、财务数据和基本面数据。

**模块路径**: `quant/datahub/providers/`

**核心特性**:
- 🔌 **插件式架构** - 统一接口，易于扩展新数据源
- 📊 **多数据类型** - 支持 K线、财务、基本面数据
- 🌍 **多市场支持** - A股、港股、美股
- 🔄 **自动转换** - 统一数据格式，屏蔽底层差异

---

## 📁 模块结构

```
quant/datahub/providers/
├── __init__.py              # 统一导出和工厂函数
├── base.py                  # 基础接口定义
├── akshare_provider.py     # AKShare 数据源
├── tushare_provider.py     # TuShare 数据源
└── yfinance_provider.py    # Yahoo Finance 数据源
```

---

## 🚀 快速开始

### 方式1：使用工厂函数（推荐）

```python
from quant.datahub.providers import get_provider
from quant.datahub.types import Exchange, Interval
import pandas as pd

# 获取 AKShare 提供者（免费，无需 Token）
provider = get_provider('akshare')

# 获取 TuShare 提供者（需要 Token）
provider = get_provider('tushare', token='your_token_here')

# 获取 Yahoo Finance 提供者
provider = get_provider('yfinance')
```

### 方式2：直接导入

```python
from quant.datahub.providers import AkshareProvider, TuShareProvider, YFProvider

# 创建实例
akshare = AkshareProvider()
tushare = TuShareProvider(token='your_token')
yfinance = YFProvider()
```

---

## 📊 数据类型支持

### 1. K线数据 (BarData)

所有 Provider 都支持 K线数据查询。

**方法**: `query_bars()`

```python
def query_bars(self, 
               symbol: str, 
               exchange: Exchange, 
               interval: Interval,
               start: pd.Timestamp, 
               end: pd.Timestamp, 
               adjust: str = "none") -> list[BarData]:
    """
    查询K线数据
    
    Args:
        symbol: 股票代码（如 "600000" 或 "600000.SH"）
        exchange: 交易所枚举 (Exchange.SSE, Exchange.SZSE, etc.)
        interval: 时间周期 (Interval.DAILY, Interval.MIN5, etc.)
        start: 开始日期
        end: 结束日期
        adjust: 复权类型 ('none', 'qfq'-前复权, 'hfq'-后复权)
        
    Returns:
        K线数据列表
    """
```

**示例**:

```python
from quant.datahub.providers import get_provider
from quant.datahub.types import Exchange, Interval
import pandas as pd

provider = get_provider('akshare')

# 查询浦发银行日线数据（前复权）
bars = provider.query_bars(
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31"),
    adjust="qfq"
)

print(f"获取到 {len(bars)} 条K线数据")
for bar in bars[:3]:
    print(f"{bar.datetime.date()}: 收盘价={bar.close_price}, 成交量={bar.volume}")
```

---

### 2. 财务数据 (FinancialData)

支持财务报表数据查询（资产负债表、利润表、现金流量表）。

**方法**: `query_financials()`

```python
def query_financials(self, 
                    symbol: str, 
                    exchange: Exchange,
                    report_type: FinancialReportType,
                    start: pd.Timestamp, 
                    end: pd.Timestamp) -> list[FinancialData]:
    """
    查询财务数据
    
    Args:
        symbol: 股票代码
        exchange: 交易所
        report_type: 报表类型
            - FinancialReportType.BALANCE_SHEET (资产负债表)
            - FinancialReportType.INCOME (利润表)
            - FinancialReportType.CASHFLOW (现金流量表)
            - FinancialReportType.INDICATOR (财务指标)
        start: 开始报告期
        end: 结束报告期
        
    Returns:
        财务数据列表
    """
```

**示例**:

```python
from quant.datahub.providers import get_provider
from quant.datahub.types import Exchange, FinancialReportType
import pandas as pd

provider = get_provider('akshare')

# 查询利润表
financials = provider.query_financials(
    symbol="600000",
    exchange=Exchange.SSE,
    report_type=FinancialReportType.INCOME,
    start=pd.Timestamp("2020-01-01"),
    end=pd.Timestamp("2024-12-31")
)

for f in financials:
    print(f"{f.report_date.date()}: 营收={f.revenue:,.0f}, 净利润={f.net_profit:,.0f}")
```

---

### 3. 基本面数据 (FundamentalData)

支持日频基本面指标查询（PE、PB、ROE等）。

**方法**: `query_fundamentals()`

```python
def query_fundamentals(self, 
                      symbol: str, 
                      exchange: Exchange,
                      start: pd.Timestamp, 
                      end: pd.Timestamp) -> list[FundamentalData]:
    """
    查询基本面数据
    
    Args:
        symbol: 股票代码
        exchange: 交易所
        start: 开始日期
        end: 结束日期
        
    Returns:
        基本面数据列表（包含PE、PB、ROE等指标）
    """
```

**示例**:

```python
from quant.datahub.providers import get_provider
from quant.datahub.types import Exchange
import pandas as pd

provider = get_provider('akshare')

# 查询基本面指标
fundamentals = provider.query_fundamentals(
    symbol="600000",
    exchange=Exchange.SSE,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)

for f in fundamentals[:5]:
    print(f"{f.date.date()}: PE={f.pe_ratio:.2f}, PB={f.pb_ratio:.2f}, ROE={f.roe:.2%}")
```

---

## 🔌 支持的数据源

### 1. AKShare Provider

**特点**:
- ✅ **免费无限制**
- ✅ 无需注册和 Token
- ✅ 数据全面（A股为主）
- ⚠️ 仅支持日线数据

**初始化**:

```python
from quant.datahub.providers import get_provider

provider = get_provider('akshare')
# 或
from quant.datahub.providers import AkshareProvider
provider = AkshareProvider()
```

**支持的功能**:
- ✅ K线数据（仅日线）
- ✅ 财务报表数据
- ✅ 基本面指标

**适用场景**:
- 个人研究和学习
- 中低频交易策略
- 财务分析

---

### 2. TuShare Provider

**特点**:
- ✅ 数据质量高
- ✅ 更新及时
- ✅ 支持多周期
- ⚠️ 需要注册获取 Token
- ⚠️ 免费版有调用限制

**初始化**:

```python
from quant.datahub.providers import get_provider

# 方式1：直接传入 token
provider = get_provider('tushare', token='your_token_here')

# 方式2：从环境变量读取
import os
os.environ['TUSHARE_TOKEN'] = 'your_token_here'
provider = get_provider('tushare')
```

**支持的功能**:
- ✅ K线数据（多周期）
- ✅ 财务报表数据
- ✅ 基本面指标
- ✅ 复权因子

**适用场景**:
- 专业量化研究
- 高频数据需求
- 生产环境

**获取 Token**:
1. 访问 https://tushare.pro
2. 注册账号
3. 在"接口Token"页面获取

---

### 3. Yahoo Finance Provider

**特点**:
- ✅ 免费
- ✅ 全球市场（美股、港股）
- ✅ 数据稳定
- ⚠️ 主要支持K线数据

**初始化**:

```python
from quant.datahub.providers import get_provider

provider = get_provider('yfinance')
# 或
from quant.datahub.providers import YFProvider
provider = YFProvider()
```

**支持的功能**:
- ✅ K线数据（多周期）
- ⚠️ 财务数据支持有限
- ⚠️ 基本面数据支持有限

**适用场景**:
- 美股、港股研究
- 全球市场分析
- 跨市场策略

**股票代码格式**:
- 美股: `AAPL`, `MSFT`
- 港股: `0700.HK`, `9988.HK`

---

## 💡 使用示例

### 示例1：完整的数据获取流程

```python
from quant.datahub.providers import get_provider
from quant.datahub.types import Exchange, Interval, FinancialReportType
import pandas as pd

# 1. 创建 Provider
provider = get_provider('akshare')

symbol = "600000"
exchange = Exchange.SSE

# 2. 获取K线数据
print("=" * 60)
print("1. 获取K线数据")
print("=" * 60)

bars = provider.query_bars(
    symbol=symbol,
    exchange=exchange,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31"),
    adjust="qfq"
)

print(f"获取到 {len(bars)} 条K线数据")
if bars:
    latest = bars[-1]
    print(f"最新数据: {latest.datetime.date()} 收盘价={latest.close_price:.2f}")

# 3. 获取财务数据
print("\n" + "=" * 60)
print("2. 获取财务数据")
print("=" * 60)

financials = provider.query_financials(
    symbol=symbol,
    exchange=exchange,
    report_type=FinancialReportType.INCOME,
    start=pd.Timestamp("2023-01-01"),
    end=pd.Timestamp("2024-12-31")
)

print(f"获取到 {len(financials)} 条财务数据")
for f in financials[-3:]:
    print(f"  {f.report_date.date()}: 营收={f.revenue:,.0f}, 净利润={f.net_profit:,.0f}")

# 4. 获取基本面数据
print("\n" + "=" * 60)
print("3. 获取基本面数据")
print("=" * 60)

fundamentals = provider.query_fundamentals(
    symbol=symbol,
    exchange=exchange,
    start=pd.Timestamp("2024-10-01"),
    end=pd.Timestamp("2024-12-31")
)

print(f"获取到 {len(fundamentals)} 条基本面数据")
if fundamentals:
    latest = fundamentals[-1]
    print(f"最新数据: {latest.date.date()}")
    print(f"  PE={latest.pe_ratio:.2f}, PB={latest.pb_ratio:.2f}")
    print(f"  市值={latest.market_cap:,.0f}")
```

---

### 示例2：切换不同数据源

```python
from quant.datahub.providers import get_provider
from quant.datahub.types import Exchange, Interval
import pandas as pd

# 定义统一的查询参数
params = {
    "symbol": "600000",
    "exchange": Exchange.SSE,
    "interval": Interval.DAILY,
    "start": pd.Timestamp("2024-01-01"),
    "end": pd.Timestamp("2024-12-31"),
    "adjust": "qfq"
}

# 尝试不同的数据源
providers = ['akshare', 'tushare', 'yfinance']

for provider_name in providers:
    try:
        print(f"\n使用 {provider_name} 获取数据...")
        
        # 创建 provider
        if provider_name == 'tushare':
            provider = get_provider(provider_name, token='your_token')
        else:
            provider = get_provider(provider_name)
        
        # 查询数据
        bars = provider.query_bars(**params)
        print(f"  ✅ 成功获取 {len(bars)} 条数据")
        
    except NotImplementedError as e:
        print(f"  ⚠️ {provider_name} 不支持该功能: {e}")
    except Exception as e:
        print(f"  ❌ {provider_name} 出错: {e}")
```

---

### 示例3：配合 Service 层使用

```python
from quant.datahub.providers import get_provider
from quant.datahub.services import BarDataService
from quant.datahub.types import Exchange, Interval
import pandas as pd

# 1. 创建 Provider
provider = get_provider('akshare')

# 2. 创建 Service
service = BarDataService()

# 3. 导入数据
count = service.import_from_provider(
    provider=provider,
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31"),
    adjust="qfq"
)

print(f"成功导入 {count} 条数据到本地存储")

# 4. 从本地加载数据（后续使用）
bars = service.load_bars("600000", Exchange.SSE, Interval.DAILY)
print(f"从本地加载 {len(bars)} 条数据")
```

---

## 🔧 自定义 Provider

如果需要添加新的数据源，只需继承 `BaseProvider` 并实现相应接口：

```python
# my_provider.py
from quant.datahub.providers.base import BaseProvider
from quant.datahub.types import BarData, Exchange, Interval
import pandas as pd

class MyCustomProvider(BaseProvider):
    """自定义数据提供者"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def query_bars(self, symbol: str, exchange: Exchange, interval: Interval,
                   start: pd.Timestamp, end: pd.Timestamp, 
                   adjust: str = "none") -> list[BarData]:
        """实现K线数据查询"""
        # 1. 调用你的数据API
        # 2. 转换为 BarData 格式
        # 3. 返回列表
        
        bars = []
        # ... 你的实现逻辑 ...
        return bars
    
    # 可选：实现财务和基本面数据接口
    # def query_financials(self, ...):
    #     raise NotImplementedError("暂不支持")
```

**注册自定义 Provider**:

```python
from quant.datahub.providers import PROVIDERS
from my_provider import MyCustomProvider

# 注册到全局注册表
PROVIDERS['mycustom'] = MyCustomProvider

# 使用
from quant.datahub.providers import get_provider
provider = get_provider('mycustom', api_key='your_key')
```

---

## ⚠️ 注意事项

### 1. 数据源差异

不同 Provider 返回的数据可能有细微差异：

| Provider | 时间周期支持 | 复权支持 | 财务数据 | 基本面数据 |
|----------|-------------|---------|---------|----------|
| AKShare  | 仅日线 | ✅ | ✅ | ✅ |
| TuShare  | 多周期 | ✅ | ✅ | ✅ |
| YFinance | 多周期 | ✅ | 部分 | 部分 |

### 2. 调用限制

- **AKShare**: 无限制，但请合理使用
- **TuShare**: 免费版有每日调用次数限制
- **YFinance**: 无明确限制，但频繁请求可能被限流

### 3. 数据质量

- 生产环境推荐使用 **TuShare**
- 研究学习推荐使用 **AKShare**
- 全球市场推荐使用 **YFinance**

### 4. 异常处理

```python
from quant.datahub.providers import get_provider

provider = get_provider('akshare')

try:
    bars = provider.query_bars(...)
except NotImplementedError as e:
    print(f"该功能不支持: {e}")
except ValueError as e:
    print(f"参数错误: {e}")
except Exception as e:
    print(f"查询失败: {e}")
```

---

## 📚 相关文档

- [Types 模块文档](../types/README.md) - 数据类型定义
- [Services 模块文档](../services/README.md) - 服务层接口
- [Stores 模块文档](../../storage/stores/README.md) - 存储层接口

---

## 🔗 外部链接

- [AKShare 官方文档](https://akshare.akfamily.xyz/)
- [TuShare 官方文档](https://tushare.pro/document/2)
- [YFinance GitHub](https://github.com/ranaroussi/yfinance)

---

## 📝 更新日志

- **2024-10-24**: 初始版本
  - 支持 AKShare、TuShare、YFinance
  - 实现 K线、财务、基本面数据接口
  - 提供工厂函数和统一注册表

---

**维护者**: AlphaGrid Team  
**最后更新**: 2024-10-24

