"""
resume_submit_button.py
简历投递按钮组件

特性：
  1. 支持简历上传和投递状态管理
  2. 投递过程中显示加载动画
  3. 投递成功/失败的状态反馈
  4. 与面试引擎集成，投递后触发简历分析流程
"""

import os
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QMessageBox,
    QSizePolicy,
    QFileDialog,
    QProgressBar,
)
from ..ButtonFactory import ButtonFactory, T


# ══════════════════════════════════════════════════════════════════════════════
# 后台 Worker：处理简历上传和分析
# ══════════════════════════════════════════════════════════════════════════════


class ResumeSubmitWorker(QObject):
    """简历投递后台处理 Worker"""

    finished = Signal(dict)  # 投递结果
    error = Signal(str)  # 错误信息
    progress = Signal(int)  # 进度百分比

    def __init__(self, resume_path: str, student_name: str = ""):
        super().__init__()
        self.resume_path = resume_path
        self.student_name = student_name

    def run(self):
        """执行简历投递流程"""
        try:
            # 模拟进度更新
            for i in range(0, 101, 20):
                self.progress.emit(i)
                QThread.msleep(200)

            # 检查文件是否存在
            if not os.path.exists(self.resume_path):
                raise RuntimeError(f"简历文件不存在：{self.resume_path}")

            # 获取文件信息
            file_size = os.path.getsize(self.resume_path)
            file_name = os.path.basename(self.resume_path)

            # 模拟简历解析和分析
            # 实际项目中这里应该调用简历解析 API 或本地处理
            result = {
                "success": True,
                "file_name": file_name,
                "file_size": file_size,
                "student_name": self.student_name,
                "message": "简历投递成功，已触发 AI 分析流程",
                "analysis_triggered": True,
            }

            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# ResumeSubmitButton 组件
# ══════════════════════════════════════════════════════════════════════════════


