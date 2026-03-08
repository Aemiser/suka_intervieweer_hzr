# UI/components.py
"""
统一 UI 组件库
供 AgentPanel、InterviewPanel 等所有面板共用
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextBrowser, QSizePolicy, QGraphicsDropShadowEffect, QWidget,
)
from PySide6.QtCore import Qt, Signal, QObject, QTimer
from PySide6.QtGui import QColor, QTextCursor, QFont, QLinearGradient, QPainter, QPen, QBrush


# ═══════════════════════════════════════════════════════════════════
# 色彩系统
# ═══════════════════════════════════════════════════════════════════

class Theme:
    BG          = "#0A0A14"
    SURFACE     = "#12121E"
    SURFACE2    = "#1A1A2E"
    SURFACE3    = "#0F1628"

    ACCENT      = "#E94560"
    NEON        = "#00D4FF"
    GREEN       = "#00FF9D"
    YELLOW      = "#FFD166"
    PURPLE      = "#B388FF"

    TEXT        = "#E8E8F5"
    TEXT_DIM    = "#7070A0"
    TEXT_MUTE   = "#404060"

    BORDER      = "#1E1E3A"
    BORDER2     = "#2A2A50"

    USER_BUBBLE = "#0F2A4A"
    AI_BUBBLE   = "#12121E"

    SUCCESS     = GREEN
    ERROR       = ACCENT
    WARNING     = YELLOW
    INFO        = NEON

    FONT        = '-apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    FONT_MONO   = '"JetBrains Mono", "Cascadia Code", "Fira Code", monospace'

T = Theme


# ═══════════════════════════════════════════════════════════════════
# Markdown → HTML 转换器（支持表格、代码块、加粗等）
# ═══════════════════════════════════════════════════════════════════

def _md_to_html(text: str) -> str:
    """
    将 Markdown 文本转换为带样式的 HTML。
    重点修复 QTextBrowser 对表格渲染的缺陷。
    """
    import re

    lines = text.split("\n")
    html_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── 表格检测：连续的 | 行 ────────────────────────────────────────────
        if "|" in line and line.strip().startswith("|"):
            table_rows = []
            while i < len(lines) and "|" in lines[i] and lines[i].strip().startswith("|"):
                table_rows.append(lines[i])
                i += 1

            # 过滤掉分隔行（---|---）
            data_rows = [r for r in table_rows if not re.match(r"^\|[\s\-:|]+\|", r)]
            if not data_rows:
                continue

            html_lines.append(f"""
<table style="
    border-collapse: collapse;
    width: 100%;
    margin: 8px 0;
    font-size: 13px;
    font-family: {T.FONT};
