# 量化研究模块 - 选股功能

## 📋 概述

本模块实现了基于多因子的量化选股功能，包括因子计算、标准化、中性化和综合评分。不包含回测逻辑，专注于股票选择。

## 🏗️ 模块结构

```
src/qp/research/
├── __init__.py              # 模块初始化
├── selector.py              # 核心选股逻辑
├── config.py                # 配置管理
├── data_interface.py        # 数据接口
└── run_stock_selection.py   # 主运行脚本
```

## 🚀 功能特性

### 1. 因子计算
- **动量因子**：120日收益率
- **波动率因子**：20日滚动波动率
- **估值因子**：PE倒数

### 2. 数据处理
- **Winsorize**：去除异常值
- **Z-score标准化**：标准化因子值
- **中性化**：行业和市值中性化

### 3. 综合评分
- 多因子加权平均
- 可配置权重
- 按得分排序选股

### 4. 输出格式
- 包含 `trade_date`, `symbol`, `score`, `rank`, `direction`, `weight`, `model_name`, `version`
- 保存为 Parquet 文件

## 📊 使用方法

### 1. 基本使用

```python
from qp.research import StockSelector, SelectionConfig

# 创建配置
config = SelectionConfig(
    top_n=50,
    momentum_window=120,
    volatility_window=20,
    model_name="multi_factor_v1"
)

# 创建选择器
selector = StockSelector(config)

# 执行选股
symbols = ["000001", "000002", "000003"]  # 股票代码列表
results = selector.select_stocks(symbols, "2024-01-15")

# 保存结果
save_path = selector.save_results(results, "2024-01-15")
```

### 2. 使用便捷函数

```python
from qp.research import run_stock_selection

# 运行选股
symbols = ["000001", "000002", "000003"]
results, save_path = run_stock_selection(symbols, "2024-01-15")

print(f"选股完成，结果保存至: {save_path}")
```

### 3. 命令行使用

```bash
# 基本选股
python src/qp/research/run_stock_selection.py --trade-date 2024-01-15 --universe hs300 --top-n 50

# 使用配置文件
python src/qp/research/run_stock_selection.py --config configs/stock_selection_config.yaml

# 创建默认配置文件
python src/qp/research/run_stock_selection.py --create-config
```

## ⚙️ 配置说明

### 配置文件结构

```yaml
selection:
  top_n: 50                    # 选择前N只股票
  lookback_days: 150           # 回看天数
  output_dir: reports/stock_selection
  model_name: multi_factor_model
  version: 1.0.0

factor_config:
  momentum_window: 120          # 动量因子窗口
  volatility_window: 20        # 波动率因子窗口
  winsorize_limits: [0.05, 0.95]
  zscore_threshold: 3.0
  neutralize_industry: true
  neutralize_market_cap: true

factor_weights:
  momentum: 0.4                # 动量因子权重
  volatility: -0.3             # 波动率因子权重（负权重）
  valuation: 0.3               # 估值因子权重

screening_rules:
  min_market_cap: 100000000    # 最小市值
  min_volume: 1000000          # 最小成交量
  min_pe: 0.1                  # 最小PE
  max_pe: 100.0                # 最大PE
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `top_n` | int | 50 | 选择前N只股票 |
| `momentum_window` | int | 120 | 动量因子窗口期 |
| `volatility_window` | int | 20 | 波动率因子窗口期 |
| `winsorize_limits` | list | [0.05, 0.95] | Winsorize限制 |
| `zscore_threshold` | float | 3.0 | Z-score阈值 |
| `neutralize_industry` | bool | True | 是否进行行业中性化 |
| `neutralize_market_cap` | bool | True | 是否进行市值中性化 |

## 📈 因子说明

### 1. 动量因子 (Momentum Factor)
- **计算方式**：120日收益率
- **权重**：0.4
- **含义**：反映股票的中期趋势

### 2. 波动率因子 (Volatility Factor)
- **计算方式**：20日滚动波动率
- **权重**：-0.3（负权重）
- **含义**：低波动率股票更受青睐

### 3. 估值因子 (Valuation Factor)
- **计算方式**：PE倒数
- **权重**：0.3
- **含义**：低估值股票更受青睐

## 📁 输出格式

选股结果包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `trade_date` | datetime | 交易日期 |
| `symbol` | str | 股票代码 |
| `score` | float | 综合得分 |
| `rank` | int | 排名 |
| `direction` | str | 方向（long/short） |
| `weight` | float | 权重 |
| `model_name` | str | 模型名称 |
| `version` | str | 模型版本 |
| `momentum_factor` | float | 动量因子值 |
| `volatility_factor` | float | 波动率因子值 |
| `valuation_factor` | float | 估值因子值 |

## 🔧 扩展功能

### 1. 自定义因子

```python
class CustomFactorCalculator(FactorCalculator):
    def calculate_custom_factor(self, data):
        # 实现自定义因子计算
        pass
```

### 2. 自定义筛选规则

```python
class CustomStockScreener(StockScreener):
    def custom_screening(self, data):
        # 实现自定义筛选逻辑
        pass
```

### 3. 数据接口扩展

```python
class CustomDataInterface(DataInterface):
    def get_custom_data(self, symbols, trade_date):
        # 实现自定义数据获取
        pass
```

## 📊 示例输出

```
选股结果摘要
============================================================
交易日期: 2024-01-15
股票池: hs300 (300 只)
选择股票数: 50
模型名称: multi_factor_model
模型版本: 1.0.0

前10只股票:
symbol     score  rank  momentum_factor  volatility_factor  valuation_factor
000001   0.234     1             0.456             -0.123             0.234
000002   0.198     2             0.345             -0.098             0.198
...

因子统计:
  动量因子: 均值=0.123, 标准差=0.456
  波动率因子: 均值=-0.098, 标准差=0.234
  估值因子: 均值=0.156, 标准差=0.345
  综合得分: 均值=0.089, 标准差=0.234
```

## 🚨 注意事项

1. **数据质量**：确保输入数据的质量和完整性
2. **因子稳定性**：定期检查因子的稳定性和有效性
3. **参数调优**：根据市场环境调整因子权重和参数
4. **风险控制**：结合风险管理进行选股
5. **回测验证**：选股结果需要通过回测验证有效性

## 📞 技术支持

如有问题，请查看：
1. 日志文件：`logs/stock_selection.log`
2. 配置文件：`configs/stock_selection_config.yaml`
3. 输出结果：`reports/stock_selection/`

## 🎯 总结

本选股模块提供了完整的量化选股功能，包括：

- ✅ 多因子计算和标准化
- ✅ 行业和市值中性化
- ✅ 综合评分和排序
- ✅ 模块化设计
- ✅ 配置文件支持
- ✅ 命令行接口
- ✅ 详细日志记录

适用于量化研究和策略开发！
