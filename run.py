#!/usr/bin/env python3
"""
TEMU & Amazon 数据处理系统启动器
"""
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox

def check_dependencies():
    """检查并安装依赖"""
    try:
        import pandas
        import openpyxl
        import chardet
        return True
    except ImportError:
        return False

def main():
    """主函数"""
    if not check_dependencies():
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        result = messagebox.askokcancel(
            "安装依赖",
            "需要安装必要的依赖包。是否继续?",
            icon=messagebox.QUESTION
        )
        
        if result:
            try:
                subprocess.call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
                messagebox.showinfo("安装完成", "依赖安装完成，程序将继续启动。")
            except Exception as e:
                messagebox.showerror("安装失败", f"依赖安装失败: {str(e)}\n请手动运行 'pip install -r requirements.txt'")
                return
        else:
            return
    
    # 创建必要的目录
    os.makedirs("数据源/TEMU", exist_ok=True)
    os.makedirs("数据源/amazon", exist_ok=True)
    os.makedirs("处理结果", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 启动应用程序
    try:
        from app import DataProcessorApp
        root = tk.Tk()
        app = DataProcessorApp(root)
        root.mainloop()
    except Exception as e:
        if 'root' in locals():
            root.destroy()
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("启动错误", f"应用启动失败: {str(e)}")

if __name__ == "__main__":
    main()
