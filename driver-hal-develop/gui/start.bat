@echo off
chcp 65001 > nul
title Driver HAL — Agent 路由可视化 Web GUI

echo.
echo ╔══════════════════════════════════════════════════╗
echo ║  🚗  Driver HAL Agent 路由可视化 Web GUI         ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: 切换到 gui/ 目录
cd /d "%~dp0"

:: 检查 Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8 及以上版本
    echo       下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python 已检测到
python --version

:: 安装依赖（首次运行或版本更新时）
echo.
echo [INFO] 正在检查 / 安装 Python 依赖...
pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo [警告] 依赖安装可能有问题，尝试继续启动...
)
echo [INFO] 依赖检查完成

:: 启动服务器
echo.
echo [INFO] 正在启动 Web 服务器...
echo [INFO] 浏览器访问: http://localhost:5000
echo [INFO] 按 Ctrl+C 可停止服务器
echo.

:: 延迟 1.5 秒后自动打开浏览器
start /b cmd /c "timeout /t 2 > nul && start http://localhost:5000"

:: 启动 Flask 服务
python server.py

echo.
echo [INFO] 服务器已停止。
pause