">""")
            for row_idx, row in enumerate(data_rows):
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                tag = "th" if row_idx == 0 else "td"
                bg  = T.SURFACE3 if row_idx == 0 else (T.SURFACE if row_idx % 2 == 1 else T.SURFACE2)
                html_lines.append("<tr>")
                for cell in cells:
                    cell_html = _inline_md(cell)
                    html_lines.append(
                        f'<{tag} style="'
                        f'border: 1px solid {T.BORDER2};'
                        f'padding: 6px 10px;'
                        f'background: {bg};'
                        f'color: {"" + T.NEON if row_idx == 0 else T.TEXT};'
                        f'font-weight: {"700" if row_idx == 0 else "400"};'
                        f'">{cell_html}</{tag}>'
                    )
                html_lines.append("</tr>")
            html_lines.append("</table>")
            continue

        # ── 代码块 ───────────────────────────────────────────────────────────
        if line.strip().startswith("```"):
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
                i += 1
            i += 1  # 跳过结束 ```
            code_content = "\n".join(code_lines)
            html_lines.append(
                f'<pre style="'
                f'background:{T.SURFACE3};'
                f'border:1px solid {T.BORDER2};'
                f'border-radius:6px;'
                f'padding:10px 12px;'
                f'margin:6px 0;'
                f'font-family:{T.FONT_MONO};'
                f'font-size:12px;'
                f'color:{T.GREEN};'
                f'white-space:pre-wrap;'
                f'word-break:break-all;'
                f'">{code_content}</pre>'
            )
            continue

        # ── 标题 ─────────────────────────────────────────────────────────────
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            level = len(m.group(1))
            size  = {1: "18px", 2: "16px", 3: "14px", 4: "13px"}.get(level, "14px")
            color = {1: T.NEON, 2: T.NEON, 3: T.TEXT, 4: T.TEXT_DIM}.get(level, T.TEXT)
            content = _inline_md(m.group(2))
            html_lines.append(
                f'<p style="font-size:{size};font-weight:700;color:{color};'
                f'margin:10px 0 4px 0;">{content}</p>'
            )
            i += 1
            continue

        # ── 无序列表 ─────────────────────────────────────────────────────────
        if re.match(r"^[\-\*\+]\s+", line):
            html_lines.append('<ul style="margin:4px 0;padding-left:20px;">')
            while i < len(lines) and re.match(r"^[\-\*\+]\s+", lines[i]):
                item = _inline_md(lines[i][2:].strip())
                html_lines.append(f'<li style="color:{T.TEXT};margin:2px 0;">{item}</li>')
                i += 1
            html_lines.append("</ul>")
            continue

        # ── 有序列表 ─────────────────────────────────────────────────────────
        if re.match(r"^\d+\.\s+", line):
            html_lines.append('<ol style="margin:4px 0;padding-left:20px;">')
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i]):
                item = _inline_md(re.sub(r"^\d+\.\s+", "", lines[i]))
                html_lines.append(f'<li style="color:{T.TEXT};margin:2px 0;">{item}</li>')
                i += 1
            html_lines.append("</ol>")
            continue

        # ── 分割线 ───────────────────────────────────────────────────────────
        if re.match(r"^[-_\*]{3,}$", line.strip()):
            html_lines.append(f'<hr style="border:none;border-top:1px solid {T.BORDER2};margin:8px 0;">')
            i += 1
            continue

        # ── 空行 ─────────────────────────────────────────────────────────────
        if not line.strip():
            html_lines.append('<br>')
            i += 1
            continue

        # ── 普通段落 ─────────────────────────────────────────────────────────
        html_lines.append(
            f'<p style="color:{T.TEXT};font-size:14px;margin:3px 0;line-height:1.7;">'
            f'{_inline_md(line)}</p>'
        )
        i += 1

    body = "\n".join(html_lines)
    return f"""
<html><body style="
    background: transparent;
    font-family: {T.FONT};
    color: {T.TEXT};
    margin: 0; padding: 0;
">{body}</body></html>
"""


def _inline_md(text: str) -> str:
    """处理行内 Markdown：加粗、斜体、行内代码、链接。"""
    import re
    # 转义 HTML 特殊字符（先处理，避免后续标签被转义）
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # 行内代码
    text = re.sub(
        r"`([^`]+)`",
        rf'<code style="background:{T.SURFACE3};color:{T.GREEN};'
        rf'padding:1px 4px;border-radius:3px;font-family:{T.FONT_MONO};font-size:12px;">\1</code>',
        text,
    )
    # 加粗
    text = re.sub(r"\*\*(.+?)\*\*", rf'<strong style="color:{T.TEXT};">\1</strong>', text)
    text = re.sub(r"__(.+?)__",     rf'<strong style="color:{T.TEXT};">\1</strong>', text)
    # 斜体
    text = re.sub(r"\*(.+?)\*", rf'<em style="color:{T.TEXT_DIM};">\1</em>', text)
    text = re.sub(r"_(.+?)_",   rf'<em style="color:{T.TEXT_DIM};">\1</em>', text)
    # 链接
    text = re.sub(
        r"\[(.+?)\]\((.+?)\)",
        rf'<a href="\2" style="color:{T.NEON};">\1</a>',
        text,
    )
    return text


# ═══════════════════════════════════════════════════════════════════
# 流式信号
# ═══════════════════════════════════════════════════════════════════

class StreamSignals(QObject):
    chunk_received = Signal(str)
    stream_done    = Signal()
    stream_error   = Signal(str)


