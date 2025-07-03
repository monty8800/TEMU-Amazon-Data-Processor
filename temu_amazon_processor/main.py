#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TEMU & Amazon 数据处理系统
这是一个用于处理和合并TEMU和亚马逊销售数据的工具
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
from datetime import datetime
import traceback
import time
import re
import json
from typing import Dict, List, Optional, Tuple, Union, Any

# 依赖包自动检测与安装
def check_and_install_dependencies():
    """
    检查并安装必要的依赖包
    """
    required_packages = {
        "pandas": "pandas>=1.5.0",
        "openpyxl": "openpyxl>=3.0.10",
        "chardet": "chardet>=4.0.0",
        "colorama": "colorama>=0.4.4"
    }
    
    missing_packages = []
    
    for package, version in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(version)
    
    if missing_packages:
        print(f"正在安装缺失的依赖包: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("依赖包安装完成!")
        except subprocess.CalledProcessError as e:
            print(f"安装依赖包时出错: {str(e)}")
            print("请手动安装以下包:")
            for package in missing_packages:
                print(f"pip install {package}")
            sys.exit(1)

# 立即检查和安装依赖
check_and_install_dependencies()

# 导入依赖包
import pandas as pd
import chardet
from colorama import Fore, Style, init

# 初始化colorama
init(autoreset=True)

# 常量定义
DATA_SOURCE_DIR = Path("数据源")
AMAZON_SOURCE_DIR = DATA_SOURCE_DIR / "亚马逊"
TEMU_SOURCE_DIR = DATA_SOURCE_DIR / "TEMU"
RESULTS_DIR = Path("处理结果")
LOGS_DIR = Path("logs")

# 设置日志记录
def setup_logging(task_dir=None):
    """
    设置日志记录器
    """
    # 确保logs目录存在
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 设置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    
    # 设置文件处理器(logs目录)
    log_file = LOGS_DIR / f"data_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    
    # 添加处理器到日志记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # 如果有任务目录，添加任务特定的日志文件
    if task_dir:
        task_log_file = task_dir / "task.log"
        task_file_handler = logging.FileHandler(task_log_file, encoding='utf-8')
        task_file_handler.setLevel(logging.INFO)
        task_file_handler.setFormatter(file_format)
        logger.addHandler(task_file_handler)
    
    return logger

# 日志辅助函数
def log_section(message):
    logging.info(f"{Fore.CYAN}{'='*20} {message} {'='*20}{Style.RESET_ALL}")
    
def log_success(message):
    logging.info(f"{Fore.GREEN}{message}{Style.RESET_ALL}")
    
def log_warning(message):
    logging.warning(f"{Fore.YELLOW}{message}{Style.RESET_ALL}")
    
def log_error(message):
    logging.error(f"{Fore.RED}{message}{Style.RESET_ALL}")
    
def log_step(message):
    logging.info(f"{Fore.BLUE}[步骤] {message}{Style.RESET_ALL}")

# 自定义TEMU数据处理器
class CustomTemuDataProcessor:
    def __init__(self, task_id, output_dir):
        self.task_id = task_id
        self.output_dir = output_dir
        self.country_mapping = {
            'US': '美国', 'UK': '英国', 'DE': '德国', 'FR': '法国',
            'IT': '意大利', 'ES': '西班牙', 'JP': '日本', 'CA': '加拿大',
            'MX': '墨西哥', 'BR': '巴西', 'AU': '澳大利亚', 'NL': '荷兰'
        }

    def _extract_country_from_filename(self, filename_or_path):
        """从文件名或路径中提取国家信息"""
        filename = os.path.basename(filename_or_path)
        path = str(filename_or_path)
        
        # 检查中文国家名
        for country_code, country_name in self.country_mapping.items():
            if country_name in path:
                return country_name
        
        # 检查英文国家代码
        for country_code in self.country_mapping.keys():
            pattern = rf'[_\-\s]({country_code})[_\-\s\.]'
            if re.search(pattern, path, re.IGNORECASE):
                return self.country_mapping[country_code]
        
        # 如果没有找到任何国家信息，返回默认值
        return '未知国家'

    def find_files(self, directory, file_type):
        """查找指定类型的文件"""
        files = []
        extensions = ['.xlsx', '.xls', '.csv']  # 支持多种文件格式
        for ext in extensions:
            pattern = f"*{file_type}*{ext}"
            files.extend(list(directory.glob(pattern)))
        
        if not files:
            log_warning(f"在 {directory} 中没有找到包含 '{file_type}' 的文件")
        else:
            log_success(f"找到 {len(files)} 个{file_type}文件")
        
        return files

    def detect_encoding(self, file_path):
        """检测文件编码"""
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read(10000))
        encoding = result['encoding']
        confidence = result['confidence']
        
        log_step(f"检测到文件 {os.path.basename(file_path)} 编码为 {encoding} (置信度: {confidence:.2f})")
        
        # 处理一些特殊情况
        if encoding.lower() in ['ascii', 'windows-1252']:
            encoding = 'utf-8'
        
        return encoding

    def read_excel_file(self, file_path):
        """读取Excel文件"""
        log_step(f"读取Excel文件: {file_path}")
        try:
            return pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            log_error(f"读取Excel文件 {file_path} 时出错: {str(e)}")
            # 尝试使用xlrd引擎
            try:
                return pd.read_excel(file_path)
            except Exception as inner_e:
                log_error(f"使用替代引擎读取 {file_path} 时出错: {str(inner_e)}")
                return pd.DataFrame()

    def read_csv_file(self, file_path):
        """读取CSV文件"""
        log_step(f"读取CSV文件: {file_path}")
        encoding = self.detect_encoding(file_path)
        try:
            return pd.read_csv(file_path, encoding=encoding)
        except Exception as e:
            log_error(f"使用 {encoding} 编码读取CSV文件 {file_path} 时出错: {str(e)}")
            # 尝试其他编码
            for encoding in ['utf-8', 'gbk', 'gb18030', 'latin-1']:
                try:
                    log_warning(f"尝试使用 {encoding} 编码重新读取")
                    return pd.read_csv(file_path, encoding=encoding)
                except Exception:
                    continue
            
            log_error(f"无法读取CSV文件 {file_path}: 所有尝试的编码都失败")
            return pd.DataFrame()

    def read_file(self, file_path):
        """根据文件类型读取文件"""
        file_ext = file_path.suffix.lower()
        if file_ext in ['.xlsx', '.xls']:
            return self.read_excel_file(file_path)
        elif file_ext == '.csv':
            return self.read_csv_file(file_path)
        else:
            log_error(f"不支持的文件类型: {file_ext}")
            return pd.DataFrame()

    def merge_bill_data(self):
        """合并对账中心文件"""
        bill_dir = TEMU_SOURCE_DIR / "对账"
        bill_files = self.find_files(bill_dir, "对账")
        
        if not bill_files:
            log_warning("没有找到对账中心文件")
            return
        
        log_section("开始处理对账中心数据")
        sheet_data = {}
        total_rows = 0
        
        for file in bill_files:
            country = self._extract_country_from_filename(file)
            log_step(f"处理 {country} 对账文件: {file}")
            
            df = self.read_file(file)
            if df.empty:
                continue
                
            sheet_name = f"{country}-对账中心"
            sheet_data.setdefault(sheet_name, []).append(df)
            total_rows += len(df)
        
        if sheet_data:
            output_path = self.output_dir / f'TEMU对账中心-{self.task_id}.xlsx'
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, dfs in sheet_data.items():
                    merged_df = pd.concat(dfs, ignore_index=True)
                    merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    log_success(f"保存 {sheet_name} 表，共 {len(merged_df)} 行数据")
            
            log_success(f"对账中心数据处理完成，共 {len(sheet_data)} 个表，{total_rows} 行数据，输出文件: {output_path}")
        else:
            log_warning("没有有效的对账中心数据可处理")

    def merge_settlement_data(self):
        """合并结算数据"""
        settlement_dir = TEMU_SOURCE_DIR / "结算"
        settlement_files = self.find_files(settlement_dir, "结算")
        
        if not settlement_files:
            log_warning("没有找到结算数据文件")
            return
        
        log_section("开始处理结算数据")
        sheet_data_dict = {}
        total_rows = 0
        
        for file in settlement_files:
            country = self._extract_country_from_filename(file)
            log_step(f"处理 {country} 结算文件: {file}")
            
            df = self.read_file(file)
            if df.empty:
                continue
            
            sheet_name = f"{country}-结算数据"
            sheet_data_dict.setdefault(sheet_name, []).append(df)
            total_rows += len(df)
        
        if sheet_data_dict:
            output_path = self.output_dir / f'TEMU结算数据-{self.task_id}.xlsx'
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, dfs in sheet_data_dict.items():
                    merged_df = pd.concat(dfs, ignore_index=True)
                    merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    log_success(f"保存 {sheet_name} 表，共 {len(merged_df)} 行数据")
            
            log_success(f"结算数据处理完成，共 {len(sheet_data_dict)} 个表，{total_rows} 行数据，输出文件: {output_path}")
        else:
            log_warning("没有有效的结算数据可处理")

    def merge_order_data(self):
        """合并订单数据"""
        order_dir = TEMU_SOURCE_DIR / "订单"
        order_files = self.find_files(order_dir, "订单")
        
        if not order_files:
            log_warning("没有找到订单数据文件")
            return
        
        log_section("开始处理订单数据")
        sheet_data_dict = {}
        total_rows = 0
        
        for file in order_files:
            country = self._extract_country_from_filename(file)
            log_step(f"处理 {country} 订单文件: {file}")
            
            df = self.read_file(file)
            if df.empty:
                continue
            
            sheet_name = f"{country}-订单数据"
            sheet_data_dict.setdefault(sheet_name, []).append(df)
            total_rows += len(df)
        
        if sheet_data_dict:
            output_path = self.output_dir / f'TEMU订单数据-{self.task_id}.xlsx'
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name, dfs in sheet_data_dict.items():
                    merged_df = pd.concat(dfs, ignore_index=True)
                    merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
                    log_success(f"保存 {sheet_name} 表，共 {len(merged_df)} 行数据")
            
            log_success(f"订单数据处理完成，共 {len(sheet_data_dict)} 个表，{total_rows} 行数据，输出文件: {output_path}")
        else:
            log_warning("没有有效的订单数据可处理")

    def process_all(self):
        """处理所有TEMU数据"""
        log_section("开始处理所有TEMU数据")
        
        self.merge_bill_data()
        self.merge_settlement_data()
        self.merge_order_data()
        
        log_section("TEMU数据处理完成")

