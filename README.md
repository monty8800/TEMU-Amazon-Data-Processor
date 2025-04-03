# TEMU & Amazon 数据处理系统

[![Version](https://img.shields.io/badge/版本-v1.2.2-blue)](https://github.com/monty8800/TEMU-Amazon-Data-Processor/releases/tag/v1.2.2)
[![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/temu-amazon-processor)](https://pypi.org/project/temu-amazon-processor/)

这是一个用于处理和合并TEMU和亚马逊销售数据的工具，能够自动处理多种类型的数据文件并生成统一格式的结果。支持多种文件格式和编码，自动提取国家信息，并提供彩色日志输出。

现在可以通过PyPI直接安装使用！

## 主要功能

- 处理TEMU各类数据文件并合并
- 处理亚马逊结算数据并合并
- 自动从文件名提取国家信息
- 多工作表合并保存到同一个Excel文件
- 支持多种文件格式(Excel和CSV)和编码(UTF-8, GBK, GB18030, Latin-1)
- 彩色日志输出，实时跟踪处理进度
- 自动依赖检测与安装，提高程序稳定性

## 功能细节

- 支持处理TEMU数据：
  - 订单数据
  - 对账中心数据
  - 发货面单费数据
  - 退货面单费数据（分为退至TEMU仓和退至商家仓）
  - 结算数据
- 支持处理亚马逊结算数据
- 交互式菜单系统，便于用户操作
- 详细的日志记录
- 自动识别数据源中的店铺名称
- 自动创建输出目录

## 使用方法

1. 将TEMU数据文件放入`数据源/TEMU/`目录下对应的店铺文件夹中
2. 将亚马逊数据文件放入`数据源/amazon/`目录下
3. 运行`python 合并基础数据.py`
4. 在菜单中选择需要的操作:
   - 选项1：仅合并亚马逊结算数据
   - 选项2：仅合并TEMU数据
   - 选项3：合并所有数据

## 文件结构

- `合并基础数据.py`: 主程序
- `country.json`: 国家数据配置文件
- `数据源/`: 存放原始数据的目录（不包含在此仓库中）
- `处理结果/`: 存放处理结果的目录（不包含在此仓库中）
- `logs/`: 日志文件目录

## 安装方法

### 从 PyPI 安装

```bash
pip install temu-amazon-processor
```

### 从源码安装

```bash
git clone https://github.com/monty8800/TEMU-Amazon-Data-Processor.git
cd TEMU-Amazon-Data-Processor
pip install -e .
```

## 使用方法

### 命令行方式

安装后，直接在命令行运行：

```bash
temu-processor
```

将启动交互式菜单，您可以选择处理TEMU数据、亚马逊数据或同时处理两者。

### 作为Python模块导入

```python
from temu_amazon_processor import main
main.main()
```

## 依赖包

- pandas>=1.5.0
- openpyxl>=3.0.10
- chardet>=4.0.0
- colorama>=0.4.4

## 特殊功能

### 自动从文件名提取国家信息
系统可以从文件名或路径中自动提取国家信息，支持多种格式：
- 订单导出-美国.csv
- 订单-US.xlsx
- UK_结算文件.xls

### 共享输出目录
解决了多TASK目录问题，当执行“合并所有数据”选项时，现在亚马逊和TEMU数据将输出到同一个TASK目录。

### 彩色日志输出
使用colorama库提供彩色日志输出，不同级别的日志使用不同颜色：
- INFO：绿色
- WARNING：黄色
- ERROR：红色
- 步骤标记：蓝色

### 自动依赖包检测与安装
程序启动时会自动检测必要的依赖包，如果缺失则自动使用pip安装。

## 注意事项

- 数据源目录和处理结果目录不包含在此仓库中，使用前需手动创建
- 首次运行程序会自动安装所需依赖
- 确保数据源文件结构正确，参考使用方法部分

## 版本更新历史

### v1.2.2 (2025-04-03)
- 发布到PyPI：通过`pip install temu-amazon-processor`安装
- 添加命令行入口点，安装后可直接运行`temu-processor`
- 完善对Python全平台的支持
- 增强依赖版本管理

### v1.2.1 (2025-04-03)
- 文档完善：添加详细的版本更新历史
- 添加特殊功能部分，详细说明关键功能
- README结构优化，添加版本和Python徒章

### v1.2.0 (2025-04-03)
- 添加彩色日志输出，使处理过程更直观
- 改进对账中心和结算数据合并方案，将所有工作表保存到同一个Excel文件
- 添加自动依赖包检测与安装功能
- 代码优化，移除未使用的导入

### v1.1.0 (2025-04-03)
- 添加CSV文件支持和多编码处理(UTF-8, GBK, GB18030, Latin-1)
- 实现从文件名提取国家信息功能
- 解决多TASK目录问题，实现共享输出目录
- 改进日志系统，确保详细日志同时输出到控制台和任务目录
- 修改输出文件命名约定，使用TASK ID而非时间戳
