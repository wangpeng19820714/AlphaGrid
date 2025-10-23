# run_backtest_portfolio.py（示例脚本）
import sys
import os

# 添加父目录到路径以便导入 engine 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置标准输出编码为 UTF-8（解决 Windows 中文乱码问题）
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from engine.data import MultiOHLCVDataset
from engine.risk import rebalance_to_weights_orders
from engine.backtest import run_close_fill_portfolio
from engine.metrics import summary
import pandas as pd

# 1) 读多标的数据（目录下若有 000001.SZ.csv / 600000.SH.csv / 510300.SH.csv ...）
ds = MultiOHLCVDataset(dir_path="data", symbols=["000001.SZ","600000.SH","510300.SH"])
df = ds.get()  # MultiIndex (symbol, date)

# 2) 设定每日目标权重（示例：等权三只，权重=1/3）
dates = df.index.get_level_values("date").unique()
symbols = ["000001.SZ","600000.SH","510300.SH"]
w = pd.DataFrame(1/3, index=dates, columns=symbols)

# 3) 生成组合 orders（目标权重→股数变化）
orders = rebalance_to_weights_orders(df_prices=df, target_weights=w, capital=1_000_000, lot_size=1)

# 4) 组合回测（收盘成交 + 费用/滑点）
res = run_close_fill_portfolio(df, orders, fee_bp=10, slip_bp=2, tax_bp_sell=0)

# 5) 绩效（用组合日度 PnL 汇总）
smry = summary(res.portfolio_pnl, capital=1_000_000, rf_annual=0.02)
print("=" * 50)
print("📊 投资组合绩效报告")
print("=" * 50)
for k, v in smry.items():
    print(f"{k}: {v}")
print("=" * 50)
