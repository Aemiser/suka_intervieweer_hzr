"""
smart_footer.py
智能底部输入区：集成 AsrButton + ChatInputBar，支持鼠标拖拽调整高度。
职责：布局编排、高度拖拽、子组件信号透传、统一状态控制
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent

from UI.components.chat_input_bar import ChatInputBar
from UI.components.button.ASR_button import AsrButton
from UI.components import T


class Footer(QFrame):
    # ── 信号透传 ────────────────────────────────────────────────────────
    send_requested  = Signal(str)
    text_changed    = Signal(str)

    asr_finished    = Signal(str)
    asr_error       = Signal(str)
    play_requested  = Signal(str)
    status_changed  = Signal(str)
    recording_started = Signal()
    recording_stopped = Signal()

    def __init__(self, min_height: int = 160, max_height: int = 400, parent=None):
        super().__init__(parent)
        self.min_height   = min_height
        self.max_height   = max_height
        self._dragging    = False
        self._start_y     = 0
        self._start_height = 0

        self.setFixedHeight(min_height)
        self.setMouseTracking(True)
        self.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border-top: 1px solid {T.BORDER};
            }}
        """)
        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════
    # UI 构建
    # ══════════════════════════════════════════════════════════════════════
    def _build_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 14)
        lay.setSpacing(10)

        self.asr_btn = AsrButton(self)
        self.asr_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self.input_bar = ChatInputBar(self)
        self.input_bar.set_placeholder("输入问题，按 Ctrl+Enter 发送...")
        self.input_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        lay.addWidget(self.asr_btn)
        lay.addWidget(self.input_bar, stretch=1)
        self._bind_signals()

    def _bind_signals(self) -> None:
        self.input_bar.send_requested.connect(self.send_requested)
        self.input_bar.text_changed.connect(self.text_changed)

        self.asr_btn.asr_finished.connect(self.asr_finished)
        self.asr_btn.asr_error.connect(self.asr_error)
        self.asr_btn.play_requested.connect(self.play_requested)
        self.asr_btn.status_changed.connect(self.status_changed)
        self.asr_btn.recording_started.connect(self._on_recording_started)
        self.asr_btn.recording_stopped.connect(self._on_recording_stopped)

    # ══════════════════════════════════════════════════════════════════════
    # 录音状态联动（只动 input_bar，绝不动 asr_btn）
    # ══════════════════════════════════════════════════════════════════════
    def _on_recording_started(self) -> None:
        self.input_bar.setEnabled(False)   # 录音中禁用文字输入
        self.recording_started.emit()

    def _on_recording_stopped(self) -> None:
        self.input_bar.setEnabled(True)    # 录音结束恢复文字输入
        self.recording_stopped.emit()

    # ══════════════════════════════════════════════════════════════════════
    # 拖拽交互
    # ══════════════════════════════════════════════════════════════════════
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton and event.y() <= 14:
            self._dragging     = True
            self._start_y      = event.globalPosition().y()
            self._start_height = self.height()
            self.setCursor(Qt.SizeVerCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging:
            delta = event.globalPosition().y() - self._start_y
            new_h = max(self.min_height, min(self._start_height - delta, self.max_height))
            if new_h != self.height():
                self.setFixedHeight(int(new_h))
            event.accept()
        else:
            self.setCursor(Qt.SizeVerCursor if event.y() <= 14 else Qt.ArrowCursor)
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self._dragging = False
        self.setCursor(Qt.ArrowCursor)
        super().mouseReleaseEvent(event)

    # ══════════════════════════════════════════════════════════════════════
    # 公共接口
    # ══════════════════════════════════════════════════════════════════════
    def set_enabled(self, enabled: bool) -> None:
        """
        流式响应期间由面板调用。
        只控制 input_bar，asr_btn 自己管理自己的状态。
        """
        self.input_bar.setEnabled(enabled)

    def set_input_text(self, text: str) -> None:
        self.input_bar.set_text(text)

    def clear_input(self) -> None:
        self.input_bar.clear()