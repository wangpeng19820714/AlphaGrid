# run_backtest_portfolio_t1.py
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
from engine.backtest import run_portfolio_t1_rebalance
from engine.metrics import summary
import pandas as pd

# 1) 读取多标的价格（目录里放 000001.SZ.csv / 600000.SH.csv / 510300.SH.csv ...）
ds = MultiOHLCVDataset(dir_path="data", symbols=["000001.SZ","600000.SH","510300.SH"])
prices = ds.get()  # MultiIndex [symbol,date]

# 2) 准备目标权重：这里做一个“等权 + 月度换仓”的示例
dates = prices.index.get_level_values("date").unique()
symbols = ["000001.SZ","600000.SH","510300.SH"]
w = pd.DataFrame(0.0, index=dates, columns=symbols)
w.iloc[0:] = 1.0 / len(symbols)  # 简单等权（你也可以按信号生成逐日权重）

# 3) 运行“动态权益 + T+1 再平衡”
res = run_portfolio_t1_rebalance(
    df=prices,
    target_weights=w,
    capital0=1_000_000,
    fee_bp=10,
    slip_bp=2,
    tax_bp_sell=0,
    lot_size=1,
)

# 4) 绩效
smry = summary(res.portfolio_pnl, capital=1_000_000, rf_annual=0.02)
print("=" * 50)
print("📊 投资组合 (T+1) 绩效报告")
print("=" * 50)
for k, v in smry.items():
    print(f"{k}: {v}")
print("=" * 50)

# 可选：看一下最终权益
print(f"\n最终权益: {float(res.equity.iloc[-1]):,.2f}")