#!/bin/bash
# AlphaGrid 简化安装脚本 - Mac/Linux
# 使用方法: 从项目根目录运行 ./scripts/install-simple.sh

# 切换到脚本所在目录的父目录（项目根目录）
cd "$(dirname "$0")/.."

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
python3 -m pip install -r requirements/requirements.txt

# 创建目录
mkdir -p quant/data quant/cache quant/reports

# 设置执行权限
chmod +x scripts/run.sh

echo "✅ 安装完成！"
echo "运行: ./scripts/run.sh"
echo "或: cd quant && python3 run_backtest.py"
