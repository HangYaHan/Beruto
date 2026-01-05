from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List

from src.system.log import get_logger

logger = get_logger(__name__)


@dataclass
class FactorConfig:
    """Factor instance wiring inside a strategy plan."""

    name: str
    module: str
    class_name: str
    symbols: List[str]
    params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FactorConfig":
        required = ("name", "module", "class", "symbols")
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"FactorConfig missing keys: {missing}")
        symbols = data.get("symbols") or []
        if isinstance(symbols, str):
            symbols = [symbols]
        return cls(
            name=str(data["name"]),
            module=str(data["module"]),
            class_name=str(data["class"]),
            symbols=[str(s) for s in symbols],
            params=dict(data.get("params", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "module": self.module,
            "class": self.class_name,
            "symbols": list(self.symbols),
            "params": dict(self.params),
        }


@dataclass
class StrategyPlan:
    """Describe how factors combine across symbols (no date fields included)."""

    name: str
    symbols: List[str]
    factors: List[FactorConfig]
    description: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StrategyPlan":
        if "name" not in data:
            raise ValueError("StrategyPlan requires a name")
        symbols_raw = data.get("symbols") or []
        symbols = symbols_raw if isinstance(symbols_raw, list) else [symbols_raw]
        factors_raw = data.get("factors") or []
        factors = [FactorConfig.from_dict(f) for f in factors_raw]
        return cls(
            name=str(data["name"]),
            symbols=[str(s) for s in symbols],
            factors=factors,
            description=data.get("description"),
            metadata=dict(data.get("metadata", {})),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "symbols": list(self.symbols),
            "factors": [f.to_dict() for f in self.factors],
            "metadata": dict(self.metadata),
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        logger.info("Saved strategy plan to %s", path)


def strategy_dir(root: Path | None = None) -> Path:
    if root is None:
        root = Path(__file__).resolve().parents[2]
    return root / "strategies"


def load_plan(plan_name: str, root: Path | None = None) -> StrategyPlan:
    directory = strategy_dir(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{plan_name}.json"
    if not path.exists():
        raise FileNotFoundError(f"Strategy plan not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    plan = StrategyPlan.from_dict(data)
    logger.info("Loaded strategy plan %s with %s factors", plan.name, len(plan.factors))
    return plan


__all__ = [
    "FactorConfig",
    "StrategyPlan",
    "load_plan",
    "strategy_dir",
]
