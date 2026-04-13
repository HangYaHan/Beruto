# Unified Portfolio + Tax-Aware Backtest Plan

## 1. Goal

把当前项目从“单标的、策略驱动、无税费”的回测，升级成一条统一主线：

- 单一系统配置文件管理账户级规则
- 单账户多标的 portfolio 回测
- 规则驱动 + 打分排序的 manager
- 兼顾股票与 ETF 的不同税费规则
- 计入手续费、交易税、过户费、现金分红、红利税
- 以 `net_return_pct` 作为主指标，同时保留毛收益和费用拆分

当前阶段不引入 ML。先把确定性的规则、账务、配置与兼容性做稳，再为后续更复杂的 manager 预留接口。

## 2. Current Architecture Constraints

### 2.1 Existing state

- 回测核心目前是单标的、单策略、逐日循环。
- `run_backtest` 只处理 `cash + shares`，没有独立账本。
- 结果结构主要围绕 `total_return_pct`、`max_drawdown_pct`、`equity_curve`。
- CLI 目前有 `backtest`、`run`、`leaderboard`、`visualize` 等入口，但没有系统级 `config` 命令。
- 当前数据源只保证日 K 线，没有独立分红事件表。

### 2.2 Design pressure

- 税费规则对不同账户通常是固定的，但对不同标的类型会有差异。
- 股票和 ETF 的税费规则不同，不能用一套通用常量硬套。
- 分红税与分红收益都必须能拆分，否则净收益会失真。
- 历史结果文件必须尽量向后兼容，不能因为 schema 变化导致旧记录失效。

## 3. Product Decisions

- 不预置具体税率数值，只提供完整配置框架与校验能力。
- 分红采用现金入账，不自动再投资。
- 红利税采用“股票按持有期分档 + ETF 独立税率规则”。
- 证券类型采用“按 symbol 前缀自动识别 + symbol 覆盖优先”。
- 成本模型第一版不引入滑点，只做手续费、税费与分红税。
- manager 第一版采用规则驱动 + 打分排序，不引入 ML。
- 回测主指标采用 `net_return_pct`，`gross_return_pct` 保留为辅助指标。
- 旧单标的流程先兼容保留，再逐步让位于 portfolio 模式。

## 4. Proposed File Map

- `src/data/settings.rs`：系统配置、规则校验、证券类型识别、配置持久化。
- `src/cli/mod.rs`：`config` 命令、backtest/portfolio 回测入口、结果展示、记录持久化。
- `src/cli/help.rs`：启动帮助与完整帮助文案。
- `src/portfolio/mod.rs`：组合账本、仓位、执行填充、风险报告。
- `src/manager/mod.rs`：manager trait、intent/score、规则驱动决策器。
- `src/backtest/engine.rs`：账本驱动的回测执行、费用与分红结算。
- `src/backtest/result.rs`：结果字段扩展与历史兼容。
- `src/backtest/visualize.rs`：新指标展示。
- `src/data/data_source.rs`：分红字段与 CSV 兼容。
- `src/data/fetcher.rs`：分红数据写入或补录通道。
- `src/data/storage.rs`：结果/批次记录兼容读取。
- `docs/PORTFOLIO_MANAGER_DESIGN.md`：portfolio/manager 方向和验证原则。

## 5. Implementation Phases

### Phase 1 - Unified domain model and config framework

目标：把规则、资产类型、账户级配置、symbol 覆盖和 manager 参数统一进一个系统配置层。

需要做的事：

1. 扩展 `AppSettings`。
2. 新增账户级费用配置。
3. 新增股票 / ETF 分类规则。
4. 新增红利税分档配置。
5. 新增 symbol 覆盖规则。
6. 增加配置校验函数。
7. 增加规则摘要结构，供回测记录持久化。

建议结构：

```rust
pub struct AppSettings {
    pub default_symbol: String,
    pub default_initial_capital: f64,
    pub active_profile: String,
    pub profiles: HashMap<String, AccountProfile>,
    pub symbol_overrides: HashMap<String, SymbolOverride>,
    pub manager_defaults: ManagerDefaults,
}
```

```rust
pub struct AccountProfile {
    pub stock_fee: FeeRule,
    pub etf_fee: FeeRule,
    pub stock_dividend_tax: DividendTaxRule,
    pub etf_dividend_tax: DividendTaxRule,
    pub auto_classify_by_prefix: bool,
}
```

```rust
pub struct FeeRule {
    pub commission_rate: f64,
    pub commission_min: f64,
    pub transfer_rate: f64,
    pub transaction_tax_rate: f64,
}
```

```rust
pub struct DividendTaxRule {
    pub brackets: Vec<DividendTaxBracket>,
}
```

```rust
pub struct DividendTaxBracket {
    pub min_holding_days: u32,
    pub max_holding_days: Option<u32>,
    pub tax_rate: f64,
}
```

```rust
pub enum AssetClass {
    Stock,
    Etf,
}
```

配置解析原则：

- 账户级规则优先于 built-in 默认。
- symbol 覆盖优先于自动识别。
- 自动识别基于 symbol 前缀，但允许在 config 中手工覆写。
- `serde(default)` 必须覆盖所有新增字段，保证旧 settings.json 可读。

### Phase 2 - New config command family

目标：让规则可以在 CLI 中查看、设置、清空、按 symbol 覆盖。

建议命令：

- `config show`
- `config init`
- `config set <path> <value>`
- `config reset`
- `config profile use <name>`
- `config profile create <name>`
- `config profile delete <name>`
- `config symbol set-class <symbol> stock|etf`
- `config symbol unset-class <symbol>`

