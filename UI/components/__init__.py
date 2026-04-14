# UI/components/__init__.py
"""
统一组件库入口。

提供：
  - 所有原子组件的直接导入
  - 全局 QSS 字符串辅助函数
"""

from .info.Theme import Theme, T
from .info.StreamSignals import StreamSignals

from .ButtonFactory import ButtonFactory
from UI.components.Bubble.ChatBubble import ChatBubble
from UI.components.Bubble.ScoreCardBubble import ScoreCardBubble
from .StatBadge import StatBadge
from .TypingIndicator import TypingIndicator

from .chart import ChartCard, GrowthChart, RadarChart

from .util.md_to_html import md_to_html

__all__ = [
    # Theme
    "Theme", "T",
    # Signals
    "StreamSignals",
    # Widgets
    "ButtonFactory",
    "ChatBubble",
    "ScoreCardBubble",
    "StatBadge",
    "TypingIndicator",
    # Charts
    "ChartCard",
    "GrowthChart",
    "RadarChart",
    # Utils
    "md_to_html",
    # QSS helpers (see below)
    "GLOBAL_QSS",
    "header_qss",
    "input_qss",
    "combo_qss",
]

# ══════════════════════════════════════════════════════════════════════════════
# 全局 QSS 字符串工具函数（适配新拟物浅色主题）
# ══════════════════════════════════════════════════════════════════════════════

GLOBAL_QSS = f"""
    QWidget {{
        background: {T.BASE};
        color: {T.TEXT};
        font-family: {T.FONT};
    }}

    /* ── 滚动条：极简新拟物风格 ───────────────────────────────────────────── */
    QScrollBar:vertical {{
        width: 6px; 
        background: transparent; 
        margin: 0;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {T.BORDER}; 
        border-radius: 3px; 
        min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{ 
        background: {T.ACCENT_SOLID}; 
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ 
        height: 0; 
    }}

    QScrollBar:horizontal {{ 
        height: 6px; 
        background: transparent; 
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{ 
        background: {T.BORDER}; 
        border-radius: 3px; 
        min-width: 40px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ 
        width: 0; 
    }}

    /* ── 下拉列表：浅色新拟物 ─────────────────────────────────────────────── */
    QComboBox QAbstractItemView {{
        background: {T.SURFACE}; 
        color: {T.TEXT};
        selection-background-color: {T.ACCENT_START}33;  /* 33 = 20% 透明度 */
        selection-color: {T.TEXT};
        border: 1px solid {T.BORDER}; 
        outline: none;
        padding: 4px 0;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 28px;
        padding: 0 12px;
    }}
    QComboBox QAbstractItemView::item:selected {{
        background: {T.ACCENT_START}44;
    }}
"""


def header_qss(border_color: str = T.BORDER) -> str:
    """顶部/分区 Header 样式：浅色凸起感"""
    return f"""
        QFrame {{
            background: {T.SURFACE};
            border-bottom: 1px solid {border_color};
            border-radius: {T.RADIUS_MD}px;
        }}
    """


def input_qss(focus_color: str = T.BORDER_FOCUS) -> str:
    """输入框样式：内凹新拟物 + 聚焦强调"""
    return f"""
        QLineEdit, QTextEdit {{
            background: {T.BASE}; 
            border: 1px solid {T.BORDER};
            border-radius: {T.RADIUS_SM}px; 
            padding: 8px 14px;
            color: {T.TEXT}; 
            font-size: 14px; 
            font-family: {T.FONT};
        }}
        QLineEdit:focus, QTextEdit:focus {{ 
            border-color: {focus_color};
            background: {T.SURFACE};
        }}
        QLineEdit:disabled, QTextEdit:disabled {{
            background: {T.DISABLED_BG}; 
            color: {T.DISABLED_TEXT};
            border-color: {T.BORDER};
        }}
        /* Placeholder 颜色 */
        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {T.TEXT_DIM};
        }}
    """


def combo_qss(focus_color: str = T.BORDER_FOCUS) -> str:
    """下拉选择框样式：新拟物 + 自定义箭头"""
    return f"""
        QComboBox {{
            background: {T.BASE}; 
            border: 1px solid {T.BORDER};
            border-radius: {T.RADIUS_SM}px; 
            padding: 6px 12px;
            color: {T.TEXT}; 
            font-size: 13px; 
            font-family: {T.FONT};
            min-height: 32px;
        }}
        QComboBox:focus {{ 
            border-color: {focus_color};
            background: {T.SURFACE};
        }}
        QComboBox:disabled {{
            background: {T.DISABLED_BG};
            color: {T.DISABLED_TEXT};
        }}
        QComboBox::drop-down {{ 
            border: none; 
            width: 24px; 
            padding-right: 4px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {T.TEXT_DIM};
            margin-right: 2px;
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: {T.TEXT};
        }}
    """


def card_qss(radius: int = T.RADIUS_LG, border: bool = True) -> str:
    """通用卡片样式：新拟物凸起感（可选边框）"""
    border_line = f"border: 1px solid {T.BORDER};" if border else "border: none;"
    return f"""
        QFrame {{
            background: {T.SURFACE};
            {border_line}
            border-radius: {radius}px;
        }}
    """


def bubble_qss(role: str = "ai") -> str:
    """
    聊天气泡专用样式（按角色区分）
    role: "user" | "ai" | "assistant" | "system"
    """
    cfg = {
        "user": {
            "bg": T.USER_BUBBLE,
            "border": T.BORDER,
            "radius": "18px 18px 4px 18px",
            "align": "right",
        },
        "ai": {
            "bg": T.AI_BUBBLE,
            "border": T.BORDER,
            "radius": "4px 18px 18px 18px",
            "align": "left",
        },
        "assistant": {
            "bg": T.AI_BUBBLE,
            "border": T.BORDER,
            "radius": "4px 18px 18px 18px",
            "align": "left",
        },
        "system": {
            "bg": "transparent",
            "border": "none",
            "radius": "8px",
            "align": "center",
        },
    }.get(role, cfg["ai"])

    return f"""
        QFrame {{
            background: {cfg['bg']};
            border: 1px solid {cfg['border']};
            border-radius: {cfg['radius']};
        }}
    """