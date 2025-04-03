#!/bin/bash

echo "安装 TEMU & Amazon 数据处理系统依赖..."

# 确保 Python 已安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python 3。请安装 Python 3 后再运行此脚本。"
    exit 1
fi

# 创建必要的目录
mkdir -p "数据源/TEMU"
mkdir -p "数据源/amazon"
mkdir -p "处理结果"
mkdir -p "logs"

# 安装依赖
python3 -m pip install -r requirements.txt

echo "依赖安装完成！"
echo "运行 'python3 app.py' 启动图形界面应用程序。"
