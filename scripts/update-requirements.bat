@echo off
chcp 65001 >nul
REM ========================================
REM AlphaGrid - Requirements 自动更新工具
REM ========================================

echo.
echo ========================================
echo   Requirements 自动更新工具
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)

REM 检查是否在虚拟环境中
python -c "import sys; exit(0 if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else 1)" >nul 2>&1
if errorlevel 1 (
    echo [警告] 当前不在虚拟环境中
    echo.
    set /p continue="是否继续? (y/n): "
    if /i not "%continue%"=="y" (
        exit /b 0
    )
)

echo [信息] 开始更新 requirements...
echo.

REM 创建requirements目录
if not exist "requirements" mkdir requirements

REM 1. 生成主requirements.txt（所有已安装包）
echo [1/4] 生成 requirements.txt...
python -m pip freeze > requirements\requirements.txt
if errorlevel 1 (
    echo [错误] 生成 requirements.txt 失败
    pause
    exit /b 1
)
echo       ✅ requirements.txt 已生成

REM 2. 生成最小化requirements（仅核心包）
echo.
echo [2/4] 生成 requirements-minimal.txt...
(
echo # 最小化依赖 - 核心包
echo pandas^>=2.0.0
echo numpy^>=1.24.0
echo pyyaml^>=6.0
echo pyarrow^>=12.0.0
) > requirements\requirements-minimal.txt
echo       ✅ requirements-minimal.txt 已生成

REM 3. 生成生产环境requirements
echo.
echo [3/4] 生成 requirements-prod.txt...
(
echo # 生产环境依赖
echo pandas^>=2.0.0
echo numpy^>=1.24.0
echo pyyaml^>=6.0
echo pyarrow^>=12.0.0
echo duckdb^>=0.9.0
echo akshare^>=1.12.0
) > requirements\requirements-prod.txt
echo       ✅ requirements-prod.txt 已生成

REM 4. 生成开发环境requirements
echo.
echo [4/4] 生成 requirements-dev.txt...
(
echo # 开发环境依赖 ^(包含所有生产依赖 + 开发工具^)
echo -r requirements-prod.txt
echo.
echo # 测试工具
echo pytest^>=7.0.0
echo pytest-cov^>=4.0.0
echo.
echo # 代码质量
echo black^>=23.0.0
echo flake8^>=6.0.0
echo mypy^>=1.0.0
echo.
echo # 文档工具
echo sphinx^>=6.0.0
echo.
echo # Jupyter
echo jupyter^>=1.0.0
echo ipykernel^>=6.0.0
) > requirements\requirements-dev.txt
echo       ✅ requirements-dev.txt 已生成

REM 统计信息
echo.
echo ========================================
echo   更新完成！
echo ========================================
for %%f in (requirements\*.txt) do (
    for /f %%a in ('find /c /v "" ^< "%%f"') do echo   %%~nxf: %%a 行
)

echo.
echo [提示] 文件位置: requirements\
echo.
pause

