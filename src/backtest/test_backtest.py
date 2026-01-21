from datetime import datetime

from src.backtest.core import BacktestEngine

if __name__ == "__main__":
    config = {
        "Universe": {
            "symbols": ["000712", "563020", "600519", "601000"],
            "start_date": "2024-01-01",
            "end_date": datetime.now().strftime("%Y-%m-%d"),
        },
        "Execution": {"initial_cash": 100000.0},
    }
    engine = BacktestEngine(config)
    snapshots = engine.run_to_end()
    print(f"Ran {len(snapshots)} steps; final assets = {snapshots[-1].total_assets if snapshots else engine._context.account.total_assets}")
