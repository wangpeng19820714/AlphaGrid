# Requirements 自动更新工具使用说明

## 📦 工具介绍

自动生成和更新项目的 requirements 文件，支持多种配置模式。

## 🚀 快速使用

### Windows
```bash
# 方式1: 使用BAT脚本
scripts\update-requirements.bat

# 方式2: 使用Python脚本（推荐）
python scripts/update_requirements.py --yes
```

### Linux/Mac
```bash
# 方式1: 使用Shell脚本
./scripts/update-requirements.sh

# 方式2: 使用Python脚本（推荐）
python scripts/update_requirements.py --yes
```

## 📋 生成的文件

工具会在 `requirements/` 目录下生成4个文件：

### 1. `requirements.txt`
完整的pip freeze输出，包含所有已安装的包及其确切版本。

**用途**: 完全复现当前环境

### 2. `requirements-minimal.txt`
只包含核心依赖的最小化配置。

**包含**:
- pandas
- numpy  
- pyyaml
- pyarrow

**用途**: 快速安装核心功能

### 3. `requirements-prod.txt`
生产环境依赖配置。

**包含**: 所有核心依赖 + 生产环境包
- 核心包（pandas, numpy, pyyaml, pyarrow）
- duckdb
- akshare

**用途**: 生产环境部署

### 4. `requirements-dev.txt`
开发环境完整配置。

**包含**: 生产依赖 + 开发工具
- 生产环境所有包
- 测试工具（pytest, pytest-cov）
- 代码质量（black, flake8, mypy）
- 文档工具（sphinx）
- Jupyter

**用途**: 本地开发环境

## 🔧 Python脚本选项

```bash
python scripts/update_requirements.py [选项]
```

### 可用选项:

| 选项 | 说明 |
|------|------|
| `--yes, -y` | 自动确认所有提示（非交互模式） |
| `--no-freeze` | 不生成完整的freeze版本 |
| `--dir DIR` | 指定输出目录（默认: requirements） |
| `--help, -h` | 显示帮助信息 |

### 使用示例:

```bash
# 自动模式，不需要确认
python scripts/update_requirements.py --yes

# 只生成精简版本，不生成freeze
python scripts/update_requirements.py --yes --no-freeze

# 输出到自定义目录
python scripts/update_requirements.py --yes --dir deps
```

## 📥 安装依赖

根据不同场景选择对应的requirements文件：

```bash
# 最小安装（仅核心功能）
pip install -r requirements/requirements-minimal.txt

# 生产环境安装
pip install -r requirements/requirements-prod.txt

# 开发环境安装（推荐开发者使用）
pip install -r requirements/requirements-dev.txt

# 完全复现环境
pip install -r requirements/requirements.txt
```

## 💡 最佳实践

### 1. 定期更新
建议每次添加新依赖后运行更新工具：

```bash
# 安装新包后
pip install new-package

# 更新requirements
python scripts/update_requirements.py --yes
```

### 2. 版本控制
将生成的requirements文件提交到git：

```bash
git add requirements/
git commit -m "chore: update requirements"
```

### 3. CI/CD集成
在CI pipeline中使用requirements文件：

```yaml
# .github/workflows/test.yml
- name: Install dependencies
  run: pip install -r requirements/requirements-dev.txt
```

### 4. 虚拟环境
建议在虚拟环境中运行更新工具：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 更新requirements
python scripts/update_requirements.py --yes
```

## ⚠️ 注意事项

1. **虚拟环境警告**: 工具会检测是否在虚拟环境中运行，如果不是会给出警告
2. **版本锁定**: requirements.txt使用==锁定版本，其他文件使用>=指定最低版本
3. **依赖冲突**: 确保手动编辑的版本要求不会产生冲突
4. **定期清理**: 定期检查并移除不再使用的依赖

## 🔄 更新流程

```
1. 修改代码/添加依赖
   ↓
2. 运行 update_requirements.py
   ↓
3. 检查生成的文件
   ↓
4. 测试安装
   ↓
5. 提交到版本控制
```

## 📊 输出示例

```
============================================================
📦 Requirements 智能更新工具
============================================================

⚠️  警告: 当前不在虚拟环境中（自动继续）
🔍 开始分析项目依赖...

[1/4] 生成 requirements.txt (freeze)...
   ✅ requirements.txt: 228 行

[2/4] 生成 requirements-minimal.txt...
   ✅ requirements-minimal.txt: 5 行

[3/4] 生成 requirements-prod.txt...
   ✅ requirements-prod.txt: 7 行

[4/4] 生成 requirements-dev.txt...
   ✅ requirements-dev.txt: 11 行

============================================================
✨ 更新完成！
============================================================

📁 文件位置: requirements/

📊 生成的文件:
   - requirements-dev.txt (234 bytes)
   - requirements-minimal.txt (91 bytes)
   - requirements-prod.txt (114 bytes)
   - requirements.txt (4384 bytes)

💡 使用方法:
   pip install -r requirements/requirements-minimal.txt  # 最小安装
   pip install -r requirements/requirements-prod.txt     # 生产环境
   pip install -r requirements/requirements-dev.txt      # 开发环境
```

## 🐛 故障排除

### 问题1: 找不到pip
**解决**: 确保Python已正确安装并添加到PATH

### 问题2: 权限错误
**解决**: 使用管理员权限运行或检查目录权限

### 问题3: 依赖冲突
**解决**: 手动编辑requirements文件调整版本要求

## 📞 支持

如有问题，请查看项目README或提交Issue。

