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
from src.system import json


if __name__ == '__main__':
    # use config next to this file (src/config.json)
    config_path = Path(__file__).resolve().parent / "config.json"
    json_cfg = json.read_json(config_path, default={"data_paths": {}})
    print("Loaded config from", config_path)
    print(json_cfg)

    # print yfinance path from config (resolve relative -> project root)
    yfinance_path = json_cfg.get("data_paths", {}).get("yfinance")
    if not yfinance_path:
        print("yfinance path not found in config")
    else:
        p = Path(yfinance_path)
        if not p.is_absolute():
            p = project_root / yfinance_path.lstrip("/\\")
        print("yfinance path (raw):", yfinance_path)
        print("yfinance path (resolved):", p)

