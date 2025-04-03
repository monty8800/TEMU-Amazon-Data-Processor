import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import logging
import logging.handlers  # 添加正确的导入
import queue
import time
import os
import sys
import json  # 导入json用于处理配置和数据
from pathlib import Path
from datetime import datetime

# 导入main.py中的处理函数
from main import TemuDataProcessor, merge_amazon_orders, setup_logging, install_required_packages

# 创建自定义的TemuDataProcessor类，允许指定源目录和输出目录
class CustomTemuDataProcessor(TemuDataProcessor):
    """自定义TEMU数据处理器，支持自定义源目录和输出目录"""
    
    def __init__(self, source_dir, output_dir):
        # 不直接调用父类的__init__，而是手动初始化需要的属性
        # 确保日志配置已完成
        if not logging.getLogger().handlers:
            from main import setup_logging
            setup_logging()
        
        # 设置源目录和输出目录
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        
        # 复用现有任务ID，这样可以直接在现有目录中运行
        self.task_id = os.path.basename(output_dir).replace('TASK_', '') if 'TASK_' in output_dir else str(int(time.time()))
        
        # 初始化目录，只创建需要的子目录，而不创建任务目录本身
        self._init_directories()

class SimpleDataProcessorApp:
    """简化版TEMU & Amazon 数据处理系统 - 图形界面"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("TEMU & Amazon 数据处理工具 - 简化版")
        # self.root.geometry("700x500")
        self.root.minsize(700, 750)
        
        # 使窗口在屏幕中心显示
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 750) // 2
        self.root.geometry(f'700x750+{x}+{y}')
        
        # 设置防止重复处理的标志
        self.processing_active = False
        # 当前任务ID
        self.current_task_id = None
        self.current_task_dir = None
        
        # 设置日志
        self.setup_logging()
        
        # 确保必要的包已安装
        install_required_packages()
        
        # 创建UI
        self.create_ui()
        
        # 在销毁窗口时停止日志监听器
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_logging(self):
        """设置日志记录"""
        # 创建日志目录
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        # 设置日志文件路径
        self.log_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        # 创建日志队列
        self.log_queue = queue.Queue()
        
        # 设置日志格式
        self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 配置根日志记录器
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # 清除现有处理器以避免重复
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # 添加控制台处理器
        console = logging.StreamHandler()
        console.setFormatter(self.formatter)
        logger.addHandler(console)
        
        # 添加主日志文件处理器
        self.main_file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        self.main_file_handler.setFormatter(self.formatter)
        logger.addHandler(self.main_file_handler)
        
        # 添加队列处理器用于GUI显示
        queue_handler = logging.handlers.QueueHandler(self.log_queue)
        queue_handler.setFormatter(self.formatter)
        logger.addHandler(queue_handler)
        
        # 保存任务日志处理器引用，方便后续删除
        self.task_log_handler = None
        
        logging.info("日志系统初始化完成")
    
    def add_task_log_handler(self, log_file):
        """添加任务特定的日志处理器"""
        logger = logging.getLogger()
        
        # 如果已经有任务日志处理器，先移除
        if self.task_log_handler:
            logger.removeHandler(self.task_log_handler)
            self.task_log_handler = None
        
        # 创建新的任务日志处理器
        try:
            self.task_log_handler = logging.FileHandler(log_file, encoding='utf-8')
            self.task_log_handler.setFormatter(self.formatter)
            logger.addHandler(self.task_log_handler)
            logging.info(f"开始将日志保存到任务目录: {log_file}")
        except Exception as e:
            logging.warning(f"添加任务日志处理器失败: {str(e)}")
        
    def create_ui(self):
        """创建用户界面"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标题
        title_label = ttk.Label(
            self.main_frame, 
            text="TEMU & Amazon 数据处理工具", 
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # 创建目录选择框架
        dir_frame = ttk.LabelFrame(self.main_frame, text="目录设置", padding="10")
        dir_frame.pack(fill=tk.X, pady=10)
        
        # 加载上次的目录设置
        config = self.load_config()
        
        # 源目录选择
        source_frame = ttk.Frame(dir_frame)
        source_frame.pack(fill=tk.X, pady=5)
        
        source_label = ttk.Label(source_frame, text="源文件目录:", width=10)
        source_label.pack(side=tk.LEFT, padx=5)
        
        # 使用上次的源目录或默认目录
        default_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), '数据源')
        saved_source = config.get('last_source_dir', '')
        if saved_source and os.path.exists(saved_source):
            default_source = saved_source
        
        self.source_var = tk.StringVar(value=default_source)
        source_entry = ttk.Entry(source_frame, textvariable=self.source_var, width=50)
        source_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        source_btn = ttk.Button(
            source_frame, 
            text="浏览...", 
            command=self.browse_source_dir,
            width=8
        )
        source_btn.pack(side=tk.LEFT, padx=5)
        
        # 输出目录选择
        output_frame = ttk.Frame(dir_frame)
        output_frame.pack(fill=tk.X, pady=5)
        
        output_label = ttk.Label(output_frame, text="输出目录:", width=10)
        output_label.pack(side=tk.LEFT, padx=5)
        
        # 使用上次的输出目录或默认目录
        default_output = os.path.join(os.path.dirname(os.path.abspath(__file__)), '处理结果')
        saved_output = config.get('last_output_dir', '')
        if saved_output and os.path.exists(saved_output):
            default_output = saved_output
            
        self.output_var = tk.StringVar(value=default_output)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_var, width=50)
        output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        output_btn = ttk.Button(
            output_frame, 
            text="浏览...", 
            command=self.browse_output_dir,
            width=8
        )
        output_btn.pack(side=tk.LEFT, padx=5)
        
        # 创建主数据类型选择框架
        type_frame = ttk.LabelFrame(self.main_frame, text="数据类型选择", padding="10")
        type_frame.pack(fill=tk.X, pady=10)
        
        # 创建两个子框架
        amazon_frame = ttk.LabelFrame(type_frame, text="Amazon数据", padding="8")
        amazon_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        temu_frame = ttk.LabelFrame(type_frame, text="TEMU数据", padding="8")
        temu_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        # 配置列宽度，使两个框架大小相等
        type_frame.columnconfigure(0, weight=1)
        type_frame.columnconfigure(1, weight=1)
        
        # Amazon数据处理选项
        self.amazon_var = tk.BooleanVar(value=True)
        amazon_check = ttk.Checkbutton(
            amazon_frame, 
            text="处理Amazon数据", 
            variable=self.amazon_var,
            style="Bold.TCheckbutton"
        )
        amazon_check.pack(pady=5, padx=5, anchor="w")
        
        # 未来可以在此添加Amazon数据的子选项
        ttk.Label(amazon_frame, text="将处理所有Amazon结算数据", foreground="#555555").pack(pady=5, padx=5, anchor="w")
        
        # TEMU数据处理选项
        self.temu_var = tk.BooleanVar(value=True)
        temu_check = ttk.Checkbutton(
            temu_frame, 
            text="处理TEMU数据", 
            variable=self.temu_var,
            command=self.toggle_temu_options,
            style="Bold.TCheckbutton"
        )
        temu_check.pack(pady=5, padx=5, anchor="w")
        
        # TEMU数据细分选项框架
        temu_options_frame = ttk.Frame(temu_frame)
        temu_options_frame.pack(fill=tk.X, pady=2, padx=15)
        
        # 创建两列网格布局
        temu_options_frame.columnconfigure(0, weight=1)
        temu_options_frame.columnconfigure(1, weight=1)
        
        # TEMU订单选项
        self.temu_orders_var = tk.BooleanVar(value=True)
        # 为子选项添加跟踪额外参数，避免无限循环
        self.temu_orders_var.trace_add("write", lambda *args: self.check_temu_suboptions(False))
        temu_orders_check = ttk.Checkbutton(
            temu_options_frame, 
            text="TEMU订单数据", 
            variable=self.temu_orders_var
        )
        temu_orders_check.grid(row=0, column=0, sticky="w", padx=5, pady=3)
        
        # TEMU对账中心选项
        self.temu_bill_var = tk.BooleanVar(value=True)
        self.temu_bill_var.trace_add("write", lambda *args: self.check_temu_suboptions(False))
        temu_bill_check = ttk.Checkbutton(
            temu_options_frame, 
            text="TEMU对账中心数据", 
            variable=self.temu_bill_var
        )
        temu_bill_check.grid(row=0, column=1, sticky="w", padx=5, pady=3)
        
        # TEMU发货面单费选项
        self.temu_shipping_var = tk.BooleanVar(value=True)
        self.temu_shipping_var.trace_add("write", lambda *args: self.check_temu_suboptions(False))
        temu_shipping_check = ttk.Checkbutton(
            temu_options_frame, 
            text="TEMU发货面单费数据", 
            variable=self.temu_shipping_var
        )
        temu_shipping_check.grid(row=1, column=0, sticky="w", padx=5, pady=3)
        
        # TEMU退货面单费选项
        self.temu_return_var = tk.BooleanVar(value=True)
        self.temu_return_var.trace_add("write", lambda *args: self.check_temu_suboptions(False))
        temu_return_check = ttk.Checkbutton(
            temu_options_frame, 
            text="TEMU退货面单费数据", 
            variable=self.temu_return_var
        )
        temu_return_check.grid(row=1, column=1, sticky="w", padx=5, pady=3)
        
        # TEMU结算数据选项
        self.temu_settlement_var = tk.BooleanVar(value=True)
        self.temu_settlement_var.trace_add("write", lambda *args: self.check_temu_suboptions(False))
        temu_settlement_check = ttk.Checkbutton(
            temu_options_frame, 
            text="TEMU结算数据", 
            variable=self.temu_settlement_var
        )
        temu_settlement_check.grid(row=2, column=0, sticky="w", padx=5, pady=3)
        
        # 进度和状态框架
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        # 进度条
        progress_label = ttk.Label(progress_frame, text="处理进度:")
        progress_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var, 
            maximum=100, 
            length=300
        )
        self.progress_bar.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # 添加百分比显示
        self.percent_var = tk.StringVar(value="0%")
        percent_label = ttk.Label(
            progress_frame, 
            textvariable=self.percent_var,
            width=5,
            anchor="e",
            font=("Arial", 9, "bold")
        )
        percent_label.pack(side=tk.LEFT, padx=5)
        
        # 状态标签
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        status_label.pack(anchor="w", padx=5)
        
        # 控制按钮框架
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 处理按钮
        self.process_btn = ttk.Button(
            button_frame, 
            text="开始处理", 
            command=self.start_processing
        )
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        # 清除日志按钮
        clear_log_btn = ttk.Button(
            button_frame, 
            text="清除日志", 
            command=self.clear_log
        )
        clear_log_btn.pack(side=tk.LEFT, padx=5)
        
        # 退出按钮
        exit_btn = ttk.Button(
            button_frame, 
            text="退出", 
            command=self.root.destroy
        )
        exit_btn.pack(side=tk.RIGHT, padx=5)
        
        # 日志显示区域
        log_frame = ttk.LabelFrame(self.main_frame, text="处理日志", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 增加日志框的高度从15增加到25
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=25)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 设置好日志处理
        self.setup_log_queue_handler()
        
        # 初始启用/禁用适当的UI元素
        self.toggle_temu_options()
    
    def toggle_temu_options(self):
        """根据TEMU选项的状态，启用或禁用子选项并设置其状态"""
        # 获取当前TEMU选项的状态
        is_temu_enabled = self.temu_var.get()
        state = "normal" if is_temu_enabled else "disabled"
        
        # 根据TEMU选项的状态设置所有TEMU相关选项
        if is_temu_enabled:
            # 如果勾选了TEMU选项，则自动勾选所有TEMU相关选项
            self.temu_orders_var.set(True)
            self.temu_bill_var.set(True)
            self.temu_shipping_var.set(True)
            self.temu_return_var.set(True)
            self.temu_settlement_var.set(True)
        else:
            # 如果取消勾选了TEMU选项，则自动取消勾选所有TEMU相关选项
            self.temu_orders_var.set(False)
            self.temu_bill_var.set(False)
            self.temu_shipping_var.set(False)
            self.temu_return_var.set(False)
            self.temu_settlement_var.set(False)
        
        # 更新所有TEMU相关选项的状态（启用/禁用）
        for widget in self.main_frame.winfo_children():
            if isinstance(widget, ttk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Frame):
                        for grandchild in child.winfo_children():
                            if isinstance(grandchild, ttk.Checkbutton) and "TEMU" in grandchild.cget("text"):
                                grandchild.configure(state=state)
    
    def check_temu_suboptions(self, from_main=True):
        """检查TEMU子选项的状态，并相应地设置主选项
        
        Args:
            from_main: 是否来自主选项的改变，如果是则不需要检查，避免循环
        """
        # 如果是从主选项触发的变化，不需要检查
        if from_main:
            return
        
        # 检查是否有任何子选项被勾选
        any_checked = (
            self.temu_orders_var.get() or
            self.temu_bill_var.get() or
            self.temu_shipping_var.get() or
            self.temu_return_var.get() or
            self.temu_settlement_var.get()
        )
        
        # 根据子选项状态设置主选项
        if any_checked:
            # 如果有任何子选项被勾选，则勾选主选项
            self.temu_var.set(True)
        else:
            # 如果所有子选项都未勾选，则取消勾选主选项
            self.temu_var.set(False)
    
    def setup_log_queue_handler(self):
        """设置日志队列处理"""
        # 创建文本处理器类
        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                # 使用after方法确保在主线程中更新UI
                self.text_widget.after(0, lambda: append_log(self.text_widget, msg + '\n'))
        
        # 向文本控件添加日志的函数
        def append_log(widget, msg):
            widget.configure(state=tk.NORMAL)
            widget.insert(tk.END, msg)
            widget.see(tk.END)
            widget.configure(state=tk.DISABLED)
        
        # 创建文本处理器并将其添加到监听器
        self.text_handler = TextHandler(self.log_text)
        self.text_handler.setLevel(logging.INFO)
        self.text_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        
        # 创建队列监听器
        self.log_listener = logging.handlers.QueueListener(
            self.log_queue, self.text_handler
        )
        self.log_listener.start()
        
        # 添加定时检查函数
        self.check_log_queue()
    
    def check_log_queue(self):
        """定时检查日志队列并刷新显示"""
        # 处理队列中的所有消息
        while True:
            try:
                # 非阻塞尝试获取日志
                record = self.log_queue.get_nowait()
                msg = self.text_handler.format(record)
                self.log_text.after(0, lambda m=msg: self.append_log_to_ui(m))
            except queue.Empty:
                break  # 队列为空时退出循环
                
        # 每100毫秒检查一次队列
        self.root.after(100, self.check_log_queue)
    
    def append_log_to_ui(self, msg):
        """向UI添加日志消息"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, msg + '\n')
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def clear_log(self):
        """清空日志显示"""
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state=tk.DISABLED)
    
    def start_processing(self):
        """开始数据处理"""
        # 检查选项
        if not self.amazon_var.get() and not self.temu_var.get():
            messagebox.showwarning("警告", "请至少选择一种数据类型进行处理")
            return
        
        # 检查是否已经有正在进行的处理任务
        if self.processing_active:
            logging.warning("已有处理任务正在进行中，请等待完成")
            return
        
        # 设置处理中标志
        self.processing_active = True
        
        # 创建新的任务ID，在开始时就生成并设置
        self.current_task_id = str(int(time.time()))
        
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
            # 初始化
            start_time = time.time()
            logging.info("开始数据处理...")
            
            # 检查源目录和输出目录是否存在
            source_dir = self.source_var.get()
            output_base_dir = self.output_var.get()
            
            # 验证源目录
            if not os.path.exists(source_dir):
                error_msg = f"源文件目录不存在: {source_dir}"
                logging.error(error_msg)
                self.root.after(0, lambda: self._handle_processing_error(error_msg))
                return
            
            # 确保输出目录存在
            if not os.path.exists(output_base_dir):
                try:
                    os.makedirs(output_base_dir, exist_ok=True)
                    logging.info(f"创建输出目录: {output_base_dir}")
                except Exception as e:
                    error_msg = f"无法创建输出目录: {str(e)}"
                    logging.error(error_msg)
                    self.root.after(0, lambda: self._handle_processing_error(error_msg))
                    return
            
            # 使用在start_processing方法中生成的任务ID
            today_str = datetime.now().strftime('%Y%m%d')
            task_id = self.current_task_id  # 使用已经生成的任务ID
            task_output_dir = os.path.join(output_base_dir, today_str, f'TASK_{task_id}')
            
            # 创建任务目录并记录日志
            if not os.path.exists(task_output_dir):
                os.makedirs(task_output_dir, exist_ok=True)
                logging.info(f"创建主任务目录: {task_output_dir}")
            else:
                logging.info(f"使用现有任务目录: {task_output_dir}")
            
            # 保存任务目录便于其他代码使用
            self.current_task_dir = task_output_dir
            
            # 添加任务特定日志文件
            task_log_file = os.path.join(task_output_dir, f'processing_log_{task_id}.log')
            self.add_task_log_handler(task_log_file)
            logging.info(f"开始将日志保存到任务目录: {task_log_file}")
            
            # 处理亚马逊数据
            if self.amazon_var.get():
                logging.info("处理亚马逊结算数据...")
                try:
                    # 更新进度
                    self.update_progress(20)
                    
                    # 调用main.py中的实际处理函数，传递当前任务的源目录和输出目录
                    # 这样所有数据处理都将使用同一个任务目录
                    merge_amazon_orders(source_dir=source_dir, output_dir=task_output_dir)
                    
                    logging.info("亚马逊数据处理完成")
                    self.update_progress(40)
                except Exception as e:
                    logging.error(f"处理亚马逊数据时出错: {str(e)}")
                    self.root.after(0, lambda: self._handle_processing_error(str(e)))
                    return
            
            # 处理TEMU数据
            if self.temu_var.get():
                logging.info("处理TEMU数据...")
                try:
                    # 创建TemuDataProcessor实例，使用自定义的源目录和输出目录
                    processor = CustomTemuDataProcessor(source_dir, task_output_dir)
                    output_path = str(processor.output_dir)
                    
                    # 更新进度
                    self.update_progress(50)
                    
                    # 判断是否选择了任何TEMU数据类型
                    if not (self.temu_orders_var.get() or self.temu_bill_var.get() or
                            self.temu_shipping_var.get() or self.temu_return_var.get() or
                            self.temu_settlement_var.get()):
                        logging.warning("未选择任何TEMU数据类型进行处理")
                    else:
                        # 根据选择分别处理数据
                        if self.temu_orders_var.get():
                            logging.info("处理TEMU订单数据...")
                            processor.merge_orders()
                            self.update_progress(60)
                        
                        if self.temu_bill_var.get():
                            logging.info("处理TEMU对账中心数据...")
                            processor.merge_bill_data()
                            self.update_progress(70)
                        
                        if self.temu_shipping_var.get():
                            logging.info("处理TEMU发货面单费数据...")
                            processor.merge_shipping_fees()
                            self.update_progress(75)
                        
                        if self.temu_return_var.get():
                            logging.info("处理TEMU退货面单费数据...")
                            processor.merge_return_fees()
                            self.update_progress(80)
                        
                        if self.temu_settlement_var.get():
                            logging.info("处理TEMU结算数据...")
                            processor.merge_settlement_data()
                            self.update_progress(85)
                    
                    logging.info("TEMU数据处理完成")
                    self.update_progress(90)
                except Exception as e:
                    logging.error(f"处理TEMU数据时出错: {str(e)}")
                    self.root.after(0, lambda: self._handle_processing_error(str(e)))
                    return
            
            # 处理完成
            elapsed_time = time.time() - start_time
            logging.info(f"所有数据处理完成，用时 {elapsed_time:.2f}秒")
            
            # 保存成功使用的目录设置
            self.save_config({
                'last_source_dir': source_dir,
                'last_output_dir': output_base_dir
            })
            
            # 在主线程中更新UI
            result = {
                'elapsed_time': elapsed_time,
                'task_output_dir': task_output_dir
            }
            # 在任务完成日志中记录输出目录
            logging.info(f"处理结果输出到: {task_output_dir}")
            self.root.after(0, lambda: self._complete_processing(result))
        
        except Exception as e:
            # 捕获并安全处理异常
            error_msg = str(e)
            logging.error(f"处理数据时出错: {error_msg}")
            self.root.after(0, lambda: self._handle_processing_error(error_msg))
    
    def update_progress(self, value):
        """更新进度条和百分比显示"""
        self.root.after(0, lambda: self._update_progress_ui(value))
    
    def _update_progress_ui(self, value):
        """在主线程中更新进度UI"""
        self.progress_var.set(value)
        self.percent_var.set(f"{value}%")
    
    def _complete_processing(self, result):
        """在主线程中处理任务完成后的操作"""
        # 更新状态
        self.status_var.set("处理完成")
        self.progress_var.set(100)
        
        # 恢复按钮的可用状态
        self.process_btn.config(state=tk.NORMAL)
        
        # 重置处理标志和任务ID
        self.processing_active = False
        
        # 为日志添加分隔线，标记当前任务结束
        logging.info("-" * 80)
        logging.info("任务处理完成")
        logging.info("-" * 80)
        
        # 给用户展示处理结果
        task_dir = result.get('task_output_dir', '')
        if task_dir:
            messagebox.showinfo("处理完成", f"数据处理已完成\n\n用时: {result['elapsed_time']:.2f}秒\n输出目录: {task_dir}")
        else:
            messagebox.showinfo("处理完成", f"数据处理已完成，用时 {result['elapsed_time']:.2f}秒")
        
        # 在完成后清除任务ID
        self.current_task_id = None
        self.current_task_dir = None
    
    def _handle_processing_error(self, error_msg):
        """在主线程中处理错误"""
        # 更新状态
        self.status_var.set("处理出错")
        
        # 恢复按钮的可用状态
        self.process_btn.config(state=tk.NORMAL)
        
        # 重置处理标志和任务ID
        self.processing_active = False
        self.current_task_id = None
        self.current_task_dir = None
        
        # 显示错误对话框
        messagebox.showerror("错误", f"处理数据时出错:\n{error_msg}")
    
    def on_closing(self):
        """在关闭窗口时清理资源"""
        try:
            # 停止日志监听器
            if hasattr(self, 'log_listener'):
                self.log_listener.stop()
        finally:
            self.root.destroy()
            
    def load_config(self):
        """加载配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 如果配置文件不存在，创建默认配置
                default_config = {'last_source_dir': '', 'last_output_dir': ''}
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, indent=4, ensure_ascii=False)
                return default_config
        except Exception as e:
            logging.warning(f"加载配置文件时出错: {str(e)}")
            return {}
    
    def save_config(self, config_updates):
        """保存配置文件"""
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        try:
            # 先加载当前配置
            current_config = self.load_config()
            # 更新配置
            current_config.update(config_updates)
            # 写入文件
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(current_config, f, indent=4, ensure_ascii=False)
            logging.info("配置已保存")
        except Exception as e:
            logging.warning(f"保存配置文件时出错: {str(e)}")
    
    def browse_source_dir(self):
        """浏览并选择源文件目录"""
        directory = filedialog.askdirectory(
            title="选择源文件目录",
            initialdir=self.source_var.get()
        )
        if directory:  # 如果用户选择了目录而不是取消
            self.source_var.set(directory)
            logging.info(f"源目录设置为: {directory}")
    
    def browse_output_dir(self):
        """浏览并选择输出目录"""
        directory = filedialog.askdirectory(
            title="选择输出目录",
            initialdir=self.output_var.get()
        )
        if directory:  # 如果用户选择了目录而不是取消
            self.output_var.set(directory)
            logging.info(f"输出目录设置为: {directory}")


if __name__ == "__main__":
    try:
        # 导入sv_ttk并应用主题
        import sv_ttk
        
        # 创建主窗口
        root = tk.Tk()
        
        # 创建加粗的Checkbutton样式
        style = ttk.Style()
        style.configure("Bold.TCheckbutton", font=("Arial", 10, "bold"))
        
        # 应用sv_ttk主题
        sv_ttk.set_theme("light")  # 切换到暗色主题，更现代化
        
        # 设置日志级别
        logging.getLogger().setLevel(logging.INFO)
        
        # 创建并运行应用
        app = SimpleDataProcessorApp(root)
        root.mainloop()
    except Exception as e:
        # 确保任何未捕获的异常都被记录
        logging.error(f"程序启动失败: {str(e)}")
        messagebox.showerror("启动错误", f"程序启动失败:\n{str(e)}")
