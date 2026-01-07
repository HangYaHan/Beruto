## 2. 核心模块架构 (Core Modules)

### 2.1 Nexus (枢纽) —— 数据与宇宙层
**职责**：作为一切的起点，负责数据的摄入、清洗以及投资标的（Symbol）的初筛。

*   **功能定义**：
    *   **Data Pylon (数据水晶)**：提供 OHLCV、财务数据、宏观数据的统一接口。
    *   **Warp In (动态宇宙)**：根据时间 $t$，动态生成合法的股票池（Universe）。
        *   *逻辑*：剔除 ST/PT、剔除刚上市 < N 天的新股、剔除停牌股票。
        *   *输出*：`List[Active_Symbol]`
*   **ML 扩展性**：Nexus 产生的数据可以直接被格式化为 `(Batch, Time, Features)` 的张量供神经网络读取。

### 2.2 Oracle (先知) —— 因子与信号层
**职责**：感知市场变化，生成原始信号。这是旧设计中 "Factor" 的升级版。

*   **功能定义**：
    *   **Revelation (显隐)**：每个 Oracle 关注一个特定的市场逻辑（如动量、价值、波动率）。
    *   **Input**：来自 Nexus 的原始数据。
    *   **Output**：`Signal Vector` (归一化到 [-1, 1] 或 [0, 1])。
    *   *特性*：Oracle 之间完全隔离，互不干扰。支持线性因子（MA Cross）和非线性因子（基于逻辑判断）。
*   **ML 扩展性**：每个 Oracle 都可以被替换为一个独立的微型模型（如 LSTM 特征提取器）。

### 2.3 Arbiter (仲裁者) —— 决策与权重层
**职责**：系统的“大脑”。接收所有 Oracle 的信号，解决冲突，决定最终持仓。**它通过逻辑控制取代了传统的 Scheduler**。

*   **功能定义**：
    *   **Recall (召回/聚合)**：根据配置权重（$\alpha$）或决策树逻辑，聚合 Oracle 信号。
    *   **Stasis Field (静滞场/防抖)**：实现你的“调度”逻辑。
        *   *逻辑*：如果新计算的 `Target_Portfolio` 与 `Current_Portfolio` 差异小于阈值（Threshold），则强制输出 `Current_Portfolio`，即“按兵不动”。
    *   **Output**：`Target Portfolio` (目标持仓权重，如：茅台 20%，现金 80%)。
*   **ML 扩展性**：**这是引入 AI 的核心切入点**。
    *   *传统模式*：加权平均。
    *   *AI 模式*：Arbiter 作为一个 **RL Agent (强化学习智能体)** 或 **XGBoost 模型**，输入是所有 Oracle 的信号，输出是最佳权重。

### 2.4 Executor (执行官) —— 交易生成层
**职责**：将 Arbiter 的理想目标转化为符合 A 股现实的交易指令。

*   **功能定义**：
    *   **Diff Calculation**：`Target` - `Current`。
    *   **Constraints (A股法则)**：
        *   *Lot Size*：向下取整到 100 股 (Round down to 100)。
        *   *T+1 Check*：检查可卖持仓（Sellable Shares）。
        *   *Limit Up/Down*：涨跌停无法成交检查。
    *   **Output**：`Order List` (Buy/Sell 指令列表)。

### 2.5 Gateway (折跃门) —— 账户与清算层
**职责**：维护账户状态，处理资金划转与撮合。这是整个系统的“真实账本”。

*   **功能定义**：
    *   **Warp Gate (撮合)**：接收 Order，基于当天的价格数据进行成交判定。
    *   **Shield Battery (护盾充能/分红)**：自动处理除权除息（XR/XD），增加现金，调整持仓股数。
    *   **State Keeping**：维护 `Total_Assets`, `Cash`, `Positions`, `Avg_Cost`。
*   **组件：Feedback (反馈/成本模型)**
    *   **Energy Drain**：计算交易摩擦成本。
    *   *逻辑*：佣金 (Commission) + 印花税 (Tax) + 滑点 (Slippage)。支持自定义滑点算法（如成交量加权）。

### 2.6 Preserver (保存者) —— 分析与记录层
**职责**：系统的“黑匣子”，记录一切历史并生成报告。

*   **功能定义**：
    *   **Khala's Memory**：按日记录净值曲线、持仓变化、交易日志。
    *   **Metrics**：计算 Sharpe, Sortino, Max Drawdown, Alpha, Beta。
    *   **Output**：可视化图表与回测报告。