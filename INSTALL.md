# AlphaGrid 安装指南

## 🚀 快速安装

### Mac / Linux 用户

#### 方法一：使用安装脚本（推荐）
```bash
# 下载项目后，在项目根目录执行：
chmod +x install.sh
./install.sh
```

#### 方法二：简化安装
```bash
chmod +x install-simple.sh
./install-simple.sh
```

#### 方法三：手动安装
```bash
# 1. 确保已安装 Python 3.8+
python3 --version

# 2. 安装依赖
pip3 install -r requirements.txt

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

## 📞 获取帮助

如果遇到问题，请：
1. 检查 Python 版本是否符合要求
2. 确保网络连接正常
3. 查看错误信息并参考故障排除部分
4. 提交 Issue 到项目仓库
