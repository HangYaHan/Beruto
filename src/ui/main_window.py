from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import (
    QDateEdit,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.backtest import run_portfolio_backtest
from core.data_repo import DataRepository
from core.models import BacktestResult
from ui.portfolio_dialog import DialogDefaults, PortfolioConfigDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Beruto")
        self.resize(1200, 800)

        cache_dir = Path(__file__).resolve().parents[1] / "cache"
        self.repo = DataRepository(cache_dir=cache_dir)
        self.state_path = cache_dir / "session_state.json"

        self.current_symbol: str | None = None
        self.current_bars: pd.DataFrame | None = None
        self.last_backtest: BacktestResult | None = None

        self._build_ui()
        self._restore_state()
        if not self.log_text.toPlainText().strip():
            self._append_log("Welcome to Beruto! This is a simple MVP now.")
            self._append_log("Example instructions: Enter 510300 or 600519 -> Click 'Update Data' -> 'Backtest'")

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)

        controls_layout = QGridLayout()

        self.symbol_input = QLineEdit("")
        controls_layout.addWidget(QLabel("Symbol(6位):"), 0, 0)
        controls_layout.addWidget(self.symbol_input, 0, 1)

        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addYears(-2))
        controls_layout.addWidget(QLabel("开始日期:"), 0, 2)
        controls_layout.addWidget(self.start_date_edit, 0, 3)

        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        controls_layout.addWidget(QLabel("结束日期:"), 0, 4)
        controls_layout.addWidget(self.end_date_edit, 0, 5)

        self.update_button = QPushButton("更新数据")
        self.backtest_button = QPushButton("回测")

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.update_button)
        btn_row.addWidget(self.backtest_button)

        root_layout.addLayout(controls_layout)
        root_layout.addLayout(btn_row)

        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        root_layout.addWidget(self.canvas)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("日志与错误输出...")
        root_layout.addWidget(self.log_text)

        self.update_button.clicked.connect(self.on_update_data)
        self.backtest_button.clicked.connect(self.on_backtest)

    def _append_log(self, message: str) -> None:
        self.log_text.append(message)

    def _save_state(self) -> None:
        state = {
            "log_lines": self.log_text.toPlainText().splitlines(),
            "symbol_input": self.symbol_input.text().strip(),
            "last_backtest": None,
        }

        if self.last_backtest is not None:
            result = self.last_backtest
            signals: list[dict] = []
            if not result.signals.empty:
                for row in result.signals.to_dict(orient="records"):
                    casted = {}
                    for k, v in row.items():
                        if k == "date":
                            casted[k] = str(pd.Timestamp(v).date())
                        elif isinstance(v, (int, float, str)) or v is None:
                            casted[k] = v
                        else:
                            casted[k] = str(v)
                    signals.append(casted)

            equity_curve: list[dict] = []
            if not result.equity_curve.empty:
                for row in result.equity_curve.to_dict(orient="records"):
                    equity_curve.append(
                        {
                            "date": str(pd.Timestamp(row["date"]).date()),
                            "equity": float(row["equity"]),
                        }
                    )

            state["last_backtest"] = {
                "metrics": result.metrics,
                "notes": result.notes,
                "signals": signals,
                "equity_curve": equity_curve,
            }

        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _restore_state(self) -> None:
        if not self.state_path.exists():
            return
        try:
            state = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                return

            log_lines = state.get("log_lines")
            if isinstance(log_lines, list):
                self.log_text.clear()
                for line in log_lines:
                    self._append_log(str(line))

            symbol_input = state.get("symbol_input")
            if isinstance(symbol_input, str):
                self.symbol_input.setText(symbol_input)

            last = state.get("last_backtest")
            if not isinstance(last, dict):
                return

            eq_rows = last.get("equity_curve", [])
            equity_curve = pd.DataFrame(eq_rows)
            if not equity_curve.empty:
                equity_curve["date"] = pd.to_datetime(equity_curve["date"])
                equity_curve["equity"] = equity_curve["equity"].astype(float)

            signals = pd.DataFrame(last.get("signals", []))
            if not signals.empty and "date" in signals.columns:
                signals["date"] = pd.to_datetime(signals["date"])

            self.last_backtest = BacktestResult(
                equity_curve=equity_curve,
                daily_returns=pd.Series(dtype=float),
                signals=signals,
                metrics=last.get("metrics", {}),
                notes=last.get("notes", []),
            )

            if not equity_curve.empty:
                self._plot_equity(self.last_backtest)
                self._append_log("已恢复最近一次回测结果。")
        except Exception as exc:
            self._append_log(f"状态恢复失败: {exc}")

    def _get_symbol(self) -> str:
        symbol = self.symbol_input.text().strip()
        if not (symbol.isdigit() and len(symbol) == 6):
            raise ValueError("Symbol 必须是 6 位数字，例如 600519 / 510300")
        return symbol

    def on_update_data(self) -> None:
        try:
            symbol = self._get_symbol()
            self._append_log(f"开始更新数据: {symbol}")
            bars = self.repo.get_bars(symbol, refresh=True)
            if bars.empty:
                self._append_log("数据为空，请检查代码或网络。")
            else:
                self._append_log(
                    f"更新完成: {len(bars)} rows, range {bars['date'].iloc[0].date()} ~ {bars['date'].iloc[-1].date()}"
                )
            self.current_symbol = symbol
            self.current_bars = bars
        except Exception as exc:
            self._append_log(f"更新数据失败: {exc}")
            QMessageBox.warning(self, "错误", str(exc))

    def on_backtest(self) -> None:
        try:
            start_date = pd.Timestamp(self.start_date_edit.date().toString("yyyy-MM-dd"))
            end_date = pd.Timestamp(self.end_date_edit.date().toString("yyyy-MM-dd"))
            seed_symbol = self.symbol_input.text().strip()

            dialog = PortfolioConfigDialog(
                defaults=DialogDefaults(
                    start_date=start_date,
                    end_date=end_date,
                    seed_symbol=seed_symbol,
                    cached_symbols=self.repo.list_cached_symbols(),
                ),
                parent=self,
            )
            if dialog.exec_() != dialog.Accepted:
                self._append_log("回测已取消。")
                return

            cfg = dialog.build_config()
            symbols = [s.symbol for s in cfg.symbols]

            bars_map, cache_errors = self.repo.get_bars_batch(symbols, refresh=False)
            errors = dict(cache_errors)
            missing = [s for s in symbols if s not in bars_map or bars_map[s].empty]

            for s in symbols:
                if s in missing:
                    continue
                self._append_log(f"数据状态[{s}]: cache hit")

            if missing:
                self._append_log(f"缓存未命中，尝试联网更新: {', '.join(missing)}")
                fresh_map, fresh_errors = self.repo.get_bars_batch(missing, refresh=True)
                bars_map.update(fresh_map)
                errors.update(fresh_errors)

                for s in missing:
                    if s in bars_map and not bars_map[s].empty:
                        self._append_log(f"数据状态[{s}]: fetched")
                    elif s in fresh_errors:
                        self._append_log(f"数据状态[{s}]: failed ({fresh_errors[s]})")
                    else:
                        self._append_log(f"数据状态[{s}]: empty")

            hard_missing = [s for s in symbols if s not in bars_map or bars_map[s].empty]
            if hard_missing:
                raise ValueError(f"以下标的无可用数据: {hard_missing}")

            if errors:
                for s, e in errors.items():
                    self._append_log(f"数据警告[{s}]: {e}")

            result = run_portfolio_backtest(bars_map, cfg)
            self.last_backtest = result

            self._plot_equity(result)

            self._append_log("回测完成。")
            for n in result.notes:
                self._append_log(f"- {n}")
            if not result.signals.empty:
                self._append_log(f"成交记录条数: {len(result.signals)}")
            if result.metrics:
                self._append_log(
                    "指标: "
                    + ", ".join(
                        [f"{k}={v:.4f}" if isinstance(v, float) else f"{k}={v}" for k, v in result.metrics.items()]
                    )
                )

            self._save_state()
        except Exception as exc:
            self._append_log(f"回测失败: {exc}")
            QMessageBox.warning(self, "错误", str(exc))

    def closeEvent(self, event) -> None:  # type: ignore[override]
        try:
            self._save_state()
        finally:
            super().closeEvent(event)

    def _plot_equity(self, result: BacktestResult) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if result.equity_curve.empty:
            ax.set_title("No data")
            self.canvas.draw_idle()
            return

        ax.plot(result.equity_curve["date"], result.equity_curve["equity"], label="Equity")
        ax.set_title("Backtest Equity Curve")
        ax.set_xlabel("Date")
        ax.set_ylabel("Net Value")
        ax.grid(True, alpha=0.3)
        ax.legend()
        self.figure.tight_layout()
        self.canvas.draw_idle()
