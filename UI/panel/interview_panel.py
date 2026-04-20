"""
interview_panel.py
面试主界面（ChatArea 解耦重构版）。

架构说明：
  - Header 组件统一管理顶部工具栏
  - ChatArea 组件独立封装聊天渲染、滚动、Toast
  - Footer 组件统一管理 AsrButton + ChatInputBar
  - 面板仅负责信号路由、状态同步、面试会话编排，零耦合 UI 细节
"""

import json
import os

from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QMessageBox,QPushButton, QSplitter
)
from datetime import datetime


from UI.components import (
    T,ButtonFactory
)
from UI.components.footer import Footer
from UI.components.button import ResumeSubmitButton
from UI.components.interview_header import InterviewHeader
from UI.components.chat_area import ChatArea  # ✅ 引入解耦组件
from UI.components import apply_theme


# ══════════════════════════════════════════════════════════════════════════════
# InterviewWorker（保持不变）
# ══════════════════════════════════════════════════════════════════════════════
class InterviewWorker(QObject):
    request_start = Signal(str, int)
    request_start_with_resume = Signal(str, int, dict)
    request_answer = Signal(str)
    request_finish = Signal()
    request_resume_analysis = Signal(str, str, str, str)

    session_started = Signal(int)
    stream_chunk = Signal(str)
    eval_received = Signal(dict)
    is_finished_flag = Signal()
    all_finished = Signal()
    score_received = Signal(float)
    stream_done = Signal(str)
    error_occurred = Signal(str)
    resume_analysis_chunk = Signal(str)
    resume_analysis_finished = Signal(dict)

    PHASE_FIRST_Q = "first_q"
    PHASE_ANSWER = "answer"
    PHASE_REPORT = "report"

    def __init__(self, engine, db):
        super().__init__()
        self.engine = engine
        self.db = db
        self.session_id: int | None = None
        self._is_finished = False

    def on_start_requested(self, name: str, job_id: int):
        try:
            row = self.db.fetchone("SELECT id FROM student WHERE name=?", (name,))
            student_id = (
                row[0]
                if row
                else self.db.execute(
                    "INSERT INTO student (name, created_at) VALUES (?,?)",
                    (name, datetime.now().isoformat()),
                ).lastrowid
            )

            self.session_id = self.engine.start_session(student_id, job_id)
            self.session_started.emit(self.session_id)

            for token in self.engine.get_first_question_stream(self.session_id):
                self.stream_chunk.emit(token)
            self.stream_done.emit(self.PHASE_FIRST_Q)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def on_start_with_resume_requested(
        self, name: str, job_id: int, resume_evaluation: dict
    ):
        """带简历评价的会话启动"""
        print("带简历评价的会话启动")
        try:
            row = self.db.fetchone("SELECT id FROM student WHERE name=?", (name,))
            student_id = (
                row[0]
                if row
                else self.db.execute(
                    "INSERT INTO student (name, created_at) VALUES (?,?)",
                    (name, datetime.now().isoformat()),
                ).lastrowid
            )

            self.session_id = self.engine.start_session_with_resume(
                student_id, job_id, resume_evaluation
            )
            self.session_started.emit(self.session_id)

            for token in self.engine.get_first_question_stream(self.session_id):
                self.stream_chunk.emit(token)
            self.stream_done.emit(self.PHASE_FIRST_Q)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def on_answer_requested(self, answer: str):
        print(f"[on_answer_requested] 收到回答: {answer[:50]}...")
        if self.session_id is None:
            self.error_occurred.emit("Session not initialized")
            return
        try:
            self._is_finished = False
            print(f"[on_answer_requested] 调用 engine.submit_answer_stream")
            for token in self.engine.submit_answer_stream(self.session_id, answer):
                if token.startswith("__EVAL__:"):
                    self.eval_received.emit(
                        json.loads(token[len("__EVAL__:") :].strip())
                    )
                elif token == "__IS_FINISHED__\n":
                    self._is_finished = True
                    self.is_finished_flag.emit()
                elif token == "__FINISHED__\n":
                    self.all_finished.emit()
                    self.stream_done.emit(self.PHASE_ANSWER)
                    return
                elif token.startswith("__ERROR__:"):
                    self.error_occurred.emit(token[len("__ERROR__:") :].strip())
                    return
                else:
                    self.stream_chunk.emit(token)
            self.stream_done.emit(self.PHASE_ANSWER)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def on_finish_requested(self):
        if self.session_id is None:
            self.error_occurred.emit("Session not initialized")
            return
        try:
            overall_score = 0.0
            report_parts: list[str] = []
            for token in self.engine.finish_session_stream(self.session_id):
                if token.startswith("__SCORE__:"):
                    overall_score = float(token[len("__SCORE__:") :].strip())
                    self.score_received.emit(overall_score)
                else:
                    report_parts.append(token)
                    self.stream_chunk.emit(token)
            report_text = "".join(report_parts)
            self.engine.confirm_finish(self.session_id, overall_score, report_text)
            self.stream_done.emit(self.PHASE_REPORT)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def on_resume_analysis_requested(
        self,
        resume_path: str,
        job_name: str,
        job_description: str,
        required_skills: str,
    ):

        print("处理简历分析请求")
        """处理简历分析请求"""
        try:
            for token in self.engine.analyze_resume_stream(
                resume_path,
                job_name,
                job_description,
                required_skills,
            ):
                self.resume_analysis_chunk.emit(token)
        except Exception as e:
            self.error_occurred.emit(f"简历分析失败: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# 主面板
# ══════════════════════════════════════════════════════════════════════════════
class InterviewPanel(QWidget):
    def __init__(self, db, engine, parent=None):
        super().__init__(parent)
        self.db = db
        self.engine = engine
        self._session_id: int | None = None
        self._resume_path: str | None = None
        self._resume_evaluation: dict | None = None

        # 流式对话状态（仅保留业务标志位）
        self._is_streaming = False
        self._stream_phase = ""
        self._pending_is_finished = False

        # 面试 Worker
        self._worker = InterviewWorker(engine, db)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._bind_worker_signals()
        self._thread.start()

        self._build_ui()
        self._bind_footer_signals()

    # ══════════════════════════════════════════════════════════════════════════
    # 信号绑定（Worker & Footer）
    # ══════════════════════════════════════════════════════════════════════════
    def _bind_worker_signals(self) -> None:
        w = self._worker
        w.request_start.connect(w.on_start_requested)
        w.request_start_with_resume.connect(w.on_start_with_resume_requested)
        w.request_answer.connect(w.on_answer_requested)
        w.request_finish.connect(w.on_finish_requested)
        w.request_resume_analysis.connect(w.on_resume_analysis_requested)

        w.session_started.connect(self._on_session_started)
        w.stream_chunk.connect(self._on_chunk)
        w.eval_received.connect(self._on_eval_received)
        w.is_finished_flag.connect(self._on_is_finished_flag)
        w.all_finished.connect(self._on_all_finished)
        w.score_received.connect(self._on_score_received)
        w.stream_done.connect(self._on_stream_done)
        w.error_occurred.connect(self._on_error)
        w.resume_analysis_chunk.connect(self._on_resume_analysis_chunk)

    def _bind_footer_signals(self) -> None:
        self.footer.send_requested.connect(self._on_text_send)
        self.footer.asr_finished.connect(self._on_asr_transcript_ready)
        self.footer.status_changed.connect(self._update_status)
        self.footer.play_requested.connect(self._play_audio_file)
        self.footer.asr_error.connect(lambda e: QMessageBox.critical(self, "转写失败", e))
        self.footer.recording_started.connect(lambda: self._update_status("🎙 录音中..."))
        self.footer.recording_stopped.connect(lambda: self._update_status("录音完成"))

    def _build_ui(self) -> None:
        apply_theme(self)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        # ── 水平布局：Header(2) | 右侧容器(8) ──
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        self.header = InterviewHeader(self.db)
        self.header.start_clicked.connect(self._start_interview)
        self.header.finish_clicked.connect(self._finish_interview)
        self.header.resume_clicked.connect(self._on_resume_submit)
        h_layout.addWidget(self.header, stretch=2)  # 水平占比 2

        # 右侧容器（用于承载垂直布局）
        right_panel = QWidget()
        v_layout = QVBoxLayout(right_panel)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(8)

        self.chat_area = ChatArea()
        v_layout.addWidget(self.chat_area, stretch=7)  # 垂直占比 7

        self.footer = Footer(min_height=190, max_height=420)
        v_layout.addWidget(self.footer, stretch=3)  # 垂直占比 3

        h_layout.addWidget(right_panel, stretch=8)  # 水平占比 8

        root.addLayout(h_layout)

    # ══════════════════════════════════════════════════════════════════════════
    # 简历投递 & 分析（逻辑不变）
    # ══════════════════════════════════════════════════════════════════════════
    def _on_resume_submit(self) -> None:
        dialog = QFrame(self)
        dialog.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        dialog.setFixedSize(420, 300)
        dialog.setStyleSheet(f"""
            QFrame {{ background: {T.BG}; border: 1px solid {T.BORDER}; border-radius: 12px; }}
        """)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("投递简历")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; font-family: {T.FONT};")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        resume_widget = ResumeSubmitButton(student_name=self.header.candidate_name)
        resume_widget.file_selected.connect(lambda path: setattr(self, "_resume_path", path))
        resume_widget.upload_finished.connect(lambda res: self._on_resume_uploaded(res, dialog))
        resume_widget.upload_error.connect(lambda msg: self._update_status(f"简历投递失败: {msg}"))
        resume_widget.status_changed.connect(self._update_status)
        layout.addWidget(resume_widget)

        close_btn = ButtonFactory.ghost("关闭", height=36)
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        dialog.show()

    def _on_resume_uploaded(self, result: dict, dialog: QFrame) -> None:
        if result.get("success"):
            self._resume_path = result.get("file_path") or self._resume_path
            self.chat_area.add_system_message(f"📄 简历已投递: {result.get('file_name', '未知文件')}")
            self.chat_area.add_system_message("🤖 AI 正在分析简历内容，面试将更有针对性...")
            QTimer.singleShot(1500, dialog.close)
            self._trigger_resume_analysis()

    def _trigger_resume_analysis(self) -> None:
        if not self._resume_path: return
        job_name = self.header.selected_job_name
        self._set_loading(True, "正在分析简历...")
        self.chat_area.add_system_message("📊 开始分析简历内容...")
        self._worker.request_resume_analysis.emit(self._resume_path, job_name, "", "")

    def _on_resume_analysis_chunk(self, chunk: str) -> None:
        chunk_stripped = chunk.strip()
        if chunk_stripped.startswith("__RESUME_EVAL__:"):
            try:
                eval_json = chunk_stripped[len("__RESUME_EVAL__:"):].strip()
                self._resume_evaluation = json.loads(eval_json)
                self._on_resume_analysis_finished(self._resume_evaluation)
            except Exception:
                self._update_status("简历分析完成，可以开始面试")
            return
        if chunk_stripped.startswith("__ERROR__:"):
            self._update_status("简历分析完成，可以开始面试")
            self._set_loading(False)
            return
        if chunk_stripped and "正在调用" not in chunk_stripped and "⚙️" not in chunk_stripped:
            self.chat_area.add_system_message(chunk_stripped)

    def _on_resume_analysis_finished(self, evaluation: dict) -> None:
        self._set_loading(False)
        self._resume_evaluation = evaluation
        overall_score = evaluation.get("overall_score", "N/A")
        self.chat_area.add_system_message(f"📊 简历分析完成！综合评分：{overall_score}/10")

        dims = evaluation.get("dimensions", {})
        dim_lines = []
        for key, label in [("skill_match", "技能匹配"), ("project_depth", "项目经验"),
                           ("tech_breadth", "技术广度"), ("growth_potential", "成长潜力"),
                           ("resume_quality", "简历质量")]:
            if key in dims:
                dim_lines.append(f"{label} {dims[key].get('score', 'N/A')}/10")
        if dim_lines: self.chat_area.add_system_message(" | ".join(dim_lines))

        strengths = evaluation.get("strengths", [])
        if strengths: self.chat_area.add_system_message("✅ 优势：" + "；".join(strengths[:2]))
        concerns = evaluation.get("concerns", [])
        if concerns: self.chat_area.add_system_message("⚠️ 关注点：" + "；".join(concerns[:2]))
        suggested = evaluation.get("suggested_questions", [])
        if suggested: self.chat_area.add_system_message("💭 建议追问：" + suggested[0][:50] + "...")
        strategy = evaluation.get("interview_strategy", "")
        if strategy:
            self.chat_area.add_system_message("🎯 面试策略：" + strategy[:80] + "...")
            self.header.start_btn.setToolTip(f"面试策略：{strategy[:50]}...")
        self.chat_area.add_system_message("✨ 分析完成，请点击「开始面试」进入 AI 面试环节！")
        self._update_status("📊 简历分析完成，可以开始面试了")

    # ══════════════════════════════════════════════════════════════════════════
    # 输入提交 & Worker 信号处理
    # ══════════════════════════════════════════════════════════════════════════
    def _on_text_send(self, text: str) -> None:
        self._submit_answer(text)

    def _on_asr_transcript_ready(self, transcript: str) -> None:
        if not transcript or self._is_streaming: return
        self.footer.set_input_text(transcript)
        self._submit_answer(transcript)

    def _submit_answer(self, answer: str) -> None:
        answer = answer.strip()
        if not answer or self._is_streaming: return
        self.footer.clear_input()
        self.chat_area.add_user_message(answer)
        self._pending_is_finished = False
        self._stream_phase = InterviewWorker.PHASE_ANSWER
        self._is_streaming = True
        self.chat_area.show_typing_indicator()
        self._set_loading(True, "AI 正在思考...")
        self._set_input_enabled(False)
        self._worker.request_answer.emit(answer)

    def _on_session_started(self, session_id: int) -> None:
        self._session_id = session_id
        self._stream_phase = InterviewWorker.PHASE_FIRST_Q
        self._is_streaming = True
        self._set_input_enabled(False)
        self.chat_area.show_typing_indicator()
        self._set_loading(True, "AI 面试官正在出题...")

    def _on_chunk(self, chunk: str) -> None:
        self.chat_area.hide_typing_indicator()
        enable_tts = self._stream_phase in (InterviewWorker.PHASE_FIRST_Q, InterviewWorker.PHASE_ANSWER)
        self.chat_area.ensure_ai_bubble(enable_tts=enable_tts)
        self.chat_area.append_ai_chunk(chunk)

    def _on_eval_received(self, data: dict) -> None:
        class _FakeEval:
            def __init__(self, d):
                self.overall_score = d.get("overall_score", d.get("overall", 0))
                self.tech_score = d.get("tech_score", d.get("tech", 0))
                self.logic_score = d.get("logic_score", d.get("logic", 0))
                self.depth_score = d.get("depth_score", d.get("depth", 0))
                self.clarity_score = d.get("clarity_score", d.get("clarity", 0))
                self.suggestion = d.get("suggestion", d.get("comment", ""))

        self.chat_area.hide_typing_indicator()
        self.chat_area.add_score_message(_FakeEval(data))
        if self._is_streaming:
            self.chat_area.show_typing_indicator()

    def _on_is_finished_flag(self) -> None:
        self._pending_is_finished = True

    def _on_all_finished(self) -> None:
        self.chat_area.add_system_message("面试已结束，请点击「结束面试」查看报告。")
        self._update_status("题目已完成，请点击「结束面试」生成报告")
        self._set_input_enabled(False)

    def _on_score_received(self, score: float) -> None:
        self.chat_area.add_system_message(f"━━  综合得分：{score}/10  ━━")

    def _on_stream_done(self, phase: str) -> None:
        print(f"[_on_stream_done] phase={phase}, _pending_is_finished={self._pending_is_finished}")
        self.chat_area.stop_ai_stream()
        self._is_streaming = False

        if phase == InterviewWorker.PHASE_FIRST_Q:
            self._set_loading(False)
            self._set_input_enabled(True)
            self.header.set_interview_controls_enabled(finish=True)
            self.chat_area.add_system_message("面试已开始，加油！🚀")
        elif phase == InterviewWorker.PHASE_ANSWER:
            self._set_loading(False)
            if self._pending_is_finished:
                self._pending_is_finished = False
                self._set_input_enabled(False)
                self._update_status("题目已完成，请点击「结束面试」生成报告")
            else:
                self._set_input_enabled(True)
        elif phase == InterviewWorker.PHASE_REPORT:
            self._set_loading(False)
            self.chat_area.add_system_message("面试完成 ✓")
            self._update_status("面试完成 ✓")
            self.header.set_interview_controls_enabled(start=True, inputs=True)
            self._session_id = None
            self._set_input_enabled(True)

    def _on_error(self, msg: str) -> None:
        self.chat_area.hide_typing_indicator()
        self.chat_area.stop_ai_stream(force=True)
        self._is_streaming = False
        self._set_loading(False)
        self._set_input_enabled(True)
        self.header.set_interview_controls_enabled(start=True, inputs=True)
        QMessageBox.critical(self, "错误", f"发生错误：{msg}")

    # ══════════════════════════════════════════════════════════════════════════
    # 业务控制 & 辅助
    # ══════════════════════════════════════════════════════════════════════════
    def _start_interview(self) -> None:
        name = self.header.candidate_name
        if not name: return self._show_toast("请输入姓名")
        if self.header.job_combo.count() == 0 or self.header.selected_job_id is None:
            return self._show_toast("请选择岗位")

        job_id = self.header.selected_job_id
        self.header.set_interview_controls_enabled(start=False, inputs=False)
        self.chat_area.clear()

        if self._resume_evaluation:
            self._worker.request_start_with_resume.emit(name, job_id, self._resume_evaluation)
            self.chat_area.add_system_message("📝 已加载简历评价，面试将更有针对性")
        else:
            self._worker.request_start.emit(name, job_id)

    def _finish_interview(self) -> None:
        self._set_loading(True, "正在生成最终报告...")
        self._set_input_enabled(False)
        self.header.set_interview_controls_enabled(finish=False)
        self._stream_phase = InterviewWorker.PHASE_REPORT
        self._is_streaming = True
        self.chat_area.add_system_message("━━━━━━  面试结束，正在生成报告  ━━━━━━")
        self.chat_area.show_typing_indicator()
        self._worker.request_finish.emit()

    def _play_audio_file(self, audio_path: str) -> None:
        try:
            if os.name == "nt":
                os.startfile(audio_path)
            elif os.name == "posix":
                import subprocess;
                subprocess.Popen(["xdg-open", audio_path])
            else:
                QMessageBox.information(self, "播放", "当前系统不支持自动播放。")
        except Exception as e:
            QMessageBox.warning(self, "播放失败", f"无法播放音频文件：{e}")

    def _update_status(self, msg: str) -> None:
        self.header.set_status(msg)

    def _set_loading(self, loading: bool, msg: str = "") -> None:
        self.header.set_loading(loading, msg)

    def _set_input_enabled(self, enabled: bool) -> None:
        self.footer.set_enabled(enabled)

    def _show_toast(self, msg: str) -> None:
        self.header.show_toast(msg)

    def closeEvent(self, event) -> None:
        self.chat_area.stop_ai_stream(force=True)
        self.footer.close()
        try:
            if self._thread and self._thread.isRunning():
                self._thread.quit()
                if not self._thread.wait(1500):
                    self._thread.terminate()
                    self._thread.wait(300)
        except Exception:
            pass
        super().closeEvent(event)