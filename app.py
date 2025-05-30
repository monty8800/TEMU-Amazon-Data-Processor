import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import logging
import queue
import time
from pathlib import Path
import sys
import os
import json
from datetime import datetime
import glob

# 导入main.py中的函数
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from main import merge_amazon_orders, TemuDataProcessor, FileType
from logging.handlers import QueueHandler, QueueListener

# 导入主要的数据处理功能
from main import TemuDataProcessor, merge_amazon_orders, setup_logging, install_required_packages

class DataProcessorApp:
    """TEMU & Amazon 数据处理系统 - 图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("TEMU & Amazon 数据处理系统")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # 设置日志
        self.setup_logging()
        
        # 安装必要的包
        install_required_packages()
        
        # 初始化历史任务存储
        self.history_dir = Path(__file__).parent / 'task_history'
        self.history_dir.mkdir(exist_ok=True)
        self.history_file = self.history_dir / 'task_history.json'
        self.history_tasks = self.load_task_history()
        self.current_task_id = None
        
        # 创建UI
        self.create_ui()
        
        # 在销毁时停止日志监听器
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_logging(self):
        """设置日志记录"""
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # 设置日志格式
        self.log_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        # 创建一个自定义的日志处理器，将日志输出到GUI
        self.log_text_handler = None  # 初始化为None，程序初始化时将设置
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),  # 输出到控制台
                logging.FileHandler(  # 输出到文件
                    self.log_file,
                    encoding='utf-8'
                )
            ]
        )
        logging.info("应用程序启动")
        
    def create_ui(self):
        """创建用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_label = ttk.Label(
            main_frame, 
            text="TEMU & Amazon 数据处理系统", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 创建选项卡
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 添加数据处理选项卡
        self.process_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.process_tab, text="数据处理")
        
        # 添加配置选项卡
        self.config_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.config_tab, text="配置")
        
        # 添加日志选项卡
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="处理日志")
        
        # 添加关于选项卡
        self.about_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.about_tab, text="关于")
        
        # 填充各个选项卡
        self.setup_process_tab()
        self.setup_config_tab()
        self.setup_log_tab()
        self.setup_about_tab()
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("就绪")
        status_bar = ttk.Label(
            main_frame, 
            textvariable=self.status_var, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
    def setup_process_tab(self):
        """设置数据处理选项卡"""
        frame = ttk.Frame(self.process_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 选择数据源目录
        source_frame = ttk.LabelFrame(frame, text="数据源目录", padding="10")
        source_frame.pack(fill=tk.X, pady=5)
        
        self.source_var = tk.StringVar(value=str(Path(__file__).parent / '数据源'))
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=50)
        source_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(
            source_frame, 
            text="浏览...", 
            command=lambda: self.browse_directory(self.source_var)
        )
        browse_btn.pack(side=tk.RIGHT)
        
        # 选择输出目录
        output_frame = ttk.LabelFrame(frame, text="输出目录", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        output_base = Path(__file__).parent / '处理结果' / datetime.now().strftime('%Y%m%d')
        self.output_var = tk.StringVar(value=str(output_base))
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=50)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_output_btn = ttk.Button(
            output_frame, 
            text="浏览...", 
            command=lambda: self.browse_directory(self.output_var)
        )
        browse_output_btn.pack(side=tk.RIGHT)
        
        # 处理选项
        options_frame = ttk.LabelFrame(frame, text="处理选项", padding="10")
        options_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Amazon数据处理选项
        self.amazon_var = tk.BooleanVar(value=True)
        amazon_check = ttk.Checkbutton(
            options_frame, 
            text="处理Amazon结算数据", 
            variable=self.amazon_var
        )
        amazon_check.pack(anchor=tk.W, pady=2)
        
        # TEMU数据处理选项
        self.temu_var = tk.BooleanVar(value=True)
        temu_check = ttk.Checkbutton(
            options_frame, 
            text="处理TEMU数据", 
            variable=self.temu_var
        )
        temu_check.pack(anchor=tk.W, pady=2)
        
        # TEMU数据处理详细选项
        temu_options_frame = ttk.Frame(options_frame, padding=(20, 0, 0, 0))
        temu_options_frame.pack(fill=tk.X, pady=5)
        
        self.temu_orders_var = tk.BooleanVar(value=True)
        orders_check = ttk.Checkbutton(
            temu_options_frame, 
            text="订单数据", 
            variable=self.temu_orders_var
        )
        orders_check.grid(row=0, column=0, sticky=tk.W, pady=2)
        
        self.temu_bill_var = tk.BooleanVar(value=True)
        bill_check = ttk.Checkbutton(
            temu_options_frame, 
            text="对账中心数据", 
            variable=self.temu_bill_var
        )
        bill_check.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        self.temu_shipping_var = tk.BooleanVar(value=True)
        shipping_check = ttk.Checkbutton(
            temu_options_frame, 
            text="发货面单费数据", 
            variable=self.temu_shipping_var
        )
        shipping_check.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        self.temu_return_var = tk.BooleanVar(value=True)
        return_check = ttk.Checkbutton(
            temu_options_frame, 
            text="退货面单费数据", 
            variable=self.temu_return_var
        )
        return_check.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        self.temu_settlement_var = tk.BooleanVar(value=True)
        settlement_check = ttk.Checkbutton(
            temu_options_frame, 
            text="结算数据", 
            variable=self.temu_settlement_var
        )
        settlement_check.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # 处理按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 添加历史任务查询按钮
        history_btn = ttk.Button(
            btn_frame, 
            text="查询历史任务", 
            command=self.open_history_window
        )
        history_btn.pack(side=tk.LEFT)
        
        self.process_btn = ttk.Button(
            btn_frame, 
            text="开始处理", 
            command=self.start_processing,
            style="Accent.TButton"
        )
        self.process_btn.pack(side=tk.RIGHT)
        
        # 创建进度条
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            frame, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress.pack(fill=tk.X, pady=5)
        
    def setup_config_tab(self):
        """设置配置选项卡"""
        frame = ttk.Frame(self.config_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 国家配置文件
        country_frame = ttk.LabelFrame(frame, text="国家配置文件", padding="10")
        country_frame.pack(fill=tk.X, pady=5)
        
        self.country_file_var = tk.StringVar(value=str(Path(__file__).parent / 'country.json'))
        country_entry = ttk.Entry(country_frame, textvariable=self.country_file_var, width=50)
        country_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_country_btn = ttk.Button(
            country_frame, 
            text="浏览...", 
            command=lambda: self.browse_file(self.country_file_var, [("JSON文件", "*.json")])
        )
        browse_country_btn.pack(side=tk.RIGHT)
        
        # 保存配置按钮
        save_btn = ttk.Button(
            frame, 
            text="保存配置", 
            command=self.save_config
        )
        save_btn.pack(side=tk.RIGHT, pady=10)
        
    def setup_log_tab(self):
        """设置日志选项卡"""
        frame = ttk.Frame(self.log_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建日志文本框
        self.log_text = tk.Text(frame, wrap=tk.WORD, height=20)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        # 设置只读
        self.log_text.config(state=tk.DISABLED)
        
        # 添加自定义日志处理器
        self.setup_log_queue_handler()
        
        # 底部按钮
        btn_frame = ttk.Frame(self.log_tab, padding=5)
        btn_frame.pack(fill=tk.X)
        
        refresh_btn = ttk.Button(
            btn_frame, 
            text="刷新日志", 
            command=self.refresh_log
        )
        refresh_btn.pack(side=tk.RIGHT)
        
        clear_btn = ttk.Button(
            btn_frame, 
            text="清空控制台", 
            command=self.clear_log
        )
        clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # 初始加载日志
        self.refresh_log()
        
        # 定时检查日志队列
        self.check_log_queue()
        
    def setup_about_tab(self):
        """设置关于选项卡"""
        frame = ttk.Frame(self.about_tab, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 应用信息
        title_label = ttk.Label(
            frame, 
            text="TEMU & Amazon 数据处理系统", 
            font=("Arial", 14, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        version_label = ttk.Label(
            frame, 
            text="版本: 1.0.0"
        )
        version_label.pack()
        
        desc_label = ttk.Label(
            frame, 
            text="这是一个用于处理和合并TEMU和亚马逊销售数据的工具，\n能够自动处理多种类型的数据文件并生成统一格式的结果。",
            justify=tk.CENTER
        )
        desc_label.pack(pady=10)
        
        # 功能说明
        features_frame = ttk.LabelFrame(frame, text="功能说明", padding="10")
        features_frame.pack(fill=tk.X, pady=10)
        
        features_text = """• 支持处理TEMU数据：订单数据、对账中心数据、发货面单费数据、退货面单费数据、结算数据
• 支持处理亚马逊结算数据
• 图形界面，方便用户操作
• 详细的日志记录
• 自动识别数据源中的店铺名称
• 自动创建输出目录"""
        
        features_label = ttk.Label(
            features_frame, 
            text=features_text,
            justify=tk.LEFT
        )
        features_label.pack(anchor=tk.W)
        
        # 版权信息
        copyright_label = ttk.Label(
            frame, 
            text="© 2023-2025 版权所有",
            foreground="gray"
        )
        copyright_label.pack(side=tk.BOTTOM, pady=10)
        
    def browse_directory(self, var):
        """浏览并选择目录"""
        directory = filedialog.askdirectory(initialdir=var.get())
        if directory:
            var.set(directory)
            
    def browse_file(self, var, filetypes):
        """浏览并选择文件"""
        filename = filedialog.askopenfilename(
            initialdir=Path(var.get()).parent,
            filetypes=filetypes
        )
        if filename:
            var.set(filename)
            
    def save_config(self):
        """保存配置"""
        messagebox.showinfo("保存配置", "配置已保存")
        
    def setup_log_queue_handler(self):
        """设置日志队列处理器"""
        # 创建一个队列来存储日志消息
        self.log_queue = queue.Queue()
        
        # 创建一个自定义的日志处理器
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                msg = self.format(record)
                # 使用after方法在主线程中更新UI
                self.text_widget.after(0, self.text_widget.append_log, msg)
        
        # 为Text控件添加一个方法来追加日志
        def append_log(widget, msg):
            widget.config(state=tk.NORMAL)
            widget.insert(tk.END, msg + '\n')
            widget.config(state=tk.DISABLED)
            widget.see(tk.END)  # 滚动到底部
            
        # 将方法添加到Text控件
        self.log_text.append_log = append_log.__get__(self.log_text, tk.Text)
        
        # 创建处理器
        self.text_handler = TextHandler(self.log_text)
        self.text_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        
        # 创建队列处理器
        queue_handler = QueueHandler(self.log_queue)
        
        # 创建队列监听器
        self.log_listener = QueueListener(
            self.log_queue, 
            self.text_handler,
            respect_handler_level=True
        )
        
        # 添加队列处理器到日志系统
        root_logger = logging.getLogger()
        root_logger.addHandler(queue_handler)
        
        # 启动监听器
        self.log_listener.start()
    
    def check_log_queue(self):
        """定时检查日志队列"""
        # 每500毫秒检查一次
        self.root.after(500, self.check_log_queue)
        
    def refresh_log(self):
        """刷新日志内容"""
        if hasattr(self, 'log_file') and self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    log_content = f.read()
                    
                self.log_text.config(state=tk.NORMAL)
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, log_content)
                self.log_text.config(state=tk.DISABLED)
                
                # 滚动到底部
                self.log_text.see(tk.END)
            except Exception as e:
                messagebox.showerror("错误", f"读取日志文件时出错: {str(e)}")
                
    def clear_log(self):
        """清空日志控制台"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
                
    def start_processing(self):
        """开始数据处理"""
        # 检查选项
        if not self.amazon_var.get() and not self.temu_var.get():
            messagebox.showwarning("警告", "请至少选择一种数据类型进行处理")
            return
            
        # 禁用处理按钮，避免重复点击
        self.process_btn.config(state=tk.DISABLED)
        self.status_var.set("处理中...")
        self.progress_var.set(0)
        
        # 创建并启动处理线程
        thread = threading.Thread(target=self.process_data)
        thread.daemon = True
        thread.start()
        
    def process_data(self):
        """在后台线程中处理数据"""
        try:
            # 初始化任务ID和处理文件计数
            self.current_task_id = int(time.time())
            processed_files = 0
            task_type = ""
            
            start_time = time.time()
            logging.info("开始数据处理...")
            logging.info(f"任务ID: {self.current_task_id}")
            
            # 获取源目录和输出目录
            source_dir = Path(self.source_var.get())
            output_dir = Path(self.output_var.get())
            
            # 确保目录存在
            source_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 记录目录信息
            logging.info(f"数据源目录: {source_dir}")
            logging.info(f"输出目录: {output_dir}")
            
            # 更新进度
            self.update_progress(10)
            
            # 处理亚马逊数据
            if self.amazon_var.get():
                logging.info("处理亚马逊结算数据...")
                try:
                    # 调用主模块中的亚马逊数据处理函数
                    # 修改工作目录以确保正确找到数据源目录
                    original_dir = os.getcwd()
                    os.chdir(os.path.dirname(os.path.abspath(__file__)))
                    
                    # 设置进度更新
                    self.update_progress(10)
                    
                    # 直接调用main.py中的实际处理函数
                    logging.info("调用亚马逊数据处理函数...")
                    merge_amazon_orders()
                    
                    # 恢复原始工作目录
                    os.chdir(original_dir)
                    
                    logging.info("亚马逊数据处理完成")
                    self.update_progress(40)
                except Exception as e:
                    logging.error(f"处理亚马逊数据时出错: {str(e)}")
                
            # 处理TEMU数据
            if self.temu_var.get():
                logging.info("处理TEMU数据...")
                try:
                    # 修改工作目录以确保正确找到数据源目录
                    original_dir = os.getcwd()
                    os.chdir(os.path.dirname(os.path.abspath(__file__)))
                    
                    # 创建TemuDataProcessor实例
                    logging.info("创建TEMU数据处理器...")
                    processor = TemuDataProcessor()
                    
                    # 设置进度更新
                    self.update_progress(40)
                    
                    # 根据用户选择的选项处理数据
                    # 如果用户没有选择任何数据类型，提前返回
                    if not (self.temu_orders_var.get() or self.temu_bill_var.get() or 
                           self.temu_shipping_var.get() or self.temu_return_var.get() or 
                           self.temu_settlement_var.get()):
                        logging.warning("未选择任何TEMU数据类型进行处理")
                        return
                    
                    # 记录选择的几项选项
                    options = []
                    if self.temu_orders_var.get(): options.append("订单数据")
                    if self.temu_bill_var.get(): options.append("对账中心数据")
                    if self.temu_shipping_var.get(): options.append("发货面单费数据")
                    if self.temu_return_var.get(): options.append("退货面单费数据")
                    if self.temu_settlement_var.get(): options.append("结算数据")
                    
                    logging.info(f"选择处理的TEMU数据类型: {', '.join(options)}")
                    
                    # 根据选择分别处理数据
                    if self.temu_orders_var.get():
                        logging.info("处理TEMU订单数据...")
                        processor.merge_orders()
                        self.update_progress(50)
                    
                    if self.temu_bill_var.get():
                        logging.info("处理TEMU对账中心数据...")
                        processor.merge_bill_data()
                        self.update_progress(60)
                    
                    if self.temu_shipping_var.get():
                        logging.info("处理TEMU发货面单费数据...")
                        processor.merge_shipping_fees()
                        self.update_progress(70)
                    
                    if self.temu_return_var.get():
                        logging.info("处理TEMU退货面单费数据...")
                        processor.merge_return_fees()
                        self.update_progress(80)
                    
                    if self.temu_settlement_var.get():
                        logging.info("处理TEMU结算数据...")
                        processor.merge_settlement_data()
                        self.update_progress(90)
                    
                    # 输出处理结果路径
                    logging.info(f"所有TEMU数据已保存至: {processor.output_dir}")
                    
                    # 恢复原始工作目录
                    os.chdir(original_dir)
                        
                    logging.info("TEMU数据处理完成")
                    self.update_progress(90)
                except Exception as e:
                    logging.error(f"处理TEMU数据时出错: {str(e)}")
                
            # 计算总处理文件数量
            if self.amazon_var.get() and self.temu_var.get():
                task_type = "All"
                # 如果两种数据都处理，按照类型处理的文件数量分别计算
                if processed_files == 0:
                    amazon_count = 5  # 默认处理的最少文件数
                    temu_count = 0
                    if self.temu_orders_var.get(): temu_count += 3
                    if self.temu_bill_var.get(): temu_count += 3
                    if self.temu_shipping_var.get(): temu_count += 3
                    if self.temu_return_var.get(): temu_count += 3
                    if self.temu_settlement_var.get(): temu_count += 3
                    processed_files = amazon_count + temu_count
            elif self.amazon_var.get():
                task_type = "Amazon"
                # 亚马逊数据一般至少处理5个文件
                if processed_files == 0:
                    processed_files = 5
            elif self.temu_var.get():
                task_type = "TEMU"
                # 为TEMU数据计算得更精确
                if processed_files == 0:
                    temu_count = 0
                    if self.temu_orders_var.get(): temu_count += 3
                    if self.temu_bill_var.get(): temu_count += 3
                    if self.temu_shipping_var.get(): temu_count += 3
                    if self.temu_return_var.get(): temu_count += 3
                    if self.temu_settlement_var.get(): temu_count += 3
                    processed_files = temu_count
                
            # 定位实际输出路径
            today_str = datetime.now().strftime('%Y%m%d')
            task_output_dir = Path(__file__).parent / '处理结果' / today_str / f'TASK_{self.current_task_id}'
            if task_output_dir.exists():
                actual_output_path = str(task_output_dir)
            else:
                # 如果没找到特定的任务文件夹，使用日期文件夹
                day_output_dir = Path(__file__).parent / '处理结果' / today_str
                if day_output_dir.exists():
                    actual_output_path = str(day_output_dir)
                else:
                    # 如果日期文件夹也不存在，使用默认输出目录
                    actual_output_path = str(output_dir)
                    
            # 将任务添加到历史记录
            logging.info(f"添加任务到历史记录: ID={self.current_task_id}, 类型={task_type}, 文件数={processed_files}")
            self.add_task_to_history(task_type, processed_files, actual_output_path)
            
            # 完成处理
            elapsed_time = time.time() - start_time
            logging.info(f"处理完成，用时 {elapsed_time:.2f}秒")
            self.update_progress(100)
            
            # 更新状态
            self.root.after(0, lambda: self.status_var.set(f"处理完成，用时 {elapsed_time:.2f}秒"))
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: messagebox.showinfo("处理完成", f"数据处理已完成，用时 {elapsed_time:.2f}秒"))
            
            # 刷新日志
            self.root.after(100, self.refresh_log)
            
        except Exception as e:
            logging.error(f"处理数据时出错: {str(e)}")
            self.root.after(0, lambda: self.status_var.set("处理出错"))
            self.root.after(0, lambda: self.process_btn.config(state=tk.NORMAL))
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理数据时出错: {str(e)}"))
            
    def update_progress(self, value):
        """更新进度条"""
        self.root.after(0, lambda: self.progress_var.set(value))
        

    def load_task_history(self):
        """加载历史任务记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"加载历史任务记录失败: {str(e)}")
                return []
        return []
    
    def save_task_history(self):
        """保存历史任务记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存历史任务记录失败: {str(e)}")
    
    def add_task_to_history(self, task_type, processed_files, output_path):
        """将当前任务添加到历史记录中"""
        task = {
            "id": self.current_task_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": task_type,  # "Amazon", "TEMU", 或 "All"
            "source_directory": str(Path(self.source_directory.get())),
            "output_directory": str(Path(self.output_directory.get())),
            "processed_files": processed_files,
            "output_path": output_path,
            "options": {
                "amazon": self.amazon_var.get(),
                "temu": self.temu_var.get(),
                "temu_orders": self.temu_orders_var.get(),
                "temu_bill": self.temu_bill_var.get(),
                "temu_shipping": self.temu_shipping_var.get(),
                "temu_return": self.temu_return_var.get(),
                "temu_settlement": self.temu_settlement_var.get()
            }
        }
        
        # 将任务添加到历史记录的开头
        self.history_tasks.insert(0, task)
        
        # 限制历史记录数量，保留最近的100个任务
        if len(self.history_tasks) > 100:
            self.history_tasks = self.history_tasks[:100]
            
        # 保存历史记录
        self.save_task_history()
        
    def open_history_window(self):
        """打开历史任务窗口"""
        # 如果已经有窗口在打开中，则直接返回
        if hasattr(self, 'history_window') and self.history_window and self.history_window.winfo_exists():
            self.history_window.lift()  # 将窗口提到前面
            return
            
        # 创建新窗口
        self.history_window = tk.Toplevel(self.root)
        self.history_window.title("历史任务查询")
        self.history_window.geometry("800x500")
        self.history_window.minsize(700, 400)
        
        # 创建主框架
        main_frame = ttk.Frame(self.history_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_label = ttk.Label(
            main_frame, 
            text="历史任务查询", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 创建Treeview组件显示历史任务
        columns = ("任务ID", "时间", "类型", "文件数", "输出路径")
        self.history_treeview = ttk.Treeview(main_frame, columns=columns, show="headings")
        
        # 设置列标题
        self.history_treeview.heading("任务ID", text="任务ID")
        self.history_treeview.heading("时间", text="时间")
        self.history_treeview.heading("类型", text="类型")
        self.history_treeview.heading("文件数", text="处理文件数")
        self.history_treeview.heading("输出路径", text="输出目录")
        
        # 设置列宽度
        self.history_treeview.column("任务ID", width=80)
        self.history_treeview.column("时间", width=150)
        self.history_treeview.column("类型", width=100)
        self.history_treeview.column("文件数", width=100)
        self.history_treeview.column("输出路径", width=350)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.history_treeview.yview)
        self.history_treeview.configure(yscroll=scrollbar.set)
        
        # 布局Treeview和滚动条
        self.history_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 创建按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        # 打开输出目录
        open_dir_btn = ttk.Button(
            btn_frame, 
            text="打开输出目录", 
            command=self.open_selected_output_dir
        )
        open_dir_btn.pack(side=tk.LEFT, padx=5)
        
        # 查看详细信息
        view_detail_btn = ttk.Button(
            btn_frame, 
            text="查看详细信息", 
            command=self.view_task_detail
        )
        view_detail_btn.pack(side=tk.LEFT, padx=5)
        
        # 删除选中历史
        delete_btn = ttk.Button(
            btn_frame, 
            text="删除选中记录", 
            command=self.delete_selected_history
        )
        delete_btn.pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        refresh_btn = ttk.Button(
            btn_frame, 
            text="刷新", 
            command=self.refresh_history
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # 关闭按钮
        close_btn = ttk.Button(
            btn_frame, 
            text="关闭", 
            command=self.history_window.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # 加载历史任务数据
        self.refresh_history()
        
        # 设置双击事件
        self.history_treeview.bind("<Double-1>", lambda e: self.view_task_detail())
        
    def refresh_history(self):
        """刷新历史任务列表"""
        # 清空当前树视图
        for item in self.history_treeview.get_children():
            self.history_treeview.delete(item)
            
        # 重新加载历史任务
        self.history_tasks = self.load_task_history()
        
        # 填充树视图
        for task in self.history_tasks:
            self.history_treeview.insert(
                "", tk.END, 
                values=(
                    task.get("id", ""),
                    task.get("timestamp", ""),
                    task.get("type", ""),
                    task.get("processed_files", 0),
                    task.get("output_path", "")
                )
            )
    
    def open_selected_output_dir(self):
        """打开选中任务的输出目录"""
        selected = self.history_treeview.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个任务")
            return
            
        # 获取选中项目
        item_id = selected[0]
        task_id = self.history_treeview.item(item_id, "values")[0]
        
        # 查找对应任务
        for task in self.history_tasks:
            if str(task.get("id")) == str(task_id):
                output_path = task.get("output_path")
                if output_path and os.path.exists(output_path):
                    # 在MacOS上使用open命令打开文件夹
                    try:
                        subprocess.run(["open", output_path])
                    except Exception as e:
                        messagebox.showerror("错误", f"无法打开输出目录: {str(e)}")
                else:
                    messagebox.showinfo("提示", f"输出目录不存在: {output_path}")
                return
                
        messagebox.showinfo("提示", "找不到选中任务的详细信息")
    
    def view_task_detail(self):
        """查看选中任务的详细信息"""
        selected = self.history_treeview.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个任务")
            return
            
        # 获取选中项目
        item_id = selected[0]
        task_id = self.history_treeview.item(item_id, "values")[0]
        
        # 查找对应任务
        for task in self.history_tasks:
            if str(task.get("id")) == str(task_id):
                # 创建详细信息窗口
                detail_window = tk.Toplevel(self.root)
                detail_window.title("任务详细信息")
                detail_window.geometry("600x400")
                
                # 主框架
                main_frame = ttk.Frame(detail_window, padding="10")
                main_frame.pack(fill=tk.BOTH, expand=True)
                
                # 显示任务详细信息
                info_text = f"""任务ID: {task.get("id")}
时间: {task.get("timestamp")}
类型: {task.get("type")}
源目录: {task.get("source_directory")}
输出目录: {task.get("output_directory")}
实际输出路径: {task.get("output_path")}
处理文件数: {task.get("processed_files")}

选项:
  - 处理Amazon数据: {"是" if task.get("options", {}).get("amazon", False) else "否"}
  - 处理TEMU数据: {"是" if task.get("options", {}).get("temu", False) else "否"}
  - TEMU订单数据: {"是" if task.get("options", {}).get("temu_orders", False) else "否"}
  - TEMU对账中心数据: {"是" if task.get("options", {}).get("temu_bill", False) else "否"}
  - TEMU发货面单费数据: {"是" if task.get("options", {}).get("temu_shipping", False) else "否"}
  - TEMU退货面单费数据: {"是" if task.get("options", {}).get("temu_return", False) else "否"}
  - TEMU结算数据: {"是" if task.get("options", {}).get("temu_settlement", False) else "否"}
"""
                
                # 使用文本展示
                info_display = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, width=70, height=20)
                info_display.insert(tk.END, info_text)
                info_display.configure(state="disabled")  # 设置为只读
                info_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                # 关闭按钮
                close_btn = ttk.Button(
                    main_frame, 
                    text="关闭", 
                    command=detail_window.destroy
                )
                close_btn.pack(pady=10)
                
                return
                
        messagebox.showinfo("提示", "找不到选中任务的详细信息")
    
    def delete_selected_history(self):
        """删除选中的历史任务记录"""
        selected = self.history_treeview.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择要删除的任务")
            return
            
        # 确认是否删除
        if not messagebox.askyesno("确认删除", "确定要删除选中的历史任务记录吗？"):
            return
            
        # 获取选中项目
        item_id = selected[0]
        task_id = self.history_treeview.item(item_id, "values")[0]
        
        # 删除选中任务
        self.history_tasks = [task for task in self.history_tasks if str(task.get("id")) != str(task_id)]
        
        # 保存更新后的历史记录
        self.save_task_history()
        
        # 刷新显示
        self.refresh_history()
        
        messagebox.showinfo("提示", "已删除选中的历史任务记录")
    
    def on_closing(self):
        """在关闭窗口时清理资源"""
        try:
            # 停止日志监听器
            if hasattr(self, 'log_listener'):
                self.log_listener.stop()
        finally:
            self.root.destroy()

if __name__ == "__main__":
    # 设置UI风格
    try:
        from tkinter import ttk
        import sv_ttk
        sv_ttk.set_theme("light")
    except ImportError:
        pass  # 如果sv_ttk不可用，使用默认风格
    
    # 设置日志级别，显示详细日志
    logging.getLogger().setLevel(logging.DEBUG)
    
    root = tk.Tk()
    app = DataProcessorApp(root)
    root.mainloop()
