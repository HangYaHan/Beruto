# 贝如塔仓库(Beruto Overview)
- **Description**: 该仓库为一个轻量量化交易 / 回测框架原型。代码位于 `src`，文档在 `docs`，数据在 `data`，测试在`tests`。

## Root Files
- **`README.md`**: 项目总体说明与快速开始（阅读入口）。
- **`CONTRIBUTING.md`**: 贡献指南（协作流程与提交规范）。
- **`requirements.txt`**: Python 依赖列表（用于创建虚拟环境）。
- **`data/`**: 放置从金融数据库拉去的原始数据csv格式。
- **`docs/`**: 项目设计与接口说明以及可能需要的基础知识（见下文）。
- **`src/`**: 核心源码包（框架的实现细节，见下文）。
- **`tests/`**: 单元/集成测试脚本和示例。 

## `docs/`（文档）
- **目的**: 存放项目设计文档、使用说明和笔记，方便理解架构与接口。
- **主要内容**:
  - `blockdesign.md`: 架构或模块划分的设计说明。
  - `plan.md`: 项目计划和任务分解。
  - `interface/`: 主要函数的使用说明。
  - `knowledge/`: 学习笔记与示例（包含编程和基本金融知识）。
  - `talk/`: 项目讨论记录或AI的回答（`talks.md`）。

## `src/`（核心代码）
- **目的**: 包含框架运行所需的模块，按功能划分为若干子包：

- **`src/main.py`**: 应用入口，负责启动流程（解析命令行、初始化日志与配置、派发运行模式）。

- **`src/backtest/`**
  - `engine.py`: 回测引擎接口与实现骨架。负责运行回测、收集交易记录与绩效数据。

- **`src/common/`**
  - `config.py`: 配置加载与保存、配置读取封装（支持文件/环境覆盖）。
  - `utils.py`: 通用工具函数（目录创建、日期解析、分块迭代等）。

- **`src/data/`**
  - `fetcher.py`: 选择对应金融库的适配器(adapters)并获取金融数据。
  - `storage.py`: 本地缓存读写。
  - `exceptions.py`: 数据相关自定义异常类型（如 `RateLimitError`, `DataNotFoundError`）。
  - `adapters/`:统一各个金融数据库如akshare,yfinance的接口使用，返回形式统一为`Dataframe`
    - `csv_adapter.py`: 从本地 CSV 读取历史行情，列名规范化并返回 `DataFrame`。
    - `yfinance_adapter.py`: 使用 `yfinance` 金融库，返回`DataFrame`。

- **`src/execution/(画饼中，暂时不需要)`**
  - `broker.py`: 负责下单/取消/订单查询等。

- **`src/portfolio/(画饼中，暂时不需要)`**
  - `manager.py`: 组合管理器接口（持仓、现金、估值、成交回调、资产分配逻辑）。

- **`src/risk/(画饼中，暂时不需要)`**
  - `risk_manager.py`: 风险管理接口（下单前合规检查、暴露/杠杆/集中度计算等）。

- **`src/strategy/`**
  - `base.py`: 回测的具体策略。
  - `indicators.py`: 一些作为判断的金融因子。

- **`src/system/`**
  - `log.py`: 集中日志配置（文件 + 控制台）。
  - `main_window.py`: 简单 PyQt5 UI 示例（桌面界面原型）。

## `tests/`（测试目录）
- **`tests/`**: 包含若干快速运行/手动测试脚本。

## `data/`（数据目录）
- **`data/`**: 存放从金融数据库拉取的原始数据。

