# 概念设计文档 (Concept Design Document)

# 草稿
这是一个非常棒的概念设计思路。引入 Arbiter (仲裁者) 和 Executor (执行官) 的架构，实际上是将量化回测系统中的 信号生成 (Signal Generation)、投资组合构建 (Portfolio Construction) 和 交易执行 (Execution) 进行了更高级的解耦。

相比于生成一张静态的“互斥表”（这在因子变多时会呈现指数级复杂度爆炸，且难以维护），你的 Arbiter/Executor 模式更符合现代量化系统的设计哲学（如 QuantConnect 或 Zipline 的架构）。

以下我为你设计的系统架构蓝图，定义了它们各自的职责和数学逻辑。

核心架构：Plan, Symbol, Factor, Arbiter, Executor
在这个体系中，数据流向应该是：

Data\xrightarrowFactorSignal\xrightarrowArbiterTarget Portfolio\xrightarrowExecutorOrders

1. Factor (因子/策略单元) —— “感知者”
你提到的 Factor 在这里不仅仅是数学因子（如 PE, RSI），更应该被定义为 Signal Generator (信号发生器)。

输入：Symbol 的市场数据（OHLCV）、财务数据。
输出：一个标准化的信号强度 (Signal Strength) 或 建议仓位 (Raw Weight)。
特性：
因子之间不需要知道彼此的存在（解耦）。
Buy & Hold 可以被视为一个特殊的因子：它始终输出 
1
.
0
1.0（满仓）的信号。
均值回归因子 可能输出 
[
−
]
[−1,1] 之间的波动信号。
1. Arbiter (仲裁者) —— “决策大脑”
这是你系统的核心。Arbiter 不直接交易，它的职责是解决冲突和分配权重。它决定了“此时此刻，我们理想的持仓应该是什么”。

职责：

信号聚合 (Aggregation)：接收所有 Factor 的输出。
冲突解决 (Conflict Resolution)：当 Factor A 想买，Factor B 想卖时，Arbiter 决定听谁的，或者取折中值。
风险控制 (Risk Constraints)：例如限制单只股票最大仓位不超过 20%。
输出：目标投资组合 (Target Portfolio / Target Weights)。
解决“互斥”的逻辑：
不需要互斥表，而是通过权重叠加或优先级掩码来处理。

场景举例：Buy & Hold vs. 择时因子
假设你有一个基准策略（Buy & Hold）和一个增强策略（MACD）。

Factor A (Buy & Hold): 输出 
S
0
S
​A
​​ =1.0 (始终建议持有)。
Factor B (MACD Sell): 输出 
S
B
=
−
​B
​​ =−0.5 (建议减仓)。
Arbiter 的逻辑：
W
5
1.0+(−0.5)=0.5（半仓）。
结论：冲突通过数学加权自然消解了，而不是硬性的“互斥”。
1. Executor (执行官) —— “行动手脚”
Executor 负责将 Arbiter 的“理想”转化为“现实”。它处理市场摩擦和实际交易规则。

输入：Arbiter 给出的 Target Portfolio（例如：持有茅台 20%，持有宁德时代 30%）。
职责：
状态对比：比较 Current Portfolio (当前持仓) 和 Target Portfolio。
生成订单 (Order Generation)：计算差额（Diff）。

​
​(Target Weight−Current Weight)×Total Equity
​​ 

交易限制 (Constraints)：
A股规则：必须是 100 股的整数倍 (Round down to lot size)。
T+1 检查：昨天的买入今天才能卖。
涨跌停检查：如果涨停，无法买入；跌停，无法卖出。
现金检查：是否有足够的 Cash。
输出：最终的 Buy/Sell 交易指令列表。
数学模型设计
为了让系统支持线性/非线性以及复杂的叠加，建议采用以下数学模型：

