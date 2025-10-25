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

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

# 检查是否在虚拟环境中
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo "[警告] 当前不在虚拟环境中"
    echo ""
    read -p "是否继续? (y/n): " continue
    if [[ ! "$continue" =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo "[信息] 开始更新 requirements..."
echo ""

# 创建requirements目录
mkdir -p requirements

# 1. 生成主requirements.txt（所有已安装包）
echo "[1/4] 生成 requirements.txt..."
python3 -m pip freeze > requirements/requirements.txt
if [ $? -ne 0 ]; then
    echo "[错误] 生成 requirements.txt 失败"
    exit 1
fi
echo "      ✅ requirements.txt 已生成"

# 2. 生成最小化requirements（仅核心包）
echo ""
echo "[2/4] 生成 requirements-minimal.txt..."
cat > requirements/requirements-minimal.txt << 'EOF'
# 最小化依赖 - 核心包
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
pyarrow>=12.0.0
EOF
echo "      ✅ requirements-minimal.txt 已生成"

# 3. 生成生产环境requirements
echo ""
echo "[3/4] 生成 requirements-prod.txt..."
cat > requirements/requirements-prod.txt << 'EOF'
# 生产环境依赖
pandas>=2.0.0
numpy>=1.24.0
pyyaml>=6.0
pyarrow>=12.0.0
duckdb>=0.9.0
akshare>=1.12.0
EOF
echo "      ✅ requirements-prod.txt 已生成"

# 4. 生成开发环境requirements
echo ""
echo "[4/4] 生成 requirements-dev.txt..."
cat > requirements/requirements-dev.txt << 'EOF'
# 开发环境依赖 (包含所有生产依赖 + 开发工具)
-r requirements-prod.txt

# 测试工具
pytest>=7.0.0
pytest-cov>=4.0.0

# 代码质量
black>=23.0.0
flake8>=6.0.0
mypy>=1.0.0

# 文档工具
sphinx>=6.0.0

# Jupyter
jupyter>=1.0.0
ipykernel>=6.0.0
EOF
echo "      ✅ requirements-dev.txt 已生成"

# 统计信息
echo ""
echo "========================================"
echo "  更新完成！"
echo "========================================"
for f in requirements/*.txt; do
    lines=$(wc -l < "$f")
    echo "  $(basename $f): $lines 行"
done

echo ""
echo "[提示] 文件位置: requirements/"
echo ""

