import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import os
import sys
import sqlite3
import platform
import datetime
import threading
import subprocess
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from temu_amazon_processor.main import process_data

DB_FILE = 'merge_history.db'

# 获取默认下载目录（兼容Win/macOS）
def get_default_download_dir():
    if platform.system() == 'Windows':
        return os.path.join(os.environ['USERPROFILE'], 'Downloads')
    else:
        return os.path.join(os.path.expanduser('~'), 'Downloads')

# 打开文件夹
def open_folder(path):
    if not os.path.exists(path):
        messagebox.showwarning('提示', '文件夹不存在！')
        return
    if platform.system() == 'Windows':
        os.startfile(path)
    elif platform.system() == 'Darwin':
        subprocess.Popen(['open', path])
    else:
        subprocess.Popen(['xdg-open', path])

# 初始化sqlite数据库
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS merge_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT,
        exec_time TEXT,
        status TEXT,
        result_dir TEXT,
        log TEXT
    )''')
    conn.commit()
    conn.close()

# 插入合并记录
def insert_history(task_id, exec_time, status, result_dir, log):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO merge_history (task_id, exec_time, status, result_dir, log) VALUES (?, ?, ?, ?, ?)',
              (task_id, exec_time, status, result_dir, log))
    conn.commit()
    conn.close()

# 查询所有合并记录
def fetch_history():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, task_id, exec_time, status, result_dir FROM merge_history ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    return rows

# 检查文件夹是否存在
def folder_exists(path):
    return os.path.exists(path)

class MergeApp:
    def __init__(self, root):
        self.root = root
        self.root.title('财务数据合并工具')
        window_width = 800
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.root.resizable(False, False)
        self.data_src = tk.StringVar()
        self.result_dir = tk.StringVar(value=get_default_download_dir())
        self.log_text = None
        self.history_tree = None
        self.progress = None
        self.merge_btn = None
        self.setup_ui()
        self.refresh_history()

    def setup_ui(self):
        # 数据源选择
        frm1 = tk.Frame(self.root)
        frm1.pack(fill='x', padx=10, pady=5)
        tk.Label(frm1, text='数据源文件夹:').pack(side='left')
        tk.Entry(frm1, textvariable=self.data_src, width=50).pack(side='left', padx=5)
        tk.Button(frm1, text='选择', command=self.select_data_src).pack(side='left')
        # 结果目录选择
        frm2 = tk.Frame(self.root)
        frm2.pack(fill='x', padx=10, pady=5)
        tk.Label(frm2, text='处理结果文件夹:').pack(side='left')
        tk.Entry(frm2, textvariable=self.result_dir, width=50).pack(side='left', padx=5)
        tk.Button(frm2, text='选择', command=self.select_result_dir).pack(side='left')
        # 合并按钮
        frm3 = tk.Frame(self.root)
        frm3.pack(fill='x', padx=10, pady=5)
        self.merge_btn = tk.Button(frm3, text='开始合并', command=self.start_merge, width=20, bg='#ffffff', fg='#000000')
        self.merge_btn.pack(side='left')
        # 判断数据源文件夹中是否有可用的文件路径，如果没有或者路径不存在，禁用合并按钮
        if not os.path.exists(self.data_src.get()) or not os.path.isdir(self.data_src.get()):
            self.merge_btn.config(state='disabled') 
        # 进度条
        self.progress = ttk.Progressbar(frm3, orient='horizontal', length=200, mode='determinate')
        self.progress.pack(side='left', padx=10)
        # 日志区
        tk.Label(self.root, text='日志输出:').pack(anchor='w', padx=10)
        self.log_text = scrolledtext.ScrolledText(self.root, height=8, state='disabled')
        self.log_text.pack(fill='x', padx=10, pady=5)
        # 合并记录区
        tk.Label(self.root, text='合并记录:').pack(anchor='w', padx=10)
        columns = ('exec_time', 'task_id', 'status', 'result_dir')
        self.history_tree = ttk.Treeview(self.root, columns=columns, show='headings')
        self.history_tree.heading('exec_time', text='执行时间')
        self.history_tree.heading('task_id', text='任务ID')
        self.history_tree.heading('status', text='执行状态')
        self.history_tree.heading('result_dir', text='处理结果')
        self.history_tree.column('exec_time', width=160)
        self.history_tree.column('task_id', width=120)
        self.history_tree.column('status', width=80)
        self.history_tree.column('result_dir', width=300)
        self.history_tree.pack(fill='both', expand=True, padx=10, pady=5)
        self.history_tree.bind('<Double-1>', self.on_history_double_click)

    def select_data_src(self):
        path = filedialog.askdirectory(title='选择数据源文件夹')
        if path:
            self.data_src.set(path)
            # 判断数据源文件夹中是否有可用的文件路径，如果没有或者路径不存在，禁用合并按钮
            if not os.path.exists(self.data_src.get()) or not os.path.isdir(self.data_src.get()):
                self.merge_btn.config(state='disabled') 
            else:
                self.merge_btn.config(state='normal')

    def select_result_dir(self):
        path = filedialog.askdirectory(title='选择处理结果文件夹')
        if path:
            self.result_dir.set(path)

    def write_log(self, msg):
        self.log_text.config(state='normal')
        self.log_text.insert('end', msg + '\n')
        self.log_text.see('end')
        self.log_text.config(state='disabled')

    def start_merge(self):
        self.merge_btn.config(state='disabled')
        self.progress['value'] = 0
        threading.Thread(target=self.merge_files, daemon=True).start()

    def merge_files(self):
        src = self.data_src.get()
        dst = self.result_dir.get()
        if not src or not os.path.isdir(src):
            self.write_log('请选择有效的数据源文件夹！')
            return
        if not dst or not os.path.isdir(dst):
            self.write_log('请选择有效的处理结果文件夹！')
            return
        task_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        exec_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        status = '进行中'
        log = ''
        result_subdir = os.path.join(dst, f'merge_{task_id}')
        try:
            self.write_log(f'任务{task_id}：开始合并...')
            process_data(process_amazon=False, process_temu=True)
            status = '成功'
            log = 'TEMU合并完成'
            self.write_log(f'任务{task_id}：合并完成。')
        except Exception as e:
            status = '失败'
            log = str(e)
            self.write_log(f'任务{task_id}：合并失败！{e}')
        insert_history(task_id, exec_time, status, result_subdir, log)
        self.refresh_history()

    def refresh_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        rows = fetch_history()
        for r in rows:
            # 检查文件夹是否存在
            folder_status = '文件已丢失' if not folder_exists(r[4]) else '打开文件夹'
            self.history_tree.insert('', 'end', iid=r[0], values=(r[2], r[1], r[3], folder_status), tags=(r[4],))

    def on_history_double_click(self, event):
        item = self.history_tree.selection()
        if not item:
            return
        iid = item[0]
        folder = self.history_tree.item(iid, 'tags')[0]
        if folder_exists(folder):
            open_folder(folder)
        else:
            messagebox.showwarning('提示', '文件夹不存在！')

if __name__ == '__main__':
    init_db()
    root = tk.Tk()
    app = MergeApp(root)
    root.mainloop()