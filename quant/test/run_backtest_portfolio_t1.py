# run_backtest_portfolio_t1.py
"""投资组合 T+1 回测脚本"""
from test_base import print_header, print_summary, print_footer, print_final_equity
from engine.data import MultiOHLCVDataset
from engine.backtest import run_portfolio_t1_rebalance
from engine.metrics import summary
from config_manager import get_config
import pandas as pd

# 加载配置
config = get_config()

# 1) 读取多标的价格
ds = MultiOHLCVDataset(
    dir_path=config.path.data_dir,
    symbols=["000001.SZ", "600000.SH", "510300.SH"]
)
prices = ds.get()

# 2) 准备目标权重：等权配置
dates = prices.index.get_level_values("date").unique()
symbols = ["000001.SZ", "600000.SH", "510300.SH"]
w = pd.DataFrame(1.0 / len(symbols), index=dates, columns=symbols)

# 3) 运行 T+1 再平衡
res = run_portfolio_t1_rebalance(
    df=prices,
    target_weights=w,
    capital0=config.backtest.capital,
    fee_bp=config.backtest.fee_bp,
    slip_bp=config.backtest.slip_bp,
    tax_bp_sell=config.backtest.tax_bp_sell,
    lot_size=config.backtest.lot_size,
)

# 4) 绩效分析
smry = summary(
    res.portfolio_pnl,
    capital=config.backtest.capital,
    rf_annual=config.backtest.rf_annual
)

# 5) 输出结果
print_header("投资组合 (T+1) 绩效报告")
print_summary(smry)
print_footer()
print_final_equity(float(res.equity.iloc[-1]))