# ═══════════════════════════════════════════════════════════════════
# 打字动画指示器
# ═══════════════════════════════════════════════════════════════════

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
                border: 1px solid {T.BORDER2};
                border-radius: 18px;
                border-top-left-radius: 4px;
            }}
        """)
        bubble.setFixedSize(76, 40)

        b_lay = QHBoxLayout(bubble)
        b_lay.setContentsMargins(16, 10, 16, 10)
        b_lay.setSpacing(6)

        self._dots = []
        for _ in range(3):
            dot = QLabel("●")
            dot.setStyleSheet(f"color: {T.NEON}33; font-size: 9px; background: transparent;")
            b_lay.addWidget(dot)
            self._dots.append(dot)

        outer.addWidget(bubble)
        outer.addStretch()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._step = 0
        self._timer.start(380)

    def _animate(self):
        for i, dot in enumerate(self._dots):
            alpha = "FF" if i == self._step % 3 else "33"
            dot.setStyleSheet(f"color: {T.NEON}{alpha}; font-size: 9px; background: transparent;")
        self._step += 1

    def stop(self):
        self._timer.stop()


# ═══════════════════════════════════════════════════════════════════
# 通用聊天气泡（修复表格渲染）
# ═══════════════════════════════════════════════════════════════════

class ChatBubble(QFrame):
    _ROLE_CFG = {
        "user": {
            "label":       "👤  你",
            "label_color": T.YELLOW,
            "bg":          T.USER_BUBBLE,
            "border":      f"{T.NEON}33",
            "radius":      "18px 18px 4px 18px",
            "align":       "right",
        },
        "assistant": {
            "label":       "🤖  AI 助手",
            "label_color": T.NEON,
            "bg":          T.AI_BUBBLE,
            "border":      T.BORDER2,
            "radius":      "4px 18px 18px 18px",
            "align":       "left",
        },
        "ai": {
            "label":       "🤖  AI 面试官",
            "label_color": T.NEON,
            "bg":          T.AI_BUBBLE,
            "border":      T.BORDER2,
            "radius":      "4px 18px 18px 18px",
            "align":       "left",
        },
        "system": {
            "label":       "",
            "label_color": T.TEXT_DIM,
            "bg":          "transparent",
            "border":      "transparent",
            "radius":      "8px",
            "align":       "center",
        },
    }

    def __init__(self, role: str, content: str = "", max_width: int = 580, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self._role    = role
        self._content = content
        self._max_width = max_width

        cfg   = self._ROLE_CFG.get(role, self._ROLE_CFG["assistant"])
        outer = QHBoxLayout(self)
        outer.setContentsMargins(6, 3, 6, 3)
        outer.setSpacing(0)

        # system 消息居中
        if role == "system":
            lbl = QLabel(content)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"""
                color: {T.TEXT_DIM}; font-size: 11px;
                padding: 4px 12px; background: transparent;
                font-family: {T.FONT};
            """)
            outer.addWidget(lbl)
            return

        # 气泡框
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
            role_lbl.setStyleSheet(f"""
                font-size: 10px; color: {cfg['label_color']};
                font-weight: 700; letter-spacing: 1px;
                background: transparent; font-family: {T.FONT};
            """)
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

        # 布局对齐
        if cfg["align"] == "right":
            outer.addStretch(2)
            outer.addWidget(self.bubble, stretch=8)
        else:
            outer.addWidget(self.bubble, stretch=8)
            outer.addStretch(2)

        if content:
            self._set_content(content)

    def _set_content(self, text: str):
        self._content = text
        self._render()
        self._adjust_height()

    def _render(self):
        """统一渲染：全部走自定义 HTML 转换器，确保表格正确显示。"""
        html = _md_to_html(self._content)
        self.text_view.setHtml(html)

    def append_chunk(self, chunk: str):
        """流式追加文字片段。"""
        self._content += chunk
        self._render()
        cursor = self.text_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.text_view.setTextCursor(cursor)
        self._adjust_height()

    def _adjust_height(self):
        w = min(self.text_view.width() or self._max_width - 28, self._max_width - 28)
        self.text_view.document().setTextWidth(w)
        h = int(self.text_view.document().size().height()) + 24
        self.text_view.setFixedHeight(max(36, h))


# ═══════════════════════════════════════════════════════════════════
# 评分卡片气泡（InterviewPanel 专用）
# ═══════════════════════════════════════════════════════════════════

class ScoreCardBubble(QFrame):
    def __init__(self, eval_result, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)

        outer = QHBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        card = QFrame()
        card.setObjectName("score_card")
        card.setStyleSheet(f"""
            QFrame#score_card {{
                background: {T.SURFACE2};
                border: 1px solid {T.NEON}22;
                border-left: 3px solid {T.NEON};
                border-radius: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(T.NEON).darker(300))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(16, 14, 16, 14)
        card_lay.setSpacing(10)

        title = QLabel("📊  本题评估报告")
        title.setStyleSheet(f"""
            font-weight: 700; font-size: 13px; color: {T.NEON};
            font-family: {T.FONT}; background: transparent;
        """)
        card_lay.addWidget(title)

        scores_row = QHBoxLayout()
        scores_row.setSpacing(0)
        score_items = [
            ("技术", eval_result.tech_score,    T.NEON),
            ("逻辑", eval_result.logic_score,   T.PURPLE),
            ("深度", eval_result.depth_score,   T.YELLOW),
            ("表达", eval_result.clarity_score, T.GREEN),
        ]
        for label, score, color in score_items:
            item_frame = QFrame()
            item_frame.setStyleSheet("background: transparent;")
            item_lay = QVBoxLayout(item_frame)
            item_lay.setContentsMargins(10, 6, 10, 6)
            item_lay.setSpacing(2)
            item_lay.setAlignment(Qt.AlignCenter)

            val_lbl = QLabel(str(score))
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setStyleSheet(f"""
                font-size: 22px; font-weight: 900; color: {color};
                font-family: {T.FONT_MONO}; background: transparent;
            """)
            name_lbl = QLabel(label)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(f"font-size: 10px; color: {T.TEXT_DIM}; background: transparent;")

            item_lay.addWidget(val_lbl)
            item_lay.addWidget(name_lbl)
            scores_row.addWidget(item_frame)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {T.BORDER2}; background: {T.BORDER2};")
        sep.setFixedWidth(1)
        scores_row.addWidget(sep)

        overall_frame = QFrame()
        overall_frame.setStyleSheet(f"background: {T.GREEN}11; border-radius: 8px;")
        overall_lay = QVBoxLayout(overall_frame)
        overall_lay.setContentsMargins(14, 8, 14, 8)
        overall_lay.setAlignment(Qt.AlignCenter)

        overall_val = QLabel(f"{eval_result.overall_score:.1f}")
        overall_val.setAlignment(Qt.AlignCenter)
        overall_val.setStyleSheet(f"""
            font-size: 26px; font-weight: 900; color: {T.GREEN};
            font-family: {T.FONT_MONO}; background: transparent;
        """)
        overall_name = QLabel("综合")
        overall_name.setAlignment(Qt.AlignCenter)
        overall_name.setStyleSheet(f"font-size: 10px; color: {T.GREEN}AA; background: transparent;")
        overall_lay.addWidget(overall_val)
        overall_lay.addWidget(overall_name)
        scores_row.addWidget(overall_frame)

        card_lay.addLayout(scores_row)

        if eval_result.suggestion:
            tip = QLabel(f"💡  {eval_result.suggestion}")
            tip.setWordWrap(True)
            tip.setStyleSheet(f"""
                font-size: 12px; color: {T.TEXT_DIM};
                background: {T.SURFACE3};
                border-radius: 6px;
                padding: 8px 10px;
                font-family: {T.FONT};
            """)
            card_lay.addWidget(tip)

        outer.addWidget(card, stretch=9)
        outer.addStretch(1)


