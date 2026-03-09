from __future__ import annotations

import pandas as pd

from core.analytics import summarize_performance
from core.models import BacktestResult, PortfolioConfig, PositionState, StrategySpec, SymbolSpec, TradeAction
from core.strategy_base import Strategy
from core.strategies.add_on_five_down import AddOnFiveDownStrategy
from core.strategies.conservative_t import ConservativeTStrategy
from core.strategies.do_nothing import DoNothingStrategy
from core.strategies.peak_drawdown_sell import PeakDrawdownSellStrategy
from core.strategies.take_profit_retrace import TakeProfitRetraceStrategy


STRATEGY_FACTORY: dict[str, type[Strategy]] = {
    "do_nothing": DoNothingStrategy,
    "peak_drawdown_sell": PeakDrawdownSellStrategy,
    "take_profit_retrace": TakeProfitRetraceStrategy,
    "conservative_t": ConservativeTStrategy,
    "add_on_five_down": AddOnFiveDownStrategy,
}


def _select_exec_price(row: pd.Series) -> tuple[float, str]:
    if "open" in row.index and pd.notna(row["open"]) and float(row["open"]) > 0:
        return float(row["open"]), "open"
    return float(row["close"]), "close"


def _recent_trade_in_last_5_bars(history: pd.DataFrame, trade_dates: list[pd.Timestamp]) -> bool:
    if history.empty or not trade_dates:
        return False
    recent_dates = set(pd.to_datetime(history["date"].tail(5)).tolist())
    for td in trade_dates:
        if pd.Timestamp(td) in recent_dates:
            return True
    return False


def _build_symbol_strategy_objects(spec: SymbolSpec) -> list[tuple[Strategy, StrategySpec]]:
    out: list[tuple[Strategy, StrategySpec]] = []
    for st in spec.strategies:
        cls = STRATEGY_FACTORY.get(st.name)
        if cls is None:
            raise ValueError(f"Unsupported strategy: {st.name}")
        out.append((cls(), st))
    return out


