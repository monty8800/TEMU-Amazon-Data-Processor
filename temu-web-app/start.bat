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
echo %BLUE%      TEMU ^& Amazon 数据处理系统 - 启动脚本           %NC%
echo %BLUE%======================================================%NC%

:: 检查Python环境
echo.
echo %YELLOW%[1/5] 检查Python环境...%NC%
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: 未找到Python，请安装Python 3.8或更高版本%NC%
    exit /b 1
)

:: 检查Node.js环境
echo.
echo %YELLOW%[2/5] 检查Node.js环境...%NC%
where node >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo %RED%错误: 未找到Node.js，请安装Node.js 18或更高版本%NC%
    exit /b 1
)

:: 检查并创建Python虚拟环境
echo.
echo %YELLOW%[3/5] 设置后端环境...%NC%
cd backend

if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 安装依赖
echo 安装后端依赖...
pip install -r requirements.txt

:: 检查前端依赖
echo.
echo %YELLOW%[4/5] 设置前端环境...%NC%
cd ..\frontend

if not exist "node_modules" (
    echo 安装前端依赖...
    npm install
)

:: 启动应用
echo.
echo %YELLOW%[5/5] 启动应用...%NC%
echo %GREEN%启动后端服务器...%NC%

:: 在新窗口中启动后端
cd ..\backend
start "TEMU & Amazon 数据处理系统 - 后端" cmd /c "call venv\Scripts\activate.bat && uvicorn main:app --host 0.0.0.0 --port 8000"

:: 启动前端
echo %GREEN%启动前端服务器...%NC%
cd ..\frontend
start "TEMU & Amazon 数据处理系统 - 前端" cmd /c "npm run dev"

echo.
echo %GREEN%应用程序已启动!%NC%
echo 前端地址: %BLUE%http://localhost:3000%NC%
echo 后端API地址: %BLUE%http://localhost:8000%NC%
echo.
echo 请在命令行窗口中按 Ctrl+C 停止各服务

:: 等待用户输入
echo 按任意键退出此窗口...
pause >nul
