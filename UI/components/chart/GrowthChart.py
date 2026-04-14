# UI/components/chart/GrowthChart.py
"""
折线面积图：展示综合得分随面试次数的趋势。
"""

import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont,
    QLinearGradient, QPainterPath,
)

from UI.components.info.Theme import T


class GrowthChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scores: list[float] = []
        self.setMinimumSize(380, 220)
        self.setStyleSheet("background: transparent;")

    def set_scores(self, scores: list[float]) -> None:
        self.scores = scores
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()
        PL, PR, PT, PB = 38, 16, 30, 28
        cw, ch = W - PL - PR, H - PT - PB

        if not self.scores:
            p.setPen(QColor(T.TEXT_DIM))
            p.setFont(QFont(T.FONT, 13))
            p.drawText(self.rect(), Qt.AlignCenter, "暂无面试记录")
            return

        # 网格线 + Y 轴标签
        p.setPen(QPen(QColor(T.BORDER), 1))
        for i in range(6):
            y = PT + ch * (1 - i / 5)
            p.drawLine(PL, int(y), W - PR, int(y))
            p.setPen(QColor(T.TEXT_MUTE))
            p.setFont(QFont(T.FONT_MONO, 8))
            p.drawText(2, int(y) + 4, str(i * 2))
            p.setPen(QPen(QColor(T.BORDER), 1))

        # 坐标点
        n = len(self.scores)
        step = cw / (n - 1) if n > 1 else cw / 2
        points = [
            QPointF(
                PL + i * step if n > 1 else PL + cw / 2,
                PT + ch * (1 - s / 10),
            )
            for i, s in enumerate(self.scores)
        ]

        # 面积填充
        if len(points) > 1:
            path = QPainterPath()
            path.moveTo(points[0].x(), PT + ch)
            for pt in points:
                path.lineTo(pt)
            path.lineTo(points[-1].x(), PT + ch)

            grad = QLinearGradient(0, PT, 0, PT + ch)
            grad.setColorAt(0, QColor(0, 212, 255, 50))
            grad.setColorAt(1, QColor(0, 212, 255, 0))
            p.fillPath(path, QBrush(grad))

        # 折线
        neon = QColor(T.INFO)
        p.setPen(QPen(neon, 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        for i in range(len(points) - 1):
            p.drawLine(points[i], points[i + 1])

        # 节点
        for pt in points:
            p.setPen(Qt.NoPen)
            p.setBrush(neon)
            p.drawEllipse(pt, 5, 5)
            p.setBrush(QColor(T.SURFACE))
            p.drawEllipse(pt, 2.5, 2.5)
            p.setBrush(neon)

        # X 轴标签
        p.setPen(QColor(T.TEXT_MUTE))
        p.setFont(QFont(T.FONT, 8))
        for i, pt in enumerate(points):
            p.drawText(int(pt.x()) - 8, H - 4, f"#{i + 1}")