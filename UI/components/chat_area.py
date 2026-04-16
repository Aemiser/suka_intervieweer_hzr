"""
chat_area.py
聊天展示区域独立组件（解耦版）。
职责：消息渲染、滚动控制、新消息 Toast 提示、流式气泡生命周期管理。
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QPushButton

from UI.components import T, ChatBubble, ScoreCardBubble, TypingIndicator


class NewMessageToast(QPushButton):
    def __init__(self, parent=None):
        super().__init__("↓  新消息", parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(110, 34)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {T.NEON}; color: #0a0a0f;
                border: none; border-radius: 17px;
                font-size: 12px; font-weight: 700;
                font-family: {T.FONT}; padding: 0 12px;
            }}
            QPushButton:hover {{ background: {T.PURPLE}; color: #ffffff; }}
        """)
        self.hide()

    def update_position(self, rect) -> None:
        self.move(rect.width() - self.width() - 18, rect.height() - self.height() - 14)
        self.raise_()


class ChatArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet(f"QScrollArea {{ background: {T.BG}; border: none; }}")

        # 容器与布局
        self._container = QWidget()
        self._container.setStyleSheet(f"background: {T.SURFACE}; border: none; ")
        self._layout = QVBoxLayout(self._container)
        self._layout.setContentsMargins(22, 20, 22, 20)
        self._layout.setSpacing(12)
        self._layout.addStretch()

        self.setWidget(self._container)

        # 内部状态
        self._user_scrolled_up = False
        self._has_new_content = False
        self._typing_indicator: TypingIndicator | None = None
        self._current_ai_bubble: ChatBubble | None = None

        # 事件绑定
        self.verticalScrollBar().valueChanged.connect(self._on_scroll_changed)

        self._toast = NewMessageToast(self)
        self._toast.clicked.connect(self.scroll_to_bottom)

        # 默认欢迎语
        self.add_system_message("请输入姓名、选择岗位，然后点击「开始面试」")

    def _on_scroll_changed(self, value: int) -> None:
        sb = self.verticalScrollBar()
        if value >= sb.maximum() - 10:
            self._user_scrolled_up = False
            self._has_new_content = False
            self._toast.hide()
        else:
            self._user_scrolled_up = True

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._toast.isVisible():
            self._toast.update_position(self.rect())

    def _notify_new_content(self) -> None:
        """新内容到达时，根据滚动状态决定自动滚动或显示 Toast"""
        if self._user_scrolled_up:
            self._has_new_content = True
            self._toast.update_position(self.rect())
            self._toast.show()
            self._toast.raise_()
        else:
            self.scroll_to_bottom()

    # ───────────────── 公开 API ─────────────────
    def scroll_to_bottom(self) -> None:
        QTimer.singleShot(
            50,
            lambda: self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        )
        self._user_scrolled_up = False
        self._has_new_content = False
        self._toast.hide()

    def clear(self) -> None:
        while self._layout.count() > 1:
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._current_ai_bubble = None
        self._typing_indicator = None

    def add_user_message(self, text: str) -> None:
        bubble = ChatBubble("user", text)
        self._layout.insertWidget(self._layout.count() - 1, bubble)
        QTimer.singleShot(10, bubble.play_entrance_animation)
        self._notify_new_content()

    def add_system_message(self, text: str) -> None:
        bubble = ChatBubble("system", text)
        self._layout.insertWidget(self._layout.count() - 1, bubble)
        # ✅ 触发入场动画
        print("add_system_message")
        QTimer.singleShot(10, bubble.play_entrance_animation)
        self._notify_new_content()

    def add_score_message(self, eval_result) -> None:
        bubble = ScoreCardBubble(eval_result)
        self._layout.insertWidget(self._layout.count() - 1, bubble)
        QTimer.singleShot(10, bubble.play_entrance_animation)
        self._notify_new_content()

    def show_typing_indicator(self) -> None:
        if self._typing_indicator is not None:
            return
        self._typing_indicator = TypingIndicator()
        self._layout.insertWidget(self._layout.count() - 1, self._typing_indicator)
        self.scroll_to_bottom()

    def hide_typing_indicator(self) -> None:
        if self._typing_indicator is None:
            return
        self._layout.removeWidget(self._typing_indicator)
        self._typing_indicator.stop()
        self._typing_indicator.deleteLater()
        self._typing_indicator = None

    def ensure_ai_bubble(self, enable_tts: bool = True) -> None:
        """确保当前存在 AI 流式气泡，不存在则创建"""
        if self._current_ai_bubble is not None:
            return
        self._current_ai_bubble = ChatBubble("ai", enable_tts=enable_tts)
        self._current_ai_bubble.start_tts()
        self._layout.insertWidget(self._layout.count() - 1, self._current_ai_bubble)
        self._notify_new_content()

    def append_ai_chunk(self, chunk: str) -> None:
        if self._current_ai_bubble:
            self._current_ai_bubble.append_chunk(chunk)
            self._notify_new_content()

    def stop_ai_stream(self, force: bool = False) -> None:
        if self._current_ai_bubble:
            self._current_ai_bubble.stop_tts(force=force)
            self._current_ai_bubble = None