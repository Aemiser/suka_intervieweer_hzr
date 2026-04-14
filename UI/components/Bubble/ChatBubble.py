# UI/components/ChatBubble.py
"""
通用聊天气泡组件。

Role 决定气泡样式，**同时决定 TTS 能力**：
  - "assistant" / "ai"  → 面试官/助手角色，支持语音播报（如环境变量齐全）
  - "user"              → 用户角色，无 TTS
  - "system"            → 系统提示，无 TTS，居中纯文本显示

TTS 设计原则
------------
- TTS 线程完全内聚在 ChatBubble 内，外部（Panel）只需调用
  `bubble.start_tts()` / `bubble.stop_tts()`，或在流式阶段让
  `append_chunk()` 自动驱动。
- 通过构造参数 `enable_tts: bool` 显式开关，默认 False，需要 TTS
  的调用方传 True；仅当 `DASHSCOPE_API_KEY` 存在时才实际启动。
- TTS 线程为 daemon 线程，不阻塞主窗口关闭。
- `stop_tts(force=False)` 可在流结束/窗口关闭时调用，非强制模式
  会等待当前句子播完再停；强制模式立即终止。
"""

from __future__ import annotations

import os
import queue
import threading
from typing import Callable

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QTextBrowser, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor

from UI.components.info.Theme import T
from UI.components.util.md_to_html import md_to_html


# ── Role 配置表 ───────────────────────────────────────────────────────────────

_ROLE_CFG: dict[str, dict] = {
    "user": {
        "label":       "你",
        "label_color": T.WARNING,      # ✅ 原 T.YELLOW → T.WARNING (#B79A7B)
        "bg":          T.USER_BUBBLE,  # ✅ 已更新为新拟物色 #E8DFD3（Theme 中已定义）
        "border":      f"{T.BORDER}55",# ✅ 原 T.NEON+alpha → 用主边框色+透明度
        "radius":      "18px 18px 4px 18px",
        "align":       "right",
        "tts":         False,
    },
    "assistant": {
        "label":       "AI 助手",
        "label_color": T.INFO,         # ✅ 原 T.NEON → T.INFO (#A89B8E)
        "bg":          T.AI_BUBBLE,    # ✅ 已更新为新拟物色 #F5EEE4
        "border":      T.BORDER,       # ✅ 原 T.BORDER2 → T.BORDER (#D8CCBC)
        "radius":      "4px 18px 18px 18px",
        "align":       "left",
        "tts":         True,
    },
    "ai": {
        "label":       "AI 面试官",
        "label_color": T.INFO,         # ✅ 同上
        "bg":          T.AI_BUBBLE,
        "border":      T.BORDER,       # ✅ 同上
        "radius":      "4px 18px 18px 18px",
        "align":       "left",
        "tts":         True,
    },
    "system": {
        "label":       "",
        "label_color": T.TEXT_DIM,     # ✅ 保留，新主题中仍定义
        "bg":          "transparent",
        "border":      "transparent",
        "radius":      "8px",
        "align":       "center",
        "tts":         False,
    },
}


# ── ChatBubble ────────────────────────────────────────────────────────────────

