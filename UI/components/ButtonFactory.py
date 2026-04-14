# UI/components/ButtonFactory.py
"""
统一按钮工厂 — Neumorphism 新拟物风格版本。

对应设计规范按键类型：
  BTN_PRIMARY          → primary()   暖色渐变强调按钮（开始面试等关键动作）
  BTN_NEU_RAISED       → raised()    通用凸起新拟物按钮
  BTN_ICON_ONLY        → icon()      图标按钮（无文字或弱文字）
  BTN_DANGER_SECONDARY → danger()    风险次级按钮（结束面试、清空等）
  BTN_DISABLED         → 通过 .setEnabled(False) 触发各按钮的 :disabled 样式

设计方向：浅色复古、奶油纸感、双阴影模拟实体按压感
"""

from PySide6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PySide6.QtCore import Qt, QSize, QPoint
from PySide6.QtGui import QColor, QFont
from UI.components.info.Theme import Theme

# ── 设计令牌引用 ────────────────────────────────────────────────────────────
T = Theme


def _apply_neu_shadow(widget: QPushButton, pressed: bool = False) -> None:
    """
    为组件应用新拟物阴影效果。

    Qt 限制：同一 widget 只能附加一个 QGraphicsDropShadowEffect，
    策略：以暗阴影为主（视觉权重更大），亮阴影通过背景渐变近似模拟。

    Args:
        widget: 目标 QPushButton
        pressed: 是否为按下态（内凹感，阴影参数反转）
    """
    shadow_config = T.SHADOW_PRESSED if pressed else T.SHADOW_RAISED
    # 使用暗阴影作为主阴影（Qt 单阴影限制下的最优解）
    dark_cfg = shadow_config["dark"]

    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setColor(QColor(dark_cfg["color"]))
    shadow.setOffset(*dark_cfg["offset"])
    shadow.setBlurRadius(dark_cfg["blur"])
    widget.setGraphicsEffect(shadow)
    # 保存配置以便状态切换时复用
    widget.setProperty("_shadow_cfg", shadow_config)


def _update_shadow_state(widget: QPushButton, pressed: bool) -> None:
    """动态切换按钮阴影状态（凸起 ↔ 内凹）"""
    effect = widget.graphicsEffect()
    if isinstance(effect, QGraphicsDropShadowEffect):
        cfg_key = "dark" if pressed else "light"  # 按下态用暗阴影强调内凹
        cfg = widget.property("_shadow_cfg")[cfg_key]
        effect.setColor(QColor(cfg["color"]))
        effect.setOffset(*cfg["offset"])
        effect.setBlurRadius(cfg["blur"])


