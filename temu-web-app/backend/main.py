from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os
import sys
import uuid
import shutil
import logging
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime
import time
import zipfile
import py7zr
import patoolib
import re

# 添加父目录到系统路径，以便导入主程序
parent_dir = Path(__file__).parent.parent.absolute()
sys.path.append(str(parent_dir))

# 定义自己的日志和数据处理函数
def setup_logging(task_dir=None):
    """设置日志记录"""
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 如果提供了任务目录，也将日志输出到文件
    if task_dir:
        file_handler = logging.FileHandler(Path(task_dir) / "process.log", encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)

class CustomTemuDataProcessor:
    """简化版的TEMU数据处理器"""
    def __init__(self, source_dir=None, output_dir=None, task_id=None):
        # 设置基本属性
        self.source_dir = source_dir if source_dir else Path("数据源")
        self.output_dir = output_dir if output_dir else Path("处理结果")
        self.task_id = task_id if task_id else str(int(time.time()))
        
    def process(self):
        """处理TEMU数据"""
        logging.info(f"开始处理TEMU数据，输出目录: {self.output_dir}")
        # 简化版实现，实际处理逻辑在这里
        return True

def merge_amazon_orders(source_dir=None, output_dir=None, task_id=None):
    """合并亚马逊订单数据"""
    logging.info(f"开始处理亚马逊数据，输出目录: {output_dir}")
    # 简化版实现，实际处理逻辑在这里
    return True

# 判断文件是否为压缩文件
def is_archive_file(file_path):
    """判断文件是否为压缩文件"""
    file_ext = file_path.suffix.lower()
    return file_ext in ['.zip', '.rar', '.7z']

# 判断文件是否为数据文件
def is_data_file(file_path):
    """判断文件是否为数据文件（Excel或CSV）"""
    file_ext = file_path.suffix.lower()
    return file_ext in ['.xlsx', '.xls', '.csv']

# 解压缩文件
def extract_archive(archive_path, extract_to):
    """根据文件类型解压缩文件"""
    file_ext = archive_path.suffix.lower()
    
    if file_ext == '.zip':
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif file_ext == '.7z':
        with py7zr.SevenZipFile(archive_path, mode='r') as z:
            z.extractall(path=extract_to)
    elif file_ext == '.rar':
        patoolib.extract_archive(str(archive_path), outdir=str(extract_to))
    else:
        # 尝试使用patool处理其他类型的压缩文件
        patoolib.extract_archive(str(archive_path), outdir=str(extract_to))

app = FastAPI(title="TEMU & Amazon 数据处理系统")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制为前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建上传和任务目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
TASKS_DIR = Path("tasks")
TASKS_DIR.mkdir(exist_ok=True)

# 任务状态存储
tasks = {}

@app.get("/")
async def read_root():
    return {"message": "TEMU & Amazon 数据处理系统 API"}

@app.post("/upload/")
async def upload_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    process_type: str = Form("3")  # 默认处理所有数据
):
    # 创建任务ID和目录
    task_id = str(uuid.uuid4())
    task_dir = UPLOAD_DIR / task_id
    task_dir.mkdir(parents=True)
    
    # 保存上传的文件
    saved_files = []
    extracted_files = []
    try:
        for file in files:
            file_path = task_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_files.append(str(file_path))
            
            # 检查是否为压缩文件，如果是则解压
            if is_archive_file(file_path):
                extract_dir = task_dir / f"extracted_{file.filename.split('.')[0]}"
                extract_dir.mkdir(exist_ok=True)
                try:
                    extract_archive(file_path, extract_dir)
                    logging.info(f"已解压文件: {file.filename} 到 {extract_dir}")
                    # 添加解压出的文件到处理列表
                    for ext_file in extract_dir.glob("**/*"):
                        if ext_file.is_file() and is_data_file(ext_file):
                            extracted_files.append(str(ext_file))
                except Exception as extract_error:
                    logging.error(f"解压文件失败: {file.filename}, 错误: {str(extract_error)}")
    except Exception as e:
        # 清理任务目录
        shutil.rmtree(task_dir)
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    # 初始化任务状态
    tasks[task_id] = {
        "id": task_id,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "files": saved_files,
        "extracted_files": extracted_files,
        "process_type": process_type,
        "result_dir": None,
        "log_file": None,
        "error": None
    }
    
    # 在后台处理数据
    background_tasks.add_task(process_task, task_id, process_type, task_dir)
    
    return {"task_id": task_id, "status": "pending", "message": "文件上传成功，开始处理数据"}

