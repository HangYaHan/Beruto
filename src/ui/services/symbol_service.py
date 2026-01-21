from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence

import akshare as ak
import pandas as pd

from src.system.settings import SettingsManager


class SymbolDataService:
    """Loads and maintains local symbol universe and saved symbol list."""

    def __init__(
        self,
        project_root: Path,
        settings: SettingsManager,
        logger: Callable[[str], None] | None = None,
    ) -> None:
        self.project_root = project_root
        self.settings = settings
        self.logger = logger
        self.symbol_cache_path = self.project_root / "data" / "symbols_a.csv"
        self.kline_cache_dir = self.project_root / "data" / "kline"
        self.kline_cache_dir.mkdir(parents=True, exist_ok=True)

        self._symbol_map: Dict[str, str] = {}
        self._name_to_code: Dict[str, str] = {}
        self._suggestions: List[str] = []

    # --- symbol universe ---
    def load_symbol_map(self, allow_fetch: bool = True) -> Dict[str, str]:
        cache_path = self.symbol_cache_path
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        if cache_path.exists():
            try:
                df = pd.read_csv(cache_path, dtype=str)
                if {"code", "name"}.issubset(df.columns):
                    mapping = dict(zip(df["code"], df["name"]))
                    self._apply_symbol_map(mapping)
                    return mapping
            except Exception as exc:
                self._log(f"Failed to read symbol cache {cache_path}: {exc}")
        if allow_fetch:
            mapping = self.fetch_and_cache_symbols()
            self._apply_symbol_map(mapping)
            return mapping
        return {}

    def fetch_and_cache_symbols(self) -> Dict[str, str]:
        try:
            a_df = ak.stock_zh_a_spot_em()[["代码", "名称"]]
            etf_df = ak.fund_etf_spot_em()[["代码", "名称"]]
            df = pd.concat([a_df, etf_df], ignore_index=True)
            df = df.drop_duplicates(subset=["代码"]).rename(columns={"代码": "code", "名称": "name"})
            df = df.sort_values("code")
            df.to_csv(self.symbol_cache_path, index=False, encoding="utf-8")
            self.set_last_refresh_date()
            mapping = dict(zip(df["code"], df["name"]))
            self._apply_symbol_map(mapping)
            return mapping
        except Exception as exc:
            self._log(f"Symbol fetch failed: {exc}")
            return {}

    def _apply_symbol_map(self, mapping: Dict[str, str]) -> None:
        self._symbol_map = mapping
        self._name_to_code = {name: code for code, name in mapping.items()}
        self._suggestions = [f"{code} {name}" for code, name in mapping.items()]

    # --- metadata ---
    def get_symbol_map(self) -> Dict[str, str]:
        return dict(self._symbol_map)

    def get_name_to_code(self) -> Dict[str, str]:
        return dict(self._name_to_code)

    def get_suggestions(self) -> List[str]:
        return list(self._suggestions)

    def set_last_refresh_date(self, date_str: str | None = None) -> None:
        if date_str is None:
            from datetime import datetime

            date_str = datetime.now().strftime("%Y-%m-%d")
        try:
            self.settings.set_last_refresh_date(date_str)
        except Exception as exc:
            self._log(f"Failed to set last refresh date: {exc}")

    def get_last_refresh_date(self) -> str:
        try:
            return self.settings.get_last_refresh_date()
        except Exception:
            return ""

    # --- saved symbols ---
    def get_saved_symbols(self) -> List[str]:
        try:
            return self.settings.get_saved_symbols()
        except Exception as exc:
            self._log(f"Failed to load saved symbols: {exc}")
            return []

    def replace_saved_symbols(self, codes: Sequence[str]) -> None:
        normalized = sorted({str(c).strip().upper() for c in codes if str(c).strip()})
        try:
            self.settings._settings.savedSymbols = list(normalized)
            self.settings.save()
        except Exception as exc:
            self._log(f"Failed to persist saved symbols: {exc}")

    def add_saved_symbol(self, code: str) -> None:
        self.settings.add_symbol(code)

    def remove_saved_symbols(self, codes: Iterable[str]) -> None:
        self.settings.remove_symbols(list(codes))

    # --- utils ---
    def _log(self, msg: str) -> None:
        if self.logger:
            try:
                self.logger(msg)
            except Exception:
                pass


__all__ = ["SymbolDataService"]