1. 因子层 (Factor Layer)
每个 Factor 
f
​​  针对某个 Symbol 
s
s 在时间 
t
t 输出一个信号 
v
i
,
​i,s,t
​​ 。
为了标准化，建议将所有因子的输出归一化到 
[
−
1
[−1,1] 或 
[
0
,
[0,1] 区间。

1. 仲裁层 (Arbiter Layer)
Arbiter 使用一个函数 
A
A 来计算目标权重 
W

其中 
Θ
Θ 是 Arbiter 的配置参数。

模式 A：线性加权 (Linear Combination)
适合多因子叠加。

W
s
,
#+ 概念设计文档 (Concept Design Document)

**版本**: 2.0  
**日期**: 2026-01-06  
**适用范围**: A 股中长线多标的回测与模拟交易引擎  
**阅读对象**: 量化工程师 / 研究员 / QA / 运维

---

## 1. 目标与范围

- 建立一套解耦、可测试、可扩展的回测/模拟交易内核，覆盖数据→信号→决策→执行→清算→报告的全链路。  
- 针对 A 股特性（T+1、100 股整手、涨跌停、分红送转、印花税）提供一等公民的工程封装。  
- 预留机器学习与强化学习的演进接口，保持输入/输出契约稳定。  
- 输出交付物：核心模块设计、数据契约、关键流程、约束与测试要求。

非目标：撮合引擎高频细粒度模拟、交易通道实盘接入、超日内（分钟级）延迟建模。

---

## 2. 关键概念与角色

- Plan：一次回测/模拟任务的配置集合（宇宙、因子列表、仲裁逻辑、执行与成本模型、调度周期）。  
- Nexus/Universe：数据入口与可交易标的筛选层。  
- Oracle/Factor：信号发生器，输出标准化强度或建议权重。  
- Arbiter：信号聚合与目标权重决策层。  
- Executor：将目标权重转化为可下单的订单草案，负责 A 股约束校验。  
- Broker/Account：成交撮合与记账，维护资金与持仓状态。  
- Scheduler：调仓节奏与阈值控制（可内嵌在 Arbiter，也可独立）。  
- Analyzer/Reporter：绩效指标与日志输出。  
- CostModel/Slippage：手续费、印花税、滑点与最低费用规则集合。

---

## 3. 整体架构与数据流

数据流：

1. Nexus：拉取并清洗当日数据；生成 `ActiveUniverse`（可交易标的列表）。  
2. Oracles：对 `ActiveUniverse` 并行计算 `SignalFrame`。  
3. Arbiter：接收 `SignalFrame` + `AccountState`，输出 `TargetPortfolio`。  
4. Executor：对比 `TargetPortfolio` 与当前持仓，生成满足约束的 `Orders`。  
5. Broker/Account：基于撮合价格与成本模型生成 `Fills`，更新 `AccountState`。  
6. Analyzer：记录当日 `Nav`, `Trades`, `Positions`，更新指标。  
7. Loop：推进到下一交易日，直至结束。

逻辑分层：
- 计算层（Oracles, Arbiter）不感知市场摩擦。  
- 约束层（Executor, Broker）收口所有 A 股特有规则与成本。  
- 状态层（Account）是唯一的资金/持仓真相源。  
- 观测层（Analyzer）只读状态与成交。

---

## 4. 核心模块设计

### 4.1 Nexus / Universe
- 输入：原始行情、财务、日历、停牌、成分变更、分红送转表。  
- 输出：`ActiveUniverse`（可交易标的列表）、对齐且缺失值处理后的 `DataFrame`/tensor。  
- 规则：剔除 ST/PT、上市小于 N 天、停牌、退市；可配置成分（如 HS300）。  
- 工程要点：
  - 数据对齐与前向填充策略明确记录；
  - 交易日历统一入口；
  - 生存偏差防护（历史成分与退市表）。

### 4.2 Oracles (Factors)
- 输入：`ActiveUniverse` 数据切片。  
- 输出：`SignalFrame`，形如 `(time, symbol) -> signal ∈ [-1,1] 或 [0,1]`，允许 `NaN` 表示无信号。  
- 设计原则：
  - 完全无副作用；
  - 不感知资金与仓位；
  - 需声明所需数据列与窗口大小，便于调度器做缓存与裁剪。  
- 示例：动量、均线、多空评分、风险开关（熔断信号）。

### 4.3 Arbiter
- 输入：`SignalFrame`, `AccountState`, 可选 `RiskSignals`。  
- 输出：`TargetPortfolio`（各 symbol 目标权重 + 现金权重）。  
- 常见策略：
  - 线性加权：$w_s = \sum_i \alpha_i \cdot signal_{i,s}$。  
  - 门控/掩码：`base_weight * (1 - risk_mask)`；重大风险信号可一票否决。  
  - 防抖：若 `|target - current| < threshold` 则保持不动。  
- 工程要点：
  - 输出权重需归一化并约束在 $[0,1]$；
  - 允许现金权重；
  - 保持接口稳定，内部可替换为 ML/RL。

### 4.4 Scheduler（可选独立）
- 功能：控制调仓频率与触发条件。  
- 示例：每月第一个交易日重平衡；或当组合变动超 5% 时触发。  
- 若不独立，则在 Arbiter 内部实现防抖逻辑。

### 4.5 Executor
- 输入：`TargetPortfolio`, `AccountState`, 当日盘口价格/限制。  
- 输出：`Orders`（满足整手、T+1、涨跌停、资金约束的买卖列表）。  
- 约束规则：
  - Lot size：数量向下取整到 100 股；
  - T+1：卖出需检查 `sellable_shares`；
  - 涨跌停：涨停不买，跌停不卖（可配置策略例外）；
  - 资金：买入金额 + 费用 ≤ 可用现金；
  - 成交价：默认收盘价或 VWAP，可配置滑点函数。  
- 订单形态：支持 `MARKET`/`LIMIT`；紧急度字段用于滑点模型。

### 4.6 Broker / Account
- 输入：`Orders`, 当日价格、分红送转事件、成本模型。  
- 输出：`Fills`, 更新后的 `AccountState`。  
- 职责：
  - 撮合：根据价格模型给出成交量与成交价；
  - 费用：佣金、印花税（卖出收取）、滑点、最低 5 元规则；
  - 分红送转：在开盘前调整持仓股数、均价与现金；
  - T+1 结算：收盘后同步 `sellable_shares = total_shares`；
  - 冻结现金：挂单占用的现金在成交或撤单后释放。  
- 状态字段：`cash`, `frozen_cash`, `positions`, `total_equity`, `nav_history`。

### 4.7 Analyzer / Reporter
- 输入：`AccountState` 时间序列、`Fills`, `Orders`。  
- 输出：指标与可视化：总收益、年化、波动、最大回撤、Sharpe/Sortino、Calmar、胜率、换手率、因子暴露；基准对比 Alpha/Beta。  
- 工程要点：
  - 指标计算需基于对齐的交易日历；
  - 可选导出 CSV/JSON，或生成图表。

### 4.8 CostModel / Slippage
- 佣金：双边费率，含最低 5 元规则。  
- 印花税：仅卖出侧收取。  
- 滑点：可选常数价差、比例价差、或基于成交额/盘口深度的函数。  
- 可配置：策略粒度或全局粒度。

---

## 5. 数据模型与接口契约

### 5.1 SignalFrame
- 索引：`time`, `symbol`。  
- 值域：`[-1,1]` 或 `[0,1]`，`NaN` 表示无信号。  
- 方法：`to_tensor()`, `align(universe, calendar)`。

### 5.2 TargetPortfolio
- 结构：`{symbol: weight}`, `cash_weight`。  
- 规则：权重非负、合计 ≤ 1；缺省部分视为现金。

### 5.3 Order
- 字段：`symbol`, `direction (BUY/SELL)`, `quantity (lot-aligned)`, `order_type`, `limit_price`, `urgency`, `created_at`。  
- 不变量：`quantity % 100 == 0`；卖单 `quantity <= sellable_shares`。

### 5.4 Position
- 字段：`symbol`, `total_shares`, `sellable_shares`, `avg_cost`, `last_price`。  
- 衍生：`market_value = total_shares * last_price`。

### 5.5 AccountState
- 字段：`cash`, `frozen_cash`, `positions: Dict[str, Position]`, `total_equity`, `nav`。  
- 方法：`position_weight(symbol)`, `cash_ratio`, `update_with_fill(fill)`。

### 5.6 CorporateAction
- 字段：`symbol`, `ex_date`, `dividend`, `split_ratio`, `rights_issue`。  
- 用途：在开盘前批处理，更新持仓与均价。

---

## 6. 核心流程（按交易日）

1. Pre-Market：
   - 读取日历、分红送转并调整持仓；
   - 解冻昨日买入至可卖。  
2. Data Load：Nexus 提供 `ActiveUniverse` 与对齐数据。  
3. Signal：Oracles 生成 `SignalFrame`。  
4. Decide：Arbiter（含防抖/调度）输出 `TargetPortfolio`。  
5. Generate Orders：Executor 应用约束与资金检查，形成 `Orders`。  
6. Match & Cost：Broker 使用价格模型成交，扣除费用，返回 `Fills`。  
7. Update State：Account 写入现金、持仓、均价、可卖股数。  
8. Record：Analyzer 记录 NAV、持仓、交易、指标。  
9. Roll：进入下一个交易日。

---

## 7. A 股特有规则

- T+1：卖出需使用 `sellable_shares`，收盘后同步。  
- 整手：数量向下取整到 100 股；零股仅在全部卖出时允许。  
- 涨跌停：涨停不买，跌停不卖（可通过配置允许打板策略）。  
- 分红送转：使用真实价格 + 事件调整，不使用复权价格回测；同步调整均价。  
- 成交日历：统一使用交易所日历，过滤节假日与临停。  
- 资金校验：买入前预占现金；成交后释放未用部分。

---

## 8. 成本与滑点模型

- `commission_rate`: 双边费率；`min_commission`: 5 元。  
- `stamp_duty_rate`: 仅卖出侧。  
- `slippage`: `f(side, price, notional, adv)`，默认常数或比例。  
- 可插拔：支持策略级或全局注册；支持回放成交记录以校准参数。

---

## 9. 风险与调仓控制

- 单票上限：`max_weight_per_symbol`（如 20%）。  
- 整体杠杆：`sum(weights) <= 1`（无融资场景）。  
- 换手率阈值：`|target-current| < eps` 时不交易。  
- 黑名单：停牌、退市、ST 列表过滤。  
- 现金底线：保留最小现金比例以覆盖费用与滑点。  
- 触发器：市场风险信号触发降仓或清仓（掩码式门控）。

---

## 10. 配置与扩展性

- Plan 配置：`universe`, `oracles`, `arbiter`, `scheduler`, `executor`, `broker`, `cost_model`, `slippage_model`, `benchmark`, `start/end_date`。  
- 序列化：YAML/JSON + Python 类。  
- 插拔：所有模块通过接口/抽象基类约束，替换不破坏其他层。

---

## 11. 机器学习演进路线

1. 规则阶段：
   - Oracles 为技术/基本面规则；Arbiter 为线性加权 + 门控。  
2. 监督学习：
   - Oracles 作为特征生成器；Arbiter 用树模型/线性模型预测期望收益，再经均值方差或风险预算求权重。  
3. 强化学习：
   - 环境：State = (SignalFrame, AccountState)，Action = 目标权重/订单，Reward = 年化收益或 Sortino。  
   - 兼容：保持输入输出契约，Executor/Broker 不变。

---

## 12. 可观测性与性能

- 日志：模块级日志（数据、信号、决策、订单、成交、成本、异常）。  
- 指标：计算耗时分布、命中率、成交率、换手、费用占比。  
- 资源：批量回测支持多进程/多线程；缓存因子计算结果。  
- 失败策略：数据缺失、价格越界、资金不足时的降级与告警。

---

## 13. 测试要求

- 单元测试：
  - 因子输出范围与缺失值处理；
  - Arbiter 权重归一化与防抖逻辑；
  - Executor 约束（整手、T+1、涨跌停、资金）；
  - 成本模型最小费用与印花税规则。  
- 集成测试：
  - 分红送转回放；
  - 典型策略日内流程回放（含空仓、满仓、部分成交）；
  - 不同调度频率的结果一致性。  
- 回测对比：与基准实现（如简化 Excel/脚本）对账，误差阈值明确。  
- 性能基线：给出单日、单策略的耗时目标与资源占用阈值。

---

## 14. 参考伪代码

```python
def run_plan(plan: Plan):
    account = AccountState.init(plan.initial_cash)
    calendar = load_calendar(plan.start, plan.end)
    for day in calendar:
        account.apply_corporate_actions(day)
        data, universe = nexus.load(day)
        signals = {o.name: o.compute(data, universe) for o in plan.oracles}
        target = plan.arbiter.decide(signals, account)
        if target is None:
            analyzer.record(day, account)
            continue
        orders = plan.executor.generate(target, account, data.prices)
        fills = plan.broker.match(orders, data.prices, plan.cost_model)
        account.update(fills)
        analyzer.record(day, account, orders, fills)
    return analyzer.report()
```

---

## 15. 术语表

- SignalFrame：按时间与标的索引的信号矩阵。  
- TargetPortfolio：目标持仓权重集合。  
- Order/Fills：下单指令 / 实际成交结果。  
- AccountState：资金与持仓的唯一真相源。  
- CostModel/Slippage：费用与滑点计算组件。  
- Analyzer：绩效与日志输出模块。
