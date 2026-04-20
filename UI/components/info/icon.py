"""
UI/components/info/icons.py ── 全局图标注册表
用法：
    from UI.theme.icons import Icons, IconSize
    icon = Icons.get("mic")
    icon = Icons.get("mic", size=IconSize.LG)
"""

import os
from dataclasses import dataclass
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtCore import QSize, Qt

# ── 图标根目录 ──────────────────────────────────────────────────────
_ROOT = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "icon")
)


@dataclass(frozen=True)
class IconSize:
    """预定义图标尺寸，全局统一"""

    XS = QSize(16, 16)
    SM = QSize(20, 20)
    MD = QSize(24, 24)  # 默认
    LG = QSize(32, 32)
    XL = QSize(48, 48)


class Icons:
    """
    图标注册中心。

    注册方式：
        1. 在 _REGISTRY 字典中手动维护（推荐，可 ctrl+F 搜）
        2. 或直接 Icons.get("文件名") 也会自动查找 icon/ 目录
    """

    # ══════════════════════════════════════════════════════════════════
    # 注册表：逻辑名 → 文件名（不含后缀）
    # 命名规范：小写下划线，与业务含义绑定，而非与文件名耦合
    # ══════════════════════════════════════════════════════════════════
    _REGISTRY: dict[str, str] = {
        # ── ASR / 语音 ─────────────────────────────────
        "mic": "mic",
        "mic_off": "mic_off",
        "play": "play_arrow",
        "play_circle": "play_circle",
        "stop": "stop",
        "stop_circle": "stop_circle",
        "record_voice": "record_voice_over",
        "play_arrow": "play_arrow",
        # ── 通用操作 ────────────────────────────────────
        "send": "send",
        "cancel": "cancel",
        "delete": "delete",
        "refresh": "refresh",
        "search": "search",
        "settings": "settings",
        "help": "help",
        "visibility": "visibility",
        "visibility_off": "visibility_off",
        "upload": "upload_file",
        "upload_file": "upload_file",
        "download": "arrow_downward",
        "arrow_downward": "arrow_downward",
        "sort": "sort",
        "filter": "tune",
        # ── 导航 ───────────────────────────────────────
        "chevron_left": "chevron_left",
        "chevron_right": "chevron_right",
        "first_page": "first_page",
        "last_page": "last_page",
        "find_replace": "find_replace",
        # ── 数据 / 统计 ────────────────────────────────
        "analytics": "analytics",
        "bar_chart": "bar_chart",
        "trending_up": "trending_up",
        "inventory": "inventory_2",
        "inventory_2": "inventory_2",
        "looks_3": "looks_3",
        "looks_one": "looks_one",
        "looks_two": "looks_two",
        # ── 状态 ───────────────────────────────────────
        "loading": "hourglass_top",
        "hourglass_top": "hourglass_top",
        "success": "task_alt",
        "task_alt": "task_alt",
        "error": "cancel",
        "history": "history",
        "sync": "sync",
        # ── 面板 ───────────────────────────────────────
        "dashboard": "dashboard",
        "article": "article",
        "category": "category",
        "group": "group",
        "library": "library",
        "library_books": "library",
        "list": "list_alt",
        "radar": "radar",
        "query_stats": "query_stats",
        "travel": "travel_explore",
        "travel_explore": "travel_explore",
        "work": "work",
        "cleaning": "cleaning_services",
        "cleaning_services": "cleaning_services",
        "smart_toy": "smart_toy",
        "menu_book": "menu_book",
        "person": "person",
        "subtitles": "subtitles",
        "shuffle": "shuffle",
        # ── AI 助手 ────────────────────────────────────
        "smart_toy": "smart_toy",
        "assessment": "bar_chart",
    }

    # ══════════════════════════════════════════════════════════════════
    # 缓存：避免重复加载同一图标
    # ══════════════════════════════════════════════════════════════════
    _cache: dict[str, QIcon] = {}

    @classmethod
    def get(
        cls,
        name: str,
        size: QSize = IconSize.MD,
    ) -> QIcon:
        """
        获取图标。优先从注册表查文件名，找不到则直接用 name 作为文件名。

        Args:
            name: 逻辑名 (如 "mic") 或文件名 (如 "some_icon")
            size: 图标尺寸，默认 24×24

        Returns:
            QIcon 对象。文件不存在则返回空 QIcon。
        """
        cache_key = f"{name}@{size.width()}x{size.height()}"
        if cache_key in cls._cache:
            return cls._cache[cache_key]

        # 查注册表 → 兜底直接用 name
        filename = cls._REGISTRY.get(name, name)
        filepath = os.path.join(_ROOT, f"{filename}.png")
        icon = QIcon()
        if os.path.isfile(filepath):
            pixmap = QPixmap(filepath).scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon = QIcon(pixmap)

        cls._cache[cache_key] = icon
        return icon

    @classmethod
    def pixmap(
        cls,
        name: str,
        size: QSize = IconSize.MD,
    ) -> QPixmap:
        """直接拿 QPixmap（某些场景比 QIcon 更方便）"""
        icon = cls.get(name, size)
        return icon.pixmap(size)

    @classmethod
    def colored_pixmap(
        cls,
        name: str,
        color: str,
        size: QSize = IconSize.MD,
    ) -> QPixmap:
        """获取着色后的 QPixmap"""
        from PySide6.QtGui import QColor, QPainter
        from PySide6.QtCore import Qt

        original = cls.pixmap(name, size)
        if original.isNull():
            return QPixmap(size)

        result = QPixmap(size)
        result.fill(Qt.transparent)

        painter = QPainter(result)
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制原图标
        painter.drawPixmap(0, 0, original)

        # 着色：用 SourceIn 模式 + fillRect（最简洁）
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(0, 0, size.width(), size.height(), QColor(color))

        painter.end()
        return result

    @classmethod
    def clear_cache(cls) -> None:
        """主题切换或热重载时调用"""
        cls._cache.clear()

    @classmethod
    def list_registered(cls) -> list[str]:
        """返回所有已注册的逻辑名（方便调试/文档生成）"""
        return sorted(cls._REGISTRY.keys())
