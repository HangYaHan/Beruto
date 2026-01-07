from __future__ import annotations

from PyQt6 import QtCore, QtGui, QtWidgets


def make_colored_icon(kind: str, color: str) -> QtGui.QIcon:
    """Create a simple colored icon for add/remove/run without external assets."""
    size = 30
    pixmap = QtGui.QPixmap(size, size)
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)

    painter = QtGui.QPainter(pixmap)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
    pen = QtGui.QPen(QtGui.QColor(color))
    pen.setWidth(3)
    painter.setPen(pen)
    painter.setBrush(QtGui.QBrush(QtGui.QColor(color)))

    center = size // 2
    offset = 9
    if kind == "add":
        painter.drawLine(center, offset, center, size - offset)
        painter.drawLine(offset, center, size - offset, center)
    elif kind == "remove":
        painter.drawLine(offset, center, size - offset, center)
    elif kind == "run":
        points = [
            QtCore.QPoint(offset, offset),
            QtCore.QPoint(size - offset, center),
            QtCore.QPoint(offset, size - offset),
        ]
        painter.drawPolygon(QtGui.QPolygon(points))
    painter.end()

    return QtGui.QIcon(pixmap)


def make_card(title: str, body: str) -> QtWidgets.QWidget:
    card = QtWidgets.QFrame()
    card.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
    card.setObjectName("card")
    vbox = QtWidgets.QVBoxLayout(card)
    vbox.setContentsMargins(10, 10, 10, 10)
    vbox.setSpacing(6)

    header = QtWidgets.QLabel(title)
    header.setStyleSheet("font-weight: bold;")
    vbox.addWidget(header)

    body_label = QtWidgets.QLabel(body)
    body_label.setWordWrap(True)
    body_label.setStyleSheet("color: #c8c8c8;")
    vbox.addWidget(body_label)
    return card
