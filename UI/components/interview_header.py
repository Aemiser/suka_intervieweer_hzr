"""
interview_header.py
面试侧边栏 Header 组件。

职责：
  - 垂直排版顶部工具栏（标题、姓名/岗位表单、操作按钮、状态提示）
  - 对外暴露信号：start_clicked / finish_clicked / resume_clicked
  - 对外暴露方法：set_status / set_loading / show_toast / load_jobs /
                  set_interview_controls_enabled
  - 不持有任何业务状态，不直接操作 Worker
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QVBoxLayout,QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QGraphicsDropShadowEffect,
)

from UI.components import T, ButtonFactory, input_qss, combo_qss
from UI.components.info.icon import Icons, IconSize

class InterviewHeader(QFrame):
    """左侧侧边栏组件，包含所有控件与信号出口。"""

    # ── 对外信号 ──────────────────────────────────────────────────────────────
    start_clicked = Signal()       # 「开始面试」按钮
    finish_clicked = Signal()      # 「结束面试」按钮
    resume_clicked = Signal()      # 「投递简历」按钮

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db

        # ✅ 侧边栏固定宽度，右侧边框隔离主内容区
        self.setFixedWidth(240)
        # 使用对象名避免样式污染到子组件
        self.setObjectName("InterviewSidebar")
        self.setStyleSheet(
            f"""
            QFrame#InterviewSidebar {{
                background: {T.SURFACE}; 
                border: none;
            }}
            """
            + input_qss()
            + combo_qss()
        )

        self._build()

    # ── 构建 Header UI ───────────────────────────────────────────────────────

    def _build(self) -> None:
        # 外层布局：设置四周留白，让背景色 SURFACE 作为间距显露出来
        outer_lay = QVBoxLayout(self)
        outer_lay.setContentsMargins(12, 12, 12, 12)  # 顶部、底部、左侧留出一定距离
        outer_lay.addSpacing(16)

        # 1. 顶部标题（独立在卡片外部）
        # 1. 顶部标题区域（图标 + 文字）
        title_container = QFrame()
        title_container.setStyleSheet("background: transparent;")
        title_lay = QHBoxLayout(title_container)
        title_lay.setContentsMargins(0, 0, 0, 0)
        title_lay.setSpacing(8)
        title_lay.setAlignment(Qt.AlignCenter)

        # 图标 QLabel
        icon_lbl = QLabel()
        icon_lbl.setPixmap(Icons.colored_pixmap("record_voice", T.TEXT, IconSize.SM))
        icon_lbl.setAlignment(Qt.AlignVCenter)

        # 文字 QLabel
        self.title = QLabel("模拟面试")
        self.title.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {T.TEXT}; font-family: {T.FONT};"
        )
        self.title.setAlignment(Qt.AlignVCenter)

        title_lay.addWidget(icon_lbl)
        title_lay.addWidget(self.title)


        # 2. 核心卡片（包含表单与按钮）
        self._card = QFrame()
        self._card.setObjectName("CoreCard")
        self._card.setStyleSheet(
            f"""
            QFrame#CoreCard {{
                background-color: {T.SURFACE3};
                border-radius: 12px;
                border: none;
            }}
            """
        )

        # 给卡片添加阴影效果
        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(20)          # 阴影模糊半径
        shadow.setColor(QColor(T.SURFACE3_DARK))
        shadow.setOffset(0, 1)            # 向下偏移4像素，更贴合悬浮感
        shadow.setXOffset(0)
        shadow.setYOffset(1)
        self._card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(self._card)
        card_lay.setContentsMargins(16, 20, 16, 20)
        card_lay.setSpacing(12)

        # --- 卡片内部：表单区域 ---
        name_lbl = QLabel("姓名")
        name_lbl.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 12px; margin-bottom: 2px;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("请输入姓名")
        self.name_input.setFixedHeight(36)
        card_lay.addWidget(name_lbl)
        card_lay.addWidget(self.name_input)

        job_lbl = QLabel("岗位")
        job_lbl.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 12px; margin-bottom: 2px;")
        self.job_combo = QComboBox()
        self.job_combo.setFixedHeight(36)
        self.load_jobs()
        card_lay.addWidget(job_lbl)
        card_lay.addWidget(self.job_combo)

        card_lay.addSpacing(4)
        card_lay.addWidget(self._h_line())
        card_lay.addSpacing(4)

        # --- 卡片内部：操作按钮 ---
        self.resume_btn = ButtonFactory.solid("投递简历", T.GREEN, height=38)
        self.resume_btn.setToolTip("上传简历，AI 将分析简历内容")
        self.resume_btn.clicked.connect(self.resume_clicked)
        card_lay.addWidget(self.resume_btn)

        self.start_btn = ButtonFactory.solid("开始面试", T.NEON, height=38)
        self.start_btn.clicked.connect(self.start_clicked)
        card_lay.addWidget(self.start_btn)

        self.finish_btn = ButtonFactory.solid("结束面试", T.PURPLE, height=38)
        self.finish_btn.setEnabled(False)
        self.finish_btn.clicked.connect(self.finish_clicked)
        card_lay.addWidget(self.finish_btn)

        # 将卡片加入外层布局
        outer_lay.addWidget(self._card)

        # 3. 弹簧将底部状态推至最下方
        outer_lay.addStretch()

        # 4. 底部状态提示（独立在卡片外部）
        self.status_lbl = QLabel("准备就绪")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setWordWrap(True)
        self.status_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 12px; font-family: {T.FONT}; padding: 8px 0;"
        )
        outer_lay.addWidget(self.status_lbl)
        self._set_icon()

    def _set_icon(self) -> None:
        self.resume_btn.setIcon(Icons.get("upload", IconSize.SM))
        self.start_btn.setIcon(Icons.get("play_circle", IconSize.SM))
        self.finish_btn.setIcon(Icons.get("stop_circle", IconSize.SM))

    def _h_line(self) -> QFrame:
        """返回一条水平分割线"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        # 适当调暗一点颜色，在 SURFACE3 背景上看起来更自然
        line.setStyleSheet(f"background: {T.SURFACE3_DARK}; max-height: 1px;")
        return line

    # ── 公开方法（逻辑完全保留）─────────────────────────────────────────────

    def load_jobs(self) -> None:
        """从数据库加载岗位列表到下拉框。"""
        self.job_combo.clear()
        try:
            rows = self.db.fetchall("SELECT id, name FROM job_position")
            for jid, name in rows:
                self.job_combo.addItem(name, jid)
        except Exception:
            self.job_combo.addItem("暂无岗位", 0)

    def set_status(self, msg: str) -> None:
        """更新状态文本（普通样式）。"""
        self.status_lbl.setText(msg)
        self.status_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 12px; font-family: {T.FONT};"
        )

    def set_loading(self, loading: bool, msg: str = "") -> None:
        """切换加载状态样式。"""
        if loading:
            self.status_lbl.setText(f"⏳  {msg}")
            self.status_lbl.setStyleSheet(
                f"color: {T.NEON}; font-size: 12px; font-weight: 600;"
                f"font-family: {T.FONT};"
            )
        else:
            self.status_lbl.setStyleSheet(
                f"color: {T.TEXT_DIM}; font-size: 12px; font-family: {T.FONT};"
            )

    def show_toast(self, msg: str) -> None:
        """在状态栏短暂显示警告信息（2 秒后恢复）。"""
        orig_text = self.status_lbl.text()
        orig_style = self.status_lbl.styleSheet()
        self.status_lbl.setText(f"⚠️  {msg}")
        self.status_lbl.setStyleSheet(
            f"color: {T.ACCENT}; font-weight: bold; font-size: 12px;"
            f"font-family: {T.FONT};"
        )
        QTimer.singleShot(
            2000,
            lambda: (
                self.status_lbl.setText(orig_text),
                self.status_lbl.setStyleSheet(orig_style),
            ),
        )

    def set_interview_controls_enabled(
        self,
        *,
        start: bool | None = None,
        finish: bool | None = None,
        inputs: bool | None = None,
    ) -> None:
        """批量控制按钮与输入框的启用状态。传 None 表示不变。"""
        if start is not None:
            self.start_btn.setEnabled(start)
        if finish is not None:
            self.finish_btn.setEnabled(finish)
        if inputs is not None:
            self.name_input.setEnabled(inputs)
            self.job_combo.setEnabled(inputs)

    # ── 便捷属性（只读代理，方便面板直接访问控件值）─────────────────────────

    @property
    def candidate_name(self) -> str:
        return self.name_input.text().strip()

    @property
    def selected_job_id(self):
        return self.job_combo.currentData()

    @property
    def selected_job_name(self) -> str:
        return self.job_combo.currentText()
