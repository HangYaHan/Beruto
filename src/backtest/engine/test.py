import numpy as np

from wrapper import ChronoEngine


def main() -> None:
    days, stocks = 5, 3
    prices = np.full((days, stocks), 10.0, dtype=np.float64)
    signals = np.zeros((days, stocks), dtype=np.float64)
    signals[0, 0] = 0.5  # buy 50% of cash on stock0
    signals[2, 0] = -0.5  # sell half of position

    eng = ChronoEngine(initial_cash=100000.0)
    equity = eng.run(prices, signals)
    print("Equity curve:", equity)


if __name__ == "__main__":
    main()
