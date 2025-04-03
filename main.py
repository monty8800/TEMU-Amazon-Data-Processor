import sys
import subprocess
import importlib.util
import json
import os
import time
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum
import warnings

# 检查并安装必要的依赖包
def check_and_install_dependencies():
    """检查并安装必要的依赖包"""
    required_packages = {
        'pandas': 'pandas>=1.5.0',
        'openpyxl': 'openpyxl>=3.0.10', 
        'chardet': 'chardet>=4.0.0',
        'colorama': 'colorama>=0.4.4'
    }
    
    missing_packages = []
    
    for package, version_spec in required_packages.items():
        if importlib.util.find_spec(package) is None:
            missing_packages.append(version_spec)
    
    if missing_packages:
        print(f"\n正在安装缺失的依赖包: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', *missing_packages])
            print("所有依赖包安装成功\n")
            
            # 重新导入初始化之前可能缺失的模块
            for package in required_packages.keys():
                if package in missing_packages:
                    globals()[package] = importlib.import_module(package)
        except Exception as e:
            print(f"安装依赖包时出错: {str(e)}")
            print("请手动安装所需的包: {', '.join(missing_packages)}")
            sys.exit(1)
    
    # 现在导入必要的模块
    global pd, chardet, colorama, Fore, Style
    import pandas as pd
    import chardet
    import colorama
    from colorama import Fore, Style

# 在脚本开始时检查依赖包
check_and_install_dependencies()

# 初始化colorama
colorama.init(autoreset=True)

# 日志辅助函数
def log_section(message):
    """输出一个高亮的区块标题"""
    logging.info(Fore.CYAN + Style.BRIGHT + "=" * 80)
    logging.info(Fore.CYAN + Style.BRIGHT + f" {message} ")
    logging.info(Fore.CYAN + Style.BRIGHT + "=" * 80)

def log_success(message):
    """输出一个成功消息"""
    logging.info(Fore.GREEN + Style.BRIGHT + f"✔ {message}")
    
def log_warning(message):
    """输出一个警告消息"""
    logging.warning(Fore.YELLOW + Style.BRIGHT + f"⚠ {message}")
    
def log_error(message):
    """输出一个错误消息"""
    logging.error(Fore.RED + Style.BRIGHT + f"✘ {message}")
    
def log_step(step_number, message):
    """输出处理步骤"""
    logging.info(Fore.BLUE + Style.BRIGHT + f"Step {step_number}: {message}")

def setup_logging(task_dir=None):
    """设置日志记录
    
    Args:
        task_dir: 可选的任务目录，如果提供，日志也会输出到该目录
    """
    # 创建日志目录
    log_dir = Path(__file__).parent / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    # 获取根日志器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 清除现有的处理器，以避免重复日志
    if logger.handlers:
        logger.handlers.clear()
    
    # 创建一个定制的格式化器类，添加颜色
    class ColoredFormatter(logging.Formatter):
        FORMATS = {
            logging.DEBUG: Fore.CYAN + '%(asctime)s - ' + Fore.BLUE + '%(levelname)-8s' + Fore.RESET + ' - %(message)s',
            logging.INFO: Fore.GREEN + '%(asctime)s - ' + Fore.BLUE + '%(levelname)-8s' + Fore.RESET + ' - %(message)s',
            logging.WARNING: Fore.YELLOW + '%(asctime)s - ' + Fore.YELLOW + '%(levelname)-8s' + Fore.RESET + ' - %(message)s',
            logging.ERROR: Fore.RED + '%(asctime)s - ' + Fore.RED + '%(levelname)-8s' + Fore.RESET + ' - %(message)s',
            logging.CRITICAL: Fore.MAGENTA + '%(asctime)s - ' + Fore.MAGENTA + '%(levelname)-8s' + Fore.RESET + ' - %(message)s'
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
            return formatter.format(record)
    
    # 普通文件格式化器
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)-8s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    
    # 控制台彩色格式化器
    color_formatter = ColoredFormatter()
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(color_formatter)
    logger.addHandler(console_handler)
    
    # 添加主日志文件处理器
    file_handler = logging.FileHandler(
        log_dir / f'data_processing_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 如果提供了任务目录，添加任务日志文件处理器
    if task_dir:
        if not isinstance(task_dir, Path):
            task_dir = Path(task_dir)
            
        # 确保任务目录存在
        task_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建任务日志文件
        task_log_file = task_dir / f'task_log_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        task_handler = logging.FileHandler(task_log_file, encoding='utf-8')
        task_handler.setFormatter(file_formatter)
        logger.addHandler(task_handler)
        
        logging.info(f'日志也将输出到任务目录: {task_dir}')
        
    # 添加分隔线，增强日志可读性
    logger.info("=" * 80)
    logger.info(f'日志系统初始化完成 - [系统启动时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]')
    logger.info("=" * 80)
    
    log_success('日志系统已初始化，开始处理数据...')

# 导入所需模块

# 安装必要的依赖包
def install_required_packages():
    required_packages = ['pandas', 'openpyxl']
    for package in required_packages:
        try:
            __import__(package)
            logging.info(f"{package} is already installed.")
        except ModuleNotFoundError:
            subprocess.call(f"pip install {package}", shell=True)
            logging.info(f"Installing {package}...")

# 忽略警告
warnings.filterwarnings('ignore')

# 加载国家配置数据
def load_country_config(config_path: str = './country.json') -> dict:
    try:
        with open(config_path, 'rb') as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)['encoding']
        
        with open(config_path, 'r', encoding=encoding) as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"加载国家配置文件失败: {e}")
        return {}


