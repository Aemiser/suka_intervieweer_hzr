# UI/components/chart/ChartCard.py
"""
暗色圆角卡片容器，常用于包裹图表组件。
"""

from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

from UI.components.info.Theme import T


class ChartCard(QFrame):
    """带投影的卡片，可自定义背景颜色。"""

    def __init__(self, bg_color: str = None, parent=None):
        super().__init__(parent)
        bg = bg_color or T.SURFACE3
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-radius: 12px;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(T.SURFACE3_DARK))
        shadow.setOffset(0, 0)
        self.setGraphicsEffect(shadow)
