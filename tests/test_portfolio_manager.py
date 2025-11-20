import pandas as pd
import pytest
from src.portfolio.manager import VirtualManager


class BuyStrategy:
    def __init__(self, symbol, qty):
        self.symbol = symbol
        self.qty = qty

    def decide(self, date, history):
        return {self.symbol: self.qty}


class SellStrategy:
    def __init__(self, symbol, qty):
        self.symbol = symbol
        self.qty = -abs(qty)

    def decide(self, date, history):
        return {self.symbol: self.qty}


def test_buy_and_hold_and_sell_flow():
    vm = VirtualManager('t1', initial_cash=1000.0)

    # 买入 10 股价格 10 -> 花费 100
    vm.add_strategy(BuyStrategy('ABC', 10))
    actions = vm._aggregate_actions(pd.Timestamp('2020-01-02'), pd.DataFrame())
    vm._execute_actions(actions, {'ABC': 10.0})

    assert vm.positions['ABC']['quantity'] == 10
    assert pytest.approx(vm.positions['ABC']['avg_cost'], rel=1e-6) == 10.0
    assert pytest.approx(vm.cash, rel=1e-6) == 900.0

    # 市场价格变为 12 -> unrealized pnl = (12-10)*10 = 20
    vm.update_market_price('ABC', 12.0)
    assert pytest.approx(vm.get_unrealized_pnl(), rel=1e-6) == 20.0
    prev_realized = vm.realized_pnl

    # 卖出全部 10 股价格 12
    vm.strategies = []
    vm.add_strategy(SellStrategy('ABC', 10))
    actions = vm._aggregate_actions(pd.Timestamp('2020-01-03'), pd.DataFrame())
    vm._execute_actions(actions, {'ABC': 12.0})

    assert 'ABC' not in vm.positions
    # realized pnl should increase by 20
    assert pytest.approx(vm.realized_pnl - prev_realized, rel=1e-6) == 20.0
    # cash returned: 900 + 120 = 1020
    assert pytest.approx(vm.cash, rel=1e-6) == 1020.0


def test_insufficient_cash_buys_partial():
    vm = VirtualManager('t2', initial_cash=50.0)
    vm.add_strategy(BuyStrategy('XYZ', 10))
    actions = vm._aggregate_actions(pd.Timestamp('2020-01-02'), pd.DataFrame())
    # price 10 -> can only buy 5 shares with 50 cash
    vm._execute_actions(actions, {'XYZ': 10.0})
    # should have bought floor(50/10) = 5
    assert vm.positions['XYZ']['quantity'] == 5
    assert vm.cash >= 0


def test_summary_and_history_records():
    vm = VirtualManager('t3', initial_cash=1000.0)
    vm.add_strategy(BuyStrategy('MNO', 3))
    vm._execute_actions(vm._aggregate_actions(pd.Timestamp('2020-01-02'), pd.DataFrame()), {'MNO': 5.0})
    summary = vm.get_summary()
    assert summary['name'] == 't3'
    assert summary['n_positions'] == 1
    assert summary['last_tx'] is not None
