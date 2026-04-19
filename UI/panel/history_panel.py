# UI/panel/history_panel.py
"""
历史记录与成长曲线面板（使用新组件库）。
"""

import json

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTextEdit,
    QFrame,
)

from UI.components import (
    T,
    ButtonFactory,
    ChartCard,
    GrowthChart,
    RadarChart,
    GLOBAL_QSS,
    combo_qss,
)
from UI.components.info.icon import Icons, IconSize


class HistoryPanel(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self._init_ui()

    def _init_ui(self) -> None:
        self.setStyleSheet(GLOBAL_QSS + combo_qss())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())

        content = QWidget()
        content.setStyleSheet(f"background: {T.BG};")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(26, 20, 26, 20)
        c_lay.setSpacing(18)

        c_lay.addLayout(self._build_charts())
        c_lay.addWidget(self._build_report(), stretch=1)
        layout.addWidget(content, stretch=1)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(58)
        header.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border-bottom: 1px solid {T.BORDER};
            }}
        """)
        lay = QHBoxLayout(header)
        lay.setContentsMargins(26, 0, 26, 0)
        lay.setSpacing(12)

        title_icon = QLabel()
        title_icon.setPixmap(Icons.colored_pixmap("query_stats", T.INFO, IconSize.MD))
        title = QLabel("成长实验室")
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 800; color: {T.TEXT}; font-family: {T.FONT};"
        )
        title_h = QHBoxLayout()
        title_h.setSpacing(8)
        title_h.addWidget(title_icon)
        title_h.addWidget(title)

        member_lbl = QLabel()
        member_lbl.setPixmap(Icons.colored_pixmap("group", T.TEXT_DIM, IconSize.SM))
        member_lbl.setFixedWidth(80)
        member_lbl.setStyleSheet("background: transparent;")

        self.student_combo = QComboBox()
        self.student_combo.setFixedSize(160, 34)

        sync_btn = ButtonFactory.solid(
            "同步数据", T.INFO, height=34, icon_name="sync", icon_size=IconSize.SM
        )
        sync_btn.setFixedWidth(110)
        sync_btn.clicked.connect(self._refresh)

        lay.addLayout(title_h)
        lay.addStretch()
        lay.addWidget(member_lbl)
        lay.addWidget(self.student_combo)
        lay.addWidget(sync_btn)

        self.student_combo.currentIndexChanged.connect(self._load_student_data)
        return header

    def _build_charts(self) -> QHBoxLayout:
        charts = QHBoxLayout()
        charts.setSpacing(16)

        # 折线图卡片
        growth_card = ChartCard(T.SCORE_TREND_BG)
        g_lay = QVBoxLayout(growth_card)
        g_lay.setContentsMargins(16, 14, 16, 14)
        g_title_h = QHBoxLayout()
        g_title_h.setSpacing(6)
        g_title_icon = QLabel()
        g_title_icon.setPixmap(
            Icons.colored_pixmap("trending_up", T.SCORE_TREND_MAIN, IconSize.SM)
        )
        g_title = QLabel("综合得分趋势")
        g_title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {T.SCORE_TREND_TITLE}; "
            f"background: transparent; font-family: {T.FONT};"
        )
        g_title_h.addWidget(g_title_icon)
        g_title_h.addWidget(g_title)
        g_title_h.addStretch()
        self.growth_chart = GrowthChart()
        g_lay.addLayout(g_title_h)
        g_lay.addWidget(self.growth_chart)

        # 雷达图卡片
        radar_card = ChartCard(T.ABILITY_BG)
        r_lay = QVBoxLayout(radar_card)
        r_lay.setContentsMargins(16, 14, 16, 14)
        r_title_h = QHBoxLayout()
        r_title_h.setSpacing(6)
        r_title_icon = QLabel()
        r_title_icon.setPixmap(
            Icons.colored_pixmap("radar", T.ABILITY_MAIN, IconSize.SM)
        )
        r_title = QLabel("最近能力维度")
        r_title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {T.ABILITY_TITLE}; "
            f"background: transparent; font-family: {T.FONT};"
        )
        r_title_h.addWidget(r_title_icon)
        r_title_h.addWidget(r_title)
        r_title_h.addStretch()
        self.radar_chart = RadarChart()
        r_lay.addLayout(r_title_h)
        r_lay.addWidget(self.radar_chart)

        charts.addWidget(growth_card, stretch=6)
        charts.addWidget(radar_card, stretch=4)
        return charts

    def _build_report(self) -> ChartCard:
        card = ChartCard(T.REVIEW_BG)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(8)

        title_h = QHBoxLayout()
        title_h.setSpacing(6)
        title_icon = QLabel()
        title_icon.setPixmap(
            Icons.colored_pixmap("article", T.REVIEW_MAIN, IconSize.SM)
        )
        title = QLabel("最近面试表现回顾")
        title.setStyleSheet(
            f"font-size: 13px; font-weight: 700; color: {T.REVIEW_TITLE}; "
            f"background: transparent; font-family: {T.FONT};"
        )
        title_h.addWidget(title_icon)
        title_h.addWidget(title)
        title_h.addStretch()

        self.report_view = QTextEdit()
        self.report_view.setReadOnly(True)
        self.report_view.setFrameShape(QFrame.NoFrame)
        self.report_view.setPlaceholderText("选择成员后查看详细历史面试反馈...")
        self.report_view.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {T.TEXT};
                font-size: 13px;
                border: none;
                font-family: {T.FONT};
                line-height: 1.7;
            }}
        """)

        lay.addLayout(title_h)
        lay.addWidget(self.report_view)
        return card

    # ── 数据逻辑 ──────────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        self.student_combo.blockSignals(True)
        self.student_combo.clear()
        rows = self.db.fetchall("SELECT id, name FROM student ORDER BY id DESC")
        for sid, name in rows:
            self.student_combo.addItem(name, sid)
        self.student_combo.blockSignals(False)
        if self.student_combo.count() > 0:
            self._load_student_data()

    def _load_student_data(self) -> None:
        sid = self.student_combo.currentData()
        if not sid:
            return

        sessions = self.db.fetchall(
            "SELECT id, overall_score, report, started_at "
            "FROM interview_session "
            "WHERE student_id=? AND status='finished' "
            "ORDER BY started_at",
            (sid,),
        )
        if not sessions:
            self.growth_chart.set_scores([])
            self.radar_chart.set_data({})
            self.report_view.setPlainText("暂无已完成的面试记录。")
            return

        scores = [s[1] for s in sessions if s[1] is not None]
        self.growth_chart.set_scores(scores)

        latest = sessions[-1]
        self.report_view.setMarkdown(latest[2] or "无报告内容")

        turns = self.db.fetchall(
            "SELECT scores FROM interview_turn "
            "WHERE session_id=? AND scores IS NOT NULL",
            (latest[0],),
        )
        if turns:
            dim_totals = {"技术": [], "逻辑": [], "深度": [], "表达": []}
            key_map = {
                "tech": "技术",
                "logic": "逻辑",
                "depth": "深度",
                "clarity": "表达",
            }
            for (sc_json,) in turns:
                sc = json.loads(sc_json)
                for k, cn in key_map.items():
                    if k in sc:
                        dim_totals[cn].append(sc[k])
            radar_data = {
                cn: round(sum(v) / len(v), 1) if v else 0
                for cn, v in dim_totals.items()
            }
            self.radar_chart.set_data(radar_data)
