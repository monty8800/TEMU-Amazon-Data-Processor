#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 打印标题
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}      TEMU & Amazon 数据处理系统 - 启动脚本           ${NC}"
echo -e "${BLUE}======================================================${NC}"

# 检查Python环境
echo -e "\n${YELLOW}[1/5] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3，请安装Python 3.8或更高版本${NC}"
    exit 1
fi

# 检查Node.js环境
echo -e "\n${YELLOW}[2/5] 检查Node.js环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}错误: 未找到Node.js，请安装Node.js 18或更高版本${NC}"
    exit 1
fi

# 检查并创建Python虚拟环境
echo -e "\n${YELLOW}[3/5] 设置后端环境...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装后端依赖..."
pip install -r requirements.txt

# 检查前端依赖
echo -e "\n${YELLOW}[4/5] 设置前端环境...${NC}"
cd ../frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

# 启动应用
echo -e "\n${YELLOW}[5/5] 启动应用...${NC}"
echo -e "${GREEN}启动后端服务器...${NC}"

# 在后台启动后端
cd ../backend
nohup uvicorn main:app --host 0.0.0.0 --port 8089 > backend.log 2>&1 &
BACKEND_PID=$!
echo "后端服务器已启动，PID: $BACKEND_PID"

# 启动前端
echo -e "${GREEN}启动前端服务器...${NC}"
cd ../frontend
npm run dev &
FRONTEND_PID=$!
echo "前端服务器已启动，PID: $FRONTEND_PID"

echo -e "\n${GREEN}应用程序已启动!${NC}"
echo -e "前端地址: ${BLUE}http://localhost:3000${NC}"
echo -e "后端API地址: ${BLUE}http://localhost:8089${NC}"
echo -e "\n按 Ctrl+C 停止应用程序"

# 保存PID到文件
echo "$BACKEND_PID $FRONTEND_PID" > .pid_file

# 捕获SIGINT信号（Ctrl+C）
trap cleanup INT

cleanup() {
    echo -e "\n${YELLOW}正在停止应用程序...${NC}"
    if [ -f ".pid_file" ]; then
        read BACKEND_PID FRONTEND_PID < .pid_file
        kill $BACKEND_PID 2>/dev/null
        kill $FRONTEND_PID 2>/dev/null
        rm .pid_file
    fi
    echo -e "${GREEN}应用程序已停止${NC}"
    exit 0
}

# 等待用户输入
wait
