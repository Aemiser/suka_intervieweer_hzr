"""
统一组件库入口。

提供：
  - 所有原子组件的直接导入
  - 全局 QSS 字符串辅助函数 (基于 Theme.py 色彩系统)
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
    # QSS helpers
    "GLOBAL_QSS",
    "header_qss",
    "input_qss",
    "combo_qss",
    "primary_btn_qss",
    "secondary_btn_qss",
    "ghost_btn_qss",
    "user_bubble_qss",
    "ai_bubble_qss",
]

# ══════════════════════════════════════════════════════════════════════════════
# 字体处理：PyQt QSS 对 font-family 支持有限，提取基础字体作为兜底
# ══════════════════════════════════════════════════════════════════════════════
# 移除单引号，保留英文字体名作为 QSS 兜底
_FONT_FALLBACK = "Microsoft YaHei, PingFang SC, sans-serif"

# ══════════════════════════════════════════════════════════════════════════════
# 全局基础 QSS (滚动条 + 全局文字)
# ══════════════════════════════════════════════════════════════════════════════

GLOBAL_QSS = f"""
    /* ── 全局基础 ───────────────────────────────────────── */
    QWidget {{
        color: {T.TEXT};
        font-family: {_FONT_FALLBACK};
        outline: none;
    }}

    /* ── 滚动条 (细滚动条设计) ───────────────────────────── */
    QScrollBar:vertical {{
        width: 6px; 
        background: transparent; 
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {T.BORDER2}; 
        border-radius: 3px; 
        min-height: 40px;
    }}
    QScrollBar::handle:vertical:hover {{ 
        background: {T.ACCENT}66;  /* 66 = ~40% 透明度 */
    }}
    QScrollBar::handle:vertical:pressed {{
        background: {T.ACCENT};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

    QScrollBar:horizontal {{ 
        height: 6px; 
        background: transparent; 
    }}
    QScrollBar::handle:horizontal {{ 
        background: {T.BORDER2}; 
        border-radius: 3px; 
        min-width: 40px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    /* ── 下拉列表弹窗 ───────────────────────────────────── */
    QComboBox QAbstractItemView {{
        background: {T.SURFACE}; 
        color: {T.TEXT};
        selection-background-color: {T.ACCENT}22;  /* 浅紫选中态 */
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
        background: {T.ACCENT}1A;  /* 10% 透明度 */
    }}
"""


# ══════════════════════════════════════════════════════════════════════════════
# 组件级 QSS 生成函数
# ══════════════════════════════════════════════════════════════════════════════

def header_qss(border_color: str = T.BORDER) -> str:
    """顶部/分割栏样式"""
    return f"""
        QFrame[role="header"], .header-frame {{
            background: {T.SURFACE};
            border-bottom: 1px solid {border_color};
        }}
    """


def input_qss(focus_color: str = T.ACCENT) -> str:
    """
    输入框样式 (QLineEdit / QTextEdit)
    - 默认: SURFACE2 背景 + BORDER 边框
    - 聚焦: 白色背景 + 强调色边框 + 轻微光晕
    """
    return f"""
        QLineEdit, QTextEdit {{
            background: {T.SURFACE2}; 
            border: 1px solid {T.BORDER};
            border-radius: 8px; 
            padding: 10px 14px;
            color: {T.TEXT}; 
            font-size: 14px;
            font-family: {_FONT_FALLBACK};
            selection-background-color: {T.ACCENT}44;
        }}
        QLineEdit:focus, QTextEdit:focus {{
            background: {T.SURFACE};
            border-color: {focus_color};
            border-width: 2px;
            padding: 9px 13px;  /* 补偿 border 变粗 */
        }}
        QLineEdit:disabled, QTextEdit:disabled {{
            background: {T.SURFACE}; 
            color: {T.TEXT_MUTE};
            border-color: {T.BORDER};
        }}
        /* 占位符颜色 */
        QLineEdit::placeholder, QTextEdit::placeholder {{
            color: {T.TEXT_MUTE};
        }}
    """


def combo_qss(focus_color: str = T.ACCENT) -> str:
    """下拉选择框样式"""
    return f"""
        QComboBox {{
            background: {T.SURFACE2}; 
            border: 1px solid {T.BORDER};
            border-radius: 8px; 
            padding: 8px 12px;
            color: {T.TEXT}; 
            font-size: 13px;
        }}
        QComboBox:focus {{
            background: {T.SURFACE};
            border-color: {focus_color};
            border-width: 2px;
            padding: 7px 11px;
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
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: {T.TEXT};
        }}
    """


def primary_btn_qss(hover_darken: str = "#6D28D9") -> str:
    """
    主按钮样式 (核心紫)
    - 用于: 开始面试 / 发送消息 / 确认操作
    """
    return f"""
        QPushButton[role="primary"], .btn-primary {{
            background: {T.ACCENT};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 24px;
            font-weight: 600;
            font-size: 14px;
        }}
        QPushButton[role="primary"]:hover {{
            background: {hover_darken};
        }}
        QPushButton[role="primary"]:pressed {{
            background: {T.ACCENT};
            padding-top: 11px;  /* 按压反馈 */
        }}
        QPushButton[role="primary"]:disabled {{
            background: {T.BORDER2};
            color: {T.TEXT_MUTE};
        }}
    """


def secondary_btn_qss() -> str:
    """
    次级按钮样式 (浅灰底)
    - 用于: 上传简历 / 取消 / 次要操作
    """
    return f"""
        QPushButton[role="secondary"], .btn-secondary {{
            background: {T.SURFACE2};
            color: {T.TEXT_DIM};
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 9px 24px;  /* 补偿 border */
            font-weight: 500;
            font-size: 14px;
        }}
        QPushButton[role="secondary"]:hover {{
            background: {T.SURFACE3};
            color: {T.TEXT};
            border-color: {T.BORDER2};
        }}
        QPushButton[role="secondary"]:pressed {{
            background: {T.BORDER};
        }}
        QPushButton[role="secondary"]:disabled {{
            color: {T.TEXT_MUTE};
            background: {T.SURFACE};
        }}
    """


def ghost_btn_qss(danger_hover: str = "#EF4444") -> str:
    """
    幽灵按钮样式 (透明底)
    - 用于: 关闭 / 结束面试 / 删除 (悬停变红)
    """
    return f"""
        QPushButton[role="ghost"], .btn-ghost {{
            background: transparent;
            color: {T.TEXT_MUTE};
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-size: 13px;
        }}
        QPushButton[role="ghost"]:hover {{
            color: {danger_hover};
            background: {T.SURFACE2};
        }}
        QPushButton[role="ghost"]:pressed {{
            background: {T.SURFACE3};
        }}
    """


def user_bubble_qss() -> str:
    """用户聊天气泡 (紫色背景 + 白字)"""
    return f"""
        QFrame[role="user-bubble"], .bubble-user {{
            background: {T.USER_BUBBLE};
            border-radius: 12px;
            border-bottom-right-radius: 2px;  /* 小尾巴效果 */
            padding: 12px 16px;
            color: white;
            font-size: 14px;
            line-height: 1.5;
        }}
        QFrame[role="user-bubble"] QLabel {{
            color: white;
            background: transparent;
        }}
    """


def ai_bubble_qss() -> str:
    """AI 聊天气泡 (白色背景 + 浅灰边框)"""
    return f"""
        QFrame[role="ai-bubble"], .bubble-ai {{
            background: {T.AI_BUBBLE};
            border: 1px solid {T.BORDER};
            border-radius: 12px;
            border-bottom-left-radius: 2px;  /* 小尾巴效果 */
            padding: 12px 16px;
            color: {T.TEXT};
            font-size: 14px;
            line-height: 1.5;
        }}
        QFrame[role="ai-bubble"] QLabel {{
            color: {T.TEXT};
            background: transparent;
        }}
    """


# ══════════════════════════════════════════════════════════════════════════════
# 便捷组合：一键应用全套样式
# ══════════════════════════════════════════════════════════════════════════════

def apply_theme(widget):
    """
    便捷函数：为 QWidget 应用全套主题样式
    用法: apply_theme(self)  # 在 MainWindow.__init__ 中调用
    """
    full_qss = GLOBAL_QSS + "\n" + "\n".join([
        header_qss(),
        input_qss(),
        combo_qss(),
        primary_btn_qss(),
        secondary_btn_qss(),
        ghost_btn_qss(),
        user_bubble_qss(),
        ai_bubble_qss(),
    ])
    widget.setStyleSheet(full_qss)