class ChatBubble(QFrame):
    """
    参数
    ----
    role        : "user" | "assistant" | "ai" | "system"
    content     : 初始 Markdown 文本（可为空，稍后通过 append_chunk 流式填充）
    max_width   : 气泡最大宽度（px）
    enable_tts  : 是否启用 TTS 语音播报（仅对支持 TTS 的 role 生效）
    tts_model   : TTS 模型名
    tts_voice   : 发音人
    """

    def __init__(
        self,
        role: str,
        content: str = "",
        max_width: int = 580,
        enable_tts: bool = False,
        tts_model: str = "qwen3-tts-instruct-flash",
        tts_voice: str = "Elias",
        parent=None,
    ):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)

        self._role      = role
        self._content   = content
        self._max_width = max_width

        # TTS 状态
        cfg = _ROLE_CFG.get(role, _ROLE_CFG["assistant"])
        self._tts_capable: bool = cfg["tts"] and enable_tts
        self._tts_model   = tts_model
        self._tts_voice   = tts_voice
        self._tts_started = False

        self._tts_queue:   queue.Queue[str | None] | None = None
        self._tts_thread:  threading.Thread | None        = None
        self._tts_player                                  = None  # StreamingAudioPlayer

        # 去重缓存
        self._tts_last_token: str             = ""
        self._tts_sentence_cache: list[str]   = []
        self._tts_last_sentence: str          = ""

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
                f"padding: 4px 12px; background: {T.BASE}80;"
                f"font-family: {T.FONT}; border-radius: 8px;"
            )
            outer.addWidget(lbl)
            return

        # 气泡主体
        self.bubble = QFrame()
        self.bubble.setObjectName("bubble")
        self.bubble.setMaximumWidth(max_width)
        self.bubble.setStyleSheet(f"""
            QFrame#bubble {{
                background: {cfg['bg']};
                border: 1px solid {cfg['border']};
                border-radius: {cfg['radius']};
            }}
        """)

        inner = QVBoxLayout(self.bubble)
        inner.setContentsMargins(14, 10, 14, 10)
        inner.setSpacing(5)

        # 角色标签
        if cfg["label"]:
            role_lbl = QLabel(cfg["label"])
            role_lbl.setStyleSheet(
                f"font-size: 10px; color: {cfg['label_color']};"
                f"font-weight: 700; letter-spacing: 1px;"
                f"background: transparent; font-family: {T.FONT};"
            )
            inner.addWidget(role_lbl)

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
        追加一个流式 token，同时驱动 TTS（如已启用）。
        必须在主线程调用。
        """
        self._content += chunk
        self._render()
        cursor = self.text_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_view.setTextCursor(cursor)
        self._adjust_height()

        if self._tts_capable and self._tts_started:
            self._feed_tts_token(chunk)

    def set_content(self, text: str) -> None:
        """非流式场景：一次性设置完整内容。"""
        self._content = text
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
        # ✅ 不在这里构造 StreamingAudioPlayer，移到线程内部
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
            # ✅ 在后台线程里才构造播放器，不阻塞主线程
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

        if force:
            # 强制：塞哨兵截断 + 关播放器
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
            # 非强制：只标记不再接受新 token，让已有队列自然播完
            # _runner 里的 _token_iter 会在队列空了之后
            # 等待下一个 token，所以需要塞哨兵告诉它结束
            if self._tts_queue is not None:
                try:
                    self._tts_queue.put(None)
                except Exception:
                    pass
            # 不 join，不 close player，让线程自己跑完
            # 只重置 _tts_started 防止新 token 继续投递
            self._tts_started = False
            # 注意：不能调 _reset_tts_state，那会把 queue/player 置 None
            # 线程还在用它们

    def _reset_tts_state(self) -> None:
        self._tts_queue   = None
        self._tts_thread  = None
        self._tts_player  = None
        self._tts_started = False
        self._tts_last_token     = ""
        self._tts_sentence_cache = []
        self._tts_last_sentence  = ""

    # ══════════════════════════════════════════════════════════════════════════
    # TTS 内部实现
    # ══════════════════════════════════════════════════════════════════════════

    def _feed_tts_token(self, token: str) -> None:
        """向 TTS 队列投递 token（含去重逻辑）。"""
        if self._tts_queue is None:
            return

        token_text = str(token or "").strip("\r")
        if not token_text:
            return

        # 去重 1：连续重复 token
        if token_text == self._tts_last_token:
            return

        # 去重 2：完整句子在短窗口内重复
        stripped = token_text.strip()
        if stripped and stripped[-1] in {"。", "！", "？", ".", "!", "?", "\n"} and len(stripped) > 3:
            if stripped in self._tts_sentence_cache:
                self._tts_last_token = token_text
                return
            self._tts_sentence_cache.append(stripped)
            if len(self._tts_sentence_cache) > 12:
                self._tts_sentence_cache.pop(0)

        self._tts_last_token = token_text
        self._tts_queue.put(token_text)

    def _on_tts_audio_chunk(self, audio_chunk: bytes, sentence: str) -> None:
        """TTS 回调：将音频块交给播放器（从 TTS 线程调用）。"""
        if not audio_chunk:
            return
        if sentence != self._tts_last_sentence:
            print(f"[ChatBubble TTS] playing: {sentence}")
            self._tts_last_sentence = sentence
        if self._tts_player is not None:
            self._tts_player.submit(audio_chunk)