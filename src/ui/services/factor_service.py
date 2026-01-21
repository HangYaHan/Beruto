from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.system.settings import SettingsManager


class FactorLibraryLoader:
    """Loads factor library names and default params from local data (settings, csv, json)."""

    def __init__(self, project_root: Path, settings_manager: Optional[SettingsManager] = None) -> None:
        self.project_root = project_root
        self.settings_manager = settings_manager

    def load(self) -> List[Dict[str, Any]]:
        base = self.project_root / "data"
        csv_path = base / "factor.csv"
        factors_dir = base / "factors"

        # 1) Primary source: settings.json factors
        library = self._load_from_settings()

        # 2) Legacy/fallback: csv list + builtin + per-factor json overrides
        builtins = [
            {"name": "Do_Nothing", "params": {"alpha": 0}},
            {"name": "Buy_&_Hold", "params": {"p1": 0, "p2": 0, "p3": 0}},
        ]

        if csv_path.exists():
            try:
                with csv_path.open("r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    if reader.fieldnames and "name" in reader.fieldnames:
                        for row in reader:
                            name = (row.get("name") or "").strip()
                            if name:
                                library.append({"name": name, "params": {}})
                    else:
                        for line in csv_path.read_text(encoding="utf-8").splitlines():
                            name = line.strip()
                            if name:
                                library.append({"name": name, "params": {}})
            except Exception:
                pass

        by_name: Dict[str, Dict[str, Any]] = {item["name"]: item for item in library if item.get("name")}
        for item in builtins:
            if item.get("name"):
                by_name.setdefault(item["name"], item)

        for name, item in list(by_name.items()):
            json_path = factors_dir / f"{name}.json"
            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        if "params" in data and isinstance(data["params"], dict):
                            item["params"] = data.get("params", {})
                        else:
                            item["params"] = data
                        desc = data.get("description") or data.get("help")
                        if desc:
                            item.setdefault("description", desc)
                    else:
                        item["params"] = data
                except Exception:
                    pass

        return list(by_name.values())

    def _load_from_settings(self) -> List[Dict[str, Any]]:
        try:
            settings_mgr = self.settings_manager or SettingsManager(project_root=self.project_root)
            factors = getattr(settings_mgr, "settings", None).factors if hasattr(settings_mgr, "settings") else {}
        except Exception:
            factors = {}
        library: List[Dict[str, Any]] = []
        if not isinstance(factors, dict):
            return library
        for name, meta in factors.items():
            if not name:
                continue
            entry: Dict[str, Any] = {"name": name}
            if isinstance(meta, dict):
                entry["params"] = meta.get("params", {}) or {}
                desc = meta.get("description") or meta.get("help") or ""
                if desc:
                    entry["description"] = desc
            else:
                entry["params"] = {}
            library.append(entry)
        return library


__all__ = ["FactorLibraryLoader"]
