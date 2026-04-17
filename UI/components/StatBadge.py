# UI/components/StatBadge.py
"""
统计徽章：图标 + 数值 + 标签，常用于仪表盘 Hero 区域。
"""

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap

from UI.components.info.Theme import T
from UI.components.info.icon import Icons, IconSize


class StatBadge(QFrame):
    def __init__(
        self,
        icon: str,
        value: str,
        label: str,
        color: str,
        parent=None,
    ):
        super().__init__(parent)
        self.setFixedSize(130, 82)
        self.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border: 1px solid {color}33;
                border-top: 2px solid {color};
                border-radius: 10px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(color).darker(200))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(2)

        # 顶部行：图标 + 数值
        top = QHBoxLayout()
        icon_lbl = QLabel()
        pixmap = Icons.colored_pixmap(icon, color, IconSize.MD)
        icon_lbl.setPixmap(pixmap)
        icon_lbl.setAlignment(Qt.AlignVCenter)
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(
            f"font-size: 20px; font-weight: 900; color: {color};"
            f"font-family: {T.FONT_MONO}; background: transparent;"
        )
        top.addWidget(icon_lbl)
        top.addStretch()
        top.addWidget(val_lbl)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(
            f"font-size: 10px; color: {T.TEXT_DIM};"
            f"font-weight: 600; background: transparent;"
        )

        lay.addLayout(top)
        lay.addWidget(name_lbl)
