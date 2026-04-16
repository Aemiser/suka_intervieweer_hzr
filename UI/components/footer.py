"""
smart_footer.py
智能底部输入区：集成 AsrButton + ChatInputBar + SendButton，支持鼠标拖拽调整高度。
职责：布局编排、高度拖拽、子组件信号透传、统一状态控制
新增：卡片化视觉呈现（内嵌 Card 实现悬浮、圆角、阴影效果）
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QSizePolicy, QPushButton
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QCursor, QColor

from UI.components.chat_input_bar import ChatInputBar
from UI.components.info.icon import Icons, IconSize
from UI.components.button.ASR_button import AsrButton
from UI.components.ButtonFactory import ButtonFactory
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

        # 【关键】外层 Frame 保持全透明，不占边距，确保鼠标拖拽区(顶部14px)永远生效
        self.setStyleSheet("QFrame { background: transparent; border: none; }")

        self._build_ui()

    def _build_ui(self) -> None:
        # ── 1. 创建内层卡片容器 ────────────────────────────────────────
        self.card = QFrame(self)
        self.card.setObjectName("FooterCard")
        self.card.setStyleSheet(f"""
            QFrame#FooterCard {{
                background: {T.SURFACE2};
                border: 1px solid {T.BORDER};
                border-radius: 12px;  /* 四角全圆 */
            }}
        """)

        # ── 阴影（参照 InterviewHeader） ──────────────────────────────
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtCore import Qt as _Qt
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(T.SURFACE2_DARK))
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        self.card.setGraphicsEffect(shadow)

        # 其余 card_lay、input_bar、bottom_lay 全部挂到 self.card 下，无需改动
        card_lay = QVBoxLayout(self.card)
        card_lay.setContentsMargins(0, 12, 0, 12)
        card_lay.setSpacing(12)

        self.input_bar = ChatInputBar(self.card)
        self.input_bar.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        card_lay.addWidget(self.input_bar, stretch=1)

        bottom_lay = QHBoxLayout()
        bottom_lay.setContentsMargins(8, 0, 8, 0)
        bottom_lay.setSpacing(12)

        self.asr_btn = AsrButton(self.card)
        self.asr_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bottom_lay.addWidget(self.asr_btn, stretch=8)

        self.send_btn = ButtonFactory.solid("发送", T.GREEN,height=42)
        self.send_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.send_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bottom_lay.addWidget(self.send_btn, stretch=2)

        card_lay.addLayout(bottom_lay)

        # ── 2. 外层透明 Frame 布局 ─────────────────────────────────────
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(6, 8, 6, 20)  # 底部 0，卡片贴底边
        root_lay.setSpacing(0)
        root_lay.addWidget(self.card, stretch=1)

        self._bind_signals()
        self._set_icon()

    def _set_icon(self) -> None:
        """集中注册 Footer 内所有子组件的静态图标"""
        # 发送按钮图标
        print("setIconInFooter")
        self.send_btn.setIcon(Icons.get("send", IconSize.MD))


    def _bind_signals(self) -> None:
        # 文本变化透传
        self.input_bar.text_changed.connect(self.text_changed)

        # 【关键】监听输入框的回车信号，触发发送按钮的逻辑
        self.input_bar.send_requested.connect(self._handle_send_request)
        # 发送按钮点击（注意这里没有参数）
        self.send_btn.clicked.connect(self._on_send_btn_clicked)
        # ASR 信号透传
        self.asr_btn.asr_finished.connect(self.asr_finished)
        self.asr_btn.asr_error.connect(self.asr_error)
        self.asr_btn.play_requested.connect(self.play_requested)
        self.asr_btn.status_changed.connect(self.status_changed)
        self.asr_btn.recording_started.connect(self._on_recording_started)
        self.asr_btn.recording_stopped.connect(self._on_recording_stopped)

    # ══════════════════════════════════════════════════════════════════════
    # 发送逻辑统筹
    # ══════════════════════════════════════════════════════════════════════
    def _on_send_btn_clicked(self) -> None:
        """中转方法：点击按钮时，主动去输入框拿文本，然后走统一发送逻辑"""
        self.input_bar.trigger_send()  # 让 input_bar 提取文本并 emit send_requested

    def _handle_send_request(self, text: str) -> None:
        """统一处理来自【回车键】和【点击发送按钮】的发送请求"""
        if not text or not text.strip():
            return
        self.send_requested.emit(text.strip())
        self.input_bar.clear()  # 真正的清空只在这里执行一次！

    # ══════════════════════════════════════════════════════════════════════
    # 录音状态联动
    # ══════════════════════════════════════════════════════════════════════
    def _on_recording_started(self) -> None:
        self.input_bar.setEnabled(False)
        self.send_btn.setEnabled(False)   # 录音时一并禁用发送按钮
        self.recording_started.emit()

    def _on_recording_stopped(self) -> None:
        self.input_bar.setEnabled(True)
        self.send_btn.setEnabled(True)    # 恢复发送按钮
        self.recording_stopped.emit()

    # ══════════════════════════════════════════════════════════════════════
    # 拖拽交互 (外层透明 Frame 保证热区绝对可用)
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
        """
        self.input_bar.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)  # 同步控制发送按钮状态

    def set_input_text(self, text: str) -> None:
        self.input_bar.set_text(text)

    def clear_input(self) -> None:
        self.input_bar.clear()
