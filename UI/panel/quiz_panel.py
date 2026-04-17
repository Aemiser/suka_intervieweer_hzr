# UI/panel/quiz_panel.py
"""
题库管理与练习面板 - 参考 UI_test_03.html 布局设计
"""

import math

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QScrollArea,
    QFrame,
    QLineEdit,
    QGraphicsDropShadowEffect,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from UI.components import (
    T,
    StatBadge,
    ButtonFactory,
    GLOBAL_QSS,
    combo_qss,
    input_qss,
)
from UI.components.info.icon import Icons, IconSize

# ── 常量配置 ─────────────────────────────────────────────────────────────────
_BASE = T.BG
_HOVER_TINT = T.SURFACE2
_SHADOW_DARK = T.SURFACE_DARK
_BORDER_FOCUS = T.BORDER2

_LEVEL_COLORS: dict[str, tuple[str, str]] = {
    "初级": (T.SUCCESS, f"{T.SUCCESS}20"),
    "中级": (T.WARNING, f"{T.WARNING}20"),
    "高级": (T.YELLOW, f"{T.YELLOW}20"),
}

_CLASSIFY_COLORS: dict[str, str] = {
    "Java基础": T.YELLOW,
    "JVM": T.INFO,
    "Spring": T.WARNING,
    "MySQL": T.SUCCESS,
    "Redis": T.SUCCESS,
    "JavaScript": T.WARNING,
    "Vue/React": T.INFO,
    "计算机网络": T.YELLOW,
    "数据结构与算法": T.INFO,
}

_ORDER_OPTIONS = [
    ("分类 A→Z", "classify ASC"),
    (
        "难度 易→难",
        "CASE level WHEN '初级' THEN 1 WHEN '中级' THEN 2 WHEN '高级' THEN 3 END ASC, classify ASC",
    ),
    (
        "难度 难→易",
        "CASE level WHEN '初级' THEN 1 WHEN '中级' THEN 2 WHEN '高级' THEN 3 END DESC, classify ASC",
    ),
    ("题号 升序", "id ASC"),
    ("题号 降序", "id DESC"),
]


def _cls_color(cls: str) -> str:
    return _CLASSIFY_COLORS.get(cls, T.INFO)


