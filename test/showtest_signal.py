# test_multi_slot.py
import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QObject, Signal, QEvent
from PySide6.QtGui import QColor, QCursor, QFont

from UI.components.ButtonFactory import ButtonFactory


class GlobalMouseFilter(QObject):
    mouse_moved   = Signal(int, int)
    mouse_clicked = Signal(int, int, int)

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.MouseMove:
            pos = QCursor.pos()
            self.mouse_moved.emit(pos.x(), pos.y())
        elif event.type() == QEvent.Type.MouseButtonPress:
            pos = QCursor.pos()
            self.mouse_clicked.emit(pos.x(), pos.y(), event.button().value)
        return False


# ─────────────────────────────────────────────
# 阴影追踪包装器
# ─────────────────────────────────────────────
class ShadowTracker:
    """
    维护单个按钮的 QGraphicsDropShadowEffect。
    光源坐标 → 阴影方向 = 反方向。
    低通滤波让阴影缓动，不瞬移。
    """
    def __init__(
        self,
        btn,
        shadow_color: str = "#00000030",
        max_offset: int = 15,
        blur: int = 20,
        axis: str = "xy",          # "x" | "y" | "xy"
    ):
        self.btn        = btn
        self.max_offset = max_offset
        self.blur       = blur
        self.axis       = axis

        self._ox = 0.0
        self._oy = 0.0

        self._effect = QGraphicsDropShadowEffect(btn)
        self._effect.setBlurRadius(blur)
        self._effect.setOffset(0, 4)        # 初始：正下方自然落影
        qc = QColor(shadow_color)
        self._effect.setColor(qc)
        btn.setGraphicsEffect(self._effect)

    def update_light(self, nx: float, ny: float):
        """
        nx, ny ∈ [-1, 1]，以屏幕中心为原点的归一化光源位置。
        阴影 = 光源反方向。
        """
        if self.axis == "x":
            ny = 0.0
        elif self.axis == "y":
            nx = 0.0

        tx = -nx * self.max_offset
        ty = -ny * self.max_offset

        # 低通平滑：每帧追 30%，阴影缓动而不抖动
        self._ox += (tx - self._ox) * 0.30
        self._oy += (ty - self._oy) * 0.30

        self._effect.setOffset(self._ox, self._oy)


