class Factor(ABC):
    """
    所有因子的基类。
    """
    
    def __init__(self, params: Dict):
        """
        初始化因子参数 (如 BuyHold 的 ratio)。
        """
        pass

    @abstractmethod
    def calculate(self, context: Context, symbol: str) -> Optional[float]:
        """
        核心计算逻辑。
        
        Args:
            context: 包含账户、历史行情、新闻等的全量上下文。
            symbol: 当前正在计算的标的。
            
        Returns:
            Target Weight (float): 目标仓位权重 (0.0 ~ 1.0)。
            None: 表示该因子对该标的没有意见 (Do Nothing)。
        """
        pass
