因子模板说明（已从旧 Task 概念重构）

概述
- `tasks/` 现在只保存“因子模板”示例，不再包含回测日期、资金、风控等信息。
- 每个模板描述**单个因子**需要的参数：模块路径、类名、默认参数。时间区间和执行设定应在后续回测/执行管线中单独提供。

文件列表
- `Templates/Base_Template.json`：通用占位模板。
- `Templates/SMA_Template.json`：均线交叉因子参数示例。
- `Templates/MACD_Template.json`：MACD 因子参数示例。
- `Templates/MACDMonotone_Template.json`：单调 MACD 因子示例。
- `Templates/SupportResistance_Template.json`：支撑阻力突破因子示例。
- `Templates/BuyAndHold_Template.json`：一次性买入并持有的因子示例。

字段约定
- `name`：模板名称（建议与计划中的因子别名一致）。
- `module`：因子所在模块的可导入路径，例如 `src.factor.builtin`。
- `class`：因子类名，例如 `SMAFactor`。
- `params`：仅包含该因子自身的参数，不涉及时间范围、成交、风控等跨因子信息。

如何使用
1. 复制一个模板 JSON。
2. 替换 `symbol` 及参数值以适配目标标的。
3. 在 `strategies/*.json` 中引用这些参数，组合成新的策略计划。

注意
- 新的“策略计划”存放于仓库根目录的 `strategies/`，格式示例见 `strategies/demo_plan.json`。
- 回测引擎重写中；当前 CLI 的 `backtest PLAN_NAME` 仅做计划预览。
