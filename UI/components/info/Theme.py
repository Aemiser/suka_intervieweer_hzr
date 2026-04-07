# UI/components/info/Theme.py
"""
全局色彩与字体常量。
所有组件统一从此处导入，避免魔法字符串散落各处。
"""


class Theme:
    # ── 背景层级 ────────────────────────────────────────────────────────────
    BG       = "#0A0A14"
    SURFACE  = "#12121E"
    SURFACE2 = "#1A1A2E"
    SURFACE3 = "#0F1628"

    # ── 强调色 ──────────────────────────────────────────────────────────────
    ACCENT = "#E94560"
    NEON   = "#00D4FF"
    GREEN  = "#00FF9D"
    YELLOW = "#FFD166"
    PURPLE = "#B388FF"

    # ── 文字 ────────────────────────────────────────────────────────────────
    TEXT      = "#E8E8F5"
    TEXT_DIM  = "#7070A0"
    TEXT_MUTE = "#404060"

    # ── 边框 ────────────────────────────────────────────────────────────────
    BORDER  = "#1E1E3A"
    BORDER2 = "#2A2A50"

    # ── 气泡背景 ────────────────────────────────────────────────────────────
    USER_BUBBLE = "#0F2A4A"
    AI_BUBBLE   = "#12121E"

    # ── 语义别名 ────────────────────────────────────────────────────────────
    SUCCESS = GREEN
    ERROR   = ACCENT
    WARNING = YELLOW
    INFO    = NEON

    # ── 字体栈 ──────────────────────────────────────────────────────────────
    FONT      = '-apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    FONT_MONO = '"JetBrains Mono", "Cascadia Code", "Fira Code", monospace'


# 便捷别名，可直接 `from UI.components.info.Theme import T`
T = Theme