建议 `set` 支持的路径示例：

- `profiles.default.stock_fee.commission_rate`
- `profiles.default.stock_fee.commission_min`
- `profiles.default.stock_dividend_tax.brackets[0].tax_rate`
- `profiles.default.auto_classify_by_prefix`
- `symbol_overrides.159581.asset_class`

输出建议：

- `config show` 输出当前生效值和来源。
- `config set` 修改后立即保存到 `.beruto/settings.json`。
- `config reset` 恢复到默认结构，但保留用户是否选择过 profile 的痕迹可讨论。

### Phase 3 - Portfolio and manager runtime layer

目标：把交易决策和交易执行分离。

核心原则：

- strategy 只负责输出 intent / score。
- manager 负责排序、筛选、仓位分配和风控。
- execution layer 负责成交、费用、税费、账本更新。

建议新增接口：

```rust
pub struct SignalIntent {
    pub symbol: String,
    pub strategy_id: String,
    pub score: f64,
    pub target_weight: f64,
}
```

```rust
pub struct ManagerContext {
    pub t_index: usize,
    pub snapshots: Vec<SymbolSnapshot>,
    pub candidate_intents: Vec<SignalIntent>,
    pub portfolio: Portfolio,
}
```

```rust
pub trait Manager {
    fn name(&self) -> &str;
    fn decide(&mut self, ctx: &ManagerContext) -> Vec<OrderDecision>;
}
```

第一版 manager 规则建议：

- 同一 symbol 只允许保留最高分 intent。
- 先按 score 排序，再按账户风险约束裁剪。
- 支持固定仓位桶，例如 0%、25%、50%、100%。
- 支持单标的权重上限和总换手上限。

### Phase 4 - Backtest accounting engine

目标：把 `cash + shares` 的简单循环改成完整账本。

交易侧要计入：

- 买入手续费
- 卖出手续费
- 交易税
- 过户费
- 成交金额对现金的即时影响

分红侧要计入：

- 现金分红入账
- 红利税扣除
- 红利税按持有期分档

结果侧要累计：

- `gross_return_pct`
- `net_return_pct`
- `dividend_yield_pct`
- `commission_total`
- `transaction_tax_total`
- `transfer_fee_total`
- `dividend_income_total`
- `dividend_tax_total`
- `tax_fee_total`

建议把账务逻辑拆成三个层次：

1. 交易信号层：策略 -> intent。
2. 决策层：manager -> order decisions。
3. 执行层：order decisions -> fills -> 账本更新。

### Phase 5 - Data and persistence model

目标：让分红和结果结构都可兼容旧数据。

需要改的地方：

- `DailyQuote` 增加 `dividend_per_share`，缺列时默认为 0。
- 如果未来接独立 corporate actions 数据表，尽量保持 `DailyQuote` 不再背过多事件字段。
- `TradeEvent` 增加费用/税费信息。
- `BacktestResult` 增加毛净收益、分红、税费分解字段。
- `BacktestRunRecord` 的历史 JSON 读取保持可兼容。

兼容性要求：

- 旧 run 文件必须能继续加载。
- 新字段全部用默认值回填。
- 可视化与排行榜不能因为旧记录缺字段崩溃。

### Phase 6 - CLI and reporting integration

目标：让用户在命令行上直接看到新的净收益和费用结构。

建议修改：

- `print_result` 默认突出 `net_return_pct`。
- `leaderboard` 默认按 `net_return_pct` 排序。
- `visualize` 显示费用拆分卡片和 gross/net 曲线说明。
- `save_backtest_record` 保存当前生效配置摘要。

### Phase 7 - Validation and regression checks

目标：避免一次大重构把旧行为打碎。

建议测试：

- 配置解析和保存/读取测试。
- symbol 自动分类测试。
- symbol 覆盖优先测试。
- 股票/ETF 费用计算测试。
- 红利税分档测试。
- 现金分红入账测试。
- 零费率、零分红对照测试。
- 旧结果文件兼容测试。
- portfolio 决策和换手约束测试。

## 6. Open Questions

需要最终拍板的问题：

1. 股票和 ETF 的前缀识别规则是否要写死在代码里，还是做成 config 可扩展映射？
2. `config reset` 是否应当保留当前 active profile，还是直接回到 `default`？
3. portfolio mode 是否要从一开始就支持多账户，还是先只做单账户多标的？
4. 红利数据短期无法自动抓取时，是否接受先通过本地 CSV 补列？
5. `config set` 是否允许任意路径写入，还是只允许白名单路径？
6. manager 的打分排序规则是统一一套，还是允许不同 strategy 先输出不同语义的 score？
7. 结果展示里是否需要同时保留毛收益排序和净收益排序两个 leaderboard？
8. 历史结果是否要做一次性迁移脚本，还是保持懒加载兼容就够？

## 7. Suggested Build Order

1. 先做 `src/data/settings.rs` 的配置框架和校验。
2. 再做 `config` 命令。
3. 同时拆 `src/portfolio/mod.rs` 与 `src/manager/mod.rs`。
4. 然后改 `src/backtest/engine.rs`。
5. 再补数据模型和历史兼容。
6. 最后补 CLI 展示和可视化。

## 8. Acceptance Criteria

- `config` 命令可查看、设置和保存系统规则。
- 回测能区分股票与 ETF 的税费规则。
- 回测能计入手续费、红利收益、红利税、税费合计。
- 输出有明确的 gross/net 拆分，且 `net_return_pct` 为主指标。
- 旧 run 文件仍可读。
- 单标的旧流程不立即崩坏，portfolio 模式可以渐进接入。