# Amazon数据处理函数
def process_amazon_data(task_id, output_dir):
    """处理所有亚马逊数据"""
    log_section("开始处理亚马逊数据")
    
    # 亚马逊结算数据处理
    settlement_dir = AMAZON_SOURCE_DIR / "结算报告"
    settlement_files = list(settlement_dir.glob("*.xlsx")) + list(settlement_dir.glob("*.xls")) + list(settlement_dir.glob("*.csv"))
    
    if not settlement_files:
        log_warning("没有找到亚马逊结算数据文件")
        return
    
    sheet_data_dict = {}
    total_rows = 0
    
    for file in settlement_files:
        # 从文件名提取站点信息
        filename = file.name
        marketplace = "未知站点"
        
        # 常见亚马逊站点标识
        marketplace_identifiers = {
            "US": "美国", "UK": "英国", "DE": "德国", "FR": "法国", 
            "IT": "意大利", "ES": "西班牙", "JP": "日本", "CA": "加拿大"
        }
        
        for code, name in marketplace_identifiers.items():
            if code in filename or name in filename:
                marketplace = name
                break
        
        log_step(f"处理 {marketplace} 结算文件: {file}")
        
        # 读取文件
        file_ext = file.suffix.lower()
        try:
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(file)
            elif file_ext == '.csv':
                # 尝试多种编码
                encodings = ['utf-8', 'gbk', 'gb18030', 'latin-1']
                success = False
                
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file, encoding=encoding)
                        success = True
                        break
                    except Exception:
                        continue
                
                if not success:
                    log_error(f"无法读取CSV文件 {file}: 所有尝试的编码都失败")
                    continue
            else:
                log_error(f"不支持的文件类型: {file_ext}")
                continue
        except Exception as e:
            log_error(f"读取文件 {file} 时出错: {str(e)}")
            continue
        
        if df.empty:
            continue
        
        sheet_name = f"{marketplace}-结算数据"
        sheet_data_dict.setdefault(sheet_name, []).append(df)
        total_rows += len(df)
    
    if sheet_data_dict:
        output_path = output_dir / f'亚马逊结算数据-{task_id}.xlsx'
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for sheet_name, dfs in sheet_data_dict.items():
                merged_df = pd.concat(dfs, ignore_index=True)
                merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
                log_success(f"保存 {sheet_name} 表，共 {len(merged_df)} 行数据")
        
        log_success(f"亚马逊数据处理完成，共 {len(sheet_data_dict)} 个表，{total_rows} 行数据，输出文件: {output_path}")
    else:
        log_warning("没有有效的亚马逊数据可处理")
    
    log_section("亚马逊数据处理完成")

