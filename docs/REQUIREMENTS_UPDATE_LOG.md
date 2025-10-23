# Requirements 工具更新说明

## 📝 更新内容

### 1. 新增工具

创建了自动更新requirements的批处理工具，包括：

- `scripts/update_requirements.py` - Python版本（推荐，跨平台）
- `scripts/update-requirements.bat` - Windows批处理版本
- `scripts/update-requirements.sh` - Linux/Mac Shell版本

### 2. 目录结构变更

将所有requirements文件移至 `requirements/` 目录：

```
AlphaGrid/
├── requirements/
│   ├── requirements.txt          # 完整依赖（pip freeze）
│   ├── requirements-minimal.txt  # 最小化依赖
│   ├── requirements-prod.txt     # 生产环境依赖
│   └── requirements-dev.txt      # 开发环境依赖
└── scripts/
    ├── update_requirements.py    # 更新工具（Python）
    ├── update-requirements.bat   # 更新工具（Windows）
    └── update-requirements.sh    # 更新工具（Linux/Mac）
```

### 3. 修复的文件

已更新以下文件以适配新的requirements路径：

- ✅ `scripts/install.bat` - Windows安装脚本
- ✅ `scripts/install-simple.bat` - Windows简化安装脚本
- ✅ `scripts/install.sh` - Linux/Mac安装脚本
- ✅ `scripts/install-simple.sh` - Linux/Mac简化安装脚本
- ✅ `README.md` - 更新了安装说明和项目结构

## 🚀 使用方法

### 更新Requirements

```bash
# Python版本（推荐）
python scripts/update_requirements.py --yes

# 只生成精简版本
python scripts/update_requirements.py --yes --no-freeze

# 自定义输出目录
python scripts/update_requirements.py --yes --dir deps

# Windows批处理
scripts\update-requirements.bat

# Linux/Mac Shell
./scripts/update-requirements.sh
```

### 安装依赖

```bash
# 最小安装
pip install -r requirements/requirements-minimal.txt

# 生产环境
pip install -r requirements/requirements-prod.txt

# 开发环境
pip install -r requirements/requirements-dev.txt

# 完整安装
pip install -r requirements/requirements.txt
```

### 使用安装脚本

```bash
# Windows - 交互式选择安装模式
scripts\install.bat

# Windows - 简化版（最小安装）
scripts\install-simple.bat

# Linux/Mac - 交互式选择安装模式
./scripts/install.sh

# Linux/Mac - 简化版（最小安装）
./scripts/install-simple.sh
```

## ✅ 测试验证

所有修复已通过测试：

1. ✅ Requirements文件路径正确（`requirements\`目录）
2. ✅ 更新工具正常工作
3. ✅ 安装脚本能正确找到所有requirements文件
4. ✅ UTF-8编码正常显示
5. ✅ Python导入测试通过

## 📚 文档

详细使用说明请参考：
- [Requirements工具文档](docs/REQUIREMENTS_TOOLS.md)
- [项目README](README.md)

## ⚠️ 注意事项

1. 旧版本的requirements文件（项目根目录）已被新版本（requirements/目录）替代
2. 所有安装脚本已更新为使用新路径
3. 建议使用Python版本的更新工具，功能更强大且跨平台

## 🎯 快速命令参考

```bash
# 更新requirements（非交互模式）
python scripts/update_requirements.py --yes

# 最小安装
pip install -r requirements/requirements-minimal.txt

# 运行回测测试
python quant/run_backtest.py

# 运行组合回测
python quant/test/run_backtest_portfolio_t1.py
```

## 🔧 故障排除

### 问题：找不到requirements文件

**解决方案**：
1. 确保在项目根目录运行脚本
2. 先运行 `python scripts/update_requirements.py --yes` 生成文件

### 问题：安装脚本报错

**解决方案**：
1. 检查路径是否正确（使用 `requirements\` 而非 `requirements-xxx.txt`）
2. 运行测试脚本：`scripts\test-install.bat`（Windows）

### 问题：中文乱码

**解决方案**：
所有脚本已添加 `chcp 65001` 和 UTF-8输出设置，应该能正常显示中文。

