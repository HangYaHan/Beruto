import time
import importlib
from .storage import read_cached, write_cache
from .exceptions import RateLimitError, DataNotFoundError
from src.system.log import get_logger

logger = get_logger(__name__)

# Map logical adapter names to module import paths. The adapter module is only
# imported when actually selected to avoid heavy optional dependencies (e.g.
# yfinance) at import time.
ADAPTER_MODULES = {
    'csv': 'src.data.adapters.csv_adapter',
    'yfinance': 'src.data.adapters.yfinance_adapter',
}


def select_adapter(name):
    module_path = ADAPTER_MODULES.get(name)
    if module_path is None:
        return None
    try:
        return importlib.import_module(module_path)
    except Exception:
        logger.exception("Failed to import adapter module: %s", module_path)
        raise


def get_history(symbol, start, end, source='yfinance', interval='1d', adjusted=True,
                cache=True, max_retries=3, backoff_factor=1, refresh=False, **kwargs):
    """Unified external interface: prefer cached data first, otherwise fetch from the adapter and write to cache.

    Implements a simple retry policy: on RateLimitError, retry with exponential backoff.
    """
    logger.info("get_history called: symbol=%s source=%s start=%s end=%s interval=%s cache=%s refresh=%s",
                symbol, source, start, end, interval, cache, refresh)

    if cache and not refresh:
        df = read_cached(symbol, start, end)
        if df is not None and not df.empty:
            logger.info("cache hit for %s rows=%s", symbol, len(df))
            return df
        logger.info("cache miss for %s", symbol)

    adapter = select_adapter(source)
    if adapter is None:
        logger.error("Unknown data source requested: %s", source)
        raise ValueError(f"Unknown data source: {source}")

    last_exc = None
    for attempt in range(max_retries):
        try:
            logger.debug("Attempt %d fetching %s from %s", attempt + 1, symbol, source)
            df = adapter.fetch(symbol, start, end, interval=interval, adjusted=adjusted, **kwargs)
            if df is None or df.empty:
                # adapter returned empty -> treat as not found
                logger.warning("Adapter returned empty for %s from %s", symbol, source)
                raise DataNotFoundError(f"No data for {symbol} from {source}")
            if cache:
                try:
                    write_cache(symbol, df)
                except Exception:
                    logger.exception("Failed to write cache for %s", symbol)
            logger.info("Fetched data for %s rows=%s", symbol, len(df))
            return df
        except RateLimitError as e:
            last_exc = e
            wait = (2 ** attempt) * backoff_factor
            logger.warning("Rate limit when fetching %s (attempt=%d), sleeping %s seconds", symbol, attempt + 1, wait)
            time.sleep(wait)
            continue
        except DataNotFoundError:
            logger.error("Data not found for %s from %s", symbol, source)
            raise
        except Exception as e:
            # other exceptions: break and rethrow later
            last_exc = e
            logger.exception("Error fetching %s from %s: %s", symbol, source, e)
            break

    logger.error("Failed to fetch %s after attempts=%s", symbol, max_retries)
    raise last_exc if last_exc is not None else RuntimeError('Failed to fetch data')

def valid_test():
    print("This is a test function.")
    pass