# ═══════════════════════════════════════════════════════════════════
# 统计徽章
# ═══════════════════════════════════════════════════════════════════

class StatBadge(QFrame):
    def __init__(self, icon: str, value: str, label: str, color: str, parent=None):
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

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px; background: transparent;")
        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"""
            font-size: 20px; font-weight: 900; color: {color};
            font-family: {T.FONT_MONO}; background: transparent;
        """)
        top.addWidget(icon_lbl)
        top.addStretch()
        top.addWidget(val_lbl)

        name_lbl = QLabel(label)
        name_lbl.setStyleSheet(f"font-size: 10px; color: {T.TEXT_DIM}; font-weight: 600; background: transparent;")

        lay.addLayout(top)
        lay.addWidget(name_lbl)


# ═══════════════════════════════════════════════════════════════════
# 按钮工厂
# ═══════════════════════════════════════════════════════════════════

class ButtonFactory:
    @staticmethod
    def primary(text: str, color: str = T.NEON, height: int = 38) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color}22; color: {color};
                border: 1px solid {color}66;
                border-radius: {height // 2}px;
                font-size: 13px; font-weight: 700;
                padding: 0 18px; font-family: {T.FONT};
            }}
            QPushButton:hover {{ background: {color}44; border-color: {color}; }}
            QPushButton:pressed {{ background: {color}66; }}
            QPushButton:disabled {{ background: {T.BORDER}; color: {T.TEXT_MUTE}; border-color: {T.BORDER}; }}
        """)
        return btn

    @staticmethod
    def solid(text: str, color: str = T.NEON, height: int = 38) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: #0A0A14;
                border: none; border-radius: {height // 2}px;
                font-size: 13px; font-weight: 800;
                padding: 0 18px; font-family: {T.FONT};
            }}
            QPushButton:hover {{ background: {color}CC; }}
            QPushButton:pressed {{ background: {color}AA; }}
            QPushButton:disabled {{ background: {T.BORDER}; color: {T.TEXT_MUTE}; }}
        """)
        return btn

    @staticmethod
    def ghost(text: str, height: int = 30) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {T.TEXT_DIM};
                border: 1px solid {T.BORDER2}; border-radius: 6px;
                font-size: 12px; padding: 0 12px; font-family: {T.FONT};
            }}
            QPushButton:hover {{ color: {T.ACCENT}; border-color: {T.ACCENT}; }}
        """)
        return btn

    @staticmethod
    def tag(text: str, color: str, height: int = 32) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.SURFACE}; color: {T.TEXT_DIM};
                border: 1px solid {T.BORDER2};
                border-radius: {height // 2}px;
                font-size: 11px; font-weight: 600;
                padding: 0 14px; font-family: {T.FONT};
            }}
            QPushButton:hover {{
                color: {color}; border-color: {color}55; background: {color}11;
            }}
        """)
        return btn


