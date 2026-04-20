# UI/components/tab_widget.py
"""
等分宽度 Tab 组件
支持图标 + 文字，自适应窗口大小，主题样式统一
"""

from PySide6.QtWidgets import QTabWidget, QTabBar
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize, Qt

from UI.components.info import Theme as T
from UI.components.info.icon import Icons, IconSize


class EqualWidthTabBar(QTabBar):
    """自定义 TabBar：所有 tab 等分宽度，支持窗口自适应"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setExpanding(False)  # 关闭默认智能扩展
        self.setDocumentMode(True)  # 启用简洁文档模式

    def tabSizeHint(self, index: int) -> QSize:
        """重写：每个 tab 返回相同宽度 = 总宽度 / tab 数量"""
        original_size = super().tabSizeHint(index)
        tab_count = self.count()
        if tab_count <= 0:
            return original_size
        equal_width = self.width() // tab_count
        return QSize(equal_width, original_size.height())

    def resizeEvent(self, event):
        """窗口大小变化时，强制刷新 tab 布局"""
        super().resizeEvent(event)
        self.updateGeometry()  # 通知布局系统重新查询尺寸
        self.update()  # 触发重绘，视觉同步


class EqualWidthTabWidget(QTabWidget):
    """
    等分宽度 Tab 组件：支持图标 + 文字，自适应窗口大小

    Usage:
        tabs = EqualWidthTabWidget()
        tabs.add_tab(panel, "icon_name", "标签文本")
        tabs.add_tabs([...])  # 批量添加
    """

    def __init__(self, parent=None, icon_size: IconSize = IconSize.LG):  # 默认图标改为 LG
        super().__init__(parent)
        self._icon_size = icon_size
        # 存储每个 tab 的图标元数据，用于动态切换颜色
        # 格式: {index: (icon_name, icon_size)}
        self._tab_icon_meta: dict[int, tuple] = {}
        self._setup_ui()
        self.currentChanged.connect(self._on_tab_changed)

    def _on_tab_changed(self, current_index: int):
        """切换 tab 时，更新所有 tab 的图标颜色"""
        for index, (icon_name, icon_size) in self._tab_icon_meta.items():
            color = T.NEON if index == current_index else "#FFFFFF"
            pixmap = Icons.colored_pixmap(icon_name, color, icon_size)
            self.setTabIcon(index, QIcon(pixmap))

    def _setup_ui(self):
        """初始化 UI 样式"""
        # 应用自定义 TabBar
        self.setTabBar(EqualWidthTabBar(self))

        # 应用主题样式
        self.setStyleSheet(f"""
            QTabWidget::pane {{ border: none;  background: transparent;  }}
            QTabBar {{  background: transparent;  }}
            QTabBar::tab {{
                background: {T.GREEN}; color: #FFFFFF;
                padding: 12px 26px; font-size: 15px; font-weight: 700;
                font-family: {T.FONT}; border: none;
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
            }}
            QTabBar::tab:selected {{
                color: {T.NEON};  background: {T.SURFACE};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            QTabBar::tab:hover:!selected {{ color: #FFFFFF; background: {T.SURFACE2}; }}
            QTabBar::tab QPushButton {{ margin: 0; padding: 0; }}
            QTabBar::tab::icon {{ subcontrol-position: left; margin-right: 6px; }}
            QTabBar::tab::text {{ 
                alignment: center; 
                elide: Qt.ElideRight; 
            }}
        """)

    def add_tab(self, widget, icon_name: str, label: str,
                icon_color: str = None, icon_size: IconSize = None):
        """
        添加一个带图标的 Tab

        Args:
            widget: 要添加的面板/控件
            icon_name: 图标逻辑名（如 "record_voice"）
            label: 显示的文字标签
            icon_color: 图标颜色，留空时自动根据选中状态决定颜色
            icon_size: 图标尺寸，默认使用组件初始化时的尺寸
        """
        if icon_size is None:
            icon_size = self._icon_size

        # 新 tab 的 index = 当前 tab 数量
        new_index = self.count()
        # 第一个 tab 添加后会成为选中态（index 0），其余默认白色
        resolved_color = icon_color if icon_color else (T.NEON if new_index == 0 else "#FFFFFF")

        pixmap = Icons.colored_pixmap(icon_name, resolved_color, icon_size)
        icon = QIcon(pixmap)
        self.addTab(widget, icon, label)

        # 记录元数据，供 _on_tab_changed 动态切换
        self._tab_icon_meta[new_index] = (icon_name, icon_size)

    def add_tabs(self, tab_configs: list):
        """
        批量添加多个 Tab

        Args:
            tab_configs: 列表，元素格式：
                - (widget, icon_name, label)  # 3 元组
                - (widget, icon_name, label, icon_color, icon_size)  # 5 元组
        """
        for config in tab_configs:
            if len(config) == 3:
                widget, icon_name, label = config
                self.add_tab(widget, icon_name, label)
            elif len(config) == 5:
                widget, icon_name, label, icon_color, icon_size = config
                self.add_tab(widget, icon_name, label, icon_color, icon_size)
            else:
                raise ValueError(f"Tab 配置格式错误: {config}")