class ButtonFactory:
    # ── 内部样式模板 ─────────────────────────────────────────────────────────
    # 使用 f-string 预编译减少重复字符串拼接，提升性能
    _PRIMARY_QSS = f"""
        QPushButton {{
            color: {T.ACCENT_TEXT};
            border: none;
            border-radius: {T.RADIUS_LG}px;
            padding: 0 20px;
            font-size: 14px;
            font-weight: 700;
            font-family: {T.FONT};
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {T.ACCENT_START}, stop:1 {T.ACCENT_END}
            );
        }}
        QPushButton:hover {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #D9AE95, stop:1 #C48870
            );
        }}
        QPushButton:pressed {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #BB8D74, stop:1 #A96E58
            );
            padding-top: 2px;
        }}
        QPushButton:disabled {{
            background: {T.DISABLED_BG};
            color: {T.DISABLED_TEXT};
            border: none;
        }}
    """

    _RAISED_QSS = f"""
        QPushButton {{
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {T.SURFACE}, stop:1 #E3D6C7
            );
            color: {T.TEXT};
            border: 1px solid {T.BORDER};
            border-radius: {{radius}}px;
            padding: 0 18px;
            font-size: 13px;
            font-weight: 600;
            font-family: {T.FONT};
        }}
        QPushButton:hover {{
            color: #463B31;
            border: 1px solid #CEBFAD;
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {T.HOVER_TINT}, stop:1 #E9DDCE
            );
        }}
        QPushButton:pressed {{
            color: #42372D;
            border: 1px solid #BEAF9D;
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {T.PRESSED_TINT}, stop:1 #F6EFE5
            );
            padding-top: 2px;
            padding-left: 2px;
        }}
        QPushButton:disabled {{
            color: {T.DISABLED_TEXT};
            border: 1px solid #E1D7CA;
            background: {T.DISABLED_BG};
        }}
    """

    _ICON_QSS = f"""
        QPushButton {{
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {T.SURFACE}, stop:1 #E3D6C7
            );
            color: {T.TEXT_DIM};
            border: 1px solid {T.BORDER};
            border-radius: {{radius}}px;
            font-size: {{font_size}}px;
            font-family: "Material Symbols Outlined", {T.FONT};
            padding: 0;
        }}
        QPushButton:hover {{
            color: {T.ACCENT_SOLID};
            border: 1px solid #CEBFAD;
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {T.HOVER_TINT}, stop:1 #E9DDCE
            );
        }}
        QPushButton:pressed {{
            color: {T.TEXT};
            border: 1px solid #BEAF9D;
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {T.PRESSED_TINT}, stop:1 #F6EFE5
            );
        }}
        QPushButton:disabled {{
            color: {T.DISABLED_TEXT};
            border: 1px solid #E1D7CA;
            background: {T.DISABLED_BG};
        }}
    """

    _DANGER_QSS = f"""
        QPushButton {{
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {T.SURFACE}, stop:1 #E8DDD2
            );
            color: {T.ERROR};
            border: 1px solid #C9A896;
            border-radius: {{radius}}px;
            padding: 0 18px;
            font-size: 13px;
            font-weight: 600;
            font-family: {T.FONT};
        }}
        QPushButton:hover {{
            color: #7A2E20;
            border: 1px solid #C09080;
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #FBF0EC, stop:1 #EFE0D8
            );
        }}
        QPushButton:pressed {{
            color: #6B2418;
            border: 1px solid #AD7E6E;
            background-image: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 #E0C8BE, stop:1 #F5EBE6
            );
            padding-top: 2px;
            padding-left: 2px;
        }}
        QPushButton:disabled {{
            color: {T.DISABLED_TEXT};
            border: 1px solid #E1D7CA;
            background: {T.DISABLED_BG};
        }}
    """

    # ── BTN_PRIMARY ─────────────────────────────────────────────────────────
    @staticmethod
    def primary(text: str, height: int = 44, width: int | None = None) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        if width: btn.setFixedWidth(width)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
                QPushButton {{
                    color: {T.ACCENT_TEXT};
                    border: none;
                    border-radius: {height // 2}px;
                    padding: 0 20px;
                    font-size: 14px;
                    font-weight: 700;
                    font-family: {T.FONT};
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {T.ACCENT_START}, stop:1 {T.ACCENT_END}
                    );
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #D9AE95, stop:1 #C48870
                    );
                }}
                QPushButton:pressed {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #BB8D74, stop:1 #A96E58
                    );
                    padding-top: 2px;
                }}
                QPushButton:disabled {{
                    background: {T.DISABLED_BG};
                    color: {T.DISABLED_TEXT};
                    border: none;
                }}
            """)
        return btn

    # ── BTN_NEU_RAISED ──────────────────────────────────────────────────────
    @staticmethod
    def raised(text: str, height: int = 40, width: int | None = None,
               shadow: bool = True, radius: int | None = None) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        if width: btn.setFixedWidth(width)
        btn.setCursor(Qt.PointingHandCursor)

        r = radius or max(height // 2, T.RADIUS_MD)
        btn.setStyleSheet(f"""
                QPushButton {{
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {T.SURFACE}, stop:1 #E3D6C7
                    );
                    color: {T.TEXT};
                    border: 1px solid {T.BORDER};
                    border-radius: {r}px;
                    padding: 0 18px;
                    font-size: 13px;
                    font-weight: 600;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    color: #463B31;
                    border: 1px solid #CEBFAD;
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {T.HOVER_TINT}, stop:1 #E9DDCE
                    );
                }}
                QPushButton:pressed {{
                    color: #42372D;
                    border: 1px solid #BEAF9D;
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {T.PRESSED_TINT}, stop:1 #F6EFE5
                    );
                    padding-top: 2px;
                    padding-left: 2px;
                }}
                QPushButton:disabled {{
                    color: {T.DISABLED_TEXT};
                    border: 1px solid #E1D7CA;
                    background: {T.DISABLED_BG};
                }}
            """)
        if shadow:
            _apply_neu_shadow(btn)
            btn.pressed.connect(lambda: _update_shadow_state(btn, True))
            btn.released.connect(lambda: _update_shadow_state(btn, False))
        return btn

    # ── BTN_ICON_ONLY ───────────────────────────────────────────────────────
    @staticmethod
    def icon(icon_name: str, size: int = 36, tooltip: str = "",
             shadow: bool = True) -> QPushButton:
        btn = QPushButton()
        btn_size = max(size, 32)
        btn.setFixedSize(QSize(btn_size, btn_size))
        btn.setCursor(Qt.PointingHandCursor)
        if tooltip: btn.setToolTip(tooltip)

        font = QFont("Material Symbols Outlined")
        font.setPixelSize(int(btn_size * 0.55))
        btn.setFont(font)
        btn.setText(icon_name)

        r = btn_size // 2
        fs = int(btn_size * 0.5)
        btn.setStyleSheet(f"""
                QPushButton {{
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {T.SURFACE}, stop:1 #E3D6C7
                    );
                    color: {T.TEXT_DIM};
                    border: 1px solid {T.BORDER};
                    border-radius: {r}px;
                    font-size: {fs}px;
                    font-family: "Material Symbols Outlined", {T.FONT};
                    padding: 0;
                }}
                QPushButton:hover {{
                    color: {T.ACCENT_SOLID};
                    border: 1px solid #CEBFAD;
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {T.HOVER_TINT}, stop:1 #E9DDCE
                    );
                }}
                QPushButton:pressed {{
                    color: {T.TEXT};
                    border: 1px solid #BEAF9D;
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {T.PRESSED_TINT}, stop:1 #F6EFE5
                    );
                }}
                QPushButton:disabled {{
                    color: {T.DISABLED_TEXT};
                    border: 1px solid #E1D7CA;
                    background: {T.DISABLED_BG};
                }}
            """)
        if shadow:
            _apply_neu_shadow(btn)
            btn.pressed.connect(lambda: _update_shadow_state(btn, True))
            btn.released.connect(lambda: _update_shadow_state(btn, False))
        return btn

    # ── BTN_DANGER_SECONDARY ────────────────────────────────────────────────
    @staticmethod
    def danger(text: str, height: int = 40, width: int | None = None,
               shadow: bool = False) -> QPushButton:
        btn = QPushButton(text)
        btn.setFixedHeight(height)
        if width: btn.setFixedWidth(width)
        btn.setCursor(Qt.PointingHandCursor)

        r = max(height // 2, T.RADIUS_MD)
        btn.setStyleSheet(f"""
                QPushButton {{
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 {T.SURFACE}, stop:1 #E8DDD2
                    );
                    color: {T.ERROR};
                    border: 1px solid #C9A896;
                    border-radius: {r}px;
                    padding: 0 18px;
                    font-size: 13px;
                    font-weight: 600;
                    font-family: {T.FONT};
                }}
                QPushButton:hover {{
                    color: #7A2E20;
                    border: 1px solid #C09080;
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #FBF0EC, stop:1 #EFE0D8
                    );
                }}
                QPushButton:pressed {{
                    color: #6B2418;
                    border: 1px solid #AD7E6E;
                    background-image: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 #E0C8BE, stop:1 #F5EBE6
                    );
                    padding-top: 2px;
                    padding-left: 2px;
                }}
                QPushButton:disabled {{
                    color: {T.DISABLED_TEXT};
                    border: 1px solid #E1D7CA;
                    background: {T.DISABLED_BG};
                }}
            """)
        if shadow:
            _apply_neu_shadow(btn)
        return btn
    # ── 工具方法 ────────────────────────────────────────────────────────────
    @staticmethod
    def set_enabled_with_style(btn: QPushButton, enabled: bool) -> None:
        """
        安全设置按钮启用状态，确保 :disabled 样式正确应用。
        （Qt 有时需要刷新样式表才能生效）
        """
        btn.setEnabled(enabled)
        # 触发样式重计算（可选，视 Qt 版本而定）
        btn.style().unpolish(btn)
        btn.style().polish(btn)

    # ── 向后兼容保留（旧接口映射到新类型）──────────────────────────────────
    @staticmethod
    def primary_legacy(text: str, color: str = "#BE886F", height: int = 38) -> QPushButton:
        """[已废弃] 原 primary()（霓虹描边风格）→ 重定向到 raised()"""
        return ButtonFactory.raised(text, height=height)

    @staticmethod
    def solid(text: str, color: str = "#BE886F", height: int = 38,
              width: int | None = None) -> QPushButton:
        """[已废弃] 原 solid()（霓虹实心填充）→ 重定向到 primary()"""
        return ButtonFactory.primary(text, height=height, width=width)

    @staticmethod
    def ghost(text: str, height: int = 30) -> QPushButton:
        """[已废弃] 原 ghost()（暗色透明底）→ 重定向到 raised(shadow=False)"""
        return ButtonFactory.raised(text, height=height, shadow=False)

    @staticmethod
    def tag(text: str, color: str = "#BE886F", height: int = 32) -> QPushButton:
        """[已废弃] 原 tag()（霓虹标签快捷按钮）→ 重定向到 raised(shadow=False)"""
        return ButtonFactory.raised(text, height=height, shadow=False)