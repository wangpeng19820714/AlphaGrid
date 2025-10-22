#!/bin/bash
# AlphaGrid 量化交易回测系统 - Mac/Linux 安装脚本
# 使用方法: chmod +x install.sh && ./install.sh

set -e  # 遇到错误立即退出

echo "🚀 AlphaGrid 量化交易回测系统安装程序"
echo "================================================"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3，请先安装 Python 3.8+"
    echo "   下载地址: https://www.python.org/downloads/"
    exit 1
fi

# 检查 pip 是否安装
if ! command -v pip3 &> /dev/null; then
    echo "❌ 错误: 未找到 pip3，请先安装 pip"
    exit 1
fi

# 显示 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ 检测到 Python 版本: $PYTHON_VERSION"

# 检查 Python 版本是否满足要求 (3.8+)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo "❌ 错误: Python 版本过低，需要 Python 3.8 或更高版本"
    echo "   当前版本: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python 版本检查通过"

# 升级 pip
echo "📦 升级 pip 到最新版本..."
python3 -m pip install --upgrade pip

# 安装依赖包
echo "📦 安装项目依赖包..."
echo "   这可能需要几分钟时间，请耐心等待..."

if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
    echo "✅ 依赖包安装完成"
else
    echo "❌ 错误: 未找到 requirements.txt 文件"
    exit 1
fi

# 创建数据目录
echo "📁 创建必要目录..."
mkdir -p quant/data
mkdir -p quant/cache
mkdir -p quant/reports

# 设置执行权限
echo "🔧 设置执行权限..."
chmod +x quant/run_backtest.py

# 验证安装
echo "🧪 验证安装..."
cd quant
if python3 -c "import pandas, numpy, pyarrow; print('✅ 核心依赖包导入成功')"; then
    echo "✅ 安装验证通过"
else
    echo "❌ 安装验证失败"
    exit 1
fi

echo ""
echo "🎉 安装完成！"
echo "================================================"
echo "📖 使用方法:"
echo "   cd quant"
echo "   python3 run_backtest.py"
echo ""
echo "📚 更多信息请查看 README.md"
echo "================================================"
