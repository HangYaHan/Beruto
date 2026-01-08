class DataProxy:
    """
    数据代理层。
    它的作用是屏蔽底层数据源的差异，并防止“未来函数”。
    因子只能通过它获取数据。
    """
    
    def on_date_change(self, new_date: datetime):
        """
        内部方法：当引擎步进时调用。
        更新内部的时间指针，确保 subsequent calls 只能拿到了解到 new_date 为止的数据。
        """
        pass

    def get_latest_bar(self, symbol: str) -> BarData:
        """
        获取今日(当前时刻)的行情。
        """
        pass

    def get_history(self, symbol: str, n: int) -> List[BarData]:
        """
        获取截止到当前时刻的前 n 条历史数据。
        """
        pass