def run_portfolio_backtest(
    bars_by_symbol: dict[str, pd.DataFrame],
    config: PortfolioConfig,
) -> BacktestResult:
    if not config.symbols:
        raise ValueError("Portfolio config has no symbols.")

    symbol_specs = {s.symbol: s for s in config.symbols}
    calendar = sorted(
        {
            pd.Timestamp(d)
            for symbol, bars in bars_by_symbol.items()
            if symbol in symbol_specs and bars is not None and not bars.empty
            for d in pd.to_datetime(bars["date"]).tolist()
        }
    )
    calendar = [d for d in calendar if config.start_date <= d <= config.end_date]
    if not calendar:
        return BacktestResult(
            equity_curve=pd.DataFrame(columns=["date", "equity"]),
            daily_returns=pd.Series(dtype=float),
            signals=pd.DataFrame(),
            metrics={},
            notes=["No overlapping bars in selected period."],
        )

    cleaned_bars: dict[str, pd.DataFrame] = {}
    indexed_bars: dict[str, pd.DataFrame] = {}
    for symbol, spec in symbol_specs.items():
        bars = bars_by_symbol.get(symbol)
        if bars is None or bars.empty:
            raise ValueError(f"No bars for symbol: {symbol}")
        b = bars.copy().sort_values("date").reset_index(drop=True)
        b = b[(b["date"] >= config.start_date) & (b["date"] <= config.end_date)].reset_index(drop=True)
        if b.empty:
            raise ValueError(f"No bars in range for symbol: {symbol}")
        cleaned_bars[symbol] = b
        indexed_bars[symbol] = b.set_index("date")

    strategy_objs = {symbol: _build_symbol_strategy_objects(spec) for symbol, spec in symbol_specs.items()}

    notes = [f"Portfolio backtest with {len(symbol_specs)} symbols."]
    cash = float(config.initial_cash)
    positions = {symbol: PositionState() for symbol in symbol_specs}

    first_date = calendar[0]
    for symbol, spec in symbol_specs.items():
        row = indexed_bars[symbol].loc[first_date] if first_date in indexed_bars[symbol].index else None
        if row is None:
            continue
        px, px_type = _select_exec_price(row)
        alloc_cash = config.initial_cash * spec.weight
        shares = alloc_cash / px if px > 0 else 0.0
        cost = shares * px * (1.0 + config.fee_rate)
        if cost > cash:
            shares = cash / (px * (1.0 + config.fee_rate)) if px > 0 else 0.0
            cost = shares * px * (1.0 + config.fee_rate)
        if shares > 0:
            positions[symbol].shares = shares
            positions[symbol].avg_buy_price = px
            positions[symbol].trade_dates.append(first_date)
            cash -= cost
            notes.append(f"Init buy {symbol}: {shares:.2f} shares @ {px_type}={px:.3f}")

    equity_vals: list[float] = []
    dates: list[pd.Timestamp] = []
    order_rows: list[dict] = []
    last_equity: float | None = None
    daily_rets: list[float] = []

    for date in calendar:
        for symbol, spec in symbol_specs.items():
            if date not in indexed_bars[symbol].index:
                continue

            symbol_bars = cleaned_bars[symbol]
            history = symbol_bars[symbol_bars["date"] < date]
            if history.empty:
                continue

            row = indexed_bars[symbol].loc[date]
            px, px_type = _select_exec_price(row)
            if px <= 0:
                continue

            position = positions[symbol]

            sell_ratio = 0.0
            buy_ratio = 0.0
            reasons: list[str] = []

            for strategy, st_spec in strategy_objs[symbol]:
                params = {
                    "x_pct": st_spec.x_pct,
                    "y_pct": st_spec.y_pct,
                    "recent_trade_in_5": _recent_trade_in_last_5_bars(history, position.trade_dates),
                }
                action = strategy.generate_action(history, date, position, params)
                if action.action == "SELL":
                    sell_ratio += action.ratio
                    reasons.append(f"{st_spec.name}:SELL({action.ratio:.2f})")
                elif action.action == "BUY":
                    buy_ratio += action.ratio
                    reasons.append(f"{st_spec.name}:BUY({action.ratio:.2f})")

            sell_ratio = min(1.0, max(0.0, sell_ratio))
            buy_ratio = min(1.0, max(0.0, buy_ratio))

            shares_sold = 0.0
            shares_bought = 0.0

            if sell_ratio > 0 and position.shares > 0:
                shares_sold = position.shares * sell_ratio
                proceeds = shares_sold * px * (1.0 - config.fee_rate)
                position.shares -= shares_sold
                cash += proceeds
                position.trade_dates.append(date)

            # Buy size uses current holding shares as base by user requirement.
            if buy_ratio > 0 and position.shares > 0:
                desired_buy = position.shares * buy_ratio
                max_affordable = cash / (px * (1.0 + config.fee_rate))
                shares_bought = min(desired_buy, max(0.0, max_affordable))
                if shares_bought > 0:
                    cost = shares_bought * px * (1.0 + config.fee_rate)
                    new_shares = position.shares + shares_bought
                    if new_shares > 0:
                        position.avg_buy_price = (
                            position.avg_buy_price * position.shares + px * shares_bought
                        ) / new_shares
                    position.shares = new_shares
                    cash -= cost
                    position.trade_dates.append(date)

            if shares_sold > 0 or shares_bought > 0:
                order_rows.append(
                    {
                        "date": date,
                        "symbol": symbol,
                        "price": px,
                        "price_type": px_type,
                        "shares_sold": shares_sold,
                        "shares_bought": shares_bought,
                        "reason": " | ".join(reasons) if reasons else "N/A",
                    }
                )

        holdings_value = 0.0
        for symbol in symbol_specs:
            if date not in indexed_bars[symbol].index:
                continue
            close_px = float(indexed_bars[symbol].loc[date]["close"])
            holdings_value += positions[symbol].shares * close_px

        equity = cash + holdings_value
        dates.append(date)
        equity_vals.append(equity)

        if last_equity is None or last_equity <= 0:
            daily_rets.append(0.0)
        else:
            daily_rets.append(equity / last_equity - 1.0)
        last_equity = equity

    equity_curve = pd.DataFrame({"date": dates, "equity": equity_vals})
    equity_curve["equity"] = equity_curve["equity"] / config.initial_cash
    daily_returns = pd.Series(daily_rets, index=dates, name="daily_return")
    signals = pd.DataFrame(order_rows)
    metrics = summarize_performance(daily_returns, equity_curve["equity"])

    return BacktestResult(
        equity_curve=equity_curve,
        daily_returns=daily_returns,
        signals=signals,
        metrics=metrics,
        notes=notes,
    )


def run_backtest(
    bars: pd.DataFrame,
    strategy: Strategy,
    start_date: str | pd.Timestamp | None = None,
    end_date: str | pd.Timestamp | None = None,
    fee_rate: float = 0.0,
    initial_weight: float = 0.0,
) -> BacktestResult:
    # Compatibility wrapper: map single-symbol run to portfolio engine.
    symbol = "SINGLE"
    cfg = PortfolioConfig(
        initial_cash=1_000_000.0,
        fee_rate=fee_rate,
        start_date=pd.Timestamp(start_date) if start_date is not None else pd.Timestamp.min,
        end_date=pd.Timestamp(end_date) if end_date is not None else pd.Timestamp.max,
        symbols=[
            SymbolSpec(
                symbol=symbol,
                weight=1.0,
                strategies=[StrategySpec(name="do_nothing", x_pct=0.0, y_pct=0.0)],
            )
        ],
    )
    result = run_portfolio_backtest({symbol: bars}, cfg)
    result.notes.append(
        "run_backtest compatibility mode uses do_nothing strategy. Use run_portfolio_backtest for full feature set."
    )
    return result