class ResumeSubmitButton(QWidget):
    """
    简历投递按钮组件

    信号：
        - submit_clicked: 用户点击投递按钮
        - file_selected: 用户选择了简历文件，参数为文件路径
        - upload_finished: 简历上传/分析完成，参数为结果字典
        - upload_error: 上传/分析出错，参数为错误信息
        - analysis_started: 开始简历分析流程
    """

    # ── 信号定义 ──────────────────────────────────────────────────────────────
    submit_clicked = Signal()
    file_selected = Signal(str)  # file_path
    upload_finished = Signal(dict)  # result dict
    upload_error = Signal(str)  # error message
    analysis_started = Signal(str)  # resume_path
    status_changed = Signal(str)  # status message

    def __init__(self, parent=None, student_name: str = ""):
        super().__init__(parent)
        self.student_name = student_name
        self._resume_path: str | None = None
        self._is_uploading: bool = False
        self._is_analyzing: bool = False

        # Worker 线程
        self._worker_thread: QThread | None = None
        self._worker: ResumeSubmitWorker | None = None

        self._build_ui()
        self._set_state("idle")

    # ══════════════════════════════════════════════════════════════════════════
    # UI 构建
    # ══════════════════════════════════════════════════════════════════════════

    def _build_ui(self) -> None:
        """构建 UI 界面"""
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(10)

        # ── 文件信息展示区 ─────────────────────────────────────────────────────
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet(f"""
            QFrame {{
                background: {T.SURFACE};
                border: 1px solid {T.BORDER};
                border-radius: 8px;
            }}
        """)
        self.info_frame.setVisible(False)

        info_lay = QHBoxLayout(self.info_frame)
        info_lay.setContentsMargins(12, 8, 12, 8)
        info_lay.setSpacing(10)

        # 文件图标
        self.lbl_icon = QLabel("📄")
        self.lbl_icon.setStyleSheet("font-size: 20px;")
        info_lay.addWidget(self.lbl_icon)

        # 文件信息
        info_text_lay = QVBoxLayout()
        info_text_lay.setSpacing(2)

        self.lbl_file_name = QLabel("未选择文件")
        self.lbl_file_name.setStyleSheet(f"""
            color: {T.TEXT};
            font-size: 13px;
            font-weight: 600;
            font-family: {T.FONT};
        """)

        self.lbl_file_size = QLabel("")
        self.lbl_file_size.setStyleSheet(f"""
            color: {T.TEXT_DIM};
            font-size: 11px;
            font-family: {T.FONT};
        """)

        info_text_lay.addWidget(self.lbl_file_name)
        info_text_lay.addWidget(self.lbl_file_size)
        info_lay.addLayout(info_text_lay, stretch=1)

        # 移除文件按钮
        self.btn_remove = ButtonFactory.ghost("移除", height=28)
        self.btn_remove.setFixedWidth(60)
        self.btn_remove.clicked.connect(self._on_remove_file)
        info_lay.addWidget(self.btn_remove)

        main_lay.addWidget(self.info_frame)

        # ── 进度条（上传/分析中显示） ──────────────────────────────────────────
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background: {T.SURFACE};
                border: 1px solid {T.BORDER};
                border-radius: 4px;
                height: 6px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: {T.INFO};
                border-radius: 3px;
            }}
        """)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        main_lay.addWidget(self.progress_bar)

        # ── 状态标签 ───────────────────────────────────────────────────────────
        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet(f"""
            color: {T.TEXT_DIM};
            font-size: 12px;
            font-family: {T.FONT};
        """)
        self.lbl_status.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(self.lbl_status)

        # ── 控制按钮区 ─────────────────────────────────────────────────────────
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(10)

        # 选择文件按钮
        self.btn_select = ButtonFactory.solid(
            "选择简历", T.TEXT_DIM, height=42, width=120
        )
        self.btn_select.clicked.connect(self._on_select_file)
        btn_lay.addWidget(self.btn_select)

        # 投递按钮（主操作）
        self.btn_submit = ButtonFactory.solid("投递简历", T.INFO, height=42, width=120)
        self.btn_submit.setEnabled(False)
        self.btn_submit.clicked.connect(self._on_submit_clicked)
        btn_lay.addWidget(self.btn_submit)

        btn_lay.addStretch()
        main_lay.addLayout(btn_lay)

        # ── 提示信息 ───────────────────────────────────────────────────────────
        self.lbl_hint = QLabel("支持 PDF、DOC、DOCX 格式，最大 10MB")
        self.lbl_hint.setStyleSheet(f"""
            color: {T.TEXT_MUTE};
            font-size: 11px;
            font-family: {T.FONT};
        """)
        self.lbl_hint.setAlignment(Qt.AlignCenter)
        main_lay.addWidget(self.lbl_hint)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

    # ══════════════════════════════════════════════════════════════════════════
    # 交互逻辑
    # ══════════════════════════════════════════════════════════════════════════

    def _on_select_file(self) -> None:
        """选择简历文件"""
        if self._is_uploading:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择简历文件",
            "",
            "简历文件 (*.pdf *.doc *.docx);;PDF 文件 (*.pdf);;Word 文件 (*.doc *.docx);;所有文件 (*.*)",
        )

        if file_path:
            self._set_resume_file(file_path)

    def _set_resume_file(self, file_path: str) -> None:
        """设置简历文件"""
        self._resume_path = file_path
        self.file_selected.emit(file_path)

        # 更新 UI
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        size_str = self._format_file_size(file_size)

        self.lbl_file_name.setText(file_name)
        self.lbl_file_size.setText(f"大小: {size_str}")
        self.info_frame.setVisible(True)
        self.btn_submit.setEnabled(True)
        self.btn_select.setText("📁 更换简历")

        self.status_changed.emit(f"已选择: {file_name}")
        self._set_state("selected")

    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"

    def _on_remove_file(self) -> None:
        """移除已选择的文件"""
        if self._is_uploading:
            return

        self._resume_path = None
        self.lbl_file_name.setText("未选择文件")
        self.lbl_file_size.setText("")
        self.info_frame.setVisible(False)
        self.btn_submit.setEnabled(False)
        self.btn_select.setText("📁 选择简历")

        self.status_changed.emit("已移除简历文件")
        self._set_state("idle")

    def _on_submit_clicked(self) -> None:
        """投递按钮点击处理"""
        if not self._resume_path or self._is_uploading:
            return

        # 验证文件
        if not os.path.exists(self._resume_path):
            QMessageBox.critical(self, "投递失败", "简历文件不存在，请重新选择")
            return

        # 检查文件大小（最大 10MB）
        file_size = os.path.getsize(self._resume_path)
        if file_size > 10 * 1024 * 1024:
            QMessageBox.warning(self, "文件过大", "简历文件大小超过 10MB 限制")
            return

        self.submit_clicked.emit()
        self._start_upload()

    def _start_upload(self) -> None:
        """开始上传/分析流程"""
        self._is_uploading = True
        self._set_state("uploading")

        self.status_changed.emit("正在投递简历...")
        self.analysis_started.emit(self._resume_path)

        # 启动 Worker 线程
        self._stop_worker()
        self._worker_thread = QThread(self)
        self._worker = ResumeSubmitWorker(self._resume_path, self.student_name)
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_upload_finished)
        self._worker.error.connect(self._on_upload_error)

        # 清理连接
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.error.connect(self._worker_thread.quit)
        self._worker_thread.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._thread_finished)

        self._worker_thread.start()

    def _on_progress(self, value: int) -> None:
        """进度更新"""
        self.progress_bar.setValue(value)
        if value < 50:
            self.lbl_status.setText(f"正在上传... {value}%")
        elif value < 100:
            self.lbl_status.setText(f"正在解析简历... {value}%")
        else:
            self.lbl_status.setText("处理完成")

    def _on_upload_finished(self, result: dict) -> None:
        """上传/分析完成"""
        self._is_uploading = False
        self._set_state("success")

        self.upload_finished.emit(result)
        self.status_changed.emit("简历投递成功")

        # 显示成功提示
        QMessageBox.information(
            self,
            "投递成功",
            f"{result.get('message', '简历投递成功')}\n\n"
            f"文件名: {result.get('file_name', '-')}\n"
            f"候选人: {result.get('student_name', '-') or '未命名'}",
        )

    def _on_upload_error(self, error_msg: str) -> None:
        """上传/分析出错"""
        self._is_uploading = False
        self._set_state("error")

        self.upload_error.emit(error_msg)
        self.status_changed.emit(f"投递失败: {error_msg}")

        QMessageBox.critical(
            self, "投递失败", f"❌ 简历投递失败:\n{error_msg}\n\n请检查文件后重试。"
        )

    def _thread_finished(self) -> None:
        """线程结束清理"""
        self._worker = None
        self._worker_thread = None

    def _stop_worker(self) -> None:
        """停止 Worker 线程"""
        if self._worker_thread and self._worker_thread.isRunning():
            self._worker_thread.quit()
            # 不阻塞等待，让线程自行结束
        self._worker = None
        self._worker_thread = None

    # ══════════════════════════════════════════════════════════════════════════
    # 状态管理
    # ══════════════════════════════════════════════════════════════════════════

    def _set_state(self, state: str) -> None:
        """设置组件状态"""
        states = {
            "idle": {
                "select_enabled": True,
                "submit_enabled": False,
                "remove_enabled": True,
                "progress_visible": False,
                "info_visible": self._resume_path is not None,
            },
            "selected": {
                "select_enabled": True,
                "submit_enabled": True,
                "remove_enabled": True,
                "progress_visible": False,
                "info_visible": True,
            },
            "uploading": {
                "select_enabled": False,
                "submit_enabled": False,
                "remove_enabled": False,
                "progress_visible": True,
                "info_visible": True,
            },
            "success": {
                "select_enabled": True,
                "submit_enabled": True,
                "remove_enabled": True,
                "progress_visible": False,
                "info_visible": True,
            },
            "error": {
                "select_enabled": True,
                "submit_enabled": True,
                "remove_enabled": True,
                "progress_visible": False,
                "info_visible": True,
            },
        }

        config = states.get(state, states["idle"])

        self.btn_select.setEnabled(config["select_enabled"])
        self.btn_submit.setEnabled(config["submit_enabled"])
        self.btn_remove.setEnabled(config["remove_enabled"])
        self.progress_bar.setVisible(config["progress_visible"])
        self.info_frame.setVisible(config["info_visible"])

        if state == "idle":
            self.lbl_status.setText("")
            self.progress_bar.setValue(0)

    # ══════════════════════════════════════════════════════════════════════════
    # 公共接口
    # ══════════════════════════════════════════════════════════════════════════

    def set_student_name(self, name: str) -> None:
        """设置候选人姓名"""
        self.student_name = name

    def get_resume_path(self) -> str | None:
        """获取当前简历文件路径"""
        return self._resume_path

    def set_resume_path(self, path: str) -> None:
        """外部设置简历路径（用于加载已保存的简历）"""
        if os.path.exists(path):
            self._set_resume_file(path)

    def is_uploading(self) -> bool:
        """是否正在上传中"""
        return self._is_uploading

    def reset(self) -> None:
        """重置组件状态"""
        self._stop_worker()
        self._is_uploading = False
        self._resume_path = None
        self.lbl_file_name.setText("未选择文件")
        self.lbl_file_size.setText("")
        self.info_frame.setVisible(False)
        self.btn_submit.setEnabled(False)
        self.btn_select.setText("选择简历")
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.lbl_status.setText("")
        self._set_state("idle")

    # ══════════════════════════════════════════════════════════════════════════
    # 生命周期
    # ══════════════════════════════════════════════════════════════════════════

    def closeEvent(self, event) -> None:
        """清理资源"""
        self._stop_worker()
        super().closeEvent(event)