# ═══════════════════════════════════════════════════════════════════
# 全局 QSS
# ═══════════════════════════════════════════════════════════════════

GLOBAL_QSS = f"""
    QWidget {{
        background: {T.BG};
        color: {T.TEXT};
        font-family: {T.FONT};
    }}
    QScrollBar:vertical {{
        width: 5px; background: transparent; margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {T.BORDER2}; border-radius: 2px; min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {T.NEON}66; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{ height: 5px; background: transparent; }}
    QScrollBar::handle:horizontal {{ background: {T.BORDER2}; border-radius: 2px; }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
    QComboBox QAbstractItemView {{
        background: {T.SURFACE2}; color: {T.TEXT};
        selection-background-color: {T.NEON}22;
        border: 1px solid {T.BORDER2}; outline: none;
    }}
"""

def header_qss(border_color: str = T.BORDER) -> str:
    return f"""
        QFrame {{
            background: {T.SURFACE};
            border-bottom: 1px solid {border_color};
        }}
    """

def input_qss(focus_color: str = T.NEON) -> str:
    return f"""
        QLineEdit, QTextEdit {{
            background: {T.BG}; border: 1px solid {T.BORDER2};
            border-radius: 10px; padding: 8px 14px;
            color: {T.TEXT}; font-size: 14px; font-family: {T.FONT};
        }}
        QLineEdit:focus, QTextEdit:focus {{ border-color: {focus_color}; }}
        QLineEdit:disabled, QTextEdit:disabled {{ background: {T.SURFACE}; color: {T.TEXT_MUTE}; }}
    """

def combo_qss(focus_color: str = T.NEON) -> str:
    return f"""
        QComboBox {{
            background: {T.BG}; border: 1px solid {T.BORDER2};
            border-radius: 8px; padding: 6px 12px;
            color: {T.TEXT}; font-size: 13px; font-family: {T.FONT};
        }}
        QComboBox:focus {{ border-color: {focus_color}; }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {T.TEXT_DIM};
            margin: 4px;
        }}
    """