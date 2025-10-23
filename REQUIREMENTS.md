# Requirements 依赖说明

## 📋 依赖文件说明

AlphaGrid 提供了 4 个不同级别的依赖配置文件，满足不同使用场景：

| 文件 | 用途 | 适用场景 |
|------|------|----------|
| `requirements-minimal.txt` | 最小依赖 | 仅运行核心回测功能 |
| `requirements.txt` | 完整依赖 | 包含所有功能和常用工具 |
| `requirements-prod.txt` | 生产环境 | 生产部署推荐配置 |
| `requirements-dev.txt` | 开发环境 | 开发、测试、文档生成 |

---

## 🚀 快速开始

### 最小安装（推荐新手）
仅安装核心依赖，快速体验回测功能：
```bash
pip install -r requirements-minimal.txt
```

**包含：**
- pandas, numpy (数据处理)
- pyarrow (数据存储)

**适用于：**
- 快速体验
- 学习回测基础
- 最小化环境

---

### 完整安装（推荐）
安装所有功能模块：
```bash
pip install -r requirements.txt
```

**包含：**
- 核心依赖
- 数据源接口 (yfinance, tushare, akshare)
- 数据存储 (DuckDB)
- 可视化工具 (matplotlib, seaborn, plotly)
- 开发工具 (pytest, black, mypy)

**适用于：**
- 日常使用
- 完整功能体验
- 策略开发

---

### 生产环境安装
生产环境优化配置：
```bash
pip install -r requirements-prod.txt
```

**包含：**
- 核心依赖
- 性能优化
- 必要的数据源
- 可视化工具

**不包含：**
- 开发工具
- 测试框架
- 文档生成工具

**适用于：**
- 生产部署
- 服务器运行
- 性能优化

---

### 开发环境安装
开发者完整工具链：
```bash
pip install -r requirements-dev.txt
```

**包含：**
- 完整依赖 (通过 -r requirements.txt)
- 测试框架 (pytest, coverage)
- 代码质量工具 (black, flake8, mypy, pylint)
- 性能分析工具 (memory-profiler, py-spy)
- 文档生成 (sphinx)
- 交互式开发 (jupyter, ipython)

**适用于：**
- 代码开发
- 测试调试
- 性能优化
- 文档编写

---

## 📦 核心依赖说明

### 必需依赖

#### 数据处理
```
pandas>=2.0.0      # 数据分析和处理
numpy>=1.24.0      # 数值计算
scipy>=1.10.0      # 科学计算
```

#### 数据存储
```
pyarrow>=10.0.0    # Parquet 文件格式支持
fastparquet>=0.8.0 # Parquet 备用引擎
duckdb>=0.9.0      # 高性能分析数据库
```

---

### 数据源

#### 市场数据获取
```
yfinance>=0.2.0    # Yahoo Finance (美股、港股)
tushare>=1.2.0     # Tushare (A股，需要token)
akshare>=1.9.0     # AKShare (A股，免费)
```

**使用建议：**
- **美股/港股**: 使用 yfinance
- **A股（免费）**: 使用 akshare
- **A股（专业）**: 使用 tushare (需要积分token)

---

### 可视化

```
matplotlib>=3.6.0  # 基础绘图
seaborn>=0.12.0    # 统计可视化
plotly>=5.14.0     # 交互式图表
```

---

### 开发工具

#### 测试框架
```
pytest>=7.0.0           # 测试框架
pytest-cov>=4.0.0       # 覆盖率
pytest-xdist>=3.0.0     # 并行测试
pytest-mock>=3.10.0     # Mock支持
```

#### 代码质量
```
black>=23.0.0      # 代码格式化
flake8>=6.0.0      # 代码检查
mypy>=1.0.0        # 类型检查
isort>=5.12.0      # 导入排序
pylint>=2.17.0     # 代码分析
```

#### 性能分析
```
memory-profiler>=0.60.0  # 内存分析
line-profiler>=4.0.0     # 行级性能
py-spy>=0.3.14          # 采样分析
```

---

## 🔧 按需安装

### 安装特定功能

#### 仅安装数据源
```bash
pip install yfinance tushare akshare
```

#### 仅安装测试工具
```bash
pip install pytest pytest-cov pytest-xdist
```

#### 仅安装代码质量工具
```bash
pip install black flake8 mypy isort
```

#### 仅安装可视化
```bash
pip install matplotlib seaborn plotly
```

---

## 🐍 Python 版本要求

- **最低版本**: Python 3.8
- **推荐版本**: Python 3.10 或 3.11
- **测试版本**: Python 3.10

---

## 📝 版本管理

### 锁定依赖版本
生产环境建议锁定版本：
```bash
pip freeze > requirements.lock
```

### 更新依赖
```bash
# 更新所有包
pip install --upgrade -r requirements.txt

# 更新特定包
pip install --upgrade pandas numpy
```

### 查看依赖树
```bash
pip install pipdeptree
pipdeptree
```

---

## 💡 常见问题

### Q: 安装 duckdb 失败？
**A**: DuckDB 需要 C++ 编译器：
- **Windows**: 安装 Visual Studio Build Tools
- **Linux**: `sudo apt-get install build-essential`
- **Mac**: `xcode-select --install`

### Q: tushare 无法使用？
**A**: Tushare 需要注册获取 token：
1. 访问 https://tushare.pro/
2. 注册账号获取 token
3. 设置环境变量: `export TUSHARE_TOKEN=your_token`

### Q: 依赖冲突怎么办？
**A**: 建议使用虚拟环境：
```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### Q: 如何减少安装体积？
**A**: 使用最小依赖：
```bash
pip install -r requirements-minimal.txt
```

---

## 🔄 更新记录

### 2025-10-23
- ✅ 添加 duckdb>=0.9.0 (高性能数据库)
- ✅ 添加 plotly>=5.14.0 (交互式图表)
- ✅ 优化依赖分类和说明
- ✅ 完善注释和文档
- ✅ 调整可选依赖

### 主要改进
- 提取 DuckDB 为核心依赖
- 区分必需和可选依赖
- 添加详细的使用说明
- 优化生产环境配置

---

## 📚 参考链接

- [Pandas 文档](https://pandas.pydata.org/)
- [DuckDB 文档](https://duckdb.org/)
- [yfinance 文档](https://github.com/ranaroussi/yfinance)
- [Tushare 文档](https://tushare.pro/)
- [AKShare 文档](https://akshare.akfamily.xyz/)

---

**最后更新**: 2025-10-23  
**维护者**: AlphaGrid Team

