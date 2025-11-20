import pandas as pd
import matplotlib.pyplot as plt
from src.portfolio.manager import VirtualManager


class MA20CrossoverStrategy:
    """Simplified MA20 crossover: long when price stays above MA20, flat otherwise."""

    def __init__(self, symbol: str, qty: int):
        self.symbol = symbol
        self.qty = qty
        self.position = 0  # 当前持仓数量

    def decide(self, date, history):
        if 'MA20' not in history.columns:
            return {}
        try:
            row = history.loc[date]
        except KeyError:
            return {}

        price = row.get('Close') if 'Close' in row else row.get('close')
        ma20 = row.get('MA20')
        if price is None or pd.isna(price) or pd.isna(ma20):
            return {}

        actions = {}
        # 当价格高于均线且无持仓 -> 建仓
        if price > ma20 and self.position <= 0:
            actions[self.symbol] = self.qty
            self.position += self.qty
        # 当价格跌破均线且有持仓 -> 平仓
        elif price < ma20 and self.position > 0:
            actions[self.symbol] = -self.position
            self.position = 0
        return actions

vm = VirtualManager("Test", initial_cash=100000)
symbol = "sh600000"
vm.add_strategy(MA20CrossoverStrategy(symbol, 10))

# 3. 读取仓库自带样本数据（注意文件名可能带后缀）
df = pd.read_csv(r"data\sh600000.parquet.csv", parse_dates=["date"], index_col="date")

# 计算 20 日均线（用于策略与绘图）
# 确保使用小写列名 'close'；如有 'Close' 列则统一为 'close'
if 'Close' in df.columns and 'close' not in df.columns:
    df = df.rename(columns={'Close': 'close'})
df['MA20'] = df['close'].rolling(window=20, min_periods=1).mean()

# 4. 回测
for date, row in df.iterrows():
    # 本地样本使用小写列名 'close'
    price = row.get("Close") if "Close" in row else row.get("close")

    vm.update_market_price(symbol, price)
    actions = vm._aggregate_actions(date, df.loc[:date])
    vm._execute_actions(actions, {symbol: price}, timestamp=date)

    vm.daily_snapshots.append({
        "date": date,
        "portfolio_value": vm.get_portfolio_value(),
        "cash": vm.cash,
        "positions": vm.positions.copy(),
    })

# 5. 查看结果
print("Final summary:")
print(vm.get_summary())

if vm.daily_snapshots:
    snapshot_df = pd.DataFrame(vm.daily_snapshots)
    if 'date' in snapshot_df.columns:
        snapshot_df = snapshot_df.set_index('date')
    snapshot_df['pnl'] = snapshot_df['portfolio_value'] - vm.initial_cash
    # 与价格数据对齐，方便绘图
    snapshot_df = snapshot_df.reindex(df.index, method='ffill')

    fig, ax_price = plt.subplots(figsize=(12, 6))
    ax_price.plot(df.index, df['close'], label='Close', color='tab:blue')
    ax_price.plot(df.index, df['MA20'], label='MA20', color='tab:orange')
    ax_price.set_xlabel('Date')
    ax_price.set_ylabel('Price')
    ax_price.grid(True)

    ax_pnl = ax_price.twinx()
    ax_pnl.plot(snapshot_df.index, snapshot_df['pnl'], label='PnL (vs initial)', color='tab:green')
    ax_pnl.set_ylabel('PnL (Absolute)')
    ax_pnl.axhline(0, color='grey', linestyle='--', linewidth=1)

    # 标注买卖点
    hist_df = pd.DataFrame(vm.history)
    if not hist_df.empty:
        hist_df['ts'] = pd.to_datetime(hist_df['timestamp'], errors='coerce')
        buys = hist_df[hist_df['type'] == 'BUY']
        sells = hist_df[hist_df['type'] == 'SELL']

        def price_at(ts):
            try:
                return df.loc[ts, 'close']
            except Exception:
                idx = df.index.get_indexer([ts], method='nearest')[0]
                return df['close'].iat[idx]

        if not buys.empty:
            ax_price.scatter(buys['ts'], [price_at(t) for t in buys['ts']], marker='^', color='green', s=70, label='Buy', zorder=5)
        if not sells.empty:
            ax_price.scatter(sells['ts'], [price_at(t) for t in sells['ts']], marker='v', color='red', s=70, label='Sell', zorder=5)

    handles_price, labels_price = ax_price.get_legend_handles_labels()
    handles_pnl, labels_pnl = ax_pnl.get_legend_handles_labels()
    ax_price.legend(handles_price + handles_pnl, labels_price + labels_pnl, loc='upper left')
    ax_price.set_title(f'Price vs MA20 vs PnL: {symbol}')

    combined_path = r"data\backtest_price_ma20_pnl.png"
    try:
        fig.savefig(combined_path, dpi=150, bbox_inches='tight')
        print(f"Saved combined plot to {combined_path}")
    except Exception as e:
        print('Failed to save combined plot:', e)

    try:
        plt.show()
    except Exception:
        pass
