@echo off
chcp 65001 >nul
REM ========================================
REM AlphaGrid - 量化回测运行脚本 (Windows)
REM ========================================

echo.
echo ========================================
echo   AlphaGrid 量化回测系统
echo ========================================
echo.

REM 保存当前目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    echo.
    pause
    exit /b 1
)

REM 检查是否存在虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo [信息] 激活虚拟环境...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo [信息] 激活虚拟环境...
    call .venv\Scripts\activate.bat
) else (
    echo [警告] 未找到虚拟环境，使用系统 Python
)

REM 检查 src/qp 目录
if not exist "src\qp" (
    echo [错误] 未找到 src\qp 目录
    echo.
    pause
    exit /b 1
)

REM 检查数据文件是否存在
if not exist "src\qp\data\stock.csv" (
    echo [警告] 未找到数据文件: src\qp\data\stock.csv
    echo 将使用默认配置运行
    echo.
)

REM 运行回测脚本
echo [运行] 启动量化回测...
echo.
python src\qp\run_backtest.py

REM 检查运行结果
if errorlevel 1 (
    echo.
    echo [错误] 回测执行失败
    echo.
    pause
    exit /b 1
)

echo.
echo [完成] 回测成功结束
echo.
pause