# 主处理函数
def process_data(process_amazon=False, process_temu=False):
    """处理指定平台的数据"""
    # 确保目录存在
    os.makedirs(DATA_SOURCE_DIR, exist_ok=True)
    os.makedirs(AMAZON_SOURCE_DIR, exist_ok=True)
    os.makedirs(TEMU_SOURCE_DIR, exist_ok=True)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # 生成任务ID和输出目录
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    task_dir = RESULTS_DIR / f"TASK_{task_id}"
    os.makedirs(task_dir, exist_ok=True)
    
    # 设置包含任务特定日志文件的日志记录
    setup_logging(task_dir)
    
    log_section("开始数据处理任务")
    log_step(f"任务ID: {task_id}")
    log_step(f"输出目录: {task_dir}")
    
    try:
        if process_amazon:
            process_amazon_data(task_id, task_dir)
        
        if process_temu:
            temu_processor = CustomTemuDataProcessor(task_id, task_dir)
            temu_processor.process_all()
        
        log_section("任务完成")
        log_success(f"处理结果已保存到 {task_dir}")
    except Exception as e:
        log_error(f"处理数据时发生错误: {str(e)}")
        log_error(traceback.format_exc())
        raise

# 显示菜单并获取用户选择
def display_menu():
    """显示主菜单"""
    print(f"\n{Fore.CYAN}{'='*20} TEMU & 亚马逊数据处理系统 {'='*20}{Style.RESET_ALL}")
    print(f"{Fore.BLUE}[1]{Style.RESET_ALL} 处理亚马逊数据")
    print(f"{Fore.BLUE}[2]{Style.RESET_ALL} 处理TEMU数据")
    print(f"{Fore.BLUE}[3]{Style.RESET_ALL} 合并所有数据")
    print(f"{Fore.BLUE}[0]{Style.RESET_ALL} 退出程序")
    
    while True:
        choice = input("\n请输入选项 [0-3]: ").strip()
        if choice in ['0', '1', '2', '3']:
            return choice
        print(f"{Fore.RED}无效选项，请重新输入{Style.RESET_ALL}")

# 主入口函数
def main():
    """
    命令行入口点
    """
    try:
        # 检查并安装必要的包
        check_and_install_dependencies()
        
        # 设置日志记录
        setup_logging()
        
        while True:
            choice = display_menu()
            
            if choice == '0':
                print(f"\n{Fore.GREEN}程序已退出{Style.RESET_ALL}")
                break
            
            if choice == '1':
                process_data(process_amazon=True, process_temu=False)
            elif choice == '2':
                process_data(process_amazon=False, process_temu=True)
            elif choice == '3':
                process_data(process_amazon=True, process_temu=True)
                
            input(f"\n{Fore.BLUE}按Enter键返回主菜单...{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}程序运行时发生错误: {str(e)}{Style.RESET_ALL}")
        logging.error(f"程序退出，发生错误: {str(e)}")
        raise

if __name__ == "__main__":
    main()
