#!/bin/bash
# ========================================
# AlphaGrid - Requirements 自动更新工具
# ========================================

set -e

echo ""
echo "========================================"
echo "  Requirements 自动更新工具"
echo "========================================"
echo ""

# 检查Python3环境
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

# 检查update_requirements.py是否存在
if [[ ! -f "update_requirements.py" ]]; then
    echo "[错误] 未找到 update_requirements.py"
    echo "[提示] 请确保在 install 目录下运行此脚本"
    exit 1
fi

echo "[信息] 开始更新 requirements..."
echo ""

# 调用Python工具
python3 update_requirements.py --yes
if [ $? -ne 0 ]; then
    echo "[错误] 更新 requirements 失败"
    exit 1
fi

echo ""
echo "========================================"
echo "  更新完成！"
echo "========================================"

# 显示生成的文件
echo ""
echo "[提示] 文件位置: install/requirements/"
echo ""
if [[ -d "requirements" ]]; then
    for f in requirements/*.txt; do
        if [[ -f "$f" ]]; then
            lines=$(wc -l < "$f")
            echo "  $(basename $f): $lines 行"
        fi
    done
fi

echo ""
echo "[使用方法]"
echo "  pip install -r install/requirements/requirements-minimal.txt"
echo "  pip install -r install/requirements/requirements-prod.txt"
echo "  pip install -r install/requirements/requirements-dev.txt"
echo ""

