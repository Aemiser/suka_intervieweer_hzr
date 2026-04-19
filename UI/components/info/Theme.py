"""
全局色彩与字体常量。
所有组件统一从此处导入，避免魔法字符串散落各处。
当前方案：莫兰迪色系 × 新拟态设计（低饱和·柔和·立体感）
"""


class Theme:
    # ── 背景层级 · 莫兰迪灰调 ────────────────────────────────────────────────
    BG = "#F5F4F2"  # 米白灰，温暖柔和的页面基底
    # BG 的阴影（用于页面整体新拟态容器）
    BG_LIGHT = "#FFFFFF"  # 亮阴影：更白，模拟左上光源
    BG_DARK = "#D8D6D4"  # 暗阴影：更深灰，模拟右下投影

    SURFACE = "#FFFFFF"  # 纯白卡片/面板，保持干净层次
    # SURFACE 的阴影（用于凸起卡片/按钮）
    SURFACE_LIGHT = "#FFFFFF"  # 亮阴影：纯白（靠透明度控制层次）
    SURFACE_DARK = "#E0DFDD"  # 暗阴影：柔和灰，避免纯黑生硬

    SURFACE2 = "#DBE9E6"  # 浅灰褐/灰蓝调，悬浮态/次级区块
    # SURFACE2 的阴影（用于次级面板/输入框）
    SURFACE2_LIGHT = "#EAF5F3"  # 亮阴影：更浅的灰蓝调
    SURFACE2_DARK = "#B8C9C5"  # 暗阴影：更深的灰蓝，保持色相一致

    SURFACE3 = "#CCD9D4"  # 中灰褐，按压态/分割区块
    # SURFACE3 的阴影（用于凹陷区域/禁用态）
    SURFACE3_LIGHT = "#DAE5E0"  # 亮阴影：提亮版本
    SURFACE3_DARK = "#A8B8B2"  # 暗阴影：加深版本，增强凹陷感

    # ── 强调色 · 低饱和莫兰迪彩 ──────────────────────────────────────────────
    ACCENT = "#9A8F9B"  # 莫兰迪紫灰，核心主色（按钮/高亮）
    NEON = "#8A9FA6"  # 莫兰迪灰蓝，链接/次要强调
    GREEN = "#8A9A8B"  # 莫兰迪灰绿，成功状态（柔和不刺眼）
    YELLOW = "#B5A67D"  # 莫兰迪土黄，警告状态（温暖不焦躁）
    PURPLE = "#B8A9C9"  # 莫兰迪浅紫灰，标签/装饰/渐变过渡

    # ── 文字 · 灰褐系层级 ────────────────────────────────────────────────────
    TEXT = "#4A4642"  # 深灰褐，主标题与正文（非纯黑，更温润）
    TEXT_DIM = "#7A7670"  # 中灰褐，副标题/说明文字
    TEXT_MUTE = "#A8A49E"  # 浅灰褐，禁用态/占位符/时间戳

    # ── 边框 · 柔和分割 ──────────────────────────────────────────────────────
    BORDER = "#E2DFDA"  # 基础分割线，低对比不抢戏
    BORDER2 = "#C9C6C0"  # 强调分割线/输入框聚焦态边缘

    # ── 气泡背景 · 对话场景 ─────────────────────────────────────────────────
    USER_BUBBLE = "#FFFFFF"  # 用户气泡：白色
    AI_BUBBLE = "#FFFFFF"  # AI气泡：白色

    # ── 语义别名 · 保持接口兼容 ─────────────────────────────────────────────
    SUCCESS = GREEN  # 灰绿 → 成功
    ERROR = "#B5838D"  # 莫兰迪红灰 → 错误/异常（柔和警示）
    WARNING = YELLOW  # 土黄 → 警告
    INFO = NEON  # 灰蓝 → 信息提示

    # ── 历史面板三卡片配色 ───────────────────────────────────────────
    # 综合得分趋势
    SCORE_TREND_BG = "#E8F0EC"
    SCORE_TREND_MAIN = "#7DB89E"
    SCORE_TREND_TITLE = "#5A967A"
    # 最近能力维度
    ABILITY_BG = "#EAE8F0"
    ABILITY_MAIN = "#A898C0"
    ABILITY_TITLE = "#7B6B8F"
    # 面试表现回顾
    REVIEW_BG = "#F5F0E8"
    REVIEW_MAIN = "#C9A96E"
    REVIEW_TITLE = "#8B7347"

    # ── 字体栈 · 跨平台优雅降级 ─────────────────────────────────────────────
    FONT = '-apple-system, "PingFang SC", "Microsoft YaHei", sans-serif'
    FONT_MONO = '"JetBrains Mono", "Cascadia Code", "Fira Code", monospace'

    # ── 新拟态阴影工具 · 快速生成 box-shadow 字符串 ─────────────────────────
    @staticmethod
    def neu_raise(
        base_light: str, base_dark: str, blur: int = 12, offset: int = 6
    ) -> str:
        """
        生成"凸起"效果的新拟态阴影（用于按钮/卡片）

        Args:
            base_light: 亮阴影颜色（如 T.SURFACE_LIGHT）
            base_dark: 暗阴影颜色（如 T.SURFACE_DARK）
            blur: 模糊半径（默认 12）
            offset: 偏移量（默认 6）

        Returns:
            CSS box-shadow 字符串
        """
        return (
            f"{-offset}px {-offset}px {blur}px {base_light}, "
            f"{offset}px {offset}px {blur}px {base_dark}"
        )

    @staticmethod
    def neu_inset(
        base_light: str, base_dark: str, blur: int = 7, offset: int = 3
    ) -> str:
        """
        生成"凹陷"效果的新拟态阴影（用于输入框/按下态）

        Args:
            base_light: 亮阴影颜色
            base_dark: 暗阴影颜色
            blur: 模糊半径（默认 7，凹陷通常更锐利）
            offset: 偏移量（默认 3）

        Returns:
            CSS box-shadow 字符串（带 inset）
        """
        return (
            f"inset {-offset}px {-offset}px {blur}px {base_light}, "
            f"inset {offset}px {offset}px {blur}px {base_dark}"
        )


# 便捷别名，可直接 `from UI.components.info.Theme import T`
T = Theme
