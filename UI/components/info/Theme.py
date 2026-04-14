# UI/components/info/Theme.py
"""
全局色彩与字体常量 - Neumorphism 浅色复古主题。
所有组件统一从此处导入，避免魔法字符串散落各处。

设计方向：Soft UI、奶油纸感、复古低饱和、实体按压感
"""


class Theme:
    # ── 基础背景层级 (暖米色复古基底) ─────────────────────────────────────
    BASE = "#EDE4D7"  # 全局中间背景，浅暖复古主基底
    SURFACE = "#F5EEE4"  # 凸起组件高光面 (Surface Raise)
    SURFACE_PRESSED = "#DFD2C1"  # 按下/内凹状态面 (Surface Press)

    # ── 新拟物阴影色 (用于 QGraphicsDropShadowEffect) ─────────────────────
    SHADOW_LIGHT = "#FFF9EF"  # 顶左亮部阴影
    SHADOW_DARK = "#C3B39E"  # 底右暗部阴影

    # ── 文字颜色 (复古棕灰系) ───────────────────────────────────────────
    TEXT = "#4E4338"  # 主文本，高对比度
    TEXT_DIM = "#7E6F61"  # 次级文本
    TEXT_MUTE = "#9B8E81"  # 禁用/辅助文本

    # ── 边框颜色 (柔和分层) ─────────────────────────────────────────────
    BORDER = "#D8CCBC"  # 轻边界，辅助分层
    BORDER_FOCUS = "#C7977E"  # 聚焦态边框（强调色低饱和版）

    # ── 气泡背景 (对话区专用) ───────────────────────────────────────────
    USER_BUBBLE = "#E8DFD3"  # 用户消息气泡，略深于基底
    AI_BUBBLE = "#F5EEE4"  # AI 消息气泡，与 Surface 一致

    # ── 强调色 (关键按钮渐变) ───────────────────────────────────────────
    ACCENT_START = "#CFA187"  # 渐变起始：暖陶土色
    ACCENT_END = "#B77B63"  # 渐变结束：深陶土色
    ACCENT_SOLID = "#BE886F"  # 纯色降级备选

    # 强调按钮文本色（确保对比度）
    ACCENT_TEXT = "#FFF8F2"

    # ── 语义别名 (映射到新配色体系) ─────────────────────────────────────
    SUCCESS = "#8FA887"  # 低饱和复古绿，用于成功状态
    ERROR = ACCENT_SOLID  # 使用强调色作为错误提示
    WARNING = "#B79A7B"  # 低饱和暖黄，用于警告
    INFO = "#A89B8E"  # 中性灰棕，用于信息提示

    # ── 交互状态色 (按钮/输入框) ─────────────────────────────────────────
    HOVER_TINT = "#FBF4EA"  # 悬停时表面提亮
    PRESSED_TINT = "#DCCFBE"  # 按下时表面收敛
    DISABLED_BG = "#EEE6DB"  # 禁用态背景
    DISABLED_TEXT = "#9B8E81"  # 禁用态文字

    # ── 字体栈 (兼顾复古质感与可读性) ───────────────────────────────────
    FONT = '-apple-system, "PingFang SC", "Microsoft YaHei", "Noto Serif SC", serif'
    FONT_MONO = '"JetBrains Mono", "Cascadia Code", "Fira Code", monospace'

    # ── 新拟物阴影参数 (供 QGraphicsDropShadowEffect 使用) ───────────────
    # 凸起态：双阴影叠加模拟实体感
    SHADOW_RAISED = {
        "light": {"color": SHADOW_LIGHT, "offset": (-4, -4), "blur": 14},
        "dark": {"color": SHADOW_DARK, "offset": (4, 4), "blur": 14},
    }
    # 按下态：内凹感，阴影权重反转 + blur 减小
    SHADOW_PRESSED = {
        "light": {"color": SHADOW_DARK, "offset": (-2, -2), "blur": 8},
        "dark": {"color": SHADOW_LIGHT, "offset": (2, 2), "blur": 8},
    }

    # ── 圆角规范 (全局统一) ─────────────────────────────────────────────
    RADIUS_SM = 12  # 输入框、小按钮
    RADIUS_MD = 14  # 通用按钮
    RADIUS_LG = 16  # 卡片、主按钮、气泡

    # ── 动效参数 (动画模块引用) ─────────────────────────────────────────
    ANIM_FAST = 180  # 微交互：180ms
    ANIM_NORMAL = 300  # 常规过渡：300ms
    ANIM_SLOW = 420  # 卡片浮现：380-420ms
    ANIM_PULSE = 1800  # 呼吸动效循环：1800ms
    ANIM_STAGGER = 40  # 列表消息错峰延迟：40ms


# 便捷别名，可直接 `from UI.components.info.Theme import T`
T = Theme