class Context:
    """
    上帝对象 (God Object)，包含因子决策所需的一切信息。
    它的生命周期贯穿整个回测过程，但在每个 step 会被更新。
    """
    
    # --- 属性声明 ---
    current_date: datetime
    account: AccountState        # 当前的账户状态
    data_proxy: 'DataProxy'      # 数据访问代理 (见下文)
    
    # --- 伪代码功能描述 ---
    # def history(self, symbol, count) -> DataFrame:
    #     便捷方法，通过 data_proxy 获取过去 N 天的历史数据
    
    # def snapshot(self) -> AccountState:
    #     返回当前账户状态的深拷贝 (用于存档)
