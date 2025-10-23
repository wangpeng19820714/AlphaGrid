@echo off
chcp 65001 >nul
REM AlphaGrid 简化安装脚本 - Windows

echo.
echo 🚀 AlphaGrid 安装程序
echo ====================

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 请先安装 Python 3.8+: https://www.python.org/downloads/
    echo    安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo ✅ Python 已安装: %%i

REM 安装依赖
echo.
echo 📦 安装依赖包...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

REM 创建目录
mkdir quant\data 2>nul
mkdir quant\cache 2>nul
mkdir quant\reports 2>nul

echo.
echo ✅ 安装完成！
echo 运行: cd quant ^&^& python run_backtest.py
pause
