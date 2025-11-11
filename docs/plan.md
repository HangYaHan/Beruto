开发路线图（详细计划）

说明：本文件为项目的可执行计划与 Sprint 划分，包含每项任务的目标、实现要点、验收标准、估时与交付物。当前优先级：先实现第 3 项“数据获取接口”（已标记为 in-progress）。

总体阶段概览

- Phase 1: 基础框架（4-6 周）
	- 项目结构与脚手架搭建
	- 数据层基础功能
	- 数据获取接口（优先）
	- 数据存储设计
	- 基础数据处理
	- 核心事件总线
	- 基础回测框架

- Phase 2: 策略开发环境（3-4 周）
	- 策略基类与接口
	- 技术指标库
	- 回测引擎完善
	- 绩效分析模块

- Phase 3: 执行与风控（4-5 周）
	- 订单管理系统
	- 风险控制框架
	- 模拟/实盘执行适配器
	- 实时数据流处理

- Phase 4: 实盘交易（3-4 周）
	- 券商 API 集成
	- 实盘风控系统
	- 监控与告警
	- 审计与日志

- Phase 5: 优化与扩展（持续）
	- 性能优化
	- 新策略与 ML 集成
	- UI 功能完善

----

详细任务（按优先级展开）

1) 项目搭建与脚手架（1-2 天）
- 目标：建立可复现开发环境，明确项目约定。
- 具体工作：
	- 创建目录结构（`src/ tests/ docs/ config/ logs/`），添加 `.gitignore`，`README.md`，`requirements.txt`。
	- 初始化 `src/main.py`（最小入口），添加 `docs/overview.md`。
	- 编写本地开发说明（如何创建 venv、安装依赖、运行最小示例）。
- 交付物：仓库基础文件、README、requirements。
- 验收：在干净环境中执行 `python -m venv .venv; .\.venv\Scripts\pip install -r requirements.txt` 不报错。

2) 开发环境与依赖（0.5-1 天）
- 目标：统一依赖与编辑器设置。
- 具体工作：
	- 完成 `requirements.txt`（含 pandas,numpy,matplotlib,yfinance,pytest,PyQt5/Streamlit 说明）。
	- 提供 VSCode 推荐设置（`.vscode/settings.json`、`launch.json`）。
- 验收：依赖安装且能运行 tests 中的示例脚本。

3) 数据获取接口（Data Fetch，2-4 天，当前 in-progress） — 详尽实现计划
- 目标：实现一个统一、可扩展、健壮的数据获取层，能从不同来源（yfinance、本地 CSV、第三方 API）拉取 OHLCV 数据，并提供缓存、重试与速率限制处理。
- 高层设计（模块与接口）
	- 目录：`src/data/`
	- 主要文件：
		- `fetcher.py`：对外统一接口（类或函数），负责调度适配器、缓存与参数校验。
		- `adapters/`：每个数据源一个适配器文件，如 `yfinance_adapter.py`, `csv_adapter.py`, `alphavantage_adapter.py`, `tushare_adapter.py`（后者国内可选）。
		- `storage.py`：本地缓存读写（parquet/csv），包含版本/日期分区策略。
		- `exceptions.py`：自定义异常（如 RateLimitError、DataNotFoundError）。
		- `tests/test_fetcher.py`：单元测试与速率限制模拟。

