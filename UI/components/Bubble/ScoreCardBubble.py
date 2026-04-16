# UI/components/ScoreCardBubble.py
"""
评分卡片气泡，在面试结束后展示各维度得分及改进建议。
依赖 eval_result 鸭子类型（含 tech/logic/depth/clarity/overall_score 和 suggestion）。

新增特性：
  - 入场动画：卡片从下方滑入并淡入
  - 分数递增：数字从 0 滚动增长到目标值
  - 建议延迟淡入：增强视觉层次感
"""

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import (
    Qt, QTimer, QPropertyAnimation,
    QRect, QEasingCurve, QParallelAnimationGroup
)
from PySide6.QtGui import QColor

from UI.components.info.Theme import T


class ScoreCardBubble(QFrame):
    def __init__(self, eval_result, parent=None, enable_animation: bool = True):
        super().__init__(parent)
        self.setFrameShape(QFrame.NoFrame)
        self._enable_animation = enable_animation
        self._eval_result = eval_result

        # 动画相关状态
        self._anim_group = None
        self._score_labels = []  # 存储分数标签用于递增动画
        self._overall_label = None

        outer = QHBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        card = QFrame()
        card.setObjectName("score_card")
        card.setStyleSheet(f"""
            QFrame#score_card {{
                background: {T.SURFACE2};
                border: 1px solid {T.NEON}22;
                border-left: 3px solid {T.NEON};
                border-radius: 12px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(T.NEON).darker(300))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)

        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(16, 14, 16, 14)
        card_lay.setSpacing(10)

        # ── 标题 ──────────────────────────────────────────────────────────────
        title = QLabel("📊  本题评估报告")
        title.setStyleSheet(
            f"font-weight: 700; font-size: 13px; color: {T.NEON};"
            f"font-family: {T.FONT}; background: transparent;"
        )
        card_lay.addWidget(title)

        # ── 得分行 ────────────────────────────────────────────────────────────
        scores_row = QHBoxLayout()
        scores_row.setSpacing(0)

        score_items = [
            ("技术", eval_result.tech_score, T.NEON),
            ("逻辑", eval_result.logic_score, T.PURPLE),
            ("深度", eval_result.depth_score, T.YELLOW),
            ("表达", eval_result.clarity_score, T.GREEN),
        ]
        for label, score, color in score_items:
            item_frame = QFrame()
            item_frame.setStyleSheet("background: transparent;")
            item_lay = QVBoxLayout(item_frame)
            item_lay.setContentsMargins(10, 6, 10, 6)
            item_lay.setSpacing(2)
            item_lay.setAlignment(Qt.AlignCenter)

            # 分数标签（用于递增动画）
            val_lbl = QLabel("0")  # 初始值为 0
            val_lbl.setAlignment(Qt.AlignCenter)
            val_lbl.setStyleSheet(
                f"font-size: 22px; font-weight: 900; color: {color};"
                f"font-family: {T.FONT_MONO}; background: transparent;"
            )
            name_lbl = QLabel(label)
            name_lbl.setAlignment(Qt.AlignCenter)
            name_lbl.setStyleSheet(
                f"font-size: 10px; color: {T.TEXT_DIM}; background: transparent;"
            )
            item_lay.addWidget(val_lbl)
            item_lay.addWidget(name_lbl)
            scores_row.addWidget(item_frame)

            # 记录标签和目标值，用于后续动画
            self._score_labels.append((val_lbl, score))

        # 分隔线
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {T.BORDER2}; background: {T.BORDER2};")
        sep.setFixedWidth(1)
        scores_row.addWidget(sep)

        # 综合得分
        overall_frame = QFrame()
        overall_frame.setStyleSheet(
            f"background: {T.GREEN}11; border-radius: 8px;"
        )
        overall_lay = QVBoxLayout(overall_frame)
        overall_lay.setContentsMargins(14, 8, 14, 8)
        overall_lay.setAlignment(Qt.AlignCenter)

        self._overall_label = QLabel("0.0")  # 初始值
        self._overall_label.setAlignment(Qt.AlignCenter)
        self._overall_label.setStyleSheet(
            f"font-size: 26px; font-weight: 900; color: {T.GREEN};"
            f"font-family: {T.FONT_MONO}; background: transparent;"
        )
        overall_name = QLabel("综合")
        overall_name.setAlignment(Qt.AlignCenter)
        overall_name.setStyleSheet(
            f"font-size: 10px; color: {T.GREEN}AA; background: transparent;"
        )
        overall_lay.addWidget(self._overall_label)
        overall_lay.addWidget(overall_name)
        scores_row.addWidget(overall_frame)

        card_lay.addLayout(scores_row)

        # ── 建议 ──────────────────────────────────────────────────────────────
        self._suggestion_label = None
        if eval_result.suggestion:
            self._suggestion_label = QLabel(f"💡  {eval_result.suggestion}")
            self._suggestion_label.setWordWrap(True)
            self._suggestion_label.setStyleSheet(f"""
                font-size: 12px; color: {T.TEXT_DIM};
                background: {T.SURFACE3};
                border-radius: 6px;
                padding: 8px 10px;
                font-family: {T.FONT};
            """)
            # 初始隐藏，等待动画触发
            if enable_animation:
                self._suggestion_label.setWindowOpacity(0.0)
            card_lay.addWidget(self._suggestion_label)

        outer.addWidget(card, stretch=9)
        outer.addStretch(1)

        # 如果启用动画，播放入场效果
        if enable_animation:
            # 延迟一帧确保布局计算完成
            QTimer.singleShot(0, self.play_entrance_animation)

    # ══════════════════════════════════════════════════════════════════════════
    # 动画系统
    # ══════════════════════════════════════════════════════════════════════════

    def play_entrance_animation(self):
        print("anime_play_in_scoreCard")
        """
        播放入场动画：上滑 + 淡入
        动画结束后自动触发分数递增和建议淡入
        """
        if not self._enable_animation:
            self._start_score_animation()
            return

        # 强制刷新确保几何信息正确
        self.show()
        self.setGeometry(self.geometry())

        target_geo = self.geometry()
        start_geo = QRect(
            target_geo.x(),
            target_geo.y() + 30,  # 起始位置下移 30px
            target_geo.width(),
            target_geo.height()
        )

        # 初始状态
        self.setGeometry(start_geo)
        self.setWindowOpacity(0.0)

        # 位移动画
        self._pos_anim = QPropertyAnimation(self, b"geometry", self)
        self._pos_anim.setDuration(220)
        self._pos_anim.setStartValue(start_geo)
        self._pos_anim.setEndValue(target_geo)
        self._pos_anim.setEasingCurve(QEasingCurve.OutCubic)

        # 透明度动画
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._opacity_anim.setDuration(220)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)

        # 并行执行
        self._anim_group = QParallelAnimationGroup(self)
        self._anim_group.addAnimation(self._pos_anim)
        self._anim_group.addAnimation(self._opacity_anim)
        self._anim_group.finished.connect(self._on_entrance_finished)
        self._anim_group.start()

    def _on_entrance_finished(self):
        """入场动画结束，触发后续动画"""
        self._start_score_animation()

    def _start_score_animation(self):
        """启动分数递增动画（带延迟错落效果）"""
        # 综合得分优先启动
        if self._overall_label and self._eval_result.overall_score is not None:
            self._animate_number(
                self._overall_label,
                0.0,
                float(self._eval_result.overall_score),
                duration=800,
                fmt="{:.1f}"
            )

        # 各维度分数延迟错落启动
        for i, (label, target) in enumerate(self._score_labels):
            QTimer.singleShot(
                150 + i * 100,  # 错落延迟：150ms + 每项间隔 100ms
                lambda l=label, t=target: self._animate_number(l, 0, t, duration=600)
            )

        # 建议文本延迟淡入
        if self._suggestion_label:
            QTimer.singleShot(
                400,  # 等待分数动画开始后淡入
                self._fade_in_suggestion
            )

    def _animate_number(self, label: QLabel, start: float, end: float,
                        duration: int = 600, fmt: str = "{:.0f}"):
        """
        数字递增动画
        :param label: 目标 QLabel
        :param start: 起始数值
        :param end: 目标数值
        :param duration: 动画时长(ms)
        :param fmt: 格式化字符串，如 "{:.1f}" 或 "{:.0f}"
        """
        anim = QPropertyAnimation(label, b"num_value", self)
        anim.setDuration(duration)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setEasingCurve(QEasingCurve.OutQuad)

        # 自定义属性更新回调
        def on_value_changed(val):
            label.setText(fmt.format(val))

        anim.valueChanged.connect(on_value_changed)
        anim.start()

    def _fade_in_suggestion(self):
        """建议文本淡入动画"""
        if not self._suggestion_label:
            return

        opacity_anim = QPropertyAnimation(
            self._suggestion_label, b"windowOpacity", self
        )
        opacity_anim.setDuration(300)
        opacity_anim.setStartValue(0.0)
        opacity_anim.setEndValue(1.0)
        opacity_anim.setEasingCurve(QEasingCurve.InOutQuad)
        opacity_anim.start()

    # ══════════════════════════════════════════════════════════════════════════
    # 公共接口
    # ══════════════════════════════════════════════════════════════════════════

    def skip_animation(self):
        """跳过所有动画，直接显示最终状态"""
        if self._anim_group and self._anim_group.state() == self._anim_group.Running:
            self._anim_group.stop()

        # 直接设置最终分数
        for label, target in self._score_labels:
            label.setText(str(target))
        if self._overall_label and self._eval_result.overall_score is not None:
            self._overall_label.setText(f"{self._eval_result.overall_score:.1f}")

        # 显示建议
        if self._suggestion_label:
            self._suggestion_label.setWindowOpacity(1.0)