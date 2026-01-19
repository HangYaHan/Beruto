from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any


DEFAULT_SETTINGS_FILENAME = "settings.json"


@dataclass
class FactorParamSpec:
    type: str
    default: Optional[Any] = None
    min: Optional[float] = None
    max: Optional[float] = None
    description: str = ""


@dataclass
class Settings:
    lastRefreshDate: str = ""
    savedSymbols: List[str] = field(default_factory=list)
    factors: Dict[str, Dict[str, Dict[str, Any]]] = field(default_factory=dict)


class SettingsManager:
    """Load/save project settings from a single JSON file under data/."""

    def __init__(self, project_root: Optional[Path] = None, filename: str = DEFAULT_SETTINGS_FILENAME) -> None:
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self.data_dir = self.project_root / "data"
        self.path = self.data_dir / filename
        self._settings = Settings()
        self._ensure_data_dir()
        self._load_or_initialize()

    def _ensure_data_dir(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)

    # --- public API ---
    @property
    def settings(self) -> Settings:
        return self._settings

    def save(self) -> None:
        obj = {
            "lastRefreshDate": self._settings.lastRefreshDate,
            "savedSymbols": sorted(set(map(str.upper, self._settings.savedSymbols))),
            "factors": self._settings.factors,
        }
        self.path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

    def set_last_refresh_date(self, date_str: str) -> None:
        self._settings.lastRefreshDate = date_str
        self.save()

    def get_last_refresh_date(self) -> str:
        return self._settings.lastRefreshDate

    def add_symbol(self, code: str) -> None:
        code = code.strip().upper()
        if not code:
            return
        if code not in self._settings.savedSymbols:
            self._settings.savedSymbols.append(code)
            self.save()

    def remove_symbols(self, codes: List[str]) -> None:
        target = {c.strip().upper() for c in codes}
        self._settings.savedSymbols = [c for c in self._settings.savedSymbols if c.upper() not in target]
        self.save()

    def get_saved_symbols(self) -> List[str]:
        return list(self._settings.savedSymbols)

    # --- internals ---
    def _load_or_initialize(self) -> None:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self._apply_loaded(data)
                return
            except Exception:
                pass
        # Initialize from legacy files then persist
        self._settings = self._load_from_legacy()
        self.save()

    def _apply_loaded(self, data: Dict[str, Any]) -> None:
        last = str(data.get("lastRefreshDate") or "")
        saved = [str(s).strip().upper() for s in (data.get("savedSymbols") or []) if str(s).strip()]
        factors = data.get("factors") or self._default_factors()
        self._settings = Settings(lastRefreshDate=last, savedSymbols=saved, factors=factors)

    def _load_from_legacy(self) -> Settings:
        # legacy files
        last_path = self.data_dir / "last_refresh.txt"
        saved_path = self.data_dir / "saved_symbols.txt"
        try:
            last = last_path.read_text(encoding="utf-8").strip()
        except Exception:
            last = ""
        try:
            saved = [line.strip().upper() for line in saved_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            saved = []
        return Settings(lastRefreshDate=last, savedSymbols=saved, factors=self._default_factors())

    def _default_factors(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        return {
            "Do_Nothing": {
                "params": {}
            },
            "Buy_Hold": {
                "params": {
                    "x": {
                        "type": "number",
                        "default": 1.0,
                        "min": 0.0,
                        "max": 1.0,
                        "description": "Fraction of initial cash to deploy equally across universe on the first day."
                    }
                }
            }
        }
