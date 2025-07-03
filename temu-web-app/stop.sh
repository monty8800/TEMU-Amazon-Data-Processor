#!/bin/bash

# 设置颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # 无颜色

# 打印标题
echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}      TEMU & Amazon 数据处理系统 - 停止脚本           ${NC}"
echo -e "${BLUE}======================================================${NC}"

echo -e "\n${YELLOW}正在停止应用程序...${NC}"

# 查找并终止后端进程
BACKEND_PID=$(ps aux | grep "uvicorn main:app" | grep -v grep | awk '{print $2}')
if [ ! -z "$BACKEND_PID" ]; then
    echo -e "停止后端服务 (PID: $BACKEND_PID)..."
    kill $BACKEND_PID
    echo -e "${GREEN}后端服务已停止${NC}"
else
    echo -e "${YELLOW}未找到运行中的后端服务${NC}"
fi

# 查找并终止前端进程
FRONTEND_PID=$(ps aux | grep "next" | grep -v grep | awk '{print $2}')
if [ ! -z "$FRONTEND_PID" ]; then
    echo -e "停止前端服务 (PID: $FRONTEND_PID)..."
    kill $FRONTEND_PID
    echo -e "${GREEN}前端服务已停止${NC}"
else
    echo -e "${YELLOW}未找到运行中的前端服务${NC}"
fi

# 清理PID文件
if [ -f ".pid_file" ]; then
    rm .pid_file
fi

echo -e "\n${GREEN}所有服务已停止${NC}"