# ─────────────────────────────────────────────
# 主窗口
# ─────────────────────────────────────────────
class TestWindow(QWidget):
    def __init__(self, mouse_filter: GlobalMouseFilter):
        super().__init__()
        self.setFixedSize(680, 400)
        self.setWindowTitle("光源追踪阴影测试")

        # ── 浅色背景：米白，阴影才看得见 ──
        self.setStyleSheet("""
            QWidget {
                background: #F2F0EB;
            }
        """)

        self._filter = mouse_filter
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(32)
        root.setContentsMargins(50, 44, 50, 44)

        # 坐标提示
        self.lbl_coords = QLabel("移动鼠标 — 光源跟随")
        self.lbl_coords.setAlignment(Qt.AlignCenter)
        self.lbl_coords.setStyleSheet(
            "color: #999; font-size: 12px; letter-spacing: 1px; background: transparent;"
        )

        # ── 三个按钮，用干净的白色卡片风格 ──
        # 直接手写样式，不走 ButtonFactory（需要白底深字）
        self.btn_x  = self._make_card_btn("X 轴感应",  "#3A7BD5")
        self.btn_y  = self._make_card_btn("Y 轴感应",  "#E05A7A")
        self.btn_xy = self._make_card_btn("XY 感应",   "#2EAA6E")

        # 阴影追踪器
        self.tracker_x  = ShadowTracker(self.btn_x,  axis="x",  shadow_color="#3A7BD540")
        self.tracker_y  = ShadowTracker(self.btn_y,  axis="y",  shadow_color="#E05A7A40")
        self.tracker_xy = ShadowTracker(self.btn_xy, axis="xy", shadow_color="#2EAA6E40")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(24)
        btn_row.addWidget(self.btn_x)
        btn_row.addWidget(self.btn_y)
        btn_row.addWidget(self.btn_xy)

        # ── 日志区 ──
        self.lbl_log_title = QLabel("点击记录")
        self.lbl_log_title.setStyleSheet(
            "color: #BBB; font-size: 10px; letter-spacing: 2px; background: transparent;"
        )

        self.log_labels: list[QLabel] = []
        log_layout = QVBoxLayout()
        log_layout.setSpacing(2)
        for _ in range(4):
            lbl = QLabel("")
            lbl.setStyleSheet(
                "color: #888; font-size: 11px;"
                "font-family: 'Courier New', monospace; background: transparent;"
            )
            self.log_labels.append(lbl)
            log_layout.addWidget(lbl)

        root.addWidget(self.lbl_coords)
        root.addLayout(btn_row)
        root.addWidget(self.lbl_log_title)
        root.addLayout(log_layout)

    @staticmethod
    def _make_card_btn(text: str, color: str):
        """白底圆角卡片按钮，适合浅色背景下展示阴影。"""
        from PySide6.QtWidgets import QPushButton
        btn = QPushButton(text)
        btn.setFixedHeight(52)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: #FFFFFF;
                color: {color};
                border: 1.5px solid {color}33;
                border-radius: 14px;
                font-size: 13px;
                font-weight: 600;
                padding: 0 24px;
                letter-spacing: 0.5px;
            }}
            QPushButton:hover {{
                background: #FAFAFA;
                border-color: {color}88;
            }}
            QPushButton:pressed {{
                background: #F5F5F5;
            }}
        """)
        return btn

    def _connect_signals(self):
        self._filter.mouse_moved.connect(self._slot_coords)
        self._filter.mouse_moved.connect(self._slot_shadow_x)
        self._filter.mouse_moved.connect(self._slot_shadow_y)
        self._filter.mouse_moved.connect(self._slot_shadow_xy)
        self._filter.mouse_clicked.connect(self._slot_log)

    # ── 槽函数 ───────────────────────────────

    def _slot_coords(self, gx: int, gy: int):
        self.lbl_coords.setText(f"光源  ({gx}, {gy})")

    # ── 修改 _normalized，用窗口自身尺寸做基准 ──────────────
    def _normalized(self, gx: int, gy: int) -> tuple[float, float]:
        """
        全局坐标 → [-1, 1]，以窗口中心为原点，窗口边缘为 ±1。
        鼠标在窗口内移动就能跑满全程，不再被屏幕尺寸稀释。
        """
        # 窗口左上角的全局坐标
        win_pos = self.mapToGlobal(self.rect().topLeft())

        # 鼠标相对窗口的位置
        rx = gx - win_pos.x()
        ry = gy - win_pos.y()

        # 以窗口中心为原点，归一化到 [-1, 1]，clamp 防止出窗口后越界
        nx = max(-1.0, min(1.0, (rx / self.width())  * 2 - 1))
        ny = max(-1.0, min(1.0, (ry / self.height()) * 2 - 1))
        return nx, ny

    def _slot_shadow_x(self, gx: int, gy: int):
        nx, ny = self._normalized(gx, gy)
        self.tracker_x.update_light(nx, ny)   # tracker 内部 axis="x" 会忽略 ny

    def _slot_shadow_y(self, gx: int, gy: int):
        nx, ny = self._normalized(gx, gy)
        self.tracker_y.update_light(nx, ny)   # axis="y" 忽略 nx

    def _slot_shadow_xy(self, gx: int, gy: int):
        nx, ny = self._normalized(gx, gy)
        self.tracker_xy.update_light(nx, ny)

    def _slot_log(self, gx: int, gy: int, btn_val: int):
        name = {1: "左键", 2: "右键", 4: "中键"}.get(btn_val, f"B{btn_val}")
        entry = f"▸ {name}  ({gx}, {gy})"
        print(entry)
        texts = [lbl.text() for lbl in self.log_labels[1:]] + [entry]
        for lbl, text in zip(self.log_labels, texts):
            lbl.setText(text)

    def closeEvent(self, event):
        self._filter.mouse_moved.disconnect()
        self._filter.mouse_clicked.disconnect()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mf = GlobalMouseFilter()
    app.installEventFilter(mf)
    win = TestWindow(mf)
    win.show()
    sys.exit(app.exec())