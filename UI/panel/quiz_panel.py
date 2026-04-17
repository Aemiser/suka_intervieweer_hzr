# UI/panel/quiz_panel.py
"""
题库管理与练习面板（分页版）。
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
from PySide6.QtWidgets import QPushButton

# ── 分类色彩映射（适配新拟物浅色主题）─────────────────────────────────────────
CLASSIFY_COLORS: dict[str, str] = {
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

LEVEL_COLORS: dict[str, tuple[str, str]] = {
    "初级": (T.SUCCESS, f"{T.SUCCESS}20"),
    "中级": (T.WARNING, f"{T.WARNING}20"),
    "高级": (T.YELLOW, f"{T.YELLOW}20"),
}

_ORDER_OPTIONS = [
    (
        "分类 A→Z",
        "classify ASC,  CASE level WHEN '初级' THEN 1 WHEN '中级' THEN 2 WHEN '高级' THEN 3 END ASC",
    ),
    (
        "难度 易→难",
        "CASE level WHEN '初级' THEN 1 WHEN '中级' THEN 2 WHEN '高级' THEN 3 END ASC,  classify ASC",
    ),
    (
        "难度 难→易",
        "CASE level WHEN '初级' THEN 1 WHEN '中级' THEN 2 WHEN '高级' THEN 3 END DESC, classify ASC",
    ),
    ("题号 升序", "id ASC"),
    ("题号 降序", "id DESC"),
]

DEFAULT_PAGE_SIZE = 10

# ── 从新 Theme 推导出的替代值 ────────────────────────────────────────────────
# T.BASE        → T.BG          米白灰底，原来的"基底层"
# T.HOVER_TINT  → T.SURFACE2    悬浮时用次级区块色
# T.PRESSED_TINT→ T.SURFACE3    按压态用更深的区块色
# T.SHADOW_DARK → T.SURFACE_DARK 新拟态暗阴影色
# T.BORDER_FOCUS→ T.BORDER2     聚焦边框用强调分割线
# T.DISABLED_TEXT→T.TEXT_MUTE   禁用文字用最浅文字色
# T.RADIUS_SM   → 6  (px)
# T.RADIUS_LG   → 16 (px)
_BASE = T.BG
_HOVER_TINT = T.SURFACE2
_PRESSED_TINT = T.SURFACE3
_SHADOW_DARK = T.SURFACE_DARK
_BORDER_FOCUS = T.BORDER2
_DISABLED_TEXT = T.TEXT_MUTE
_RADIUS_SM = 6
_RADIUS_LG = 16


def _cls_color(cls: str) -> str:
    return CLASSIFY_COLORS.get(cls, T.INFO)


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
        lvl_fg, lvl_bg = LEVEL_COLORS.get(level, (T.TEXT_DIM, T.SURFACE))

        self.setStyleSheet(f"""
                    QFrame#QCard {{
                        background: {T.SURFACE};
                        border: 1px solid {T.BORDER};
                        border-left: 3px solid {cls_color};
                        border-radius: 5px;
                    }}
                    QFrame#QCard:hover {{
                        background: {_HOVER_TINT};
                        border-color: {cls_color}66;
                    }}
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(_SHADOW_DARK))
        shadow.setOffset(2, 3)
        self.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(10)

        # 顶部标签行
        header = QHBoxLayout()
        header.setSpacing(6)

        num_lbl = QLabel(f"#{global_index:03d}  ID:{qid}")
        num_lbl.setStyleSheet(
            f"color: {T.TEXT_MUTE}; font-size: 11px; font-family: {T.FONT_MONO};"
            f"font-weight: 700; background: transparent;"
        )
        cls_tag = QLabel(f" {classify} ")
        cls_tag.setStyleSheet(
            f"background: {cls_color}18; color: {cls_color};"
            f"border: 1px solid {cls_color}55; border-radius: 4px;"
            f"font-size: 11px; font-weight: 700; padding: 1px 7px; font-family: {T.FONT};"
        )
        lvl_tag = QLabel(f" {level} ")
        lvl_tag.setStyleSheet(
            f"background: {lvl_bg}; color: {lvl_fg};"
            f"border-radius: 4px; font-size: 11px; font-weight: 700;"
            f"padding: 1px 7px; font-family: {T.FONT};"
        )

        header.addWidget(num_lbl)
        header.addWidget(cls_tag)
        header.addWidget(lvl_tag)
        header.addStretch()
        lay.addLayout(header)

        # 题目内容
        q_lbl = QLabel(content)
        q_lbl.setWordWrap(True)
        q_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        q_lbl.setStyleSheet(
            f"color: {T.TEXT}; font-size: 14px; line-height: 1.6; font-weight: 500;"
            f"background: transparent; font-family: {T.FONT};"
        )
        lay.addWidget(q_lbl)

        # 答案折叠区
        self.answer_frame = QFrame()
        self.answer_frame.setVisible(False)
        self.answer_frame.setStyleSheet(f"""
                    QFrame {{
                        background: {_BASE};
                        border: 1px dashed {T.BORDER};
                        border-radius: {_RADIUS_SM}px;
                    }}
        """)
        ans_lay = QVBoxLayout(self.answer_frame)
        ans_lay.setContentsMargins(12, 10, 12, 10)
        ans_lay.setSpacing(4)

        ans_title = QLabel("💡  参考答案")
        ans_title.setStyleSheet(
            f"color: {T.INFO}; font-size: 11px; font-weight: 700;"
            f"background: transparent; font-family: {T.FONT};"
        )
        ans_text = QLabel(answer)
        ans_text.setWordWrap(True)
        ans_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        ans_text.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 13px; line-height: 1.6;"
            f"background: transparent; font-family: {T.FONT};"
        )
        ans_lay.addWidget(ans_title)
        ans_lay.addWidget(ans_text)
        lay.addWidget(self.answer_frame)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.toggle_btn = QPushButton("查看答案")
        self.toggle_btn.setFixedHeight(28)
        self.toggle_btn.setFixedWidth(110)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.setIcon(Icons.get("visibility", IconSize.SM))
        self._update_toggle_btn_style()
        self.toggle_btn.clicked.connect(self._toggle_answer)
        btn_row.addWidget(self.toggle_btn)
        btn_row.addStretch()
        lay.addLayout(btn_row)

    def _update_toggle_btn_style(self) -> None:
        color = T.INFO
        self.toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: {color}22; color: {color};
                border: 1px solid {color}66;
                border-radius: 14px;
                font-size: 12px; font-weight: 600;
                padding: 0 12px 0 8px; font-family: {T.FONT};
            }}
            QPushButton:hover  {{ background: {color}44; border-color: {color}; }}
            QPushButton:pressed {{ background: {color}66; }}
        """)

    def _toggle_answer(self) -> None:
        self._answer_visible = not self._answer_visible
        self.answer_frame.setVisible(self._answer_visible)
        if self._answer_visible:
            self.toggle_btn.setText("收起答案")
            self.toggle_btn.setIcon(Icons.get("visibility_off", IconSize.SM))
        else:
            self.toggle_btn.setText("查看答案")
            self.toggle_btn.setIcon(Icons.get("visibility", IconSize.SM))


# ── 分页导航条 ────────────────────────────────────────────────────────────────


class PaginationBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        self.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border-top: 1px solid {T.BORDER};
            }}
        """)

        self._current_page = 1
        self._total_pages = 1
        self._page_changed_cb = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(6)

        self._first_btn = self._mk_nav_btn("first_page", "第一页")
        self._prev_btn = self._mk_nav_btn("chevron_left", "上一页")

        self._page_info = QLabel("1 / 1")
        self._page_info.setFixedWidth(80)
        self._page_info.setAlignment(Qt.AlignCenter)
        self._page_info.setStyleSheet(
            f"color: {T.TEXT}; font-size: 13px; font-family: {T.FONT_MONO}; background: transparent;"
        )

        self._next_btn = self._mk_nav_btn("chevron_right", "下一页")
        self._last_btn = self._mk_nav_btn("last_page", "最后一页")

        jump_lbl = QLabel("跳转")
        jump_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 12px; background: transparent;"
        )
        self._jump_box = QLineEdit()
        self._jump_box.setFixedSize(46, 28)
        self._jump_box.setAlignment(Qt.AlignCenter)
        self._jump_box.setPlaceholderText("页")
        self._jump_box.setStyleSheet(f"""
            QLineEdit {{
                background: {_BASE}; border: 1px solid {T.BORDER};
                border-radius: 6px; color: {T.TEXT};
                font-size: 12px; font-family: {T.FONT_MONO};
                padding: 2px 4px;
            }}
            QLineEdit:focus {{ border-color: {_BORDER_FOCUS}; }}
        """)
        self._jump_box.returnPressed.connect(self._on_jump)

        size_lbl = QLabel("每页")
        size_lbl.setStyleSheet(
            f"color: {T.TEXT_DIM}; font-size: 12px; background: transparent;"
        )
        self._size_combo = QComboBox()
        self._size_combo.setFixedSize(62, 28)
        for s in [5, 10, 20, 50]:
            self._size_combo.addItem(str(s), s)
        self._size_combo.setCurrentIndex(1)
        self._size_combo.setStyleSheet(f"""
            QComboBox {{
                background: {_BASE}; border: 1px solid {T.BORDER};
                border-radius: 6px; color: {T.TEXT}; font-size: 12px;
                padding: 2px 6px; font-family: {T.FONT};
            }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
            QComboBox::down-arrow {{
                border-left: 3px solid transparent;
                border-right: 3px solid transparent;
                border-top: 4px solid {T.TEXT_DIM};
                margin: 3px;
            }}
            QComboBox QAbstractItemView {{
                background: {T.SURFACE}; color: {T.TEXT};
                selection-background-color: {T.INFO}22;
                border: 1px solid {T.BORDER};
            }}
        """)

        self._total_lbl = QLabel()
        self._total_lbl.setStyleSheet(
            f"color: {T.TEXT_MUTE}; font-size: 11px; background: transparent;"
        )

        lay.addWidget(self._first_btn)
        lay.addWidget(self._prev_btn)
        lay.addWidget(self._page_info)
        lay.addWidget(self._next_btn)
        lay.addWidget(self._last_btn)
        lay.addSpacing(12)
        lay.addWidget(jump_lbl)
        lay.addWidget(self._jump_box)
        lay.addSpacing(12)
        lay.addWidget(size_lbl)
        lay.addWidget(self._size_combo)
        lay.addStretch()
        lay.addWidget(self._total_lbl)

        self._first_btn.clicked.connect(lambda: self._go(1))
        self._prev_btn.clicked.connect(lambda: self._go(self._current_page - 1))
        self._next_btn.clicked.connect(lambda: self._go(self._current_page + 1))
        self._last_btn.clicked.connect(lambda: self._go(self._total_pages))

    def _mk_nav_btn(self, icon_name: str, tip: str) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(32, 28)
        btn.setToolTip(tip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setIcon(Icons.get(icon_name, IconSize.SM))
        btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {T.SURFACE}; color: {T.TEXT_DIM};
                        border: 1px solid {T.BORDER}; border-radius: 6px; font-size: 11px;
                    }}
                    QPushButton:hover {{ color: {T.INFO}; border-color: {_BORDER_FOCUS}; }}
                    QPushButton:disabled {{ color: {_DISABLED_TEXT}; border-color: {T.BORDER}; }}
                    QPushButton:pressed {{
                        background: {_PRESSED_TINT};
                        padding-top: 1px;
                        padding-left: 1px;
                    }}
                """)
        return btn

    def set_page_changed_callback(self, cb) -> None:
        self._page_changed_cb = cb

    def get_page_size(self) -> int:
        return self._size_combo.currentData()

    def connect_size_changed(self, cb) -> None:
        self._size_combo.currentIndexChanged.connect(lambda _: cb())

    def update(self, current: int, total: int, total_records: int) -> None:
        self._current_page = current
        self._total_pages = max(total, 1)
        self._page_info.setText(f"{current} / {self._total_pages}")
        self._total_lbl.setText(f"共 {total_records} 题")
        self._first_btn.setEnabled(current > 1)
        self._prev_btn.setEnabled(current > 1)
        self._next_btn.setEnabled(current < self._total_pages)
        self._last_btn.setEnabled(current < self._total_pages)

    def _go(self, page: int) -> None:
        page = max(1, min(page, self._total_pages))
        if page != self._current_page and self._page_changed_cb:
            self._page_changed_cb(page)

    def _on_jump(self) -> None:
        try:
            page = int(self._jump_box.text().strip())
            self._go(page)
        except ValueError:
            pass
        finally:
            self._jump_box.clear()


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

        root.addWidget(self._build_hero())
        root.addWidget(self._build_toolbar())
        root.addWidget(self._build_content(), stretch=1)
        root.addWidget(self._build_pagination())
        root.addWidget(self._build_statusbar())

    def _build_hero(self) -> QFrame:
        hero = QFrame()
        hero.setFixedHeight(148)
        hero.setStyleSheet(f"""
                    QFrame {{
                        background: qlineargradient(
                            x1:0, y1:0, x2:0, y2:1,
                            stop:0 {T.SURFACE},
                            stop:1 {_BASE}
                        );
                        border-bottom: 1px solid {T.BORDER};
                        border-radius: 0 0 {_RADIUS_LG}px {_RADIUS_LG}px;
                    }}
        """)
        lay = QVBoxLayout(hero)
        lay.setContentsMargins(28, 16, 28, 16)
        lay.setSpacing(12)

        title_row = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)

        title = QLabel("题库练习中心")
        title.setStyleSheet(
            f"font-size: 22px; font-weight: 900; color: {T.TEXT};"
            f"font-family: {T.FONT}; background: transparent;"
        )
        sub = QLabel("QUESTION BANK · PRACTICE MODE")
        sub.setStyleSheet(
            f"font-size: 10px; color: {T.INFO}; font-weight: 700;"
            f"letter-spacing: 3px; background: transparent; font-family: {T.FONT};"
        )
        col.addWidget(title)
        col.addWidget(sub)
        title_row.addLayout(col)
        title_row.addStretch()

        self._stats_container = QHBoxLayout()
        self._stats_container.setSpacing(10)
        self._stats_widget = QWidget()
        self._stats_widget.setStyleSheet("background: transparent;")
        self._stats_widget.setLayout(self._stats_container)
        title_row.addWidget(self._stats_widget)

        lay.addLayout(title_row)
        return hero

    def _build_toolbar(self) -> QFrame:
        bar = QFrame()
        bar.setFixedHeight(56)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border-bottom: 1px solid {T.BORDER};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(22, 0, 22, 0)
        lay.setSpacing(10)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  搜索题目关键词...")
        self.search_box.setFixedSize(210, 34)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._on_filter_changed)
        self.search_box.textChanged.connect(lambda: self._search_timer.start(400))

        cls_lbl = QLabel("分类")
        cls_lbl.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 12px;")
        self.cls_combo = QComboBox()
        self.cls_combo.setFixedSize(130, 34)
        self.cls_combo.addItem("全部分类", "")
        for (cls,) in self.db.fetchall(
            "SELECT DISTINCT classify FROM question_bank ORDER BY classify"
        ):
            self.cls_combo.addItem(cls, cls)
        self.cls_combo.currentIndexChanged.connect(self._on_filter_changed)

        lvl_lbl = QLabel("难度")
        lvl_lbl.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 12px;")
        self.lvl_combo = QComboBox()
        self.lvl_combo.setFixedSize(86, 34)
        self.lvl_combo.addItem("全部", "")
        for lvl in ["初级", "中级", "高级"]:
            self.lvl_combo.addItem(lvl, lvl)
        self.lvl_combo.currentIndexChanged.connect(self._on_filter_changed)

        sort_lbl = QLabel("排序")
        sort_lbl.setStyleSheet(f"color: {T.TEXT_DIM}; font-size: 12px;")
        self.sort_combo = QComboBox()
        self.sort_combo.setFixedSize(110, 34)
        for label, _ in _ORDER_OPTIONS:
            self.sort_combo.addItem(label)
        self.sort_combo.currentIndexChanged.connect(self._on_filter_changed)

        lay.addWidget(self.search_box)
        lay.addSpacing(4)
        lay.addWidget(cls_lbl)
        lay.addWidget(self.cls_combo)
        lay.addWidget(lvl_lbl)
        lay.addWidget(self.lvl_combo)
        lay.addWidget(sort_lbl)
        lay.addWidget(self.sort_combo)
        lay.addStretch()

        all_btn = ButtonFactory.primary(
            "全部题目", height=34, icon_name="list", icon_size=IconSize.SM
        )
        ref_btn = ButtonFactory.ghost(
            "刷新", height=34, icon_name="refresh", icon_size=IconSize.SM
        )
        ref_btn.setFixedSize(80, 34)
        all_btn.clicked.connect(self._show_all)
        ref_btn.clicked.connect(self.refresh)

        lay.addWidget(all_btn)
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
        self._content_layout.setContentsMargins(22, 18, 22, 18)
        self._content_layout.setSpacing(12)
        self._content_layout.addStretch()

        self._scroll.setWidget(self._content_widget)
        return self._scroll

    def _build_pagination(self) -> PaginationBar:
        self._pagination = PaginationBar()
        self._pagination.set_page_changed_callback(self._go_to_page)
        self._pagination.connect_size_changed(self._on_page_size_changed)
        return self._pagination

    def _build_statusbar(self) -> QLabel:
        self._status_bar = QLabel("正在加载题库...")
        self._status_bar.setFixedHeight(24)
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {T.SURFACE}; color: {T.TEXT_DIM};
            font-size: 11px; border-top: 1px solid {T.BORDER};
            font-family: {T.FONT};
        """)
        return self._status_bar

    # ── 数据查询 ──────────────────────────────────────────────────────────────

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
        self._update_status(len(rows), total_pages)

    def _render(self, rows: list, offset: int) -> None:
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not rows:
            empty = QLabel("🔍  没有找到符合条件的题目")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(
                f"color: {T.TEXT_DIM}; font-size: 15px; padding: 60px; background: transparent;"
            )
            self._content_layout.insertWidget(0, empty)
            return

        for i, (qid, cls, lvl, content, answer) in enumerate(rows):
            card = QuestionCard(qid, cls, lvl, content, answer, offset + i + 1)
            self._content_layout.insertWidget(i, card)

        QTimer.singleShot(50, lambda: self._scroll.verticalScrollBar().setValue(0))

    def _update_status(self, shown: int, total_pages: int) -> None:
        page_size = self._pagination.get_page_size()
        offset = (self._current_page - 1) * page_size
        end = min(offset + shown, self._total_records)
        if self._total_records == 0:
            self._status_bar.setText("无符合条件的题目")
        else:
            self._status_bar.setText(
                f"显示第 {offset + 1}–{end} 题，共 {self._total_records} 题  |  "
                f"第 {self._current_page}/{total_pages} 页  |  点击「查看答案」展开解析"
            )

    def _load_stats(self) -> None:
        while self._stats_container.count():
            item = self._stats_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total = self.db.fetchone("SELECT COUNT(*) FROM question_bank")[0] or 0
        easy = (
            self.db.fetchone("SELECT COUNT(*) FROM question_bank WHERE level='初级'")[0]
            or 0
        )
        mid = (
            self.db.fetchone("SELECT COUNT(*) FROM question_bank WHERE level='中级'")[0]
            or 0
        )
        hard = (
            self.db.fetchone("SELECT COUNT(*) FROM question_bank WHERE level='高级'")[0]
            or 0
        )
        cls_count = (
            self.db.fetchone("SELECT COUNT(DISTINCT classify) FROM question_bank")[0]
            or 0
        )

        for icon, val, lbl, color in [
            ("inventory", str(total), "总题数", T.INFO),
            ("looks_one", str(easy), "初级", T.SUCCESS),
            ("looks_two", str(mid), "中级", T.WARNING),
            ("looks_3", str(hard), "高级", T.YELLOW),
            ("category", str(cls_count), "分类", T.YELLOW),
        ]:
            self._stats_container.addWidget(StatBadge(icon, val, lbl, color))

    def _on_filter_changed(self) -> None:
        self._current_page = 1
        self._query_and_render()

    def _on_page_size_changed(self) -> None:
        self._current_page = 1
        self._query_and_render()

    def _go_to_page(self, page: int) -> None:
        self._current_page = page
        self._query_and_render()

    def _show_all(self) -> None:
        self.cls_combo.setCurrentIndex(0)
        self.lvl_combo.setCurrentIndex(0)
        self.sort_combo.setCurrentIndex(0)
        self.search_box.clear()
        self._current_page = 1
        self._query_and_render()

    def refresh(self) -> None:
        self._load_stats()
        self._current_page = 1
        self._query_and_render()