class FileType(Enum):
    ORDER = "订单导出"
    BILL = "对账中心"
    SHIPPING = "发货面单费"
    RETURN_TEMU = "退至TEMU仓-退货面单费"
    RETURN_MERCHANT = "退至商家仓-退货面单费"
    RETURN = "退货面单费"  # 用于处理未分类的退货面单费文件
    SETTLEMENT = "结算数据"


class FileInfo:
    def __init__(self,store_name,file_path):
        self.store_name = store_name
        self.file_path = file_path

    def __str__(self):
        return f"{self.store_name},{self.file_path}"

    def __repr__(self):
        return f"{self.store_name},{self.file_path}"


class TemuDataProcessor:
    """TEMU数据处理器"""
    def __init__(self):
        # 确保日志配置已完成
        if not logging.getLogger().handlers:
            setup_logging()
            
        # 源数据目录
        self.source_dir = Path(__file__).parent / '数据源'
        
        # 结果输出目录
        today_str = datetime.now().strftime('%Y%m%d')
        self.task_id = str(int(time.time()))
        self.output_dir = Path(__file__).parent / '处理结果' / today_str / f'TASK_{self.task_id}'
        

class CustomTemuDataProcessor(TemuDataProcessor):
    """TEMU数据处理器，可使用定制的输出目录和任务ID"""
    def __init__(self, source_dir=None, output_dir=None, task_id=None):
        # 不调用父类的__init__，因为我们要自定义变量
        # 确保日志配置已完成
        if not logging.getLogger().handlers:
            setup_logging()
            
        # 设置源数据目录
        if source_dir:
            self.source_dir = source_dir
        else:
            self.source_dir = Path(__file__).parent / '数据源'
            
        # 设置任务ID和输出目录
        if task_id:
            self.task_id = task_id
        else:
            self.task_id = str(int(time.time()))
            
        if output_dir:
            self.output_dir = output_dir
        else:
            today_str = datetime.now().strftime('%Y%m%d')
            self.output_dir = Path(__file__).parent / '处理结果' / today_str / f'TASK_{self.task_id}'
        
        # 初始化目录
        self._init_directories()
        
    def _extract_country_from_filename(self, file_path: Path) -> str:
        """从文件名中提取国家信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取到的国家名称，如果没有找到则返回空字符串
        """
        file_name = file_path.name
        parent_dir = file_path.parent.name
        full_path_str = str(file_path)
        
        # 常见国家名称映射
        country_patterns = {
            '美国': '美国',
            'US': '美国',
            '法国': '法国',
            'FR': '法国',
            '英国': '英国',
            'UK': '英国',
            '德国': '德国',
            'DE': '德国',
            '意大利': '意大利',
            'IT': '意大利',
            '西班牙': '西班牙',
            'ES': '西班牙',
            '日本': '日本',
            'JP': '日本',
            '加拿大': '加拿大',
            'CA': '加拿大',
            '澳大利亚': '澳大利亚',
            'AU': '澳大利亚',
            '荷兰': '荷兰',
            'NL': '荷兰',
            '中国': '中国',
            'CN': '中国'
        }
        
        # 下面是两个常见模式：
        # 1. 订单导出-国家.csv
        # 2. 订单导出-国家-其他信息.csv
        match = re.search(r'订单导出-([^\.\-]+)', file_name)
        if match:
            country_key = match.group(1).strip()
            logging.info(f'从文件名提取到国家关键字：{country_key}')
            if country_key in country_patterns:
                return country_patterns[country_key]
        
        # 尝试从目录名中提取
        for country_key, country_value in country_patterns.items():
            if country_key in parent_dir or country_key in full_path_str:
                logging.info(f'从路径提取到国家关键字：{country_key}')
                return country_value
        
        logging.warning(f'无法从文件路径提取国家信息：{file_path}')
        return ''
        
    def _process_order_file(self, file_info: FileInfo) -> Optional[pd.DataFrame]:
        """处理订单文件
        
        Args:
            file_info: 文件信息
            
        Returns:
            处理后的DataFrame，如果处理失败返回None
        """
        try:
            # 提取国家信息
            country = self._extract_country_from_filename(file_info.file_path)
            
            # 首先检查Excel文件是否有工作表
            file_path_str = str(file_info.file_path)
            if file_path_str.endswith('.xlsx'):
                excel_file = pd.ExcelFile(file_info.file_path)
                if len(excel_file.sheet_names) == 0:
                    logging.warning(f'文件 {file_info.file_path} 没有工作表，跳过处理')
                    return None


            if file_path_str.endswith('.csv'):
                # 尝试多种编码方式读取CSV文件
                try:
                    df = pd.read_csv(file_info.file_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        # 如果UTF-8编码失败，尝试GBK编码
                        df = pd.read_csv(file_info.file_path, encoding='gbk')
                    except UnicodeDecodeError:
                        try:
                            # 尝试gb18030编码
                            df = pd.read_csv(file_info.file_path, encoding='gb18030')
                        except UnicodeDecodeError:
                            # 最后尝试latin-1编码，它能处理任何8位字符
                            logging.info(f'尝试使用latin-1编码读取文件: {file_info.file_path.name}')
                            df = pd.read_csv(file_info.file_path, encoding='latin-1')
            else:
                df = pd.read_excel(file_info.file_path, engine='openpyxl')

                
            df.insert(0, column='店铺', value=file_info.store_name)
            
            # 添加国家信息到数据中(如果提取到了)
            if country:
                df.insert(1, column='国家', value=country)
                logging.info(f'将国家信息 [{country}] 添加到订单数据中')
            
            logging.info(f'处理店铺订单：{file_info.store_name}, {len(df)} 条')
            return df
        except Exception as e:
            logging.error(f'处理订单文件 {file_info.file_path} 失败: {str(e)}')
            return None
    def _init_directories(self) -> None:
        """Initialize and validate directories"""
        if not self.source_dir.exists():
            logging.error(f'源数据目录不存在: {self.source_dir}')
            raise FileNotFoundError(f'源数据目录不存在: {self.source_dir}')
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def process(self):
        """处理所有TEMU数据"""
        log_section('开始 TEMU 数据处理流程')
        start_time = time.time()
        
        try:
            # 创建输出目录
            self.output_dir.mkdir(parents=True, exist_ok=True)
            log_step(1, f'准备数据目录')
            logging.info(f'源数据目录: {self.source_dir}')
            logging.info(f'结果输出目录: {self.output_dir}')
            
            # 合并订单数据
            log_step(2, '处理订单数据')
            self.merge_orders()
            
            # 合并对账中心数据
            log_step(3, '处理对账中心数据')
            self.merge_bill_data()
            
            # 合并面单费用数据
            log_step(4, '处理面单费用数据')
            self.merge_shipping_fees()
            
            # 合并退货面单费数据
            log_step(5, '处理退货面单费数据')
            self.merge_return_fees()
            
            # 合并结算数据
            log_step(6, '处理结算数据')
            self.merge_settlement_data()
            
            # 输出处理统计
            elapsed_time = time.time() - start_time
            log_section('TEMU 数据处理完成')
            log_success(f'总处理用时: {elapsed_time:.2f}秒')
            log_success(f'所有数据已保存至: {self.output_dir}')
            
        except Exception as e:
            log_error(f'TEMU数据处理失败: {str(e)}')
            raise


    def _load_country_data(self) -> dict:
        try:
            country_file = self.base_dir / 'country.json'
            with open(country_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"加载country.json失败: {e}")
            raise

    def _extract_store_name(self, file_path: Path) -> str:
        """
        从文件路径中提取店铺名称
        
        Args:
            file_path: 文件路径
            
        Returns:
            店铺名称
        """
        # 尝试从路径中提取店铺名称
        path_parts = file_path.parts
        
        # 如果路径中包含“TEMU”文件夹，则取其下一级目录作为店铺名称
        try:
            temu_index = path_parts.index('数据源')
            if temu_index + 2 < len(path_parts):
                return path_parts[temu_index + 2]
        except ValueError:
            pass
            
        # 如果无法从路径提取，则使用文件名的前缀作为店铺名称
        file_name = file_path.name
        parts = file_name.split('-')
        if len(parts) > 1:
            return parts[0]
            
        # 如果以上方法均失败，则返回“未知店铺”
        return '未知店铺'
        
    def find_files(self, file_type: FileType) -> List[FileInfo]:
        """
        查找指定类型的数据文件
        
        Args:
            file_type: 要查找的文件类型
            
        Returns:
            匹配的文件信息列表
        """
        result = []
        type_value = file_type.value
        
        # 如果是退货面单费，则需要分别处理退至TEMU仓和退至商家仓
        if file_type == FileType.RETURN:
            temu_type = FileType.RETURN_TEMU.value
            merchant_type = FileType.RETURN_MERCHANT.value
            
            for root, _, files in os.walk(self.source_dir):
                for file in files:
                    if file.endswith(('.xlsx', '.xls', '.csv')) and not file.startswith('~$'):
                        file_path = Path(root) / file
                        
                        # 如果文件路径包含退货面单费关键字
                        if temu_type in str(file_path) or merchant_type in str(file_path):
                            # 提取店铺名称
                            store_name = self._extract_store_name(file_path)
                            result.append(FileInfo(store_name, file_path))
        else:
            for root, _, files in os.walk(self.source_dir):
                for file in files:
                    if file.endswith(('.xlsx', '.xls', '.csv')) and not file.startswith('~$'):
                        file_path = Path(root) / file
                        
                        # 如果文件路径包含指定类型的关键字
                        if type_value in str(file_path):
                            # 提取店铺名称
                            store_name = self._extract_store_name(file_path)
                            result.append(FileInfo(store_name, file_path))
        
        return result

    def _process_excel_file(self, file_info: FileInfo) -> Optional[pd.DataFrame]:
        """处理Excel文件
        
        Args:
            file_info: 文件信息
            
        Returns:
            处理后的DataFrame，如果处理失败返回None
        """
        try:
            # 首先检查Excel文件是否有工作表
            file_path_str = str(file_info.file_path)
            if file_path_str.endswith('.xlsx'):
                excel_file = pd.ExcelFile(file_info.file_path)
                if len(excel_file.sheet_names) == 0:
                    logging.warning(f'文件 {file_info.file_path} 没有工作表，跳过处理')
                    return None


            if file_path_str.endswith('.csv'):
                # 尝试多种编码方式读取CSV文件
                try:
                    df = pd.read_csv(file_info.file_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        # 如果UTF-8编码失败，尝试GBK编码
                        df = pd.read_csv(file_info.file_path, encoding='gbk')
                    except UnicodeDecodeError:
                        try:
                            # 尝试gb18030编码
                            df = pd.read_csv(file_info.file_path, encoding='gb18030')
                        except UnicodeDecodeError:
                            # 最后尝试latin-1编码，它能处理任何8位字符
                            logging.info(f'尝试使用latin-1编码读取文件: {file_info.file_path.name}')
                            df = pd.read_csv(file_info.file_path, encoding='latin-1')
            else:
                df = pd.read_excel(file_info.file_path, engine='openpyxl')
    
                
            df.insert(0, column='店铺', value=file_info.store_name)
            logging.info(f'处理店铺数据：{file_info.store_name}, {len(df)} 条')
            return df
        except Exception as e:
            logging.error(f'处理文件 {file_info.file_path} 失败: {str(e)}')
            return None
            
    def _merge_data(self, file_type: FileType, description: str) -> None:
        """
        合并指定类型的数据文件
        
        Args:
            file_type: 要合并的文件类型
            description: 处理描述，用于日志
        """
        logging.info(f'开始合并{description}数据')
        
        # 查找指定类型的文件
        files = self.find_files(file_type)
        
        if not files:
            logging.warning(f'未找到{description}类型的文件')
            return
            
        # 初始化数据存储
        all_data = []
        store_stats = {}
        
        # 处理每个文件
        for file_info in files:
            try:
                df = self._process_excel_file(file_info)
                
                if df is not None and not df.empty:
                    # 记录每个店铺的数据量
                    store_name = file_info.store_name
                    rows = len(df)
                    
                    if store_name in store_stats:
                        store_stats[store_name] += rows
                    else:
                        store_stats[store_name] = rows
                        
                    all_data.append(df)
                    logging.info(f'处理文件 {Path(file_info.file_path).name} 成功，包含 {rows} 条数据')
            except Exception as e:
                logging.error(f'处理文件 {file_info.file_path} 失败: {str(e)}')
                continue
                
        if not all_data:
            logging.warning(f'没有成功处理任何{description}数据文件')
            return
            
        # 合并所有数据
        merged_df = pd.concat(all_data, ignore_index=True)
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 生成输出文件名
        timestamp = int(time.time())
        output_file = self.output_dir / f'TEMU{description}汇总-{timestamp}.xlsx'
        
        # 保存合并后的数据
        merged_df.to_excel(output_file, index=False)
        
        # 输出统计信息
        total_rows = sum(store_stats.values())
        logging.info(f'{description}数据合并完成，共处理 {len(files)} 个文件，{total_rows} 条数据')
        logging.info(f'数据已保存至: {output_file}')
        
        # 输出各店铺的数据统计
        logging.info('各店铺数据统计:')
        for store, count in store_stats.items():
            logging.info(f'  {store}: {count} 条')
            
    def merge_shipping_fees(self) -> None:
        """合并发货面单费数据"""
        self._merge_data(FileType.SHIPPING, '发货面单费')
        
    def merge_return_fees(self) -> None:
        """合并退货面单费数据，区分退至TEMU仓和退至商家仓"""
        start_time = time.time()
        logging.info('开始合并退货面单费数据')
        
        try:
            # 处理退至TEMU仓的数据
            temu_files = self.find_files(FileType.RETURN_TEMU)
            temu_dfs = []
            
            # 处理退至商家仓的数据
            merchant_files = self.find_files(FileType.RETURN_MERCHANT)
            merchant_dfs = []
            
            # 处理未分类的退货面单费文件
            other_files = self.find_files(FileType.RETURN)
            other_dfs = []
            
            # 处理所有文件
            for file_info in temu_files:
                df = self._process_excel_file(file_info)
                if df is not None:
                    df['退货仓库类型'] = 'TEMU仓'
                    temu_dfs.append(df)
                    
            for file_info in merchant_files:
                df = self._process_excel_file(file_info)
                if df is not None:
                    df['退货仓库类型'] = '商家仓'
                    merchant_dfs.append(df)
                    
            for file_info in other_files:
                df = self._process_excel_file(file_info)
                if df is not None:
                    df['退货仓库类型'] = '未分类'
                    other_dfs.append(df)
            
            # 合并所有数据
            all_dfs = temu_dfs + merchant_dfs + other_dfs
            if all_dfs:
                merged_df = pd.concat(all_dfs, ignore_index=True)
                output_path = self.output_dir / f'TEMU退货面单费-{self.task_id}.xlsx'
                merged_df.to_excel(output_path, index=False)
                logging.info(f'退货面单费数据合并完成，总数据量：{len(merged_df)}条')
                logging.info(f'数据已保存至: {output_path}')
                
                # 输出各类型的统计信息
                type_stats = merged_df.groupby('退货仓库类型').size()
                for warehouse_type, count in type_stats.items():
                    logging.info(f'{warehouse_type}退货数据：{count}条')
            else:
                logging.warning('没有找到有效的退货面单费数据文件')
                
        except Exception as e:
            logging.error(f'合并退货面单费数据时发生错误: {str(e)}')
            raise
        finally:
            elapsed_time = time.time() - start_time
            log_success(f'TEMU结算数据处理完成，用时 {elapsed_time:.2f}s')
        
    def merge_settlement_data(self) -> None:
        """合并结算数据"""
        start_time = time.time()
        log_section('开始合并TEMU结算数据')
        
        try:
            files = self.find_files(FileType.SETTLEMENT)
            if not files:
                logging.warning('未找到结算数据文件')
                return
                
            # 按工作表分类存储数据
            sheet_data_dict = {}
            
            # 处理每个文件
            for file_info in files:
                file_sheets = self._process_settlement_file(file_info)
                
                # 合并每个工作表的数据
                for sheet_name, df in file_sheets.items():
                    if sheet_name in sheet_data_dict:
                        sheet_data_dict[sheet_name].append(df)
                    else:
                        sheet_data_dict[sheet_name] = [df]
            
            # 将所有工作表保存到同一个Excel文件中
            if sheet_data_dict:
                output_path = self.output_dir / f'TEMU结算数据-{self.task_id}.xlsx'
                log_step(1, f'创建多工作表Excel文件: {output_path}')
                
                # 创建ExcelWriter对象
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    # 遍历所有工作表，将数据写入各自的sheet
                    sheet_count = 0
                    total_rows = 0
                    
                    for sheet_name, dfs in sheet_data_dict.items():
                        if dfs:
                            sheet_count += 1
                            merged_df = pd.concat(dfs, ignore_index=True)
                            row_count = len(merged_df)
                            total_rows += row_count
                            merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            log_success(f'工作表 {sheet_name} 数据合并完成，共 {row_count} 条数据')
                    
                log_section('TEMU结算数据合并完成')
                log_success(f'共处理 {sheet_count} 个工作表，总数据量 {total_rows} 条')
                log_success(f'所有工作表数据已保存至: {output_path}')
                    
        except Exception as e:
            logging.error(f'合并结算数据时发生错误: {str(e)}')
            raise
        finally:
            elapsed_time = time.time() - start_time
            log_success(f'TEMU结算数据处理完成，用时 {elapsed_time:.2f}s')

    def _process_bill_file(self, file_info: FileInfo) -> Dict[str, pd.DataFrame]:
        """处理对账中心文件
        
        Args:
            file_info: 文件信息
            
        Returns:
            按工作表分类的DataFrame字典
        """
        try:
            excel_file = pd.ExcelFile(file_info.file_path)
            sheet_data = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                df.insert(0, column='店铺', value=file_info.store_name)
                sheet_data[sheet_name] = df
                logging.info(f'处理店铺 {file_info.store_name} 工作表 {sheet_name}: {len(df)} 条')
                
            return sheet_data
        except Exception as e:
            logging.error(f'处理对账中心文件 {file_info.file_path} 失败: {str(e)}')
            return {}
            
    def _process_settlement_file(self, file_info: FileInfo) -> Dict[str, pd.DataFrame]:
        """处理结算数据文件
        
        Args:
            file_info: 文件信息
            
        Returns:
            按工作表分类的DataFrame字典
        """
        try:
            file_path_str = str(file_info.file_path)
            sheet_data = {}
            
            # 提取国家信息
            country = self._extract_country_from_filename(file_info.file_path)
            
            # 处理CSV文件
            if file_path_str.endswith('.csv'):
                try:
                    # 尝试多种编码读取CSV文件
                    try:
                        df = pd.read_csv(file_info.file_path, encoding='utf-8-sig')
                    except UnicodeDecodeError:
                        try:
                            df = pd.read_csv(file_info.file_path, encoding='gbk')
                        except UnicodeDecodeError:
                            try:
                                df = pd.read_csv(file_info.file_path, encoding='gb18030')
                            except UnicodeDecodeError:
                                logging.info(f'尝试使用latin-1编码读取文件: {file_info.file_path.name}')
                                df = pd.read_csv(file_info.file_path, encoding='latin-1')
                    
                    # 添加店铺信息
                    df.insert(0, column='店铺', value=file_info.store_name)
                    
                    # 添加国家信息(如果有)
                    if country:
                        df.insert(1, column='国家', value=country)
                        logging.info(f'将国家信息 [{country}] 添加到结算数据中')
                    
                    # 使用文件名作为工作表名
                    sheet_name = '主表'
                    sheet_data[sheet_name] = df
                    logging.info(f'处理店铺 {file_info.store_name} CSV文件: {len(df)} 条')
                    
                except Exception as csv_e:
                    logging.error(f'处理CSV结算数据文件 {file_info.file_path} 失败: {str(csv_e)}')
            
            # 处理Excel文件
            else:
                excel_file = pd.ExcelFile(file_info.file_path)
                
                for sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    df.insert(0, column='店铺', value=file_info.store_name)
                    
                    # 添加国家信息(如果有)
                    if country:
                        df.insert(1, column='国家', value=country)
                        logging.info(f'将国家信息 [{country}] 添加到结算数据中')
                    
                    sheet_data[sheet_name] = df
                    logging.info(f'处理店铺 {file_info.store_name} 工作表 {sheet_name}: {len(df)} 条')
                
            return sheet_data
        except Exception as e:
            logging.error(f'处理结算数据文件 {file_info.file_path} 失败: {str(e)}')
            return {}
    
    def merge_bill_data(self) -> None:
        """合并对账中心数据"""
        start_time = time.time()
        log_section('开始合并TEMU对账中心数据')
        
        try:
            # 查找对账中心文件
            files = self.find_files(FileType.BILL)
            
            if not files:
                logging.warning('未找到对账中心数据文件')
                return
                
            # 按工作表分类存储数据
            sheet_data = {}
            
            # 处理每个文件
            for file_info in files:
                try:
                    # 处理对账中心文件，返回按工作表分类的数据
                    file_sheets = self._process_bill_file(file_info)
                    
                    if file_sheets:
                        # 合并到总数据中
                        for sheet_name, df in file_sheets.items():
                            if sheet_name in sheet_data:
                                sheet_data[sheet_name].append(df)
                            else:
                                sheet_data[sheet_name] = [df]
                except Exception as e:
                    logging.error(f'处理文件 {file_info.file_path} 时发生错误: {str(e)}')
                    continue
            
            # 创建输出目录
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # 将所有工作表的数据保存到同一个Excel文件中，每个工作表保持原来的名称
            if sheet_data:
                output_path = self.output_dir / f'TEMU对账中心-{self.task_id}.xlsx'
                log_step(1, f'创建多工作表Excel文件: {output_path}')
                
                # 创建ExcelWriter对象
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    # 遍历所有工作表，将数据写入各自的sheet
                    sheet_count = 0
                    total_rows = 0
                    for sheet_name, dfs in sheet_data.items():
                        if dfs:
                            sheet_count += 1
                            merged_df = pd.concat(dfs, ignore_index=True)
                            row_count = len(merged_df)
                            total_rows += row_count
                            merged_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            log_success(f'工作表 {sheet_name} 数据合并完成，共 {row_count} 条数据')
                
                log_section('对账中心数据合并完成')
                log_success(f'共处理 {sheet_count} 个工作表，总数据量 {total_rows} 条')
                log_success(f'所有工作表数据已保存至: {output_path}')
        except Exception as e:
            logging.error(f'合并对账中心数据时发生错误: {str(e)}')
            raise
        finally:
            elapsed_time = time.time() - start_time
            log_success(f'TEMU结算数据处理完成，用时 {elapsed_time:.2f}s')
            
    def _process_excel_file(self, file_info: FileInfo) -> Optional[pd.DataFrame]:
        """处理Excel文件
        
        Args:
            file_info: 文件信息
            
        Returns:
            处理后的DataFrame，如果处理失败返回None
        """
        try:
            # 首先检查Excel文件是否有工作表
            file_path_str = str(file_info.file_path)
            if file_path_str.endswith('.xlsx'):
                excel_file = pd.ExcelFile(file_info.file_path)
                if len(excel_file.sheet_names) == 0:
                    logging.warning(f'文件 {file_info.file_path} 没有工作表，跳过处理')
                    return None


            if file_path_str.endswith('.csv'):
                # 尝试多种编码方式读取CSV文件
                try:
                    df = pd.read_csv(file_info.file_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        # 如果UTF-8编码失败，尝试GBK编码
                        df = pd.read_csv(file_info.file_path, encoding='gbk')
                    except UnicodeDecodeError:
                        try:
                            # 尝试gb18030编码
                            df = pd.read_csv(file_info.file_path, encoding='gb18030')
                        except UnicodeDecodeError:
                            # 最后尝试latin-1编码，它能处理任何8位字符
                            logging.info(f'尝试使用latin-1编码读取文件: {file_info.file_path.name}')
                            df = pd.read_csv(file_info.file_path, encoding='latin-1')
            else:
                df = pd.read_excel(file_info.file_path, engine='openpyxl')
    
                
            df.insert(0, column='店铺', value=file_info.store_name)
            logging.info(f'处理店铺数据：{file_info.store_name}, {len(df)} 条')
            return df
        except Exception as e:
            logging.error(f'处理文件 {file_info.file_path} 失败: {str(e)}')
            return None
    
    def _process_order_file(self, file_info: FileInfo) -> Optional[pd.DataFrame]:
        """处理订单文件
        
        Args:
            file_info: 文件信息
            
        Returns:
            处理后的DataFrame，如果处理失败返回None
        """
        try:
            # 首先检查Excel文件是否有工作表
            file_path_str = str(file_info.file_path)
            if file_path_str.endswith('.xlsx'):
                excel_file = pd.ExcelFile(file_info.file_path)
                if len(excel_file.sheet_names) == 0:
                    logging.warning(f'文件 {file_info.file_path} 没有工作表，跳过处理')
                    return None


            if file_path_str.endswith('.csv'):
                # 尝试多种编码方式读取CSV文件
                try:
                    df = pd.read_csv(file_info.file_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    try:
                        # 如果UTF-8编码失败，尝试GBK编码
                        df = pd.read_csv(file_info.file_path, encoding='gbk')
                    except UnicodeDecodeError:
                        try:
                            # 尝试gb18030编码
                            df = pd.read_csv(file_info.file_path, encoding='gb18030')
                        except UnicodeDecodeError:
                            # 最后尝试latin-1编码，它能处理任何8位字符
                            logging.info(f'尝试使用latin-1编码读取文件: {file_info.file_path.name}')
                            df = pd.read_csv(file_info.file_path, encoding='latin-1')
            else:
                df = pd.read_excel(file_info.file_path, engine='openpyxl')
    
                
            df.insert(0, column='店铺', value=file_info.store_name)
            logging.info(f'处理店铺订单：{file_info.store_name}, {len(df)} 条')
            return df
        except Exception as e:
            logging.error(f'处理订单文件 {file_info.file_path} 失败: {str(e)}')
            return None
            
    def merge_orders(self) -> None:
        """合并订单数据"""
        start_time = time.time()
        logging.info('开始合并订单数据')
        
        try:
            files = self.find_files(FileType.ORDER)
            if not files:
                logging.info('信息: 数据源目录中没有找到订单文件。订单文件应存放在具有"订单导出"字样的目录或文件名中。')
                return
                
            # 处理订单文件
            all_dfs = []
            for file_info in files:
                df = self._process_order_file(file_info)
                if df is not None:
                    all_dfs.append(df)
                    
            if not all_dfs:
                logging.warning('没有成功处理任何订单文件')
                return
                
            # 合并所有数据
            merged_df = pd.concat(all_dfs, ignore_index=True)
            
            # 保存结果
            output_path = self.output_dir / f'TEMU订单数据-{self.task_id}.xlsx'
            merged_df.to_excel(output_path, index=False)
            logging.info(f'订单数据合并完成，总数据量：{len(merged_df)}条')
            logging.info(f'数据已保存至: {output_path}')
            
        except Exception as e:
            logging.error(f'合并订单数据时发生错误: {str(e)}')
            raise
        finally:
            elapsed_time = time.time() - start_time
            logging.info(f'订单数据处理完成，用时 {elapsed_time:.2f}s')
# 获取汇总表头
def get_all_names():
    # 加载列名映射文件
    json_file = Path(__file__).parent / 'country.json'
    if not json_file.exists():
        raise FileNotFoundError(f'列名映射文件不存在: {json_file}')
        
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    return list(json_data.get('US', {}).keys())

# 获取列名映射值
def get_value(country: str, key: str) -> str:
    json_file = Path(__file__).parent / 'country.json'
    if not json_file.exists():
        raise FileNotFoundError(f'列名映射文件不存在: {json_file}')
        
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    return json_data.get(country, {}).get(key, key)
    
def convert_to_numeric(value):
    """将包含逗号的金额字符串转换为数值"""
    if isinstance(value, str):
        # 移除金额符号和空格
        value = value.replace('$', '').replace('£', '').replace('€', '').strip()
        # 移除逗号
        if ',' in value:
            value = value.replace(',', '')
        try:
            return float(value)
        except ValueError:
            return value
    return value

def merge_amazon_orders(source_dir=None, output_dir=None, task_id=None):
    """
    合并亚马逊所有店铺结算数据，从AMZ结算数据文件夹读取各个店铺的CSV文件并合并
    
    Args:
        source_dir: 源数据目录，默认为程序目录下的'数据源/AMZ结算数据'
        output_dir: 输出目录，默认为程序目录下的'处理结果/当前日期/TASK_时间戳'
    """
    # 确保日志配置已完成
    if not logging.getLogger().handlers:
        setup_logging()
        
    log_section('开始亚马逊结算数据处理')
    start_time = time.time()
    store_count = 0
    file_count = 0
    total_rows = 0
    
    try:
        # 初始化数据框
        col_names = get_all_names()
        col_names.extend(['store', 'country'])
        all_data = []
        
        # 确定源数据目录
        if source_dir:
            amz_data_path = Path(source_dir) / 'AMZ结算数据'
        else:
            amz_data_path = Path(__file__).parent / '数据源' / 'AMZ结算数据'
            
        if not amz_data_path.exists():
            raise FileNotFoundError(f'AMZ结算数据文件夹不存在: {amz_data_path}')
            
        store_count = 0
        file_count = 0
        total_rows = 0
        
        for store_dir in amz_data_path.iterdir():
            if not store_dir.is_dir() or store_dir.name.startswith('.'):
                continue
                
            store_count += 1
            store_name = store_dir.name
            log_step(store_count, f'处理店铺：{store_name}')
            
            # 确定店铺所属国家
            store_country = None
            json_file = Path(__file__).parent / 'country.json'
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
                
            for country in json_data.keys():
                if country in store_name:
                    store_country = country
                    break
                    
            if not store_country:
                logging.warning(f'无法确定店铺 {store_name} 的国家/地区，跳过处理')
                continue
                
            # 处理店铺下的所有CSV文件
            for csv_file in store_dir.glob('*.csv'):
                file_count += 1
                logging.info(f'处理文件 {file_count}: {csv_file.name}')
                
                try:
                    # 根据不同地区设置不同的header行数
                    header_index = 6 if 'AE' in store_name else 7
                    
                    # 读取CSV文件
                    try:
                        # 先尝试UTF-8编码
                        df = pd.read_csv(
                            csv_file,
                            header=header_index,
                            encoding='utf-8-sig',
                            on_bad_lines='skip'
                        )
                    except UnicodeDecodeError:
                        try:
                            # 如果UTF-8编码失败，尝试GBK编码
                            df = pd.read_csv(
                                csv_file,
                                header=header_index,
                                encoding='gbk',
                                on_bad_lines='skip'
                            )
                        except UnicodeDecodeError:
                            try:
                                # 尝试gb18030编码
                                df = pd.read_csv(
                                    csv_file,
                                    header=header_index,
                                    encoding='gb18030',
                                    on_bad_lines='skip'
                                )
                            except UnicodeDecodeError:
                                # 最后尝试latin-1编码，它能处理任何8位字符
                                logging.info(f'尝试使用latin-1编码读取文件: {csv_file.name}')
                                df = pd.read_csv(
                                    csv_file,
                                    header=header_index,
                                    encoding='latin-1',
                                    on_bad_lines='skip'
                                )
                    
                    if df.empty:
                        logging.warning(f'文件为空：{csv_file}')
                        continue
                        
                    # 重命名列
                    sheet_keys = list(json_data.get(store_country).keys())
                    rename_dict = {get_value(store_country, key): key for key in sheet_keys}
                    df.rename(columns=rename_dict, inplace=True)
                    
                    # 添加店铺和国家信息到第一和第二列
                    df.insert(0, 'store', store_name)
                    df.insert(1, 'country', store_country)
                    
                    # 转换金额列为数值格式
                    numeric_columns = [
                        'product sales', 'product sales tax', 'shipping credits',
                        'shipping credits tax', 'gift wrap credits', 'giftwrap credits tax',
                        'Regulatory Fee', 'Tax On Regulatory Fee', 'promotional rebates',
                        'promotional rebates tax', 'marketplace withheld tax',
                        'selling fees', 'fba fees', 'other transaction fees',
                        'other', 'total'
                    ]
                    
                    for col in numeric_columns:
                        if col in df.columns:
                            df[col] = df[col].apply(convert_to_numeric)
                    
                    # 记录数据量
                    rows = len(df)
                    total_rows += rows
                    logging.info(f'文件 {csv_file.name} 包含 {rows} 条数据')
                    
                    all_data.append(df)
                    
                except Exception as e:
                    logging.error(f'处理文件 {csv_file} 时出错: {str(e)}')
                    continue
        
        # 合并所有数据
        if not all_data:
            logging.warning('没有找到有效的数据文件')
            return
            
        merged_df = pd.concat(all_data, ignore_index=True)
        
        # 确定输出目录
        if output_dir:
            folder_result = Path(output_dir)
        else:
            # 如果没有提供输出目录，使用默认路径
            timestamp = int(time.time())
            folder_result = Path(__file__).parent / '处理结果' / time.strftime('%Y%m%d') / f'TASK_{timestamp}'
            folder_result.mkdir(parents=True, exist_ok=True)
            
        # 生成输出文件名，使用task_id作为文件名的一部分
        # 如果没有提供task_id，则使用当前时间戳
        if task_id:
            file_id = task_id
        else:
            file_id = int(time.time())
        output_path = folder_result / f'亚马逊结算数据汇总-{file_id}.xlsx'
        merged_df.to_excel(output_path, index=False)
        
        # 输出统计信息
        log_section('亚马逊结算数据处理完成')
        log_success(f'总处理用时：{time.time() - start_time:.2f}秒')
        log_success(f'处理店铺数：{store_count}')
        log_success(f'处理文件数：{file_count}')
        log_success(f'总数据量：{total_rows}条')
        log_success(f'数据已保存至：{output_path}')
        
        # 输出各店铺的数据统计
        store_stats = merged_df.groupby(['store', 'country']).size()
        logging.info('\n各店铺数据统计：')
        for (store, country), count in store_stats.items():
            logging.info(f'{store} ({country}): {count}条')
            
    except Exception as e:
        logging.error(f'合并亚马逊结算数据时发生错误: {str(e)}')
        raise

def display_menu():
    """
    显示主菜单并获取用户选择
    """
    print("\n=== TEMU & Amazon 数据处理系统 ===")
    print("1. 合并亚马逊结算数据")
    print("2. 合并TEMU数据")
    print("3. 合并所有数据")
    print("0. 退出程序")
    print("=============================")
    
    while True:
        try:
            choice = input("\n请选择要执行的功能 (0-3): ")
            if choice in ['0', '1', '2', '3']:
                return choice
            print("无效的选择，请重新输入")
        except KeyboardInterrupt:
            print("\n程序已取消")
            return '0'

def process_data(choice: str):
    """
    根据用户选择执行相应的数据处理功能
    """
    print(f"\n开始执行选项 {choice}...")
    
    if choice == '1':
        print("合并亚马逊结算数据...\n")
        merge_amazon_orders()
    elif choice == '2':
        print("合并TEMU数据...\n")
        processor = TemuDataProcessor()
        processor.process()
    elif choice == '3':
        print("合并所有数据...\n")
        
        # 创建共享的任务ID和输出目录
        today_str = datetime.now().strftime('%Y%m%d')
        task_id = str(int(time.time()))
        output_dir = Path(__file__).parent / '处理结果' / today_str / f'TASK_{task_id}'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志并输出初始信息
        setup_logging(task_dir=output_dir)
        logging.info(f'创建共享输出目录: {output_dir}')
        
        # 先处理亚马逊数据
        print("先处理亚马逊结算数据...\n")
        logging.info('先处理亚马逊结算数据')
        merge_amazon_orders(source_dir=None, output_dir=output_dir, task_id=task_id)
        
        # 再处理TEMU数据
        print("\n再处理TEMU数据...\n")
        logging.info('再处理TEMU数据')
        # 创建CustomTemuDataProcessor实例，传入共享目录
        processor = CustomTemuDataProcessor(source_dir=Path(__file__).parent / '数据源', 
                                       output_dir=output_dir, 
                                       task_id=task_id)
        processor.process()
        
        # 输出处理完成信息
        logging.info(f'所有数据已保存至: {output_dir}')
    
    print("\n处理完成!")

if __name__ == '__main__':
    try:
        # 检查并安装必要的包
        install_required_packages()
        
        # 设置日志记录
        setup_logging()
        
        while True:
            choice = display_menu()
            
            if choice == '0':
                print("\n程序已退出")
                break
                
            process_data(choice)
            
            # 询问是否继续
            continue_choice = input("\n是否继续处理其他数据？(y/n): ").lower()
            if continue_choice != 'y':
                print("\n程序已退出")
                break
                
    except KeyboardInterrupt:
        print("\n程序已被用户中断")
    except Exception as e:
        logging.error(f"程序执行出错: {str(e)}")
        raise        # processor.merge_return_fees()
        
        # # 处理结算数据
        # processor.merge_settlement_data()
        
        # 处理亚马逊数据
        merge_amazon_orders()
    except Exception as e:
        logging.error(f"处理失败: {e}")
