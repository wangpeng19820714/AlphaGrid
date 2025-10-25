# AlphaGrid 数据模块使用示例

## 快速开始

### 1. 基本导入

```python
# 导入统一接口
from qp.data import get_bars, save_bars, query_bars
from qp.data import get_minute_bars, save_minute_bars, query_minute_bars
from qp.data import get_financials, save_financials, query_financials

# 或者导入具体模块
from qp.data import BarData, Exchange, Interval
from qp.data import BarStore, MinuteStore, FinancialStore
from qp.data import get_provider, PROVIDERS
```

### 2. 获取K线数据

```python
# 使用默认提供者 (AKShare)
bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31', 'daily')

# 使用不同提供者
bars_tushare = get_bars('000001.SZ', '2023-01-01', '2023-12-31', 
                        'daily', provider='tushare', token='your_token')

bars_yfinance = get_bars('AAPL', '2023-01-01', '2023-12-31', 
                         'daily', provider='yfinance')

# 获取不同时间间隔
weekly_bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31', 'weekly')
monthly_bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31', 'monthly')
```

### 3. 获取分钟线数据

```python
# 获取1分钟数据
minute_bars = get_minute_bars('000001.SZ', '2023-01-01', '1m')

# 获取不同时间间隔
minute_5m = get_minute_bars('000001.SZ', '2023-01-01', '5m')
minute_15m = get_minute_bars('000001.SZ', '2023-01-01', '15m')
minute_30m = get_minute_bars('000001.SZ', '2023-01-01', '30m')
minute_1h = get_minute_bars('000001.SZ', '2023-01-01', '1h')
```

### 4. 获取财务数据

```python
# 获取财务数据
financials = get_financials('000001.SZ', '2023-01-01', '2023-12-31')

# 获取基本面数据
fundamentals = get_fundamentals('000001.SZ', '2023-01-01', '2023-12-31')
```

## 数据存储

### 1. 保存数据

```python
# 保存K线数据
bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31')
save_bars(bars)

# 保存分钟线数据
minute_bars = get_minute_bars('000001.SZ', '2023-01-01', '1m')
save_minute_bars(minute_bars)

# 保存财务数据
financials = get_financials('000001.SZ', '2023-01-01', '2023-12-31')
save_financials(financials)

# 保存基本面数据
fundamentals = get_fundamentals('000001.SZ', '2023-01-01', '2023-12-31')
save_fundamentals(fundamentals)
```

### 2. 查询数据

```python
# 查询K线数据
bars = query_bars('000001.SZ', '2023-01-01', '2023-12-31')

# 查询分钟线数据
minute_bars = query_minute_bars('000001.SZ', '2023-01-01', '2023-12-31')

# 查询财务数据
financials = query_financials('000001.SZ', '2023-01-01', '2023-12-31')

# 查询基本面数据
fundamentals = query_fundamentals('000001.SZ', '2023-01-01', '2023-12-31')
```

## 便捷函数

### 1. 快速获取并保存

```python
# 快速获取并保存K线数据
bars = quick_bars('000001.SZ', '2023-01-01', '2023-12-31')

# 快速获取并保存分钟线数据
minute_bars = quick_minute_bars('000001.SZ', '2023-01-01', '1m')

# 不保存到本地
bars = quick_bars('000001.SZ', '2023-01-01', '2023-12-31', save=False)
```

## 高级用法

### 1. 使用数据中心

```python
# 获取数据中心实例
hub = get_data_hub()

# 使用数据中心获取数据
bars = hub.get_bars('000001.SZ', '2023-01-01', '2023-12-31')
minute_bars = hub.get_minute_bars('000001.SZ', '2023-01-01', '1m')
financials = hub.get_financials('000001.SZ', '2023-01-01', '2023-12-31')
```

### 2. 自定义存储配置

```python
from qp.data import StoreConfig, BarStore

# 创建自定义存储配置
config = StoreConfig(
    root="custom_data_path",
    partition_by="year",
    file_format="parquet"
)

# 使用自定义配置保存数据
store = BarStore(config)
bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31')
store.save_bars(bars)
```

### 3. 使用数据服务

```python
from qp.data import BarDataService, MinuteDataService, FinancialDataService

# 创建数据服务实例
bar_service = BarDataService()
minute_service = MinuteDataService()
financial_service = FinancialDataService()

# 使用服务获取数据
bars = bar_service.get_bars('000001.SZ', '2023-01-01', '2023-12-31')
minute_bars = minute_service.get_minute_bars('000001.SZ', '2023-01-01', '1m')
financials = financial_service.get_financials('000001.SZ', '2023-01-01', '2023-12-31')
```

### 4. 批量处理

```python
# 批量获取多只股票数据
symbols = ['000001.SZ', '000002.SZ', '000858.SZ']
all_bars = []

for symbol in symbols:
    bars = get_bars(symbol, '2023-01-01', '2023-12-31')
    all_bars.extend(bars)
    save_bars(bars)  # 保存每只股票的数据

# 批量查询数据
all_queries = []
for symbol in symbols:
    bars = query_bars(symbol, '2023-01-01', '2023-12-31')
    all_queries.extend(bars)
```

### 5. 数据转换

```python
from qp.data import bars_to_df, df_to_bars

# 将BarData列表转换为DataFrame
bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31')
df = bars_to_df(bars)

# 将DataFrame转换为BarData列表
bars_from_df = df_to_bars(df)
```

## 错误处理

```python
try:
    bars = get_bars('000001.SZ', '2023-01-01', '2023-12-31')
    save_bars(bars)
    print(f"成功获取并保存 {len(bars)} 条K线数据")
except Exception as e:
    print(f"获取数据失败: {e}")
```

## 性能优化

```python
# 使用批量操作
from qp.data import load_multi_bars, load_multi_minutes

# 批量加载多只股票的K线数据
symbols = ['000001.SZ', '000002.SZ', '000858.SZ']
bars_dict = load_multi_bars(symbols, '2023-01-01', '2023-12-31')

# 批量加载分钟线数据
minute_bars_dict = load_multi_minutes(symbols, '2023-01-01', '1m')
```

## 配置管理

```python
# 使用配置文件
hub = get_data_hub('config/data_config.yaml')

# 或者直接使用默认配置
hub = get_data_hub()
```

这个统一接口提供了完整的数据获取、存储、查询功能，支持多种数据源和存储方式，使用简单且功能强大。
