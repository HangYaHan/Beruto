"""
VirtualManager：支持装载任意数量策略（strategy），按日基于历史数据由每个策略产生操作（买/卖 X 股），
将各策略返回的操作求和得到 next_action，并在当日价格下执行（买/卖），记录持仓、现金、已实现/未实现盈亏和历史。

策略接口约定（必须实现）：
- decide(date: pd.Timestamp, history: pd.DataFrame) -> Dict[str, int]
    返回以 symbol 为键、正数表示买入股数、负数表示卖出股数的字典（可以为 0 / 省略）。
    history 为包含过去日期（不含当前日）的价格 DataFrame，index 为日期，columns 为 symbol。

注意：此实现为简化模型，不包含手续费、滑点、部分成交等复杂逻辑，适合作为回测基础。
"""
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import copy
import pandas as pd


class VirtualManager:
    def __init__(self, name: str, initial_cash: float = 100000.0) -> None:
        if initial_cash < 0:
            raise ValueError("initial_cash must be non-negative")
        self.name: str = name
        self.initial_cash: float = float(initial_cash)
        self.cash: float = float(initial_cash)
        # positions: symbol -> {'quantity': int, 'avg_cost': float}
        self.positions: Dict[str, Dict[str, float]] = {}
        # market prices: symbol -> last known price
        self._market_prices: Dict[str, float] = {}
        self.realized_pnl: float = 0.0
        # 交易历史（逐笔）
        self.history: List[Dict[str, Any]] = []
        # 每日快照历史（用于回测输出）
        self.daily_snapshots: List[Dict[str, Any]] = []
        # 策略列表
        self.strategies: List[Any] = []

    # --- 策略管理 ---
    def add_strategy(self, strategy: Any) -> None:
        """
        添加策略实例。策略需实现 decide(date, history) 方法（见顶部约定）。
        """
        if not hasattr(strategy, "decide") or not callable(strategy.decide):
            raise ValueError("strategy must implement decide(date, history) -> Dict[str,int]")
        self.strategies.append(strategy)

    # --- 市场价与估值 ---
    def update_market_price(self, symbol: str, price: float) -> None:
        if price is None or price < 0:
            return
        self._market_prices[symbol] = float(price)

    def get_portfolio_value(self) -> float:
        market_value = 0.0
        for sym, pos in self.positions.items():
            qty = pos.get("quantity", 0)
            price = self._market_prices.get(sym, pos.get("avg_cost", 0.0))
            market_value += qty * price
        return float(self.cash + market_value)

    def get_unrealized_pnl(self) -> float:
        unreal = 0.0
        for sym, pos in self.positions.items():
            qty = pos.get("quantity", 0)
            avg = pos.get("avg_cost", 0.0)
            price = self._market_prices.get(sym, avg)
            unreal += (price - avg) * qty
        return float(unreal)

    # --- 买卖执行（简化：全部以传入 price 成交） ---
    def _buy_at(self, symbol: str, quantity: int, price: float, timestamp: Optional[datetime] = None) -> bool:
        if quantity <= 0 or price <= 0:
            return False
        total = quantity * price
        if self.cash < total:
            # 资金不足：按比例缩减（简单处理），也可以直接拒绝
            max_affordable = int(self.cash // price)
            if max_affordable <= 0:
                return False
            quantity = max_affordable
            total = quantity * price
        self.cash -= total
        if symbol in self.positions:
            pos = self.positions[symbol]
            old_qty = pos["quantity"]
            old_avg = pos["avg_cost"]
            new_qty = old_qty + quantity
            new_avg = ((old_avg * old_qty) + total) / new_qty
            pos["quantity"] = new_qty
            pos["avg_cost"] = new_avg
        else:
            self.positions[symbol] = {"quantity": quantity, "avg_cost": float(price)}
        self.update_market_price(symbol, price)
        self._record_tx("BUY", symbol, quantity, price, timestamp)
        return True

    def _sell_at(self, symbol: str, quantity: int, price: float, timestamp: Optional[datetime] = None) -> bool:
        if quantity <= 0 or price <= 0:
            return False
        pos = self.positions.get(symbol)
        if not pos or pos.get("quantity", 0) <= 0:
            return False
        available = pos["quantity"]
        if quantity > available:
            # 如果卖出量大于持仓，卖出全部
            quantity = available
        proceeds = quantity * price
        avg = pos["avg_cost"]
        self.cash += proceeds
        # realized pnl
        self.realized_pnl += (price - avg) * quantity
        pos["quantity"] -= quantity
        if pos["quantity"] == 0:
            del self.positions[symbol]
            self._market_prices.pop(symbol, None)
        else:
            self.positions[symbol] = pos
        self.update_market_price(symbol, price)
        self._record_tx("SELL", symbol, quantity, price, timestamp)
        return True

    def _record_tx(self, side: str, symbol: str, quantity: int, price: float, timestamp: Optional[datetime] = None) -> None:
        """
        记录逐笔交易到 `self.history`。保留成交类型、标的、数量、价格、时间、成交后现金和持仓快照。
        """
        tx = {
            "type": side,
            "symbol": symbol,
            "quantity": int(quantity),
            "price": float(price),
            "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp),
            "cash": float(self.cash),
            "positions": copy.deepcopy(self.positions),
        }
        self.history.append(tx)

    # --- 策略决策汇总与执行 ---
    def _aggregate_actions(self, date: pd.Timestamp, history: pd.DataFrame) -> Dict[str, int]:
        """
        调用所有策略的 decide，汇总每个 symbol 的净买卖数量（整数）。
        返回字典 symbol -> net_quantity（正为买入，负为卖出）。
        """
        agg: Dict[str, int] = {}
        for strat in self.strategies:
            try:
                actions = strat.decide(date, history) or {}
                if not isinstance(actions, dict):
                    continue
                for sym, qty in actions.items():
                    if qty is None:
                        continue
                    agg[sym] = agg.get(sym, 0) + int(qty)
            except Exception:
                # 策略出错时忽略本次决策（上层可记录日志）
                continue
        return agg

    def _execute_actions(self, actions: Dict[str, int], price_map: Dict[str, float], timestamp: Optional[datetime] = None) -> None:
        """
        执行汇总后的 actions：
        - 对每个 symbol，正数调用 _buy_at，负数调用 _sell_at
        - price_map 为当日价格字典 symbol->price（必须提供用于成交价格）
        """
        for sym, net_qty in actions.items():
            if net_qty == 0:
                continue
            price = price_map.get(sym)
            if price is None or price <= 0:
                # 无法成交（价格未知），跳过
                continue
            if net_qty > 0:
                self._buy_at(sym, net_qty, price, timestamp)
            else:
                self._sell_at(sym, -net_qty, price, timestamp)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "initial_cash": self.initial_cash,
            "cash": self.cash,
            "positions": copy.deepcopy(self.positions),
            "market_prices": copy.deepcopy(self._market_prices),
            "portfolio_value": float(self.get_portfolio_value()),
            "unrealized_pnl": float(self.get_unrealized_pnl()),
            "realized_pnl": float(self.realized_pnl),
            "total_pnl": float(self.realized_pnl + self.get_unrealized_pnl()),
            "return_pct": (self.get_portfolio_value() - self.initial_cash) / self.initial_cash if self.initial_cash else 0.0,
            "n_positions": len(self.positions),
            "last_tx": self.history[-1] if self.history else None,
        }

    def get_history(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self.history)

    def get_daily_snapshots(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self.daily_snapshots)
