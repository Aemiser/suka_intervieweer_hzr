# UI/components/chart/RadarChart.py
"""
雷达图：多维度能力可视化（技术 / 逻辑 / 深度 / 表达）。
"""

import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont,
    QPolygonF,
)

from UI.components.info.Theme import T


class RadarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: dict[str, float] = {}
        self.setMinimumSize(260, 260)
        self.setStyleSheet("background: transparent;")

    def set_data(self, data: dict[str, float]) -> None:
        self.data = data
        self.update()

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        W, H = self.width(), self.height()
        cx, cy = W / 2, H / 2
        r = min(cx, cy) - 44

        if not self.data:
            p.setPen(QColor(T.TEXT_DIM))
            p.drawText(self.rect(), Qt.AlignCenter, "等待数据...")
            return

        cats = list(self.data.keys())
        n    = len(cats)
        step = 2 * math.pi / n

        # 蜘蛛网底框
        p.setPen(QPen(QColor(T.BORDER2), 1))
        for level in range(1, 6):
            cur_r = r * (level / 5)
            pts = [
                QPointF(
                    cx + cur_r * math.cos(i * step - math.pi / 2),
                    cy + cur_r * math.sin(i * step - math.pi / 2),
                )
                for i in range(n)
            ]
            p.drawPolygon(QPolygonF(pts + [pts[0]]))

        # 轴线 + 标签
        p.setFont(QFont(T.FONT, 10, QFont.Bold))
        for i, cat in enumerate(cats):
            angle = i * step - math.pi / 2
            ex, ey = cx + r * math.cos(angle), cy + r * math.sin(angle)
            p.setPen(QPen(QColor(T.BORDER2), 1))
            p.drawLine(int(cx), int(cy), int(ex), int(ey))

            tx = cx + (r + 22) * math.cos(angle)
            ty = cy + (r + 22) * math.sin(angle)
            p.setPen(QColor(T.TEXT_DIM))
            bw = p.fontMetrics().horizontalAdvance(cat)
            p.drawText(int(tx - bw / 2), int(ty + 4), cat)

        # 数据多边形
        data_pts = [
            QPointF(
                cx + r * (self.data.get(cat, 0) / 10) * math.cos(i * step - math.pi / 2),
                cy + r * (self.data.get(cat, 0) / 10) * math.sin(i * step - math.pi / 2),
            )
            for i, cat in enumerate(cats)
        ]
        poly = QPolygonF(data_pts + [data_pts[0]])
        p.setPen(QPen(QColor(T.NEON), 2))
        p.setBrush(QColor(T.BG_LIGHT))
        p.drawPolygon(poly)

        # 数据节点
        p.setBrush(QColor(T.NEON))
        p.setPen(Qt.NoPen)
        for pt in data_pts:
            p.drawEllipse(pt, 4, 4)