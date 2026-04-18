# UI/components/ChatBubble.py
"""
通用聊天气泡组件。

Role 决定气泡样式，**同时决定 TTS 能力**：
  - "assistant" / "ai"  → 面试官/助手角色，支持语音播报（如环境变量齐全）
  - "user"              → 用户角色，无 TTS
  - "system"            → 系统提示，无 TTS，居中纯文本显示

新增特性：
  - 入场动画：气泡从下方滑入并淡入
  - 打字机效果：AI 回复支持逐字显示
"""

from __future__ import annotations

import os
import queue
import threading
from typing import Callable

from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QRect,
    QEasingCurve,
    QParallelAnimationGroup,
)
from PySide6.QtGui import QTextCursor, QPixmap

from UI.components.info.Theme import T
from UI.components.util.md_to_html import md_to_html
from UI.components.info.icon import Icons, IconSize

# ── Role 配置表 ───────────────────────────────────────────────────────────────

_ROLE_CFG: dict[str, dict] = {
    "user": {
        "label": "你",
        "label_icon": "person",
        "label_color": T.NEON,
        "bg": T.USER_BUBBLE,
        "border": T.BORDER,
        "radius": "18px 18px 4px 18px",
        "align": "right",
        "tts": False,
    },
    "assistant": {
        "label": "AI 助手",
        "label_icon": "smart_toy",
        "label_color": T.NEON,
        "bg": T.AI_BUBBLE,
        "border": T.BORDER,
        "radius": "4px 18px 18px 18px",
        "align": "left",
        "tts": True,
    },
    "ai": {
        "label": "AI 面试官",
        "label_icon": "smart_toy",
        "label_color": T.NEON,
        "bg": T.AI_BUBBLE,
        "border": T.BORDER,
        "radius": "4px 18px 18px 18px",
        "align": "left",
        "tts": True,
    },
    "system": {
        "label": "",
        "label_icon": None,
        "label_color": T.TEXT_DIM,
        "bg": "transparent",
        "border": "transparent",
        "radius": "8px",
        "align": "center",
        "tts": False,
    },
}


# ── ChatBubble ────────────────────────────────────────────────────────────────


