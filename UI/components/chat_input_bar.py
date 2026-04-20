"""
chat_input_bar.py
布局驱动自适应输入框组件
职责：根据父容器高度实时拉伸、支持滚轮、快捷键拦截、发送信号触发
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeyEvent, QWheelEvent,QTextCursor
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QTextEdit, QSizePolicy

from UI.components import ButtonFactory, T


class _ResizableTextEdit(QTextEdit):
    """内部类：支持弹性拉伸与滚轮的文本编辑区"""
    send_requested = Signal()

    _BORDER_NORMAL   = T.BORDER        # 默认边框
    _BORDER_FOCUS    = T.NEON          # 聚焦/输入时高亮
    _BORDER_RADIUS   = "8px"           # 圆角
    _BORDER_WIDTH    = "1px"           # 线宽
    _TRANSITION_MS   = 120             # 样式过渡动画时长

    def __init__(self, min_h: int = 40, parent=None):
        super().__init__(parent)
        self.min_h = min_h
        self.setMinimumHeight(min_h)

        # 垂直滚动条按需显示，水平永远隐藏
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QTextEdit.NoFrame)

        # 允许垂直方向弹性拉伸，填满父容器分配的空间
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 关键：初始化默认边框 + 开启平滑过渡
        self._apply_border_style(self._BORDER_NORMAL)
        self.setStyleSheet(f"""
            QTextEdit {{
                border-radius: {self._BORDER_RADIUS};
                transition: border-color {self._TRANSITION_MS}ms ease;
            }}
        """)

        # 🔑 绑定事件：焦点变化 + 文本变化 都触发高亮更新
        self.textChanged.connect(self._on_text_changed)
    def wheelEvent(self, event: QWheelEvent) -> None:
        # 拦截滚轮事件，优先作用于本输入框，不向上传递给聊天滚动区
        super().wheelEvent(event)
        event.accept()
    def focusInEvent(self, event) -> None:
        """🎯 获得焦点时高亮"""
        super().focusInEvent(event)
        self._update_highlight()

    def focusOutEvent(self, event) -> None:
        """👋 失去焦点时：有内容则保持高亮，无内容则恢复默认"""
        super().focusOutEvent(event)
        self._update_highlight()

    def _on_text_changed(self) -> None:
        """✍️ 文本变化时同步更新高亮状态"""
        self._update_highlight()

    def wheelEvent(self, event: QWheelEvent) -> None:
        super().wheelEvent(event)
        event.accept()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.send_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # Ctrl+Enter 发送，Enter 换行
        if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
            self.send_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

        # ═══════════════════════════════════════════════════════════════
        # 样式管理（原子操作，避免重复代码）
        # ═══════════════════════════════════════════════════════════════

    def _apply_border_style(self, color: str) -> None:
        """🎨 应用边框颜色（保留原有 padding/背景等样式）"""
        # 获取当前样式，仅替换 border-color，避免覆盖其他样式
        current = self.styleSheet()
        # 移除旧的 border 相关声明（防止重复）
        lines = [l for l in current.split(';') if 'border' not in l.lower()]
        # 拼接新边框
        new_border = f"border: {self._BORDER_WIDTH} solid {color}"
        # 重组样式
        self.setStyleSheet(f"""
            QTextEdit {{
                {'; '.join(lines)};
                {new_border};
            border-radius: {self._BORDER_RADIUS};
                transition: border-color {self._TRANSITION_MS}ms ease;
            }}
        """)

    def _update_highlight(self) -> None:
        """✨ 根据「焦点状态 + 文本内容」决定是否高亮"""
        has_focus = self.hasFocus()
        has_text = bool(self.toPlainText().strip())
        # ✅ 高亮条件：有焦点 或 有内容（避免输入后失焦边框突然消失）
        target_color = self._BORDER_FOCUS if (has_focus or has_text) else self._BORDER_NORMAL
        self._apply_border_style(target_color)


class ChatInputBar(QWidget):
    # ── 信号定义 ──────────────────────────────────────────────────────────────
    send_requested = Signal(str)
    text_changed   = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 允许垂直拉伸以填满 Footer 高度
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._build_ui()

    # ══════════════════════════════════════════════════════════════════════════
    # UI 构建
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        lay = QHBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(8)

        self.text_edit = _ResizableTextEdit(min_h=40)
        self.text_edit.setPlaceholderText("输入你的回答... ")
        self.text_edit.textChanged.connect(lambda: self.text_changed.emit(self.text_edit.toPlainText()))
        self.text_edit.send_requested.connect(self.trigger_send)

        # 发送按钮：固定宽度，高度跟随输入框
        lay.addWidget(self.text_edit, stretch=1)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)


    # ══════════════════════════════════════════════════════════════════════════
    # 公共接口
    # ══════════════════════════════════════════════════════════════════════════

    def trigger_send(self) -> None:
        text = self.text_edit.toPlainText().strip()
        if not text:
            return
        self.send_requested.emit(text)

    def set_enabled(self, enabled: bool) -> None:
        self.text_edit.setEnabled(enabled)
        if enabled:
            self.text_edit.setFocus()

    def set_text(self, text: str) -> None:
        self.text_edit.setPlainText(text)
        self.text_edit.moveCursor(QTextCursor.End)

    def clear(self) -> None:
        self.text_edit.clear()

    def set_placeholder(self, text: str) -> None:
        self.text_edit.setPlaceholderText(text)