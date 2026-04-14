# TODO

## 当前优先级

- 把 manager 的事件循环从“单标的决策”升级成“全局 observation -> manager -> execution”的统一循环。
- 给 manager 增加可训练配置层，明确哪些字段属于策略参数，哪些字段属于训练超参数。
- 为 `naive_dca_daily`、`naive_equal_weight_rebalance` 这类朴素 manager 补上正式实现。
- 把 manager fixtures 变成稳定的回归测试输入，后续新增 manager 也沿用同一套格式。
- 继续补齐分红、红利税和费用模型的边界测试。

## 中期事项

- 让 `run --plan` 支持更明确的路径提示和计划来源展示。
- 继续减少 `src` 里尚未使用的 scaffold 警告。
- 把 portfolio state 真正接入 manager 决策链，而不是只停留在结构定义。

## 设计提醒

- `run` 是唯一执行入口。
- `plan` 描述 manager、symbols、参数和执行约束。
- `portfolio` 是运行时状态，不应该被写成静态配置。
- `manager` 要能看见多标的、指数和外生特征，不能只看单根 K 线。