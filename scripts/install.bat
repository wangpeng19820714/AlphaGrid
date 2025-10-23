@echo off
chcp 65001 >nul
REM AlphaGrid 量化交易回测系统 - Windows 安装脚本
REM 使用方法: 双击运行 install.bat 或在命令行中执行

echo.
echo 🚀 AlphaGrid 量化交易回测系统安装程序
echo ================================================

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.8+
    echo    下载地址: https://www.python.org/downloads/
    echo    安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

REM 显示 Python 版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ 检测到 Python 版本: %PYTHON_VERSION%

REM 检查 pip 是否安装
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 pip，请先安装 pip
    pause
    exit /b 1
)

echo ✅ Python 环境检查通过

REM 升级 pip
echo.
echo 📦 升级 pip 到最新版本...
python -m pip install --upgrade pip

REM 安装依赖包
echo.
echo 📦 安装项目依赖包...
echo    这可能需要几分钟时间，请耐心等待...

REM 选择安装模式
echo.
echo 请选择安装模式:
echo 1) 最小安装 (仅核心功能)
echo 2) 完整安装 (包含所有功能)
echo 3) 生产环境 (推荐用于生产)
echo 4) 开发环境 (包含开发工具)
echo.
set /p choice=请输入选择 (1-4): 

if "%choice%"=="1" (
    echo 🔧 执行最小安装...
    if exist "requirements-minimal.txt" (
        python -m pip install -r requirements-minimal.txt
        if errorlevel 1 (
            echo ❌ 最小依赖包安装失败
            pause
            exit /b 1
        )
        echo ✅ 最小依赖包安装完成
    ) else (
        echo ❌ 错误: 未找到 requirements-minimal.txt 文件
        pause
        exit /b 1
    )
) else if "%choice%"=="2" (
    echo 🔧 执行完整安装...
    if exist "requirements.txt" (
        python -m pip install -r requirements.txt
        if errorlevel 1 (
            echo ❌ 完整依赖包安装失败
            pause
            exit /b 1
        )
        echo ✅ 完整依赖包安装完成
    ) else (
        echo ❌ 错误: 未找到 requirements.txt 文件
        pause
        exit /b 1
    )
) else if "%choice%"=="3" (
    echo 🔧 执行生产环境安装...
    if exist "requirements-prod.txt" (
        python -m pip install -r requirements-prod.txt
        if errorlevel 1 (
            echo ❌ 生产环境依赖包安装失败
            pause
            exit /b 1
        )
        echo ✅ 生产环境依赖包安装完成
    ) else (
        echo ❌ 错误: 未找到 requirements-prod.txt 文件
        pause
        exit /b 1
    )
) else if "%choice%"=="4" (
    echo 🔧 执行开发环境安装...
    if exist "requirements-dev.txt" (
        python -m pip install -r requirements-dev.txt
        if errorlevel 1 (
            echo ❌ 开发环境依赖包安装失败
            pause
            exit /b 1
        )
        echo ✅ 开发环境依赖包安装完成
    ) else (
        echo ❌ 错误: 未找到 requirements-dev.txt 文件
        pause
        exit /b 1
    )
) else (
    echo ⚠️  无效选择，使用默认完整安装...
    if exist "requirements.txt" (
        python -m pip install -r requirements.txt
        if errorlevel 1 (
            echo ❌ 依赖包安装失败
            pause
            exit /b 1
        )
        echo ✅ 依赖包安装完成
    ) else (
        echo ❌ 错误: 未找到 requirements.txt 文件
        pause
        exit /b 1
    )
)

REM 创建数据目录
echo.
echo 📁 创建必要目录...
if not exist "quant\data" mkdir "quant\data"
if not exist "quant\cache" mkdir "quant\cache"
if not exist "quant\reports" mkdir "quant\reports"

REM 验证安装
echo.
echo 🧪 验证安装...
cd quant
python -c "import pandas, numpy, pyarrow; print('✅ 核心依赖包导入成功')"
if errorlevel 1 (
    echo ❌ 安装验证失败
    pause
    exit /b 1
)

echo ✅ 安装验证通过

echo.
echo 🎉 安装完成！
echo ================================================
echo 📖 使用方法:
echo    cd quant
echo    python run_backtest.py
echo.
echo 📚 更多信息请查看 README.md
echo ================================================
echo.
pause
