from __future__ import annotations

from pathlib import Path
from typing import Callable
import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt6 import QtCore, QtGui, QtWidgets
import akshare as ak


class KlineDownloadWorker(QtCore.QObject):
    progress = QtCore.pyqtSignal(int)
    message = QtCore.pyqtSignal(str)
    finished = QtCore.pyqtSignal(pd.DataFrame)
    error = QtCore.pyqtSignal(str)

    def __init__(self, code: str, start_date: str, end_date: str, cache_path: Path) -> None:
        super().__init__()
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.cache_path = cache_path

    def run(self) -> None:
        try:
            self.message.emit(f"Downloading {self.code} K-line data...")
            self.progress.emit(10)
            df = self._fetch_kline()
            self.progress.emit(80)
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(self.cache_path, index=False)
            self.progress.emit(100)
            self.finished.emit(df)
        except Exception as exc:  # pragma: no cover - network dependent
            self.error.emit(str(exc))

    def _fetch_kline(self) -> pd.DataFrame:
        last_error: Exception | None = None
        for fetcher in (self._fetch_stock, self._fetch_etf):
            try:
                raw = fetcher()
                if raw is not None and not raw.empty:
                    return self._normalize(raw)
            except Exception as exc:  # pragma: no cover - network dependent
                last_error = exc
        if last_error:
            raise last_error
        raise RuntimeError(f"akshare returned empty data for {self.code}")

    def _fetch_stock(self) -> pd.DataFrame:
        return ak.stock_zh_a_hist(
            symbol=self.code,
            period="daily",
            start_date=self.start_date,
            end_date=self.end_date,
            adjust="qfq",
        )

    def _fetch_etf(self) -> pd.DataFrame:
        return ak.fund_etf_hist_em(
            symbol=self.code,
            period="daily",
            start_date=self.start_date,
            end_date=self.end_date,
        )

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_map = {
            "日期": "date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
        }
        normalized = df.rename(columns=rename_map)
        missing = {"date", "open", "high", "low", "close"} - set(normalized.columns)
        if missing:
            raise ValueError(f"Missing columns after normalization: {missing}")
        normalized = normalized[
            ["date", "open", "high", "low", "close", "volume"]
            if "volume" in normalized.columns
            else ["date", "open", "high", "low", "close"]
        ]
        normalized["date"] = pd.to_datetime(normalized["date"])
        normalized = normalized.sort_values("date").reset_index(drop=True)
        return normalized


class CandlestickItem(pg.GraphicsObject):
    def __init__(self, data: list[tuple[float, float, float, float, float]], width: float, up_color: str, down_color: str) -> None:
        super().__init__()
        self.data = data
        self.width = width
        self._up_color = up_color
        self._down_color = down_color
        self.picture = QtGui.QPicture()
        self._generate_picture()

    def _generate_picture(self) -> None:
        up_color = pg.mkColor(self._up_color)
        down_color = pg.mkColor(self._down_color)
        painter = QtGui.QPainter(self.picture)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        half = self.width / 2
        for t, open_, high, low, close in self.data:
            is_rise = close >= open_
            color = up_color if is_rise else down_color
            painter.setPen(pg.mkPen(color, width=1.2))
            painter.drawLine(QtCore.QPointF(t, low), QtCore.QPointF(t, high))
            top = open_ if is_rise else close
            bottom = close if is_rise else open_
            rect = QtCore.QRectF(
                t - half,
                top,
                self.width,
                bottom - top if bottom - top != 0 else 0.0001,
            )
            painter.fillRect(rect, pg.mkBrush(color))
            painter.drawRect(rect)
        painter.end()

    def paint(self, painter: QtGui.QPainter, *args: object) -> None:  # pragma: no cover - GUI drawing
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self) -> QtCore.QRectF:  # pragma: no cover - GUI drawing
        return QtCore.QRectF(self.picture.boundingRect())