# ── 题目卡片 ──────────────────────────────────────────────────────────────────
class QuestionCard(QFrame):
    def __init__(
        self,
        qid: int,
        classify: str,
        level: str,
        content: str,
        answer: str,
        global_index: int,
        parent=None,
    ):
        super().__init__(parent)
        self._answer_visible = False
        self.setObjectName("QCard")

        cls_color = _cls_color(classify)
        lvl_fg, lvl_bg = _LEVEL_COLORS.get(level, (T.TEXT_DIM, T.SURFACE))

        self.setStyleSheet(f"""
            QFrame#QCard {{
                background: {T.SURFACE};
                border: 1px solid {T.BORDER};
                border-radius: 12px;
                min-height: 80px;
            }}
            QFrame#QCard:hover {{
                background: {_HOVER_TINT};
                border-color: {cls_color}66;
            }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(_SHADOW_DARK))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.setMinimumHeight(80)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 14, 16, 14)
        lay.setSpacing(16)

        # 左侧内容区
        content_col = QVBoxLayout()
        content_col.setSpacing(8)
        content_col.setStretch(0, 0)
        content_col.setStretch(1, 0)

        # 标签行
        tags_row = QHBoxLayout()
        tags_row.setSpacing(6)

        num_lbl = QLabel(f"#{global_index:03d}")
        num_lbl.setStyleSheet(
            f"color: {T.TEXT_MUTE}; font-size: 11px; font-weight: 700;"
        )
        cls_tag = QLabel(f" {classify} ")
        cls_tag.setStyleSheet(f"""
            background: {cls_color}18; color: {cls_color};
            border: 1px solid {cls_color}55; border-radius: 4px;
            font-size: 11px; font-weight: 600; padding: 2px 8px;
        """)
        lvl_tag = QLabel(f" {level} ")
        lvl_tag.setStyleSheet(f"""
            background: {lvl_bg}; color: {lvl_fg};
            border-radius: 4px; font-size: 11px; font-weight: 600; padding: 2px 8px;
        """)
        tags_row.addWidget(num_lbl)
        tags_row.addWidget(cls_tag)
        tags_row.addWidget(lvl_tag)
        tags_row.addStretch()
        content_col.addLayout(tags_row)

        # 题目内容
        q_lbl = QLabel(content)
        q_lbl.setWordWrap(True)
        q_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        q_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        q_lbl.setStyleSheet(f"""
            color: {T.TEXT}; font-size: 14px; line-height: 1.6;
            font-weight: 500; background: transparent;
        """)
        content_col.addWidget(q_lbl)

        # 答案折叠区
        self.answer_frame = QFrame()
        self.answer_frame.setVisible(False)
        self.answer_frame.setStyleSheet(f"""
            background: {_BASE}; border: 1px dashed {T.BORDER};
            border-radius: 8px; margin-top: 8px;
        """)
        ans_lay = QVBoxLayout(self.answer_frame)
        ans_lay.setContentsMargins(12, 10, 12, 10)
        ans_lay.setSpacing(4)

        ans_title_h = QHBoxLayout()
        ans_title_h.setSpacing(6)
        ans_icon = QLabel()
        ans_icon.setPixmap(Icons.colored_pixmap("task_alt", T.INFO, IconSize.SM))
        ans_title = QLabel("参考答案")
        ans_title.setStyleSheet(f"color: {T.INFO}; font-size: 12px; font-weight: 700;")
        ans_title_h.addWidget(ans_icon)
        ans_title_h.addWidget(ans_title)
        ans_title_h.addStretch()

        ans_text = QLabel(answer)
        ans_text.setWordWrap(True)
        ans_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ans_text.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 13px; line-height: 1.6;"
        )

        ans_lay.addLayout(ans_title_h)
        ans_lay.addWidget(ans_text)
        content_col.addWidget(self.answer_frame)

        lay.addLayout(content_col, stretch=1)

        # 右侧操作按钮
        self.toggle_btn = QPushButton("查看答案")
        self.toggle_btn.setFixedSize(100, 34)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setIcon(Icons.get("visibility", IconSize.SM))
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {T.SURFACE}; color: {T.TEXT_DIM};
                border: 1px solid {T.BORDER}; border-radius: 8px;
                font-size: 12px; font-weight: 600; padding: 0 12px 0 8px;
            }}
            QPushButton:hover {{ color: {T.INFO}; border-color: {T.INFO}; }}
        """)
        self.toggle_btn.clicked.connect(self._toggle_answer)
        lay.addWidget(self.toggle_btn, alignment=Qt.AlignTop)

    def _toggle_answer(self) -> None:
        self._answer_visible = not self._answer_visible
        self.answer_frame.setVisible(self._answer_visible)
        if self._answer_visible:
            self.toggle_btn.setText("收起答案")
            self.toggle_btn.setIcon(Icons.get("visibility_off", IconSize.SM))
        else:
            self.toggle_btn.setText("查看答案")
            self.toggle_btn.setIcon(Icons.get("visibility", IconSize.SM))


