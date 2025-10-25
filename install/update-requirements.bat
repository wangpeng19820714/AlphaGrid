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

REM 检查Python3环境
python3 --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python3
    pause
    exit /b 1
)

REM 检查update_requirements.py是否存在
if not exist "update_requirements.py" (
    echo [错误] 未找到 update_requirements.py
    echo [提示] 请确保在 install 目录下运行此脚本
    pause
    exit /b 1
)

echo [信息] 开始更新 requirements...
echo.

REM 调用Python工具
python3 update_requirements.py --yes
if errorlevel 1 (
    echo [错误] 更新 requirements 失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo   更新完成！
echo ========================================

REM 显示生成的文件
echo.
echo [提示] 文件位置: install/requirements/
echo.
for %%f in (requirements\*.txt) do (
    if exist "%%f" (
        for /f %%a in ('find /c /v "" ^< "%%f"') do echo   %%~nxf: %%a 行
    )
)

echo.
echo [使用方法]
echo   pip install -r install/requirements/requirements-minimal.txt
echo   pip install -r install/requirements/requirements-prod.txt
echo   pip install -r install/requirements/requirements-dev.txt
echo.
pause

