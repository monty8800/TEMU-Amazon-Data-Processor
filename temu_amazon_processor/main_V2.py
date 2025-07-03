#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TEMU & Amazon 数据处理系统
这是一个用于处理和合并TEMU和亚马逊销售数据的工具
# version: 2.0
# author: MONTY
# date: 2025-07-03
# description: 该脚本支持从指定目录读取TEMU和亚马逊的
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
            'US': '美国', 
            'JP': '日本', 
            'EU': '欧区', 
            'GLOBAL': '全球', 
        }
        
    def rename_bill_detail_files(self, directory=None):
        """
        检查并重命名文件名中包含“对账中心-明细”的文件为“账务中心-明细”
        """
        if directory is None:
            directory = TEMU_SOURCE_DIR
        directory = Path(directory)
        pattern = re.compile(r"(对账中心-明细)(.+)")
        count = 0
        for file in directory.rglob("*"):
            if file.is_file():
                m = pattern.search(file.name)
                if m:
                    new_name = file.name.replace("对账中心-明细", "账务中心-明细", 1)
                    new_path = file.with_name(new_name)
                    file.rename(new_path)
                    log_success(f"文件重命名: {file} → {new_path}")
                    count += 1
        if count == 0:
            log_warning("未发现需要重命名的‘对账中心-明细’文件")
        else:
            log_success(f"已重命名 {count} 个‘对账中心-明细’文件")

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

    def find_files(self, file_type, directory=None):
        """
        查找TEMU_SOURCE_DIR下每个店铺目录内，包含file_type关键字且扩展名为xlsx/xls/csv的文件。
        返回格式：[{'store': 店铺名, 'country': 国家, 'file': 文件路径}, ...]
        """
        if directory is None:
            directory = TEMU_SOURCE_DIR
        directory = Path(directory)
        result = []
        extensions = ['.xlsx', '.xls', '.csv']
        store_dirs = [d for d in directory.iterdir() if d.is_dir()]
        for store_dir in store_dirs:
            store_name = store_dir.name
            for file in store_dir.iterdir():
                if file.is_file() and file_type in file.name and file.suffix.lower() in extensions:
                    country = self._extract_country_from_filename(file)
                    result.append({'store': store_name, 'country': country, 'file': file})
        if not result:
            log_warning(f"在 {directory} 下各店铺目录中没有找到包含 '{file_type}' 的文件")
        else:
            log_success(f"共找到 {len(result)} 个包含 '{file_type}' 的文件")
        return result

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
        """将所有对账中心文件中每个sheet分别合并，保存为单独文件，并增加‘店铺’和‘国家’两列"""
        bill_files = self.find_files("对账中心")
        log_step("开始处理对账中心数据")
        log_success(f"找到 {len(bill_files)} 个对账中心文件")
        if not bill_files:
            log_warning("没有找到对账中心文件")
            return

        log_section("开始处理对账中心数据")
        # {sheet_name: [df, ...]}
        sheet_data = {}
        total_rows = 0

        for item in bill_files:
            store = item['store']
            country = item['country']
            file = item['file']
            log_step(f"处理 {store} - {country} 对账文件: {file}")
            try:
                xl = pd.ExcelFile(file)
                for sheet_name in xl.sheet_names:
                    df = xl.parse(sheet_name)
                    if df.empty:
                        continue
                    df.insert(0, "店铺", store)
                    df.insert(1, "国家", country)
                    sheet_data.setdefault(sheet_name, []).append(df)
                    total_rows += len(df)
            except Exception as e:
                log_error(f"读取 {file} 失败: {e}")

        if sheet_data:
            for sheet_name, dfs in sheet_data.items():
                merged_df = pd.concat(dfs, ignore_index=True)
                output_path = self.output_dir / f"TEMU对账中心-{sheet_name}-{self.task_id}.xlsx"
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    merged_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
                log_success(f"保存 {sheet_name} 合并表，共 {len(merged_df)} 行数据，输出文件: {output_path}")
            log_success(f"对账中心数据处理完成，共 {len(sheet_data)} 个sheet，{total_rows} 行数据")
        else:
            log_warning("没有有效的对账中心数据可处理")


    def merge_order_data(self):
        """合并所有订单数据到一个sheet，并增加‘店铺’和‘国家’两列"""
        order_files = self.find_files("订单")
        
        if not order_files:
            log_warning("没有找到订单数据文件")
            return
        
        log_section("开始处理订单数据")
        all_data = []
        total_rows = 0
        
        for item in order_files:
            store = item['store']
            country = item['country']
            file = item['file']
            log_step(f"处理 {store} - {country} 订单文件: {file}")
            
            df = self.read_file(file)
            if df.empty:
                continue
            
            # 删除同名列
            df = df.drop(columns=['店铺', '国家'], errors='ignore')
            
            df.insert(0, "店铺", store)
            df.insert(1, "国家", country)
            all_data.append(df)
            total_rows += len(df)
        
        if all_data:
            merged_df = pd.concat(all_data, ignore_index=True)
            output_path = self.output_dir / f'TEMU订单数据-{self.task_id}.xlsx'
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                merged_df.to_excel(writer, sheet_name="订单数据", index=False)
            log_success(f"订单数据处理完成，共 {total_rows} 行数据，输出文件: {output_path}")
        else:
            log_warning("没有有效的订单数据可处理")

    def merge_shipping_label_fee(self):
        """合并所有发货面单费文件到一个表，并增加‘店铺’和‘国家’两列，表头统一为中文"""
        col_map = {
            "Package Number": "包裹号",
            "Waybill Number": "运单号",
            "Service Provider Code": "服务商code",
            "Bill Type": "账单类型",
            "Shipping Fee (Unit: Yuan)": "运费(单位元)",
            "Currency": "币种",
            "Reconciliation Bill Status": "对账单状态",
            "Expense/Refund Time (Time Zone: GMT+8)": "支出/退款时间(时区：GMT+8)"
        }
        label_files = self.find_files("发货面单费")
        log_step("开始处理发货面单费数据")
        log_success(f"找到 {len(label_files)} 个发货面单费文件")
        if not label_files:
            log_warning("没有找到发货面单费文件")
            return

        log_section("开始处理发货面单费数据")
        all_data = []
        total_rows = 0

        for item in label_files:
            store = item['store']
            country = item['country']
            file = item['file']
            log_step(f"处理 {store} - {country} 发货面单费文件: {file}")
            df = self.read_file(file)
            if df.empty:
                continue
            # 删除同名列
            df = df.drop(columns=['店铺', '国家'], errors='ignore')
            # 英文表头转中文
            df.rename(columns=col_map, inplace=True)
            df.insert(0, "店铺", store)
            df.insert(1, "国家", country)
            all_data.append(df)
            total_rows += len(df)

        if all_data:
            merged_df = pd.concat(all_data, ignore_index=True)
            # 再统一一次表头顺序（如需固定顺序可如下指定）
            col_order = ["店铺", "国家", "包裹号", "运单号", "服务商code", "账单类型", "运费(单位元)", "币种", "对账单状态", "支出/退款时间(时区：GMT+8)"]
            merged_df = merged_df[[col for col in col_order if col in merged_df.columns] + [col for col in merged_df.columns if col not in col_order]]
            output_path = self.output_dir / f'TEMU发货面单费-{self.task_id}.xlsx'
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                merged_df.to_excel(writer, sheet_name="发货面单费", index=False)
            log_success(f"发货面单费数据处理完成，共 {total_rows} 行数据，输出文件: {output_path}")
        else:
            log_warning("没有有效的发货面单费数据可处理")
    
    def merge_return_label_fee(self):
        """合并所有退货面单费文件到一个表，并增加‘店铺’和‘国家’两列，表头统一为中文"""
        col_map = {
            "reconciliationId": "账务单ID",
            "waybill sn": "运单号",
            "parent orderSn": "PO单号",
            "deduct type desc": "账单类型",
            "seller currency": "币种",
            "freight charge": "金额",
            "deduct time": "账单支出/退款时间"
        }
        label_files = self.find_files("退货面单费")
        log_step("开始处理退货面单费数据")
        log_success(f"找到 {len(label_files)} 个退货面单费文件")
        if not label_files:
            log_warning("没有找到退货面单费文件")
            return

        log_section("开始处理退货面单费数据")
        all_data = []
        total_rows = 0

        for item in label_files:
            store = item['store']
            country = item['country']
            file = item['file']
            log_step(f"处理 {store} - {country} 退货面单费文件: {file}")
            df = self.read_file(file)
            if df.empty:
                continue
            # 删除同名列
            df = df.drop(columns=['店铺', '国家'], errors='ignore')
            # 英文表头转中文
            df.rename(columns=col_map, inplace=True)
            df.insert(0, "店铺", store)
            df.insert(1, "国家", country)
            all_data.append(df)
            total_rows += len(df)

        if all_data:
            merged_df = pd.concat(all_data, ignore_index=True)
            # 统一表头顺序
            col_order = ["店铺", "国家", "账务单ID", "运单号", "PO单号", "账单类型", "币种", "金额", "账单支出/退款时间"]
            merged_df = merged_df[[col for col in col_order if col in merged_df.columns] + [col for col in merged_df.columns if col not in col_order]]
            output_path = self.output_dir / f'TEMU退货面单费-{self.task_id}.xlsx'
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                merged_df.to_excel(writer, sheet_name="退货面单费", index=False)
            log_success(f"退货面单费数据处理完成，共 {total_rows} 行数据，输出文件: {output_path}")
        else:
            log_warning("没有有效的退货面单费数据可处理")
            
    def merge_finance_detail(self):
        """合并所有账务中心-明细文件到一个表，并增加‘店铺’和‘国家’两列"""
        detail_files = self.find_files("账务中心-明细")
        log_step("开始处理账务中心-明细数据")
        log_success(f"找到 {len(detail_files)} 个账务中心-明细文件")
        if not detail_files:
            log_warning("没有找到账务中心-明细文件")
            return

        log_section("开始处理账务中心-明细数据")
        all_data = []
        total_rows = 0

        for item in detail_files:
            store = item['store']
            country = item['country']
            file = item['file']
            log_step(f"处理 {store} - {country} 账务中心-明细文件: {file}")
            xl = pd.ExcelFile(file)
            for sheet_name in xl.sheet_names:
                df = xl.parse(sheet_name)
                if df.empty:
                    continue
                # 删除同名列
                df = df.drop(columns=['店铺', '国家'], errors='ignore')
                df.insert(0, "店铺", store)
                df.insert(1, "国家", country)
                all_data.append(df)
                total_rows += len(df)

        if all_data:
            merged_df = pd.concat(all_data, ignore_index=True)
            output_path = self.output_dir / f'TEMU账务中心-明细-{self.task_id}.xlsx'
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                merged_df.to_excel(writer, sheet_name="账务中心-明细", index=False)
            log_success(f"账务中心-明细数据处理完成，共 {total_rows} 行数据，输出文件: {output_path}")
        else:
            log_warning("没有有效的账务中心-明细数据可处理")
        
    def process_all(self):
        """处理所有TEMU数据"""
        log_section("开始处理所有TEMU数据")
        self.rename_bill_detail_files()
        self.merge_bill_data()
        self.merge_order_data()
        self.merge_shipping_label_fee()
        self.merge_return_label_fee()
        self.merge_finance_detail()
        log_section("TEMU数据处理完成")

# 主处理函数
def process_data(process_temu=False):
    """处理指定平台的数据"""
    # 确保目录存在
    os.makedirs(DATA_SOURCE_DIR, exist_ok=True)
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
        if process_temu:
            temu_processor = CustomTemuDataProcessor(task_id, task_dir)
            temu_processor.process_all()
        
        log_section("任务完成")
        log_success(f"处理结果已保存到 {task_dir}")
    except Exception as e:
        log_error(f"处理数据时发生错误: {str(e)}")
        log_error(traceback.format_exc())
        raise


if __name__ == "__main__":
    process_data(process_temu=True)
