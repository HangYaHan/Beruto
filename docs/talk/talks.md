## 核心设计思想（总览）

将“数据获取”拆成若干职责清晰、低耦合的模块：适配器（Adapter）、协调器/门面（Fetcher）、持久化/缓存（Storage）、统一异常层（Exceptions）与测试（Tests）。主要设计原则：

- 单一职责（SRP）：每个模块只负责一种角色，便于维护和复用。
- 依赖倒置 / 接口优先（DI/IoC）：上层代码依赖抽象，不直接耦合具体实现，方便替换与扩展。
- 可测试性：通过接口和 mock 能独立做单元测试。
- 可观测与健壮：统一日志、异常和重试策略，提高系统可靠性。
- 可扩展性：新增数据源只需新增适配器，不改动上层逻辑。

下面按模块详细说明设计意图、好处与实现要点。

## Fetcher（统一对外接口 / 协调器）

设计意图

Fetcher 提供单一、语义明确的对外 API（例如 `get_history(...)`），负责：缓存优先策略、选择适配器、统一重试/退避、参数校验与返回规范化数据。适配器只负责从源获取原始数据，Fetcher 负责调度与容错。

为什么这么设计（好处）

- 简化调用者：上层（UI、策略、回测）只需一处调用，不关心细节。
- 统一策略：缓存、重试与日志在同一层实现，便于监控和调优。
- 容错能力强：网络或速率限制由 Fetcher 统一处理，适配器仅需抛出标准异常。

实现要点

- API 示例：

```python
def get_history(symbol: str, start: str, end: str,
				source: str = 'yfinance', interval: str = '1d',
				adjusted: bool = True, cache: bool = True,
				max_retries: int = 3, backoff_factor: int = 5,
				refresh: bool = False) -> pd.DataFrame:
	...
```

- 行为约定：优先返回缓存（除非 `refresh=True`）；调用适配器失败时按指数退避重试；适配器返回空数据时抛出 `DataNotFoundError`。

## Adapters（数据源适配器）

设计意图

每个数据源（yfinance、CSV、本地/第三方 API）实现一个适配器，负责把源数据拉取并最少量规范化（列名、时间索引）。适配器不负责全局缓存与统一重试策略，但可对特定错误做局部重试。

为什么这么设计（好处）

- 低耦合、易扩展：新增数据源只需新增适配器文件，不改动 Fetcher。
- 隐藏复杂性：分页、签名、速率限制等源端复杂逻辑都封装在适配器内，便于调试。
- 易测试：可以单独 mock 每个适配器来测试 Fetcher 的行为。

实现要点

- 统一签名：`fetch(symbol, start, end, interval, **kwargs) -> pd.DataFrame`。
- 在适配器内部将第三方异常映射为统一异常类型（见下文）。

## Storage（本地缓存/存储）

设计意图

使用高效的列式格式（推荐 parquet）并按 `symbol/year/month` 分区存储，提供简洁读写接口，维护元数据信息（如最后更新时间、来源、频率）。

为什么这么设计（好处）

- 减少重复请求、节省带宽并规避速率限制。
- 提高回测与开发效率：本地读取速度远高于网络拉取。
- 统一格式便于后续使用分布式工具（如 Spark）处理。

实现要点

- 接口：`read_cached(symbol, start, end)`, `write_cache(symbol, df)`, `list_cached_symbols()`。
- 建议维护 `symbols_meta.json` 记录元数据与更新时间。

## Exceptions（统一异常层）

设计意图

定义一组标准异常类型（例如 `RateLimitError`, `DataNotFoundError`, `AdapterError`, `NetworkError`），适配器将第三方错误映射到这些异常，Fetcher 根据异常类型决定重试或降级策略。

为什么这么设计（好处）

- 上层逻辑无需解析各厂商错误消息，只依据异常类型采取动作（如指数退避或立刻失败）。
- 有助于写测试：直接抛出指定异常即可覆盖退避与错误处理路径。

## Tests（测试策略）

设计要点

- 单元测试：使用 mock/stub 模拟适配器返回正常数据、空数据、`RateLimitError`、网络异常，验证 Fetcher 的缓存命中、重试行为与异常传播。
- 集成测试（可选）：对接真实 API（如 yfinance）拉取少量样本，验证列名、时间索引与连续性。
- 将单元测试作为 CI 门禁，避免回归。

## 落地建议（一步步实现）

1. 建模块骨架：`src/data/`, `src/data/adapters/`, `src/data/tests/`, `docs/`。
2. 先实现最简单的本地适配器：`adapters/csv_adapter.py`，把 CSV 转为标准 OHLCV DataFrame（列名与时间索引）。
3. 实现 `storage.py` 的基本读写（parquet 或 csv），以及 `fetcher.py` 的最小逻辑（先读缓存，未命中则调用 csv_adapter 并写缓存）。
4. 为 Fetcher 写单元测试（pytest + monkeypatch），mock 适配器行为以覆盖缓存与异常分支。
5. 实现 `adapters/yfinance_adapter.py` 并将 yfinance 特有异常映射到 `RateLimitError`。
6. 在 Fetcher 层加入可配置的重试/退避（可使用 `tenacity`），并完善日志记录。

## 推荐学习路径与资源

- 阅读设计原则：《Clean Architecture》（Robert C. Martin）、Martin Fowler 的架构文章。
- 学习设计模式：Adapter、Facade、Repository、Strategy（GoF 设计模式）。
- 掌握测试工具：pytest、unittest.mock、responses（用于 HTTP mocking）。
- 学习可靠性工具：`tenacity`（重试库）、结构化日志（JSON）、监控基础（Prometheus）。

如果你愿意，我可以：

- 立即在仓库中生成代码模板（`fetcher.py`、`adapters/csv_adapter.py`、`adapters/yfinance_adapter.py`、`storage.py`、`exceptions.py`、基础测试文件），并运行快速单元测试；或
- 先生成更详尽的设计文档（含序列图与示例请求/响应流）供你评审。

请选择下一步（生成代码 / 生成文档），我会立刻开始并汇报结果。
