class BacktestEngine:
    """
    回测主控程序。
    """
    
    # --- 状态存储 ---
    _history_states: List[AccountState] # 历史快照列表 (时光机)
    _current_index: int                 # 当前时间步的索引
    _context: Context                   # 运行时上下文
    _factors: List[Factor]              # 注册的因子列表
    
    def __init__(self, config: Dict):
        """
        根据 JSON 配置初始化：
        1. 加载数据到 DataProxy
        2. 初始化 AccountState (初始资金)
        3. 实例化 Factors
        """
        pass

    def step(self) -> AccountState:
        """
        [核心方法] 向前推演一天。
        
        流程伪代码:
        1. 时间指针 +1
        2. context.data_proxy.on_date_change(new_date)
        3. 更新持仓市值 (Mark to Market)
        4. target_weights = 聚合所有 factor.calculate(context) 的结果
        5. orders = 生成交易指令(target_weights, current_positions)
        6. 执行 orders，扣费，更新 context.account
        7. snapshot = context.snapshot()
        8. _history_states.append(snapshot)
        9. return snapshot
        """
        pass

    def back(self) -> AccountState:
        """
        [核心方法] 向后回退一天。
        
        流程伪代码:
        1. 检查 _current_index 是否 > 0
        2. _current_index -= 1
        3. state = _history_states[_current_index]
        4. 恢复环境: context.account = state.clone()
        5. 恢复数据指针: context.data_proxy.on_date_change(state.date)
        6. _history_states.pop() # 丢弃刚才那个"未来"的状态
        7. return state
        """
        pass

    def run_to_end(self):
        """
        便捷方法：连续调用 step() 直到结束。
        """
        pass
