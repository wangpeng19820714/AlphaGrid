#!/bin/bash
# ========================================
# AlphaGrid - 量化回测运行脚本 (Linux/Mac)
# ========================================

set -e  # 遇到错误立即退出

echo ""
echo "========================================"
echo "  AlphaGrid 量化回测系统"
echo "========================================"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查是否存在虚拟环境
if [ -f "venv/bin/activate" ]; then
    echo "[信息] 激活虚拟环境..."
    source venv/bin/activate
elif [ -f ".venv/bin/activate" ]; then
    echo "[信息] 激活虚拟环境..."
    source .venv/bin/activate
else
    echo "[警告] 未找到虚拟环境，使用系统 Python"
fi

# 检查 src/qp 目录
if [ ! -d "src/qp" ]; then
    echo "[错误] 未找到 src/qp 目录"
    exit 1
fi

# 检查数据文件是否存在
if [ ! -f "src/qp/data/stock.csv" ]; then
    echo "[警告] 未找到数据文件: src/qp/data/stock.csv"
    echo "将使用默认配置运行"
    echo ""
fi

# 运行回测脚本
echo "[运行] 启动量化回测..."
echo ""
python3 src/qp/run_backtest.py

# 检查运行结果
if [ $? -eq 0 ]; then
    echo ""
    echo "[完成] 回测成功结束"
    echo ""
else
    echo ""
    echo "[错误] 回测执行失败"
    echo ""
    exit 1
fi