class KLineChartPanel(QtWidgets.QFrame):
    def __init__(self, on_symbol_requested: Callable[[str], None], parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._on_symbol_requested = on_symbol_requested
        self.setAcceptDrops(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)

        palette = self.palette()
        self._bg_color = palette.window().color().name()
        self._text_color = palette.text().color().name()
        # Use A-share convention: red for up, green for down
        self._up_color = "#ff4d4f"
        self._down_color = "#2ecc71"

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QtWidgets.QHBoxLayout()
        header.setSpacing(6)
        self.title_label = QtWidgets.QLabel("K-line Chart")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.hint_label = QtWidgets.QLabel("Double-click or drag a symbol to view K-line")
        self.hint_label.setStyleSheet(f"color: {self._text_color}; opacity: 0.7;")
        header.addWidget(self.title_label)
        header.addStretch(1)
        header.addWidget(self.hint_label)
        layout.addLayout(header)

        axis = pg.graphicsItems.DateAxisItem.DateAxisItem(orientation="bottom")
        self.plot = pg.PlotWidget(axisItems={"bottom": axis})
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.setBackground(self._bg_color)
        self.plot.setLabel("left", "Price", **{"color": self._text_color})
        self.plot.setLabel("bottom", "Date", **{"color": self._text_color})
        self.plot.getAxis("left").setTextPen(pg.mkPen(self._text_color))
        self.plot.getAxis("bottom").setTextPen(pg.mkPen(self._text_color))
        self.plot.getAxis("left").setPen(pg.mkPen(self._text_color))
        self.plot.getAxis("bottom").setPen(pg.mkPen(self._text_color))
        self.plot.setAcceptDrops(True)
        self.plot.setAcceptDrops(True)
        self.plot.installEventFilter(self)
        self.plot.viewport().setAcceptDrops(True)
        self.plot.viewport().installEventFilter(self)
        layout.addWidget(self.plot, stretch=1)

        self.empty_label = QtWidgets.QLabel(
            "Drag a symbol to the chart area or use the context menu to view daily K-line."
        )
        self.empty_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {self._text_color}; padding: 12px; opacity: 0.7;")
        layout.addWidget(self.empty_label)

    def display_symbol(self, code: str, df: pd.DataFrame) -> None:
        df = df.copy()
        if df.empty:
            self.empty_label.setText(f"{code}: 无数据")
            self.empty_label.show()
            return
        self.empty_label.hide()
        self.title_label.setText(f"{code} K-line")
        self.plot.clear()

        df = df.sort_values("date")
        timestamps = np.array([pd.to_datetime(ts).timestamp() for ts in df["date"]], dtype=float)
        opens = df["open"].astype(float).to_numpy()
        highs = df["high"].astype(float).to_numpy()
        lows = df["low"].astype(float).to_numpy()
        closes = df["close"].astype(float).to_numpy()

        if len(timestamps) > 1:
            step = float(np.median(np.diff(timestamps)))
            width = step * 0.75  # slightly wider candles for readability
        else:
            width = 60 * 60 * 12  # half-day for single point

        candle_data = list(zip(timestamps, opens, highs, lows, closes))
        item = CandlestickItem(candle_data, width, up_color=self._up_color, down_color=self._down_color)
        self.plot.addItem(item)

        x_min, x_max = float(timestamps.min()), float(timestamps.max())
        y_min, y_max = float(lows.min()), float(highs.max())
        padding = (y_max - y_min) * 0.05 if y_max > y_min else 1.0
        self.plot.setXRange(x_min, x_max)
        self.plot.setYRange(y_min - padding, y_max + padding)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:  # noqa: N802 - Qt override
        if event.mimeData().hasText():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:  # noqa: N802 - Qt override
        text = event.mimeData().text().strip()
        if not text:
            event.ignore()
            return
        code = text.split()[0].strip().upper()
        if self._on_symbol_requested:
            self._on_symbol_requested(code)
        event.acceptProposedAction()

    def eventFilter(self, obj: QtCore.QObject, event: QtCore.QEvent) -> bool:  # noqa: N802 - Qt override
        if obj in (self.plot, self.plot.viewport()):
            if event.type() == QtCore.QEvent.Type.DragEnter:
                self.dragEnterEvent(event)  # type: ignore[arg-type]
                return True
            if event.type() == QtCore.QEvent.Type.DragMove:
                self.dragMoveEvent(event)  # type: ignore[arg-type]
                return True
            if event.type() == QtCore.QEvent.Type.Drop:
                self.dropEvent(event)  # type: ignore[arg-type]
                return True
        return super().eventFilter(obj, event)


__all__ = ["KLineChartPanel", "KlineDownloadWorker", "CandlestickItem"]
