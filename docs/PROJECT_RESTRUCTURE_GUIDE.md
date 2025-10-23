# 项目结构重组指南

## 📋 当前问题

项目根目录下文件较多，包括：
- 4个安装脚本（install.bat, install.sh, install-simple.bat, install-simple.sh）
- 2个运行脚本（run.bat, run.sh）
- 4个requirements文件
- 多个文档文件

这导致根目录显得杂乱，不利于项目维护和新手理解。

---

## 🎯 推荐的项目结构

### 标准 Python 项目结构

```
AlphaGrid/
│
├── 📜 scripts/                    # 所有可执行脚本
│   ├── install.bat               # Windows完整安装
│   ├── install.sh                # Linux/Mac完整安装
│   ├── install-simple.bat        # Windows简化安装
│   ├── install-simple.sh         # Linux/Mac简化安装
│   ├── run.bat                   # Windows运行脚本
│   └── run.sh                    # Linux/Mac运行脚本
│
├── 📦 requirements/               # 依赖管理（分类清晰）
│   ├── base.txt                  # 基础依赖（原 requirements.txt）
│   ├── dev.txt                   # 开发依赖（原 requirements-dev.txt）
│   ├── prod.txt                  # 生产依赖（原 requirements-prod.txt）
│   └── minimal.txt               # 最小依赖（原 requirements-minimal.txt）
│
├── 📚 docs/                       # 所有文档
│   ├── INSTALL.md                # 安装文档
│   ├── API.md                    # API文档
│   ├── CHANGELOG.md              # 更新日志
│   └── optimization/             # 优化文档
│       ├── DATA_MODULE_OPTIMIZATION.md
│       └── PARQUET_STORE_TEST_REPORT.md
│
├── 💼 quant/                      # 核心代码（保持不变）
│   ├── config_manager.py
│   ├── run_backtest.py
│   ├── engine/
│   ├── strategies/
│   ├── datahub/
│   ├── storage/
│   ├── test/
│   └── ...
│
├── 📖 README.md                   # 项目主文档（保留根目录）
├── 📄 LICENSE                     # 许可证（可选）
├── 📋 .gitignore                  # Git忽略文件
└── 🔧 setup.py                    # 包安装配置（可选）
```

---

## ✨ 优点

### 1. **清晰的目录职责**
- `scripts/` - 一看就知道是脚本
- `requirements/` - 依赖管理集中
- `docs/` - 文档独立存放

### 2. **便于维护**
- 查找文件更快
- 添加新脚本/依赖有明确位置
- 减少根目录混乱

### 3. **符合行业标准**
- 遵循 Python 项目最佳实践
- 新手更容易理解
- CI/CD 配置更简单

---

## 🔄 迁移步骤

### 步骤1: 创建新目录
```bash
mkdir scripts requirements docs docs/optimization
```

### 步骤2: 移动脚本文件
```bash
# Windows
move install*.bat scripts\
move install*.sh scripts\
move run.bat scripts\
move run.sh scripts\

# Linux/Mac
mv install*.{bat,sh} scripts/
mv run.{bat,sh} scripts/
```

### 步骤3: 重组requirements文件
```bash
# Windows
move requirements.txt requirements\base.txt
move requirements-dev.txt requirements\dev.txt
move requirements-prod.txt requirements\prod.txt
move requirements-minimal.txt requirements\minimal.txt

# Linux/Mac
mv requirements.txt requirements/base.txt
mv requirements-dev.txt requirements/dev.txt
mv requirements-prod.txt requirements/prod.txt
mv requirements-minimal.txt requirements/minimal.txt
```

### 步骤4: 移动文档
```bash
# Windows
move INSTALL.md docs\
move DATA_MODULE_OPTIMIZATION.md docs\optimization\
move PARQUET_STORE_TEST_REPORT.md docs\optimization\

# Linux/Mac
mv INSTALL.md docs/
mv DATA_MODULE_OPTIMIZATION.md docs/optimization/
mv PARQUET_STORE_TEST_REPORT.md docs/optimization/
```

---

## 📝 需要更新的文件

### 1. **install脚本**
更新 requirements 文件路径：
```bash
# 原来
pip install -r requirements.txt

# 更新为
pip install -r requirements/base.txt
```

### 2. **README.md**
更新文档链接：
```markdown
# 原来
详见 [INSTALL.md](INSTALL.md)

# 更新为
详见 [docs/INSTALL.md](docs/INSTALL.md)
```

### 3. **CI/CD配置**（如果有）
更新路径引用

---

## 🎯 另一种方案（更简化）

如果觉得上面的结构太复杂，可以采用更简化的方案：

```
AlphaGrid/
├── scripts/          # 只移动脚本
├── docs/             # 只移动文档
├── quant/            # 核心代码
├── requirements.txt  # 主依赖（保留根目录）
├── requirements-*.txt # 其他依赖（保留根目录）
└── README.md
```

**这种方案的优点：**
- requirements 文件保持在根目录（符合很多项目习惯）
- 改动最小，兼容性最好
- 只需移动脚本和文档

---

## 💡 推荐方案

**我推荐使用「方案2：更简化」**，原因：

1. ✅ requirements 文件在根目录是业界常见做法
2. ✅ 只移动脚本和文档，改动最小
3. ✅ 向后兼容性好
4. ✅ 大多数 Python 工具默认在根目录查找 requirements.txt

**简化后的结构：**
```
AlphaGrid/
├── scripts/                    # 📜 所有脚本
│   ├── install*.bat/sh
│   └── run*.bat/sh
├── docs/                       # 📚 所有文档
│   ├── INSTALL.md
│   └── optimization/
├── quant/                      # 💼 核心代码
├── requirements.txt            # 📦 保留在根目录
├── requirements-*.txt          # 📦 保留在根目录
└── README.md                   # 📖 保留在根目录
```

---

## 🚀 快速执行

### Windows (PowerShell)
```powershell
# 创建目录
New-Item -ItemType Directory -Force scripts, docs, docs\optimization

# 移动脚本
Move-Item install*.bat, install*.sh, run.bat, run.sh scripts\

# 移动文档
Move-Item INSTALL.md docs\
Move-Item DATA_MODULE_OPTIMIZATION.md, PARQUET_STORE_TEST_REPORT.md docs\optimization\
```

### Linux/Mac (Bash)
```bash
# 创建目录
mkdir -p scripts docs/optimization

# 移动脚本
mv install*.{bat,sh} run.{bat,sh} scripts/

# 移动文档
mv INSTALL.md docs/
mv DATA_MODULE_OPTIMIZATION.md PARQUET_STORE_TEST_REPORT.md docs/optimization/
```

---

## ✅ 检查清单

重组后需要验证：
- [ ] 安装脚本能正常运行
- [ ] 运行脚本能正常运行
- [ ] README 链接已更新
- [ ] Git 仓库已提交更改
- [ ] CI/CD 配置已更新（如果有）

---

**最后更新：** 2025-10-23  
**推荐方案：** 简化方案（scripts/ + docs/ + requirements保留根目录）

