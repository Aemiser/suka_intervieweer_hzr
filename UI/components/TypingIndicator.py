# UI/components/TypingIndicator.py
"""
打字动画指示器：三个脉冲圆点，模拟 AI 思考中的视觉反馈。
"""

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import QTimer

from UI.components.info.Theme import T


class TypingIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(8, 4, 8, 4)

        bubble = QFrame()
        bubble.setObjectName("typing_bubble")
        bubble.setStyleSheet(f"""
            QFrame#typing_bubble {{
                background: {T.AI_BUBBLE};
                border: 1px solid {T.BORDER};
                border-radius: 18px;
                border-top-left-radius: 4px;
            }}
        """)
        bubble.setFixedSize(76, 40)

        b_lay = QHBoxLayout(bubble)
        b_lay.setContentsMargins(16, 10, 16, 10)
        b_lay.setSpacing(6)

        self._dots: list[QLabel] = []
        for _ in range(3):
            dot = QLabel("●")
            dot.setStyleSheet(
                f"color: {T.INFO}33; font-size: 9px; background: transparent;"
            )
            b_lay.addWidget(dot)
            self._dots.append(dot)

        outer.addWidget(bubble)
        outer.addStretch()

        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(380)

    # ── 动画 ──────────────────────────────────────────────────────────────────

    def _animate(self) -> None:
        for i, dot in enumerate(self._dots):
            alpha = "FF" if i == self._step % 3 else "33"
            dot.setStyleSheet(
                f"color: {T.INFO}{alpha}; font-size: 9px; background: transparent;"
            )
        self._step += 1

    def stop(self) -> None:
        """停止动画，在从布局移除前调用以避免定时器孤立。"""
        self._timer.stop()