# run_backtest_portfolio.py
"""投资组合回测脚本"""
from test_base import print_header, print_summary, print_footer
from engine.data import MultiOHLCVDataset
from engine.risk import rebalance_to_weights_orders
from engine.backtest import run_close_fill_portfolio
from engine.metrics import summary
from config_manager import get_config
import pandas as pd

# 加载配置
config = get_config()

# 1) 读取多标的数据
ds = MultiOHLCVDataset(
    dir_path=config.path.data_dir,
    symbols=["000001.SZ", "600000.SH", "510300.SH"]
)
df = ds.get()

# 2) 设定每日目标权重：等权配置
dates = df.index.get_level_values("date").unique()
symbols = ["000001.SZ", "600000.SH", "510300.SH"]
w = pd.DataFrame(1/3, index=dates, columns=symbols)

# 3) 生成组合 orders
orders = rebalance_to_weights_orders(
    df_prices=df,
    target_weights=w,
    capital=config.backtest.capital,
    lot_size=config.backtest.lot_size
)

# 4) 组合回测
res = run_close_fill_portfolio(
    df, orders,
    fee_bp=config.backtest.fee_bp,
    slip_bp=config.backtest.slip_bp,
    tax_bp_sell=config.backtest.tax_bp_sell
)

# 5) 绩效分析
smry = summary(
    res.portfolio_pnl,
    capital=config.backtest.capital,
    rf_annual=config.backtest.rf_annual
)

# 6) 输出结果
print_header("投资组合绩效报告")
print_summary(smry)
print_footer()

