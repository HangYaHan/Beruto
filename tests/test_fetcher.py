# This file is designed to test anything in the src directory
import sys
from pathlib import Path

# Make it possible to run this file directly (python src/test.py)
# by ensuring the project root is on sys.path so `src` can be imported.
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from src.data import fetcher
from datetime import datetime
from src.data import fetcher
from src.data.exceptions import AdapterError


def main():
    symbol = "sh600000"      # example: 浦发银行
    start_date = "20200101"
    end_date = "20251112"

    print(f"Fetching {symbol} from {start_date} to {end_date} via akshare...")
    try:
        df = fetcher.get_history(symbol, start_date, end_date, source='akshare', cache=True, refresh=False)
        print(f"Fetched rows: {len(df)}")
        if not df.empty:
            print("Cached to disk under data_cache/ (parquet or csv fallback)")
    except AdapterError as ae:
        print("Adapter error:", ae)
        print("Hint: ensure `akshare` is installed in your environment: `pip install akshare`")
    except Exception as e:
        print("Failed to fetch:", e)


if __name__ == '__main__':
    main()