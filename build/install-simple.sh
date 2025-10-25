#!/bin/bash
# AlphaGrid 简化安装脚本 - Mac/Linux

echo "🚀 AlphaGrid 安装程序"
echo "===================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 请先安装 Python 3.8+: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 已安装: $(python3 --version)"

# 安装依赖
echo "📦 安装依赖包..."
python3 -m pip install --upgrade pip
python3 -m pip install -e .

# 创建目录
mkdir -p src/qp/cache src/qp/reports data

echo "✅ 安装完成！"
echo "运行: python3 -m qp.cli --help"
echo "运行: python3 src/qp/run_backtest.py"