async def process_task(task_id: str, process_type: str, task_dir: Path):
    """在后台处理任务"""
    try:
        # 更新任务状态
        tasks[task_id]["status"] = "processing"
        
        # 设置日志文件
        log_file = TASKS_DIR / f"{task_id}.log"
        tasks[task_id]["log_file"] = str(log_file)
        
        # 创建结果目录
        today_str = datetime.now().strftime('%Y%m%d')
        result_dir = Path("处理结果") / today_str / f"TASK_{task_id}"
        result_dir.mkdir(parents=True, exist_ok=True)
        tasks[task_id]["result_dir"] = str(result_dir)
        
        # 设置日志
        setup_logging(task_dir=result_dir)
        
        # 记录文件信息
        logging.info(f"原始文件数量: {len(tasks[task_id]['files'])}")
        if tasks[task_id]['extracted_files']:
            logging.info(f"解压文件数量: {len(tasks[task_id]['extracted_files'])}")
            for ext_file in tasks[task_id]['extracted_files']:
                logging.info(f"  - {os.path.basename(ext_file)}")
        
        # 根据处理类型执行相应的操作
        if process_type == "1":  # 仅处理亚马逊数据
            merge_amazon_orders(source_dir=task_dir, output_dir=result_dir, task_id=task_id)
        elif process_type == "2":  # 仅处理TEMU数据
            processor = CustomTemuDataProcessor(source_dir=task_dir, output_dir=result_dir, task_id=task_id)
            processor.process()
        else:  # 处理所有数据
            # 先处理亚马逊数据
            merge_amazon_orders(source_dir=task_dir, output_dir=result_dir, task_id=task_id)
            
            # 再处理TEMU数据
            processor = CustomTemuDataProcessor(source_dir=task_dir, output_dir=result_dir, task_id=task_id)
            processor.process()
        
        # 更新任务状态为完成
        tasks[task_id]["status"] = "completed"
        
    except Exception as e:
        # 记录错误并更新任务状态
        logging.error(f"任务处理失败: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks[task_id]

@app.get("/tasks/{task_id}/logs")
async def get_task_logs(task_id: str):
    """获取任务日志"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    log_file = tasks[task_id].get("log_file")
    if not log_file or not os.path.exists(log_file):
        return {"logs": "暂无日志"}
    
    with open(log_file, "r", encoding="utf-8") as f:
        logs = f.read()
    
    return {"logs": logs}

@app.get("/tasks/{task_id}/download/{filename}")
async def download_result(task_id: str, filename: str):
    """下载处理结果文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    result_dir = tasks[task_id].get("result_dir")
    if not result_dir:
        raise HTTPException(status_code=404, detail="结果目录不存在")
    
    file_path = Path(result_dir) / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(path=file_path, filename=filename)

@app.get("/tasks/{task_id}/files")
async def list_result_files(task_id: str):
    """列出结果文件"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    result_dir = tasks[task_id].get("result_dir")
    if not result_dir or not os.path.exists(result_dir):
        return {"files": []}
    
    files = []
    for file in Path(result_dir).glob("**/*"):
        if file.is_file():
            files.append({
                "name": file.name,
                "path": str(file.relative_to(Path(result_dir))),
                "size": file.stat().st_size,
                "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
            })
    
    return {"files": files}

@app.get("/tasks")
async def list_tasks():
    """列出所有任务"""
    return {"tasks": list(tasks.values())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8089, reload=True)
