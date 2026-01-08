@dataclass
class BarData:
    """
    单条行情数据，代表某个标的在某一天的数据。
    """
    symbol: str
    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    # 预留扩展：可以存放 news_sentiment 等异构数据
    extra: Dict[str, Any]

@dataclass
class Position:
    """
    持仓状态。
    """
    symbol: str
    volume: int        # 持股数量
    avg_price: float   # 持仓成本
    last_price: float  # 最新市价 (用于计算浮盈)
    
    # 伪代码功能描述:
    # def market_value(self) -> float: 返回 volume * last_price
    # def unrealized_pnl(self) -> float: 返回 (last_price - avg_price) * volume

@dataclass
class AccountState:
    """
    账户在某一时刻的完整快照。
    用于支持“回退”功能，历史列表里存的就是这个对象。
    """
    date: datetime
    cash: float
    positions: Dict[str, Position]  # Key: Symbol
    total_assets: float             # cash + sum(position values)
    
    # 伪代码功能描述:
    # def clone(self): 返回自身的深拷贝 (Deep Copy)

@dataclass
class Order:
    """
    交易指令。
    """
    symbol: str
    volume: int       # 正数买入，负数卖出
    price: float      # 期望成交价 (市价单则为 None)