- 详细功能分解与实现要点
	a) 统一接口设计（`fetcher.py`）
		 - API 示例：
			 - `get_history(symbol: str, start: str, end: str, source: str = 'yfinance', refresh: bool = False) -> pd.DataFrame`
			 - 支持参数：`interval`（1d/1m/1h），`adjusted`（是否复权），`cache`（是否使用本地缓存），`max_retries`, `backoff_factor`。
		 - 行为约定：在缓存存在且 `refresh=False` 时优先返回缓存；发生网络错误或速率限制时按指数退避重试；若适配器返回空数据，抛出 `DataNotFoundError`。

	b) 适配器实现（`adapters/`）
		 - 每个适配器实现 `fetch(symbol, start, end, interval, **kwargs) -> pd.DataFrame`。
		 - yfinance 适配器注意点：使用 `yf.download(..., auto_adjust=True)`，并处理 YFRateLimitError；在请求失败时记录重试日志。
		 - csv 适配器：支持读取带有标准列名（Open,High,Low,Close,Adj Close,Volume,Datetime）的本地文件，并支持日期解析与筛选范围。
		 - 其他 API（AlphaVantage/TuShare）：封装速率限制、API key 管理（从环境变量读取），并实现分页/批量请求。

	c) 本地缓存（`storage.py`）
		 - 存储格式：parquet（按 symbol/year/month 分区）为主，CSV 作为互换格式。
		 - 接口：`read_cached(symbol, start, end)`, `write_cache(symbol, df)`。
		 - 元数据：维护 `symbols_meta.json`（记录最后更新日期、来源、数据频率）。

	d) 错误与速率限制处理
		 - 全局重试策略：`max_retries` + `backoff_factor`（指数退避），针对 YFRateLimitError 或 HTTP 429 使用更长的等待时间。
		 - 可配置代理支持（从 `os.environ` 读取 `HTTP_PROXY/HTTPS_PROXY`）。
		 - 在适配器内部对异常进行归类并抛出统一异常供 `fetcher` 处理。

	e) 接口示例代码片段（`src/data/fetcher.py`）
	```python
	# 伪代码示例
	from .adapters import yfinance_adapter, csv_adapter
	from .storage import read_cached, write_cache
	from .exceptions import RateLimitError

	def get_history(symbol, start, end, source='yfinance', refresh=False, **kwargs):
			if not refresh:
					df = read_cached(symbol, start, end)
					if df is not None and not df.empty:
							return df

			adapter = select_adapter(source)
			for attempt in range(kwargs.get('max_retries', 3)):
					try:
							df = adapter.fetch(symbol, start, end, **kwargs)
							if not df.empty:
									write_cache(symbol, df)
							return df
					except RateLimitError:
							sleep((2 ** attempt) * kwargs.get('backoff_factor', 5))
			raise RuntimeError('Failed to fetch data after retries')
	```

	f) 测试與验收
		 - 单元测试：模拟器（mock） yfinance 返回、测试缓存命中/未命中、测试退避策略、测试 CSV 读取边界（时区、缺失列）。
		 - 集成测试：对接真实 yfinance 获取少量历史数据并验证列名、时间索引与数据连续性。
		 - 验收标准：在本地运行 `pytest tests/test_fetcher.py` 通过；缓存读写正确，速率限制发生时能完成重试逻辑。

	g) 估时与分配（将该项拆成日任务）
		 - Day 1: 设计接口、实现 `fetcher.py` 框架、编写 `adapters/yfinance_adapter.py`。
		 - Day 2: 实现 `adapters/csv_adapter.py` 与 `storage.py`（parquet 支持）、基础单元测试。
		 - Day 3: 实现速率限制退避与 `alphavantage_adapter`（可选），写完整测试并修复 bug。
		 - Day 4（缓冲）：整理文档、示例脚本、在 CI 中运行测试。

	h) 交付物（对于第 3 项）
		 - `src/data/fetcher.py`、`src/data/adapters/*`、`src/data/storage.py`、`src/data/exceptions.py`、`tests/test_fetcher.py`、`docs/data_fetcher.md`。

	i) 运行示例（本地快速验证）
	```powershell
	# 在 Windows PowerShell 中（在项目根目录）
	python -m venv .venv
	.\.venv\Scripts\pip install -r requirements.txt
	python -c "from src.data.fetcher import get_history; print(get_history('600519.SS','2022-01-01','2022-12-31').head())"
	```

----

4) 数据存储与格式（1-2 天）
- 目标：标准化数据格式与高效读取接口。
- 具体工作与验收略（见概要清单）。

5) 基础数据清洗与处理（2-3 天）
- 目标：提供 ETL 工具链，保证回测数据质量。

6) 技术指标库（2-4 天）
- 目标：实现向量化指标库并提供示例与测试。

7) 策略框架与基类（2-3 天）
- 目标：定义策略生命周期并提供示例均线策略。

8) 回测引擎（4-6 天）
- 目标：实现时间序列驱动事件循环并输出交易日志。

（其余项请参见 TODO 列表，已同步到任务跟踪）

----

下一步（我将为你执行的操作）

1. 我已经把第 3 项在任务跟踪中标记为 in-progress（见项目 todo）。
2. 如果你确认要我继续，我可以：
	 - 立即在 `src/data/` 下生成文件模板（`fetcher.py`、`adapters/yfinance_adapter.py`、`storage.py`、`exceptions.py`、`tests/test_fetcher.py`）并提交初始实现与测试；或
	 - 先把第 3 项的详细设计文档 `docs/data_fetcher.md` 写入 `docs/` 供审阅。

请选择你想要我下一步执行的动作（生成代码模板 / 写设计文档 / 其它），我会立刻开始并把改动写入仓库并运行快速测试。 