from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any


PLAN_SIGNATURE = "BERUTO_PLAN_V1"


@dataclass
class PlanValidationError(Exception):
    message: str

    def __str__(self) -> str:  # pragma: no cover - simple wrapper
        return self.message


class PlanStorage:
    """Save/load plan JSON with signature validation and summary rendering."""

    def __init__(self, signature: str = PLAN_SIGNATURE) -> None:
        self.signature = signature

    def load(self, path: Path) -> Dict[str, Any]:
        try:
            content = path.read_text(encoding="utf-8")
            plan = json.loads(content)
        except Exception as exc:
            raise PlanValidationError(f"Failed to read plan: {exc}")
        self._validate_signature(plan)
        return plan

    def save(self, plan: Dict[str, Any], path: Path) -> Path:
        self.ensure_signature(plan)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def ensure_signature(self, plan: Dict[str, Any]) -> None:
        plan.setdefault("signature", self.signature)

    def summary_lines(self, plan: Dict[str, Any], path: Path | None = None) -> str:
        md = plan.get("Metadata", {}) if plan else {}
        univ = plan.get("Universe", {}) if plan else {}
        arb = plan.get("Scoring", {}) if plan else {}
        orc = plan.get("Factors", {}) if plan else {}
        exc = plan.get("Execution", {}) if plan else {}
        name = md.get("name") or md.get("plan_id", "(unnamed)")
        created = md.get("created_at", "")
        symbols = univ.get("symbols", [])
        holdings = univ.get("holdings", []) or []
        mode = arb.get("fusion_mode", "")
        freq = arb.get("scheduling", {}).get("frequency", "")
        thresh = arb.get("scheduling", {}).get("rebalance_threshold", "")
        max_pos = arb.get("constraints", {}).get("max_position_per_symbol", "")
        factors = orc.get("selected_factors", [])
        cash = exc.get("initial_cash", "")
        injections = univ.get("cash_injections", {}) if isinstance(univ.get("cash_injections", {}), dict) else {}
        inj_daily = injections.get("daily", 0)
        inj_weekly = injections.get("weekly", 0)
        inj_monthly = injections.get("monthly", 0)

        lines = [
            f"Name: {name}",
            f"Created: {created}",
            f"Universe: {len(symbols)} symbols ({', '.join(symbols[:6])}{'...' if len(symbols) > 6 else ''})",
            f"Holdings: {sum(1 for _ in holdings)} entries, injections (d/w/m) = {inj_daily}/{inj_weekly}/{inj_monthly}",
            f"Factors: {len(factors)} selected",
            f"Scoring: mode={mode}, freq={freq}, threshold={thresh}, max_pos={max_pos}",
            f"Execution: initial_cash={cash}",
        ]
        if path:
            lines.append(f"Path: {path}")
        return "\n".join(lines)

    def _validate_signature(self, plan: Dict[str, Any]) -> None:
        if plan.get("signature") != self.signature:
            raise PlanValidationError("Invalid plan signature")


class PlanDefaultsLoader:
    """Loads plan default template from data/plan_defaults.json."""

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root

    def load(self) -> Dict[str, Any]:
        defaults_path = self.project_root / "data" / "plan_defaults.json"
        try:
            return json.loads(defaults_path.read_text(encoding="utf-8"))
        except Exception:
            return {
                "version": 1,
                "Universe": {
                    "cash_injections": {"daily": 0, "weekly": 0, "monthly": 0},
                    "holdings": [],
                },
                "Factors": {},
                "Scoring": {},
                "Execution": {},
                "Metadata": {},
            }


__all__ = ["PlanStorage", "PlanDefaultsLoader", "PlanValidationError", "PLAN_SIGNATURE"]