# ── 分页导航 ────────────────────────────────────────────────────────────────────
class PaginationBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setStyleSheet(
            f"background: {T.SURFACE}; border-top: 1px solid {T.BORDER};"
        )

        self._current_page = 1
        self._total_pages = 1
        self._page_changed_cb = None
        self._page_buttons: list[QPushButton] = []

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(8)

        self._prev_btn = self._mk_icon_btn("chevron_left", "上一页")

        self._pages_container = QWidget()
        self._pages_lay = QHBoxLayout(self._pages_container)
        self._pages_lay.setContentsMargins(0, 0, 0, 0)
        self._pages_lay.setSpacing(4)

        self._next_btn = self._mk_icon_btn("chevron_right", "下一页")

        self._total_lbl = QLabel("共 0 题")
        self._total_lbl.setStyleSheet(f"color: {T.TEXT_MUTE}; font-size: 12px;")

        lay.addWidget(self._prev_btn)
        lay.addWidget(self._pages_container)
        lay.addWidget(self._next_btn)
        lay.addStretch()
        lay.addWidget(self._total_lbl)

        self._prev_btn.clicked.connect(lambda: self._go(self._current_page - 1))
        self._next_btn.clicked.connect(lambda: self._go(self._current_page + 1))

    def _mk_icon_btn(self, icon_name: str, tip: str) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(36, 32)
        btn.setToolTip(tip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIcon(Icons.get(icon_name, IconSize.SM))
        btn.setStyleSheet(f"""
            QPushButton {{ background: {T.SURFACE}; color: {T.TEXT_DIM};
                border: 1px solid {T.BORDER}; border-radius: 8px; }}
            QPushButton:hover {{ color: {T.INFO}; border-color: {T.INFO}; }}
            QPushButton:disabled {{ color: {T.TEXT_MUTE}; border-color: {T.BORDER}; }}
        """)
        return btn

    def _mk_page_btn(self, page: int) -> QPushButton:
        btn = QPushButton(str(page))
        btn.setFixedSize(40, 32)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{ background: {T.SURFACE}; color: {T.TEXT_DIM};
                border: 1px solid {T.BORDER}; border-radius: 8px;
                font-size: 13px; font-weight: 500; }}
            QPushButton:hover {{ color: {T.INFO}; border-color: {T.INFO}; }}
        """)
        btn.clicked.connect(lambda: self._go(page))
        return btn

    def _build_page_buttons(self) -> None:
        for btn in self._page_buttons:
            btn.setParent(None)
            btn.deleteLater()
        self._page_buttons.clear()

        total = self._total_pages
        current = self._current_page

        if total <= 7:
            for i in range(1, total + 1):
                btn = self._mk_page_btn(i)
                if i == current:
                    btn.setStyleSheet(f"""
                        QPushButton {{ background: {T.INFO}; color: #fff;
                            border: 1px solid {T.INFO}; border-radius: 8px;
                            font-size: 13px; font-weight: 600; }}
                    """)
                self._page_buttons.append(btn)
                self._pages_lay.addWidget(btn)
        else:
            if current <= 4:
                for i in range(1, 6):
                    btn = self._mk_page_btn(i)
                    if i == current:
                        btn.setStyleSheet(f"""
                            QPushButton {{ background: {T.INFO}; color: #fff;
                                border: 1px solid {T.INFO}; border-radius: 8px;
                                font-size: 13px; font-weight: 600; }}
                        """)
                    self._page_buttons.append(btn)
                    self._pages_lay.addWidget(btn)
                self._add_ellipsis()
                self._page_buttons.append(self._mk_page_btn(total))
                self._pages_lay.addWidget(self._page_buttons[-1])
            elif current >= total - 3:
                self._page_buttons.append(self._mk_page_btn(1))
                self._pages_lay.addWidget(self._page_buttons[-1])
                self._add_ellipsis()
                for i in range(total - 4, total + 1):
                    btn = self._mk_page_btn(i)
                    if i == current:
                        btn.setStyleSheet(f"""
                            QPushButton {{ background: {T.INFO}; color: #fff;
                                border: 1px solid {T.INFO}; border-radius: 8px;
                                font-size: 13px; font-weight: 600; }}
                        """)
                    self._page_buttons.append(btn)
                    self._pages_lay.addWidget(btn)
            else:
                self._page_buttons.append(self._mk_page_btn(1))
                self._pages_lay.addWidget(self._page_buttons[-1])
                self._add_ellipsis()
                for i in range(current - 1, current + 2):
                    btn = self._mk_page_btn(i)
                    if i == current:
                        btn.setStyleSheet(f"""
                            QPushButton {{ background: {T.INFO}; color: #fff;
                                border: 1px solid {T.INFO}; border-radius: 8px;
                                font-size: 13px; font-weight: 600; }}
                        """)
                    self._page_buttons.append(btn)
                    self._pages_lay.addWidget(btn)
                self._add_ellipsis()
                self._page_buttons.append(self._mk_page_btn(total))
                self._pages_lay.addWidget(self._page_buttons[-1])

    def _add_ellipsis(self) -> None:
        ellipsis = QLabel("...")
        ellipsis.setStyleSheet(
            f"color: {T.TEXT_MUTE}; font-size: 13px; padding: 0 4px;"
        )
        self._pages_lay.addWidget(ellipsis)

    def set_page_changed_callback(self, cb) -> None:
        self._page_changed_cb = cb

    def get_page_size(self) -> int:
        return 10

    def update(self, current: int, total: int, total_records: int) -> None:
        self._current_page = current
        self._total_pages = max(total, 1)
        self._total_lbl.setText(f"共 {total_records} 题")
        self._prev_btn.setEnabled(current > 1)
        self._next_btn.setEnabled(current < self._total_pages)
        self._build_page_buttons()

    def _go(self, page: int) -> None:
        page = max(1, min(page, self._total_pages))
        if page != self._current_page and self._page_changed_cb:
            self._page_changed_cb(page)


# ── 主面板 ────────────────────────────────────────────────────────────────────
class QuizPanel(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._current_page = 1
        self._total_records = 0

        self._build_ui()
        self._load_stats()
        self._query_and_render()

    def _build_ui(self) -> None:
        self.setStyleSheet(GLOBAL_QSS + combo_qss() + input_qss())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_content(), stretch=1)
        root.addWidget(self._build_pagination())

    def _build_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(
            f"background: {T.SURFACE}; border-bottom: 1px solid {T.BORDER};"
        )

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(12)

        # 搜索框
        search_frame = QFrame()
        search_frame.setStyleSheet("background: transparent; border: none;")
        search_lay = QHBoxLayout(search_frame)
        search_lay.setContentsMargins(0, 0, 8, 0)
        search_lay.setSpacing(8)
        self.search_icon = QLabel()
        self.search_icon.setPixmap(
            Icons.colored_pixmap("search", T.TEXT_MUTE, IconSize.SM)
        )
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索题目关键词...")
        self.search_box.setStyleSheet(
            "background: transparent; border: none; padding: 8px 0;"
        )
        self.search_box.setFixedHeight(34)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._on_filter_changed)
        self.search_box.textChanged.connect(lambda: self._search_timer.start(400))
        search_lay.addWidget(self.search_icon)
        search_lay.addWidget(self.search_box, stretch=1)
        lay.addWidget(search_frame, stretch=1)

        # 分类筛选
        cls_frame = self._make_filter_with_icon("category", "全部分类", 120)
        self.cls_combo = cls_frame.findChild(QComboBox)
        for (cls,) in self.db.fetchall(
            "SELECT DISTINCT classify FROM question_bank ORDER BY classify"
        ):
            self.cls_combo.addItem(cls, cls)
        self.cls_combo.currentIndexChanged.connect(self._on_filter_changed)
        lay.addWidget(cls_frame)

        # 难度筛选
        lvl_frame = self._make_filter_with_icon("tune", "全部难度", 100)
        self.lvl_combo = lvl_frame.findChild(QComboBox)
        for lvl in ["初级", "中级", "高级"]:
            self.lvl_combo.addItem(lvl, lvl)
        self.lvl_combo.currentIndexChanged.connect(self._on_filter_changed)
        lay.addWidget(lvl_frame)

        # 排序
        sort_frame = self._make_filter_with_icon("sort", "排序", 110)
        self.sort_combo = sort_frame.findChild(QComboBox)
        for label, _ in _ORDER_OPTIONS:
            self.sort_combo.addItem(label)
        self.sort_combo.currentIndexChanged.connect(self._on_filter_changed)
        lay.addWidget(sort_frame)

        # 刷新按钮
        ref_btn = ButtonFactory.ghost(
            "刷新", height=32, icon_name="refresh", icon_size=IconSize.SM
        )
        ref_btn.setFixedWidth(90)
        ref_btn.clicked.connect(self.refresh)
        lay.addWidget(ref_btn)

        return bar

    def _build_content(self) -> QScrollArea:
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: {_BASE}; border: none; }}"
        )

        self._content_widget = QWidget()
        self._content_widget.setStyleSheet(f"background: {_BASE};")
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(16, 16, 16, 16)
        self._content_layout.setSpacing(12)

        self._scroll.setWidget(self._content_widget)
        return self._scroll

    def _build_pagination(self) -> PaginationBar:
        self._pagination = PaginationBar()
        self._pagination.set_page_changed_callback(self._go_to_page)
        return self._pagination

    def _build_where(self) -> tuple[str, list]:
        keyword = self.search_box.text().strip()
        cls = self.cls_combo.currentData()
        lvl = self.lvl_combo.currentData()

        conds, params = [], []
        if keyword:
            conds.append("(content LIKE ? OR answer LIKE ?)")
            params += [f"%{keyword}%", f"%{keyword}%"]
        if cls:
            conds.append("classify=?")
            params.append(cls)
        if lvl:
            conds.append("level=?")
            params.append(lvl)

        where = ("WHERE " + " AND ".join(conds)) if conds else ""
        return where, params

    def _current_order_sql(self) -> str:
        idx = self.sort_combo.currentIndex()
        return (
            _ORDER_OPTIONS[idx][1]
            if 0 <= idx < len(_ORDER_OPTIONS)
            else _ORDER_OPTIONS[0][1]
        )

    def _query_and_render(self) -> None:
        page_size = self._pagination.get_page_size()
        offset = (self._current_page - 1) * page_size
        where, params = self._build_where()
        order = self._current_order_sql()

        total_row = self.db.fetchone(
            f"SELECT COUNT(*) FROM question_bank {where}", tuple(params)
        )
        self._total_records = total_row[0] if total_row else 0
        total_pages = max(1, math.ceil(self._total_records / page_size))

        if self._current_page > total_pages:
            self._current_page = total_pages

        rows = self.db.fetchall(
            f"SELECT id, classify, level, content, answer FROM question_bank "
            f"{where} ORDER BY {order} LIMIT ? OFFSET ?",
            tuple(params) + (page_size, offset),
        )

        self._render(rows, offset)
        self._pagination.update(self._current_page, total_pages, self._total_records)

    def _render(self, rows: list, offset: int) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not rows:
            empty_h = QHBoxLayout()
            empty_h.addStretch()
            empty_icon = QLabel()
            empty_icon.setPixmap(
                Icons.colored_pixmap("search", T.TEXT_MUTE, IconSize.LG)
            )
            empty_lbl = QLabel("没有找到符合条件的题目")
            empty_lbl.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 14px;")
            empty_h.addWidget(empty_icon)
            empty_h.addWidget(empty_lbl)
            empty_h.addStretch()
            self._content_layout.insertLayout(0, empty_h)
            return

        for i, (qid, cls, lvl, content, answer) in enumerate(rows):
            card = QuestionCard(qid, cls, lvl, content, answer, offset + i + 1)
            self._content_layout.insertWidget(i, card)

        self._content_layout.addStretch()
        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(0))

    def _make_filter_with_icon(
        self, icon_name: str, first_text: str, width: int
    ) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet("background: transparent; border: none;")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(Icons.colored_pixmap(icon_name, T.TEXT_MUTE, IconSize.SM))

        combo = QComboBox()
        combo.setFixedSize(width, 32)
        combo.addItem(first_text, "")
        combo.setStyleSheet(f"""
            QComboBox {{
                background: transparent;
                border: 1px solid {T.BORDER};
                border-radius: 6px;
                color: {T.TEXT_DIM};
                font-size: 13px;
                font-weight: 500;
                padding: 0 8px 0 4px;
            }}
            QComboBox:hover {{
                border-color: {T.INFO};
                color: {T.TEXT};
            }}
            QComboBox::drop-down {{
                border: none;
                subcontrol-origin: padding;
                subcontrol-position: right center;
                width: 24px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {T.TEXT_MUTE};
            }}
            QComboBox:on {{
                border-color: {T.INFO};
            }}
            QComboBox QAbstractItemView {{
                background: {T.SURFACE};
                color: {T.TEXT};
                selection-background-color: {T.INFO}33;
                border: 1px solid {T.BORDER};
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                min-height: 32px;
                padding: 4px 8px;
                border-radius: 4px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {T.INFO}22;
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: {T.INFO}44;
                color: {T.TEXT};
            }}
        """)

        lay.addWidget(icon_lbl)
        lay.addWidget(combo)
        return frame

    def _load_stats(self) -> None:
        pass

    def _on_filter_changed(self) -> None:
        self._current_page = 1
        self._query_and_render()

    def _go_to_page(self, page: int) -> None:
        self._current_page = page
        self._query_and_render()

    def refresh(self) -> None:
        self._current_page = 1
        self._query_and_render()
