@echo off
setlocal enabledelayedexpansion

:: 设置颜色
set "GREEN=[92m"
set "BLUE=[94m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

:: 打印标题
echo %BLUE%======================================================%NC%
echo %BLUE%      TEMU ^& Amazon 数据处理系统 - 停止脚本           %NC%
echo %BLUE%======================================================%NC%

echo.
echo %YELLOW%正在停止应用程序...%NC%

:: 停止后端进程
echo 停止后端服务...
taskkill /FI "WINDOWTITLE eq TEMU & Amazon 数据处理系统 - 后端*" /F
if %ERRORLEVEL% equ 0 (
    echo %GREEN%后端服务已停止%NC%
) else (
    echo %YELLOW%未找到运行中的后端服务%NC%
)

:: 停止前端进程
echo 停止前端服务...
taskkill /FI "WINDOWTITLE eq TEMU & Amazon 数据处理系统 - 前端*" /F
if %ERRORLEVEL% equ 0 (
    echo %GREEN%前端服务已停止%NC%
) else (
    echo %YELLOW%未找到运行中的前端服务%NC%
)

echo.
echo %GREEN%所有服务已停止%NC%

echo 按任意键退出...
pause >nul
