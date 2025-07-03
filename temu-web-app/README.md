# TEMU & Amazon 数据处理系统 - Web版

这是TEMU & Amazon 数据处理系统的Web版本，基于Next.js和FastAPI构建，提供了友好的用户界面，使数据处理更加便捷。

## 功能特点

- **文件上传**：支持多文件上传，包括Excel和CSV格式
- **数据处理**：保留了原Python脚本的所有处理功能
- **实时状态**：显示任务处理进度和状态
- **结果下载**：处理完成后可直接下载结果文件
- **任务管理**：查看历史任务和处理结果

## 技术架构

- **前端**：Next.js + TypeScript + Tailwind CSS
- **后端**：FastAPI + Python
- **数据处理**：复用现有的temu-amazon-processor包

## 安装和运行

### 前提条件

- Node.js 18+
- Python 3.8+
- pip

### 安装步骤

1. **克隆仓库**

```bash
git clone <仓库地址>
cd temu-web-app
```

2. **安装后端依赖**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **安装前端依赖**

```bash
cd ../frontend
npm install
```

4. **运行应用**

启动后端：

```bash
cd ../backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

启动前端：

```bash
cd ../frontend
npm run dev
```

5. **访问应用**

打开浏览器访问：http://localhost:3000

## 使用方法

1. 在首页上传数据文件（Excel或CSV格式）
2. 选择处理类型（亚马逊数据、TEMU数据或全部）
3. 点击"开始处理"按钮
4. 等待处理完成，查看处理日志
5. 下载处理结果文件

## 文件结构

```
temu-web-app/
├── backend/               # FastAPI后端
│   ├── main.py            # 主应用入口
│   └── requirements.txt   # 依赖列表
│
├── frontend/              # Next.js前端
│   ├── src/
│   │   ├── app/           # 页面组件
│   │   │   ├── page.tsx   # 首页
│   │   │   └── tasks/     # 任务相关页面
│   │   ├── components/    # 可复用组件
│   │   └── ...
│   └── ...
│
└── README.md              # 项目说明文档
```

## 功能增强

该Web应用保留了原Python脚本的所有功能，包括：

1. **文件格式支持**：支持Excel和CSV格式
2. **国家信息提取**：自动从文件名和路径中提取国家信息
3. **多TASK目录处理**：支持共享输出目录
4. **日志系统**：详细记录处理过程

## 贡献与反馈

如有问题或建议，请提交Issue或Pull Request。

## 许可证

[MIT](LICENSE)
