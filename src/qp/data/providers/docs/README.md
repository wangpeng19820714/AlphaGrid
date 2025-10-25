# DataHub Providers

数据提供者模块 - 统一的多数据源接口

## 快速开始

```python
from qp.data.providers import get_provider
from qp.data.types import Exchange, Interval
import pandas as pd

# 获取数据提供者
provider = get_provider('akshare')  # 或 'tushare', 'yfinance'

# 查询K线数据
bars = provider.query_bars(
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31"),
    adjust="qfq"
)

print(f"获取到 {len(bars)} 条K线数据")
```

## 支持的数据源

| Provider | Token | K线 | 财务 | 基本面 | 适用场景 |
|----------|-------|-----|------|--------|---------|
| **AKShare** | ❌ 不需要 | ✅ 日线 | ✅ | ✅ | 个人研究、学习 |
| **TuShare** | ✅ 需要 | ✅ 多周期 | ✅ | ✅ | 专业量化、生产 |
| **YFinance** | ❌ 不需要 | ✅ 多周期 | 部分 | 部分 | 全球市场 |

## 主要功能

### 1. K线数据
```python
bars = provider.query_bars(symbol, exchange, interval, start, end, adjust)
```

### 2. 财务数据
```python
from qp.data.types import FinancialReportType

financials = provider.query_financials(
    symbol, exchange, 
    FinancialReportType.INCOME,  # 或 BALANCE_SHEET, CASHFLOW
    start, end
)
```

### 3. 基本面数据
```python
fundamentals = provider.query_fundamentals(symbol, exchange, start, end)
```

## 目录结构

```
providers/
├── __init__.py              # 工厂函数和统一导出
├── base.py                  # 基础接口定义
├── akshare_provider.py      # AKShare 实现
├── tushare_provider.py      # TuShare 实现
├── yfinance_provider.py     # YFinance 实现
├── USAGE_GUIDE.md           # 详细使用指南
└── README.md                # 本文件
```

## 详细文档

查看 [USAGE_GUIDE.md](./USAGE_GUIDE.md) 获取：
- 完整的API文档
- 详细的使用示例
- 各数据源对比
- 自定义 Provider 教程
- 常见问题解答

## 示例

### 配合 Service 层使用

```python
from qp.data.providers import get_provider
from qp.data.services import BarDataService

provider = get_provider('akshare')
service = BarDataService()

# 导入数据到本地
count = service.import_from_provider(
    provider=provider,
    symbol="600000",
    exchange=Exchange.SSE,
    interval=Interval.DAILY,
    start=pd.Timestamp("2024-01-01"),
    end=pd.Timestamp("2024-12-31")
)
```

### 切换数据源

```python
# 根据需求切换数据源
provider_name = 'akshare'  # 或 'tushare', 'yfinance'
provider = get_provider(provider_name)
```

## 注意事项

1. **TuShare 需要 Token**
   ```python
   provider = get_provider('tushare', token='your_token')
   # 或设置环境变量 TUSHARE_TOKEN
   ```

2. **调用限制**
   - AKShare: 无限制
   - TuShare: 免费版有每日调用限制
   - YFinance: 避免频繁请求

3. **数据质量**
   - 生产环境 → TuShare
   - 研究学习 → AKShare
   - 全球市场 → YFinance

## 相关链接

- [AKShare 文档](https://akshare.akfamily.xyz/)
- [TuShare 文档](https://tushare.pro/document/2)
- [YFinance GitHub](https://github.com/ranaroussi/yfinance)