class ChatBubble(QFrame):
    """
    参数
    ----
    role        : "user" | "assistant" | "ai" | "system"
    content     : 初始 Markdown 文本
    max_width   : 气泡最大宽度
    enable_tts  : 是否启用 TTS
    enable_typewriter : 是否启用打字机效果（仅 AI 角色建议开启）
    """

    def __init__(
        self,
        role: str,
        content: str = "",
        max_width: int = 580,
        enable_tts: bool = False,
        enable_typewriter: bool = False,
        tts_model: str = "qwen3-tts-instruct-flash",
        tts_voice: str = "Elias",
        parent=None,
    ):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)

        self._role = role
        self._content = content
        self._max_width = max_width

        # TTS 状态
        cfg = _ROLE_CFG.get(role, _ROLE_CFG["assistant"])
        self._tts_capable: bool = cfg["tts"] and enable_tts
        self._tts_model = tts_model
        self._tts_voice = tts_voice
        self._tts_started = False

        self._tts_queue: queue.Queue[str | None] | None = None
        self._tts_thread: threading.Thread | None = None
        self._tts_player = None

        # 去重缓存
        self._tts_last_token: str = ""
        self._tts_sentence_cache: list[str] = []
        self._tts_last_sentence: str = ""

        # ── 动画 & 打字机状态 ───────────────────────────────────────────────
        self._anim_group = None
        self._typewriter_enabled = enable_typewriter
        self._typewriter_timer = QTimer(self)
        self._typewriter_timer.timeout.connect(self._type_next_char)
        self._typed_text = ""  # 已打出的文字
        self._buffer_text = ""  # 等待打出的文字（流式累积）

        # ── 布局 ──────────────────────────────────────────────────────────────
        outer = QHBoxLayout(self)
        outer.setContentsMargins(6, 3, 6, 3)
        outer.setSpacing(0)

        # system 消息：居中纯文本，提前返回
        if role == "system":
            lbl = QLabel(content)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(
                f"color: {T.TEXT_DIM}; font-size: 11px;"
                f"padding: 4px 12px; background: transparent;"
                f"font-family: {T.FONT};"
            )
            outer.addWidget(lbl)
            return

        # 气泡主体
        self.bubble = QFrame()
        self.bubble.setObjectName("bubble")
        self.bubble.setMaximumWidth(max_width)
        self.bubble.setStyleSheet(f"""
            QFrame#bubble {{
                background: {cfg["bg"]};
                border: 1px solid {cfg["border"]};
                border-radius: {cfg["radius"]};
            }}
        """)

        inner = QVBoxLayout(self.bubble)
        inner.setContentsMargins(14, 10, 14, 10)
        inner.setSpacing(5)

        # 角色标签
        if cfg["label"]:
            role_lbl_h = QHBoxLayout()
            role_lbl_h.setSpacing(4)
            role_lbl_h.setContentsMargins(0, 0, 0, 0)

            if cfg.get("label_icon"):
                role_icon = QLabel()
                role_icon.setPixmap(
                    Icons.colored_pixmap(
                        cfg["label_icon"], cfg["label_color"], IconSize.XS
                    )
                )
                role_lbl_h.addWidget(role_icon)

            role_lbl = QLabel(cfg["label"])
            role_lbl.setStyleSheet(
                f"font-size: 10px; color: {cfg['label_color']};"
                f"font-weight: 700; letter-spacing: 1px;"
                f"background: transparent; font-family: {T.FONT};"
            )
            role_lbl_h.addWidget(role_lbl)
            role_lbl_h.addStretch()
            inner.addLayout(role_lbl_h)

        # 内容视图
        self.text_view = QTextBrowser()
        self.text_view.setOpenExternalLinks(True)
        self.text_view.setFrameShape(QFrame.NoFrame)
        self.text_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.text_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.text_view.setStyleSheet(f"""
            QTextBrowser {{
                background: transparent;
                color: {T.TEXT};
                font-size: 14px;
                border: none;
                font-family: {T.FONT};
                line-height: 1.7;
            }}
        """)
        inner.addWidget(self.text_view)

        if cfg["align"] == "right":
            outer.addStretch(2)
            outer.addWidget(self.bubble, stretch=8)
        else:
            outer.addWidget(self.bubble, stretch=8)
            outer.addStretch(2)

        if content:
            self._render()
            self._adjust_height()

    # ══════════════════════════════════════════════════════════════════════════
    # 动画 & 打字机
    # ══════════════════════════════════════════════════════════════════════════

    # ChatBubble.py - play_entrance_animation 方法修改
    def play_entrance_animation(self):
        # 确保已显示
        self.show()

        # ✅ 使用 QGraphicsOpacityEffect 替代 windowOpacity
        from PySide6.QtWidgets import QGraphicsOpacityEffect

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._opacity_effect)
        self._opacity_effect.setOpacity(0.0)

        # 透明度动画（作用于 effect 而非 widget）
        self._opacity_anim = QPropertyAnimation(self._opacity_effect, b"opacity", self)
        self._opacity_anim.setDuration(180)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.setEasingCurve(QEasingCurve.OutCubic)

        # ✅ 位移动画改用 margin 动画（兼容布局管理器）
        self._margin_anim = QPropertyAnimation(self, b"contentsMargins", self)
        self._margin_anim.setDuration(180)
        self._margin_anim.setStartValue((0, 40, 0, 0))  # 顶部预留 40px
        self._margin_anim.setEndValue((0, 0, 0, 0))
        self._margin_anim.setEasingCurve(QEasingCurve.OutCubic)

        # 并行执行
        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(self._opacity_anim)
        self._anim_group.addAnimation(self._margin_anim)
        self._anim_group.finished.connect(self._on_entrance_finished)
        self._anim_group.start()

    def _on_entrance_finished(self):
        """入场动画结束，如果是 AI 且未开始打字，则启动打字机"""
        if self._role in ("ai", "assistant") and self._typewriter_enabled:
            self._start_typewriter()

    def _start_typewriter(self):
        """启动打字机效果"""
        if not self._typewriter_timer.isActive():
            self._typed_text = ""
            self._typewriter_timer.start(15)  # 每 15ms 输出一个字符

    def _type_next_char(self):
        if not self._buffer_text:
            # 如果缓冲区空了，检查是否有内容在流式输入中，没有则停止
            if not self._tts_started:  # 简单判断：TTS 停了通常流也停了
                self._typewriter_timer.stop()
            return

        # 取出一个字符
        char = self._buffer_text[0]
        self._buffer_text = self._buffer_text[1:]
        self._typed_text += char

        # 渲染当前已打出的文字
        self.text_view.setHtml(md_to_html(self._typed_text))
        self._adjust_height()

    # ══════════════════════════════════════════════════════════════════════════
    # 内容渲染
    # ══════════════════════════════════════════════════════════════════════════

    def _render(self) -> None:
        """将 _content 渲染为 HTML 并更新 text_view。"""
        self.text_view.setHtml(md_to_html(self._content))

    def _adjust_height(self) -> None:
        """根据渲染后的文档高度动态调整 text_view 高度。"""
        w = min(
            self.text_view.width() or (self._max_width - 28),
            self._max_width - 28,
        )
        self.text_view.document().setTextWidth(w)
        h = int(self.text_view.document().size().height()) + 24
        self.text_view.setFixedHeight(max(36, h))

    # ══════════════════════════════════════════════════════════════════════════
    # 流式追加（外部调用）
    # ══════════════════════════════════════════════════════════════════════════

    def append_chunk(self, chunk: str) -> None:
        """
        追加一个流式 token，同时驱动 TTS 和 打字机。
        """
        self._content += chunk

        if self._typewriter_enabled and self._typewriter_timer.isActive():
            # 打字机模式：存入缓冲区，等待定时器消费
            self._buffer_text += chunk
        else:
            # 非打字机模式（或用户消息）：直接渲染
            self._render()
            cursor = self.text_view.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.text_view.setTextCursor(cursor)
            self._adjust_height()

        # 驱动 TTS
        if self._tts_capable and self._tts_started:
            self._feed_tts_token(chunk)

    def set_content(self, text: str) -> None:
        """非流式场景：一次性设置完整内容。"""
        self._content = text
        self._buffer_text = text  # 如果启用了打字机，从这里开始打
        self._render()
        self._adjust_height()

    # ══════════════════════════════════════════════════════════════════════════
    # TTS 公共接口
    # ══════════════════════════════════════════════════════════════════════════

    def start_tts(self) -> None:
        if not self._tts_capable or self._tts_started:
            return
        api_key = os.getenv("DASHSCOPE_API_KEY", "").strip()
        if not api_key:
            return

        try:
            from service.voice_sdk.audio.player import StreamingAudioPlayer
            from service.voice_sdk.tts.pipeline import stream_interview_tts_from_tokens
        except ImportError:
            return

        self._tts_queue = queue.Queue()
        self._tts_last_token = ""
        self._tts_sentence_cache = []
        self._tts_last_sentence = ""

        def _token_iter():
            assert self._tts_queue is not None
            while True:
                token = self._tts_queue.get()
                if token is None:
                    break
                yield token

        def _runner():
            self._tts_player = StreamingAudioPlayer()
            try:
                stream_interview_tts_from_tokens(
                    token_stream=_token_iter(),
                    on_audio_chunk=self._on_tts_audio_chunk,
                    api_key=api_key,
                    model=self._tts_model,
                    voice=self._tts_voice,
                    sentence_punctuations=frozenset(
                        {".", "。", "!", "！", "?", "？", ";", "；", ":", "：", "\n"}
                    ),
                    ordered_output=False,
                    max_workers=1,
                    max_buffer_length=64,
                )
            except Exception as exc:
                print(f"[ChatBubble TTS] error: {exc}")
            finally:
                if self._tts_player is not None:
                    self._tts_player.close()

        self._tts_thread = threading.Thread(target=_runner, daemon=True)
        self._tts_thread.start()
        self._tts_started = True

    def stop_tts(self, force: bool = False) -> None:
        if not self._tts_started:
            return

        # 停止打字机
        if self._typewriter_timer.isActive():
            # 把剩余缓冲区全部打出
            self._typed_text += self._buffer_text
            self._buffer_text = ""
            self._render()
            self._adjust_height()
            self._typewriter_timer.stop()

        if force:
            if self._tts_queue is not None:
                try:
                    self._tts_queue.put(None)
                except Exception:
                    pass
            if self._tts_player is not None:
                try:
                    self._tts_player.close()
                except Exception:
                    pass
            self._reset_tts_state()
        else:
            if self._tts_queue is not None:
                try:
                    self._tts_queue.put(None)
                except Exception:
                    pass
            self._tts_started = False

    def _reset_tts_state(self) -> None:
        self._tts_queue = None
        self._tts_thread = None
        self._tts_player = None
        self._tts_started = False
        self._tts_last_token = ""
        self._tts_sentence_cache = []
        self._tts_last_sentence = ""

    # ══════════════════════════════════════════════════════════════════════════
    # TTS 内部实现
    # ══════════════════════════════════════════════════════════════════════════

    def _feed_tts_token(self, token: str) -> None:
        if self._tts_queue is None:
            return
        token_text = str(token or "").strip("\r")
        if not token_text:
            return

        if token_text == self._tts_last_token:
            return

        stripped = token_text.strip()
        if (
            stripped
            and stripped[-1] in {"。", "！", "？", ".", "!", "?", "\n"}
            and len(stripped) > 3
        ):
            if stripped in self._tts_sentence_cache:
                self._tts_last_token = token_text
                return
            self._tts_sentence_cache.append(stripped)
            if len(self._tts_sentence_cache) > 12:
                self._tts_sentence_cache.pop(0)

        self._tts_last_token = token_text
        self._tts_queue.put(token_text)

    def _on_tts_audio_chunk(self, audio_chunk: bytes, sentence: str) -> None:
        if not audio_chunk:
            return
        if sentence != self._tts_last_sentence:
            print(f"[ChatBubble TTS] playing: {sentence}")
            self._tts_last_sentence = sentence
        if self._tts_player is not None:
            self._tts_player.submit(audio_chunk)
