from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any

from PyQt6 import QtWidgets

from src.backtest.core import BacktestEngine
from src.backtest.datatype import AccountState


class MainController:
    """Bridge between backend backtest engine and the Beruto UI."""

    def __init__(self, window: Any, project_root: Path) -> None:
        self.window = window
        self.project_root = Path(project_root)
        self.history: List[AccountState] = []

    def run_backtest(self, json_path: str) -> None:
        path = Path(json_path)
        if not path.is_absolute():
            path = (self.project_root / path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Plan file not found: {path}")

        plan = self._load_plan(path)
        engine = BacktestEngine(plan)
        history = engine.run_to_end()
        self.history = history
        if hasattr(self.window, "history"):
            self.window.history = history
        metrics = self._compute_metrics(history)

        # Push to UI
        if hasattr(self.window, "update_global_info"):
            self.window.update_global_info(metrics)
        if hasattr(self.window, "calendar_widget"):
            self.window.calendar_widget.load_history(history)
        # Initial render of day 0 if available
        if history:
            self.window.on_replay_step(0)

    def _load_plan(self, path: Path) -> Dict[str, Any]:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _compute_metrics(self, history: List[AccountState]) -> Dict[str, float]:
        if not history:
            return {"total_return": 0.0, "max_drawdown": 0.0}
        equity_curve = [float(st.total_assets) for st in history]
        start = equity_curve[0]
        end = equity_curve[-1]
        total_return = (end / start - 1.0) if start else 0.0
        max_drawdown = self._max_drawdown(equity_curve)
        return {"total_return": total_return, "max_drawdown": max_drawdown}

    def _max_drawdown(self, equity: List[float]) -> float:
        peak = equity[0]
        max_dd = 0.0
        for v in equity:
            if v > peak:
                peak = v
            drawdown = (v - peak) / peak if peak else 0.0
            if drawdown < max_dd:
                max_dd = drawdown
        return max_dd

    # --- UI action slots ---
    def on_action_run_backtest_triggered(self) -> None:
        # Basic dirty handling: if current plan exists but path is missing, ask user to save; otherwise reuse current path.
        current_plan = getattr(self.window, "current_plan", None)
        current_path = getattr(self.window, "current_plan_path", None)

        if not current_plan:
            QtWidgets.QMessageBox.information(self.window, "Run Backtest", "No plan is open. Please open or create a plan first.")
            return

        # Ensure we have a path; prompt Save As if needed
        if not current_path:
            path_str, _ = QtWidgets.QFileDialog.getSaveFileName(
                self.window,
                "Save Plan JSON",
                str(self.project_root / "plan" / "plan.json"),
                "JSON Files (*.json)",
            )
            if not path_str:
                return
            current_path = Path(path_str)
            try:
                self.window.plan_storage.save(current_plan, current_path)
                self.window.current_plan_path = current_path
            except Exception as exc:
                QtWidgets.QMessageBox.warning(self.window, "Save Failed", str(exc))
                return
        else:
            # Optionally ensure latest in-memory plan is on disk
            try:
                self.window.plan_storage.save(current_plan, current_path)
            except Exception:
                # If save fails, allow user to continue
                pass

        try:
            self.run_backtest(str(current_path))
        except Exception as exc:
            QtWidgets.QMessageBox.warning(self.window, "Backtest Failed", str(exc))


__all__ = ["MainController"]
