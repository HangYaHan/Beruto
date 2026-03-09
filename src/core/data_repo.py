from __future__ import annotations

from pathlib import Path

import akshare as ak
import pandas as pd


class DataRepository:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def normalize_bars(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])

        col_candidates = {
            "date": ["date", "日期", "时间"],
            "open": ["open", "开盘"],
            "high": ["high", "最高"],
            "low": ["low", "最低"],
            "close": ["close", "收盘"],
            "volume": ["volume", "成交量"],
        }

        selected: dict[str, str] = {}
        for target, candidates in col_candidates.items():
            src = next((c for c in candidates if c in df.columns), None)
            if src is None:
                raise ValueError(f"Data missing required column for '{target}', candidates={candidates}")
            selected[target] = src

        out = pd.DataFrame({target: df[src] for target, src in selected.items()})
        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        for c in ["open", "high", "low", "close", "volume"]:
            out[c] = pd.to_numeric(out[c], errors="coerce")

        out = out.dropna(subset=["date", "close"]).drop_duplicates(subset=["date"]).sort_values("date")
        out = out.reset_index(drop=True)
        return out

    def cache_path(self, symbol: str) -> Path:
        return self.cache_dir / f"{symbol}.csv"

    def list_cached_symbols(self) -> list[str]:
        symbols: list[str] = []
        for p in self.cache_dir.glob("*.csv"):
            s = p.stem.strip()
            if s.isdigit() and len(s) == 6:
                symbols.append(s)
        return sorted(set(symbols))

    def load_cache(self, symbol: str) -> pd.DataFrame:
        p = self.cache_path(symbol)
        if not p.exists():
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        df = pd.read_csv(p)
        return self.normalize_bars(df)

    def save_cache(self, symbol: str, bars: pd.DataFrame) -> None:
        p = self.cache_path(symbol)
        bars.to_csv(p, index=False)

    def _fetch_stock_hist(self, symbol: str, start_date: str | None = None) -> pd.DataFrame:
        kwargs = {
            "symbol": symbol,
            "period": "daily",
            "adjust": "qfq",
        }
        if start_date:
            kwargs["start_date"] = start_date
            kwargs["end_date"] = pd.Timestamp.today().strftime("%Y%m%d")
        return ak.stock_zh_a_hist(**kwargs)

    def _fetch_etf_hist(self, symbol: str, start_date: str | None = None) -> pd.DataFrame:
        kwargs = {
            "symbol": symbol,
            "period": "daily",
            "adjust": "qfq",
        }
        if start_date:
            kwargs["start_date"] = start_date
            kwargs["end_date"] = pd.Timestamp.today().strftime("%Y%m%d")
        return ak.fund_etf_hist_em(**kwargs)

    def fetch_remote(self, symbol: str, start_date: str | None = None) -> pd.DataFrame:
        errors: list[str] = []

        for fetcher in (self._fetch_stock_hist, self._fetch_etf_hist):
            try:
                raw = fetcher(symbol, start_date=start_date)
                normalized = self.normalize_bars(raw)
                if not normalized.empty:
                    return normalized
                errors.append(f"{fetcher.__name__}: empty result")
            except Exception as exc:
                errors.append(f"{fetcher.__name__}: {exc}")

        if start_date:
            # Incremental updates can be empty when no new trading day is available.
            return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        raise RuntimeError("AkShare fetch failed. " + " | ".join(errors))

    def get_bars(self, symbol: str, refresh: bool = True) -> pd.DataFrame:
        symbol = symbol.strip()
        if not (symbol.isdigit() and len(symbol) == 6):
            raise ValueError("symbol must be a 6-digit code, e.g. 600519 or 510300")

        cached = self.load_cache(symbol)
        if not refresh:
            return cached

        start_date = None
        if not cached.empty:
            next_day = cached["date"].iloc[-1] + pd.Timedelta(days=1)
            start_date = next_day.strftime("%Y%m%d")

            if next_day.normalize() > pd.Timestamp.today().normalize():
                return cached

        fresh = self.fetch_remote(symbol, start_date=start_date)

        if cached.empty:
            merged = fresh
        elif fresh.empty:
            merged = cached
        else:
            merged = pd.concat([cached, fresh], ignore_index=True)
            merged = self.normalize_bars(merged)

        self.save_cache(symbol, merged)
        return merged

    def get_bars_batch(self, symbols: list[str], refresh: bool = False) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
        bars_map: dict[str, pd.DataFrame] = {}
        errors: dict[str, str] = {}
        for symbol in symbols:
            try:
                bars_map[symbol] = self.get_bars(symbol, refresh=refresh)
            except Exception as exc:
                errors[symbol] = str(exc)
        return bars_map, errors
