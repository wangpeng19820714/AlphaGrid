# AlphaGrid 安装指南

## 🚀 快速安装

### Mac / Linux 用户

#### 方法一：使用安装脚本（推荐）
```bash
# 下载项目后，在项目根目录执行：
chmod +x install.sh
./install.sh
```

安装脚本会提供以下选项：
- **最小安装**：仅核心功能 (pandas, numpy, pyarrow)
- **完整安装**：包含所有功能
- **生产环境**：推荐用于生产部署
- **开发环境**：包含开发工具和测试框架

#### 方法二：简化安装
```bash
chmod +x install-simple.sh
./install-simple.sh
```

#### 方法三：手动安装
```bash
# 1. 确保已安装 Python 3.8+
python3 --version

# 2. 选择安装模式
# 最小安装（仅核心功能）
pip3 install -r requirements-minimal.txt

# 完整安装（包含所有功能）
pip3 install -r requirements.txt

# 生产环境（推荐用于生产）
pip3 install -r requirements-prod.txt

# 开发环境（包含开发工具）
pip3 install -r requirements-dev.txt

# 3. 创建必要目录
mkdir -p quant/data quant/cache quant/reports

# 4. 运行回测
cd quant
python3 run_backtest.py
```

### Windows 用户

#### 方法一：使用安装脚本（推荐）
1. 双击运行 `install.bat`
2. 按照提示完成安装

#### 方法二：简化安装
1. 双击运行 `install-simple.bat`
2. 按照提示完成安装

#### 方法三：手动安装
1. 确保已安装 Python 3.8+（从 https://www.python.org/downloads/ 下载）
2. 安装时勾选 "Add Python to PATH"
3. 打开命令提示符（cmd）或 PowerShell
4. 进入项目目录
5. 执行以下命令：
```cmd
pip install -r requirements.txt
mkdir quant\data
mkdir quant\cache
mkdir quant\reports
cd quant
python run_backtest.py
```

## 📋 系统要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows 10+, macOS 10.14+, Linux
- **内存**: 至少 4GB RAM
- **磁盘空间**: 至少 1GB 可用空间

## 🔧 故障排除

### 常见问题

1. **"python: command not found"**
   - 确保 Python 已正确安装并添加到 PATH
   - Windows: 重新安装 Python 并勾选 "Add Python to PATH"
   - Mac: 使用 Homebrew 安装：`brew install python`

2. **"pip: command not found"**
   - 升级 pip：`python -m pip install --upgrade pip`
   - 或使用：`python -m pip install -r requirements.txt`

3. **权限错误（Mac/Linux）**
   - 使用 `sudo` 运行安装脚本
   - 或使用虚拟环境：`python3 -m venv venv && source venv/bin/activate`

4. **网络连接问题**
   - 使用国内镜像：`pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/`

### 验证安装

安装完成后，运行以下命令验证：

```bash
cd quant
python3 run_backtest.py  # Mac/Linux
# 或
python run_backtest.py   # Windows
```

如果看到回测结果输出，说明安装成功！

## 📋 依赖项说明

### 核心依赖（必需）
- **pandas** (>=2.0.0): 数据处理和分析
- **numpy** (>=1.24.0): 数值计算
- **pyarrow** (>=10.0.0): 数据缓存优化

### 生产环境依赖
- **fastparquet** (>=0.8.0): Parquet 格式支持
- **scipy** (>=1.10.0): 科学计算
- **matplotlib** (>=3.6.0): 数据可视化
- **seaborn** (>=0.12.0): 统计图表
- **yfinance** (>=0.2.0): Yahoo Finance 数据
- **tushare** (>=1.2.0): 中国股票数据
- **akshare** (>=1.9.0): 开源财经数据接口
- **scikit-learn** (>=1.3.0): 机器学习
- **loguru** (>=0.7.0): 现代化日志
- **psutil** (>=5.9.0): 系统监控

### 开发环境依赖
- **pytest** (>=7.0.0): 测试框架
- **pytest-cov** (>=4.0.0): 测试覆盖率
- **pytest-xdist** (>=3.0.0): 并行测试
- **black** (>=23.0.0): 代码格式化
- **flake8** (>=6.0.0): 代码检查
- **mypy** (>=1.0.0): 类型检查
- **isort** (>=5.12.0): 导入排序
- **pre-commit** (>=3.0.0): Git 钩子
- **sphinx** (>=6.0.0): 文档生成
- **jupyter** (>=1.0.0): 交互式开发

### 安装模式对比

| 模式 | 包数量 | 用途 | 安装时间 |
|------|--------|------|----------|
| 最小安装 | 3个 | 基础功能 | ~30秒 |
| 完整安装 | 26个 | 所有功能 | ~3分钟 |
| 生产环境 | 13个 | 生产部署 | ~1分钟 |
| 开发环境 | 23个 | 开发调试 | ~2分钟 |

## 🔍 依赖项验证

使用提供的验证脚本检查依赖项安装状态：

```bash
python3 verify_requirements.py
```

## 📞 获取帮助

如果遇到问题，请：
1. 检查 Python 版本是否符合要求
2. 确保网络连接正常
3. 查看错误信息并参考故障排除部分
4. 提交 Issue 到项目仓库
