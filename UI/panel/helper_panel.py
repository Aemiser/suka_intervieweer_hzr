"""
AI 知识助手面板（ChatArea 解耦重构版）。

架构说明：
  - ChatArea 组件独立封装聊天渲染、滚动、TypingIndicator、TTS 状态
  - 面板仅负责信号路由、流式对话编排、工具状态同步
  - TTS 与滚动逻辑完全交由 ChatArea 内部接管，面板零感知
"""

import threading

from PySide6.QtWidgets import (
    QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame,QWidget
)
from PySide6.QtCore import Qt, QTimer

from UI.components import (
    T, StreamSignals, ButtonFactory, GLOBAL_QSS, input_qss
)
from UI.components.footer import Footer
from UI.components.chat_area import ChatArea

# ── 快捷提示 ──────────────────────────────────────────────────────────────────
HINTS = [
    ("🎲", "随机抽题", "从题库随机抽5道题", T.NEON),
    ("🔍", "搜索题目", "搜索 Redis 相关题目", T.PURPLE),
    ("📊", "题库统计", "查看题库分类统计", T.YELLOW),
    ("🌐", "联网搜索", "搜索 Spring Boot 3.0 新特性", T.GREEN),
    ("📚", "知识检索", "什么是 MVCC？", T.NEON),
    ("🏆", "历史记录", "查看学生ID=1的面试记录", T.ACCENT),
]

class HelperPanel(QWidget):
    def __init__(self, agent, parent=None):
        super().__init__(parent)
        self.agent = agent

        # 流式信号中枢（保持跨线程安全）
        self._stream_signals = StreamSignals()
        self._is_streaming = False

        # 信号路由至 ChatArea
        self._stream_signals.chunk_received.connect(self._on_chunk)
        self._stream_signals.stream_done.connect(self._on_stream_done)
        self._stream_signals.stream_error.connect(self._on_stream_error)

        self._build_ui()
        self._bind_footer_signals()

        # 初始化欢迎语（复用 ChatArea 的系统消息通道）
        self.chat_area.add_system_message(
            "你好！我是 **AI 知识助手** 🤖\n\n"
            "我可以帮你：\n"
            "- 🎲 随机抽题练习\n"
            "- 🔍 搜索题目和查看答案\n"
            "- 📊 题库统计与分析\n"
            "- 🌐 联网搜索最新技术资料\n"
            "- 📚 知识库技术概念检索\n"
            "- 🏆 查看历史面试记录\n\n"
            "点击上方快捷按钮，或直接输入问题开始！"
        )

    # ── 信号绑定 ──────────────────────────────────────────────────────────────
    def _bind_footer_signals(self) -> None:
        self.footer.send_requested.connect(self._send)
        self.footer.asr_finished.connect(self._on_asr_transcript)
        self.footer.status_changed.connect(lambda s: self._tool_status.setText(s))

    def _on_asr_transcript(self, text: str) -> None:
        if text:
            self.footer.set_input_text(text)
            self._send()  # 自动提交

    # ── UI 构建 ───────────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        self.setStyleSheet(GLOBAL_QSS + input_qss())
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        root.addWidget(self._build_header())
        root.addWidget(self._build_hints())

        # ✅ 替换原手动构建的 QScrollArea + ChatBubble/TypingIndicator
        self.chat_area = ChatArea()
        root.addWidget(self.chat_area, stretch=1)

        self.footer = Footer(min_height=160, max_height=400)
        root.addWidget(self.footer)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"QFrame {{ background: {T.SURFACE}; border-bottom: 1px solid {T.BORDER}; }}")
        lay = QHBoxLayout(header)
        lay.setContentsMargins(22, 0, 22, 0)

        title = QLabel("🤖  AI 知识助手")
        title.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {T.TEXT}; font-family: {T.FONT};")

        self._tool_status = QLabel()
        self._refresh_tool_status()
        self._tool_status.setStyleSheet(f"""
            font-size: 11px; color: {T.GREEN}; font-weight: 600;
            background: {T.GREEN}11; border: 1px solid {T.GREEN}33;
            border-radius: 10px; padding: 2px 10px;
        """)

        clear_btn = ButtonFactory.ghost("清空对话")
        clear_btn.clicked.connect(self._clear)

        lay.addWidget(title)
        lay.addStretch()
        lay.addWidget(self._tool_status)
        lay.addSpacing(12)
        lay.addWidget(clear_btn)
        return header

    def _build_hints(self) -> QFrame:
        frame = QFrame()
        frame.setFixedHeight(52)
        frame.setStyleSheet(f"QFrame {{ background: {T.SURFACE2}; border-bottom: 1px solid {T.BORDER}; }}")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(18, 10, 18, 10)
        lay.setSpacing(8)

        for icon, label, tooltip, color in HINTS:
            btn = ButtonFactory.tag(f"{icon} {label}", color)
            btn.setToolTip(tooltip)
            btn.clicked.connect(lambda checked, t=tooltip: self._quick_send(t))
            lay.addWidget(btn)
        lay.addStretch()
        return frame

    # ── 业务逻辑 ──────────────────────────────────────────────────────────────
    def _refresh_tool_status(self) -> None:
        count = (
            len(self.agent.get_registered_tools())
            if hasattr(self.agent, "get_registered_tools") else 8
        )
        self._tool_status.setText(f"● {count} 个工具就绪")

    def _quick_send(self, text: str) -> None:
        self.footer.set_input_text(text)
        self._send()

    def _send(self) -> None:
        if self._is_streaming:
            return
        text = self.footer.input_bar.text_edit.toPlainText().strip()
        if not text:
            return
        self.footer.clear_input()
        self.chat_area.add_user_message(text)  # ✅ 替代原 _add_user_bubble
        self._start_stream(text)

    def _start_stream(self, text: str) -> None:
        self._is_streaming = True
        self._set_input_enabled(False)
        self.chat_area.show_typing_indicator()  # ✅ 替代原手动创建 TypingIndicator

        def _run() -> None:
            try:
                for chunk in self.agent.stream(text):
                    self._stream_signals.chunk_received.emit(chunk)
                self._stream_signals.stream_done.emit()
            except Exception as e:
                self._stream_signals.stream_error.emit(str(e))

        threading.Thread(target=_run, daemon=True).start()

    def _on_chunk(self, chunk: str) -> None:
        self.chat_area.hide_typing_indicator()          # ✅
        self.chat_area.ensure_ai_bubble(enable_tts=True) # ✅ 内部接管气泡创建与 TTS 标记
        self.chat_area.append_ai_chunk(chunk)            # ✅

    def _on_stream_done(self) -> None:
        self.chat_area.stop_ai_stream()                  # ✅ 内部接管 TTS 停止与流状态清理
        self._is_streaming = False
        self._set_input_enabled(True)
        self.footer.input_bar.text_edit.setFocus()

    def _on_stream_error(self, msg: str) -> None:
        self.chat_area.hide_typing_indicator()
        self.chat_area.stop_ai_stream(force=True)        # ✅ 强制中断
        self.chat_area.add_system_message(f"❌ 出错了：{msg}")
        self._is_streaming = False
        self._set_input_enabled(True)

    def _clear(self) -> None:
        self.chat_area.clear()                           # ✅ 替代原布局遍历删除
        self.agent.clear_conversation()
        # 可选：清空后重新显示欢迎语
        # self.chat_area.add_system_message("对话已清空，请重新开始提问...")

    def _set_input_enabled(self, enabled: bool) -> None:
        self.footer.set_enabled(enabled)