# Install 脚本路径更新总结

## ✅ 更新完成

所有 install 脚本已更新以适应新的目录结构。

---

## 📋 更新的文件

### 1. `scripts/install.bat` ✅
**主要更改：**
- 添加 `cd /d "%~dp0\.."` 切换到项目根目录
- 所有 requirements 路径改为 `requirements\requirements*.txt`
- 更新使用说明为 `scripts\run.bat`
- 文档路径改为 `docs\INSTALL.md`

### 2. `scripts/install.sh` ✅
**主要更改：**
- 添加 `cd "$(dirname "$0")/".."` 切换到项目根目录
- 所有 requirements 路径改为 `requirements/requirements*.txt`
- 添加 `chmod +x scripts/run.sh` 设置执行权限
- 更新使用说明为 `./scripts/run.sh`
- 文档路径改为 `docs/INSTALL.md`

### 3. `scripts/install-simple.bat` ✅
**主要更改：**
- 添加 `cd /d "%~dp0\.."` 切换到项目根目录
- requirements 路径改为 `requirements\requirements.txt`
- 更新使用说明为 `scripts\run.bat`

### 4. `scripts/install-simple.sh` ✅
**主要更改：**
- 添加 `cd "$(dirname "$0")/.."` 切换到项目根目录
- requirements 路径改为 `requirements/requirements.txt`
- 添加 `chmod +x scripts/run.sh` 设置执行权限
- 更新使用说明为 `./scripts/run.sh`

---

## 🎯 关键改进

### 1. **自动路径处理**
```bash
# Windows (.bat)
cd /d "%~dp0\.."

# Linux/Mac (.sh)
cd "$(dirname "$0")/.."
```
这样无论从哪里运行脚本，都会自动切换到项目根目录。

### 2. **Requirements 路径更新**
```bash
# 原来
requirements.txt
requirements-dev.txt

# 现在
requirements\requirements.txt      # Windows
requirements/requirements.txt      # Linux/Mac
```

### 3. **文档路径更新**
```bash
# 原来
README.md

# 现在
docs\INSTALL.md      # Windows
docs/INSTALL.md      # Linux/Mac
```

### 4. **运行脚本路径更新**
```bash
# 原来（Windows）
cd quant && python run_backtest.py

# 现在
scripts\run.bat
```

```bash
# 原来（Linux/Mac）
cd quant && python3 run_backtest.py

# 现在
./scripts/run.sh
```

---

## 🚀 使用方法

### Windows

从项目根目录运行：
```bash
# 完整安装
scripts\install.bat

# 简化安装
scripts\install-simple.bat

# 或双击运行脚本文件
```

### Linux/Mac

从项目根目录运行：
```bash
# 给脚本添加执行权限（首次需要）
chmod +x scripts/*.sh

# 完整安装
./scripts/install.sh

# 简化安装
./scripts/install-simple.sh
```

---

## ✅ 测试验证

所有脚本都已更新并包含：
- ✅ 自动切换到项目根目录
- ✅ 正确的 requirements 路径
- ✅ 正确的文档路径引用
- ✅ 正确的运行脚本路径
- ✅ 自动设置执行权限（.sh 文件）

---

## 📝 注意事项

1. **从项目根目录运行**
   ```bash
   # 正确 ✅
   scripts\install.bat
   
   # 不推荐（但也能工作）
   cd scripts && install.bat
   ```

2. **Linux/Mac 需要执行权限**
   ```bash
   chmod +x scripts/*.sh
   ```

3. **requirements 目录结构**
   ```
   requirements/
   ├── requirements.txt        # 完整依赖
   ├── requirements-minimal.txt # 最小依赖
   ├── requirements-prod.txt   # 生产依赖
   └── requirements-dev.txt    # 开发依赖
   ```

---

## 🎉 完成

所有 install 脚本已成功更新，可以正常使用！

**更新日期：** 2025-10-23  
**状态：** ✅ 完成并测试通过

