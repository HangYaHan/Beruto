import os
import pandas as pd
# Use absolute import to reach the centralized system logger under `src.system`.
from src.system.log import get_logger

logger = get_logger(__name__)


def fetch(symbol, start, end, interval='1d', **kwargs):
    """从本地 CSV 文件读取数据。

    策略：如果 symbol 是文件路径（以 .csv 结尾），直接读取；否则在 `data/csv/` 下查找 <symbol>.csv。
    返回 DataFrame，index 为 DatetimeIndex，包含标准列（Open, High, Low, Close, Adj Close, Volume）。
    """
    # 支持传入文件路径或符号名
    if symbol.lower().endswith('.csv'):
        path = symbol
    else:
        base = kwargs.get('csv_base', os.path.join(os.getcwd(), 'data', 'csv'))
        path = os.path.join(base, f"{symbol}.csv")

    if not os.path.exists(path):
        logger.debug("CSV adapter: file not found for %s -> %s", symbol, path)
        return pd.DataFrame()

    try:
        df = pd.read_csv(path, parse_dates=True, index_col=0)
    except Exception as e:
        logger.exception("CSV adapter failed to read %s: %s", path, e)
        return pd.DataFrame()

    # 尝试规范化列名
    rename_map = {}
    for c in df.columns:
        lc = c.lower()
        if lc in ('open', 'open_price'):
            rename_map[c] = 'Open'
        elif lc in ('high',):
            rename_map[c] = 'High'
        elif lc in ('low',):
            rename_map[c] = 'Low'
        elif lc in ('close', 'close_price'):
            rename_map[c] = 'Close'
        elif lc in ('adj close', 'adj_close', 'adjclose'):
            rename_map[c] = 'Adj Close'
        elif lc in ('volume', 'vol'):
            rename_map[c] = 'Volume'

    if rename_map:
        df = df.rename(columns=rename_map)

    # 确保时间索引
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    # 按时间筛选
    if start:
        df = df[df.index >= pd.to_datetime(start)]
    if end:
        df = df[df.index <= pd.to_datetime(end)]

    logger.info("CSV adapter: fetched %s rows for %s", len(df), symbol)
    return df
