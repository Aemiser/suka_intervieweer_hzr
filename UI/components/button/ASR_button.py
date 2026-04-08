"""
ASR_button.py
语音录制与转写按钮组件
特性：
  1. 录音时明确分离「停止录音」与「取消录音」按钮
  2. 录音失败自动重置 UI，支持立即重试
  3. 停止录音增加 3 秒超时保护，彻底杜绝 UI 卡死
"""

import os
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QSizePolicy
)
from service.voice_sdk.audio.recorder import VoiceRecorder
from service.voice_sdk.stt.client import STTClient
from service.voice_sdk.models import RecordBundle, VoiceResult  # 补充 VoiceResult
from ..ButtonFactory import ButtonFactory, T


# ══════════════════════════════════════════════════════════════════════════════
# 后台 Worker（保持不变）
# ══════════════════════════════════════════════════════════════════════════════

class VoiceWorker(QObject):
    finished = Signal(object)   # RecordBundle
    error    = Signal(str)

    def __init__(self):
        super().__init__()
        self.recorder = VoiceRecorder()

    def stop(self): self.recorder.stop()
    def cancel(self): self.recorder.cancel()

    def run(self):
        try:
            audio_path, duration = self.recorder.record(60)
            if not audio_path or duration <= 0:
                raise RuntimeError("录音路径或时长无效")
            if not os.path.exists(audio_path):
                raise RuntimeError(f"录音文件不存在：{audio_path}")
            if os.path.getsize(audio_path) < 1000:
                raise RuntimeError("录音文件过小，可能未成功捕获音频")

            self.finished.emit(RecordBundle(
                transcript="", audio_path=audio_path, duration=duration,
                emotion="流畅", compressed_audio_file="", non_speech=False,
            ))
        except Exception as e:
            self.error.emit(str(e))


class ASRWorker(QObject):
    finished = Signal(object)   # VoiceResult
    error    = Signal(str)

    def __init__(self, audio_path: str):
        super().__init__()
        self.audio_path = audio_path

    def run(self):
        try:
            self.finished.emit(STTClient().analyze(self.audio_path))
        except Exception as e:
            self.error.emit(str(e))


# ══════════════════════════════════════════════════════════════════════════════
# AsrButton 组件（重构版）
# ══════════════════════════════════════════════════════════════════════════════

class AsrButton(QWidget):
    # ── 信号定义 ──────────────────────────────────────────────────────────────
    recording_started = Signal()
    recording_stopped = Signal()
    recording_error   = Signal(str)

    audio_recorded    = Signal(object)  # RecordBundle
    asr_started       = Signal()
    asr_finished      = Signal(str)
    asr_error         = Signal(str)

    play_requested    = Signal(str)     # audio_path
    bundle_sent       = Signal(object)  # RecordBundle
    status_changed    = Signal(str)

    def _debug_btn_state(self, label: str = "") -> None:
        """🔥 暴力打印按钮所有关键状态，直接复制粘贴用"""
        for name, btn in [
            ("btn_start", getattr(self, "btn_start", None)),
            ("btn_stop", getattr(self, "btn_stop", None)),
            ("btn_cancel", getattr(self, "btn_cancel", None)),
        ]:
            if btn is None:
                print(f"[{label}] {name} = None ❌")
                continue
            print(f"\n[{label}] {name} ({type(btn).__name__}):")
            print(f"  • isEnabled()      : {btn.isEnabled()}")
            print(f"  • isVisible()      : {btn.isVisible()}")
            print(f"  • text()           : {btn.text()}")
            print(f"  • isVisibleTo(self): {btn.isVisibleTo(self)}")
            print(f"  • underMouse()     : {btn.underMouse()}")
            print(f"  • hasFocus()       : {btn.hasFocus()}")
            print(f"  • isActiveWindow() : {btn.isActiveWindow()}")
            # 样式表原始内容（排查 :disabled 是否生效）
            style = btn.styleSheet()
            if ":disabled" in style:
                print(f"  • :disabled 样式   : ✅ 已定义")
            else:
                print(f"  • :disabled 样式   : ❌ 未定义 ⚠️")
            # 直接尝试调用 setEnabled 看是否报错
            try:
                btn.setEnabled(btn.isEnabled())  # 设为当前值，测试方法是否存在
                print(f"  • setEnabled() 调用: ✅ 成功")
            except AttributeError as e:
                print(f"  • setEnabled() 调用: ❌ 报错 -> {e}")
            except Exception as e:
                print(f"  • setEnabled() 调用: ❌ 异常 -> {e}")
            print(f"  • parent enabled   : {btn.parent().isEnabled() if btn.parent() else 'N/A'}")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_recording       = False
        self._is_asr_processing  = False
        self._pending_bundle     = None
        self._auto_transcribe    = False
        self._stop_timeout_timer = QTimer(self)  # 超时保护定时器
        self._stop_timeout_timer.setSingleShot(True)  # 改为单次触发更安全
        self._stop_timeout_timer.timeout.connect(self._force_reset_on_timeout)  # 🔑 关键补充

        self._voice_thread: QThread | None = None
        self._voice_worker: VoiceWorker | None = None
        self._asr_thread: QThread | None = None
        self._asr_worker: ASRWorker | None = None

        self._build_ui()
        self._set_state("idle")

    # ══════════════════════════════════════════════════════════════════════════
    # UI 构建（分离开始/停止/取消按钮）
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self) -> None:
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(8)

        # 控制行
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        # 1. 初始/空闲状态按钮
        self.btn_start = ButtonFactory.solid("🎤 语音", T.PURPLE, height=48, width=90)
        self.btn_start.clicked.connect(self._start_recording)

        # 2. 录音中：停止按钮
        self.btn_stop = ButtonFactory.solid("⏹ 停止录音", T.NEON, height=48, width=100)
        self.btn_stop.setVisible(False)
        self.btn_stop.clicked.connect(self._stop_recording)

        # 3. 录音中：取消按钮
        self.btn_cancel = ButtonFactory.solid("❌ 取消", T.ACCENT, height=48, width=80)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self._cancel_recording)

        ctrl_row.addWidget(self.btn_start)
        ctrl_row.addWidget(self.btn_stop)
        ctrl_row.addWidget(self.btn_cancel)
        main_lay.addLayout(ctrl_row)

        # 预览控制栏（默认隐藏）
        self.preview_frame = QFrame()
        self.preview_frame.setStyleSheet(f"QFrame {{ background: {T.SURFACE}; border: 1px solid {T.BORDER}; border-radius: 8px; }}")
        self.preview_frame.setVisible(False)
        vp_lay = QHBoxLayout(self.preview_frame)
        vp_lay.setContentsMargins(8, 4, 8, 4)
        vp_lay.setSpacing(8)

        self.lbl_preview = QLabel("")
        self.lbl_preview.setStyleSheet(f"color: {T.TEXT}; font-size:12px;")
        self.lbl_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.btn_play = ButtonFactory.solid("▶ 播放", T.TEXT_DIM, height=30, width=80)
        self.btn_play.setVisible(False)
        self.btn_play.clicked.connect(self._on_play_clicked)

        self.btn_transcribe = ButtonFactory.solid("转文字", T.GREEN, height=30, width=80)
        self.btn_transcribe.clicked.connect(self._on_transcribe_clicked)

        self.btn_send = ButtonFactory.solid("发送", T.NEON, height=30, width=80)
        self.btn_send.clicked.connect(self._on_send_clicked)

        self.btn_clear = ButtonFactory.solid("清除", T.ACCENT, height=30, width=80)
        self.btn_clear.clicked.connect(self._on_clear_preview)

        vp_lay.addWidget(self.lbl_preview)
        vp_lay.addWidget(self.btn_play)
        vp_lay.addWidget(self.btn_transcribe)
        vp_lay.addWidget(self.btn_send)
        vp_lay.addWidget(self.btn_clear)
        main_lay.addWidget(self.preview_frame)

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        QTimer.singleShot(100, lambda: self._debug_btn_state("INIT"))  # 延迟确保布局完成

    # ══════════════════════════════════════════════════════════════════════════
    # 交互逻辑（明确的状态流转）
    # ══════════════════════════════════════════════════════════════════════════

    def _start_recording(self) -> None:
        if self._is_asr_processing: return
        self._clear_pending_bundle()
        self._is_recording = True

        # 切换 UI 状态
        self.btn_start.setEnabled(False)  # ← 补上
        self.btn_start.setVisible(False)
        self.btn_stop.setEnabled(True)
        self.btn_stop.setVisible(True)
        self.btn_stop.setText("⏹ 停止录音")
        self.btn_cancel.setEnabled(True)
        self.btn_cancel.setVisible(True)

        self.status_changed.emit("录音中... 点击停止或取消")
        self.recording_started.emit()
        self._start_voice_thread()
        self._debug_btn_state("start_recording")
    def _stop_recording(self) -> None:
        if not self._is_recording:
            print("[WARN] 停止按钮点击失败：当前未在录音")
            return

        if self._voice_worker:
            try:
                self._voice_worker.stop()
            except Exception as e:
                print(f"[WARN] stop 调用异常: {e}")

        self.btn_stop.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.btn_stop.setText("⏳ 处理中...")
        self.status_changed.emit("正在结束录音...")
        self._stop_timeout_timer.start(3000)
        self._debug_btn_state("stop_recording")

    def _cancel_recording(self) -> None:
        if not self._is_recording:
            print("[WARN] 取消按钮点击失败：当前未在录音")
            return

        if self._voice_worker:
            try:
                self._voice_worker.cancel()
            except Exception as e:
                print(f"[WARN] cancel 调用异常: {e}")

        self._stop_timeout_timer.stop()
        self._reset_to_idle_state()
        self.status_changed.emit("已取消录音，可立即重试")
        self._debug_btn_state("cancel_recording")

    def _force_reset_on_timeout(self) -> None:
        """超时兜底：强制终止线程并恢复 UI"""
        print("[WARN] 录音停止超时，强制重置状态机")
        self._stop_thread("_voice_thread", "_voice_worker", stop_worker=True)
        self._reset_to_idle_state()
        self.status_changed.emit("录音超时已强制结束，请重试")
        self._debug_btn_state("force_reset_on_timeout")

    def _on_voice_result(self, bundle: object) -> None:
        self._stop_timeout_timer.stop()
        self._reset_to_idle_state()

        self._pending_bundle = bundle
        self.recording_stopped.emit()

        self.lbl_preview.setText(f"语音条：{bundle.duration:.1f}s")
        self.lbl_preview.setToolTip(f"文件：{os.path.basename(bundle.audio_path)}")
        self.preview_frame.setVisible(True)
        self.btn_play.setVisible(True)
        self._set_preview_buttons_enabled(True)

        self.status_changed.emit("录音完成：可播放、转文字、发送或清除")
        self.audio_recorded.emit(bundle)

    def _on_voice_error(self, err: str) -> None:
        self._stop_timeout_timer.stop()
        self._is_recording = False  # 🔑 先重置状态
        self._reset_to_idle_state()  # 🔑 再恢复 UI
        self.status_changed.emit("录音失败，可立即重试")
        self.recording_error.emit(err)
        self._debug_btn_state("voice_error")
        # 弹窗放在最后，避免阻塞状态恢复
        QMessageBox.critical(
            self, "语音输入失败",
            f"{err}\n\n请检查麦克风权限或设备占用后重试。"
        )

    # 预览区操作
    def _on_play_clicked(self) -> None:
        if not self._pending_bundle or not os.path.exists(self._pending_bundle.audio_path):
            QMessageBox.warning(self, "播放失败", "未找到语音文件。")
            return
        self.play_requested.emit(self._pending_bundle.audio_path)

    def _on_transcribe_clicked(self) -> None:
        if not self._pending_bundle or self._is_asr_processing: return
        if not os.path.exists(self._pending_bundle.audio_path):
            QMessageBox.warning(self, "转文字失败", "录音文件不存在")
            return
        self._auto_transcribe = False
        self._start_asr_thread()

    def _on_send_clicked(self) -> None:
        if not self._pending_bundle or self._is_asr_processing: return
        self._auto_transcribe = True
        self.bundle_sent.emit(self._pending_bundle)
        self._start_asr_thread()

    def _on_clear_preview(self) -> None:
        self._clear_pending_bundle()
        self.status_changed.emit("已清除录音")

    def _on_asr_result(self, result: object) -> None:
        self._is_asr_processing = False
        self._set_preview_buttons_enabled(True)

        transcript = (result.transcript or "").strip()
        if transcript and not transcript.startswith("[未检测到语音内容]"):
            self.status_changed.emit("转写完成" if not self._auto_transcribe else "语音已发送，AI 正在处理...")
            self.asr_finished.emit(transcript)
            if self._auto_transcribe: self._clear_pending_bundle()
        else:
            msg = "未识别到有效语音，请重试"
            self.status_changed.emit(msg)
            if self._auto_transcribe:
                QMessageBox.warning(self, "发送失败", msg)
            self.asr_finished.emit("")

    def _on_asr_error(self, err: str) -> None:
        self._is_asr_processing = False
        self._set_preview_buttons_enabled(True)
        self.status_changed.emit("转文字失败")
        self.asr_error.emit(err)
        QMessageBox.critical(self, "转文字失败", err)

    # ══════════════════════════════════════════════════════════════════════════
    # 状态与线程管理
    # ══════════════════════════════════════════════════════════════════════════

    def _set_state(self, state: str) -> None:
        if state == "idle":
            self._set_preview_buttons_enabled(True)
        elif state == "processing":
            self.btn_transcribe.setEnabled(False)
            self.btn_send.setEnabled(False)
            self.btn_clear.setEnabled(False)

    def _set_preview_buttons_enabled(self, enabled: bool) -> None:
        self.btn_transcribe.setEnabled(enabled)
        self.btn_send.setEnabled(enabled)
        self.btn_clear.setEnabled(enabled)

    def _reset_to_idle_state(self) -> None:
        self._is_recording = False
        self._is_asr_processing = False

        # ✅ 先 setEnabled，再 setVisible，顺序很重要
        self.btn_start.setEnabled(True)
        self.btn_start.setVisible(True)

        self.btn_stop.setText("⏹ 停止录音")
        self.btn_stop.setEnabled(True)
        self.btn_stop.setVisible(False)

        self.btn_cancel.setEnabled(True)
        self.btn_cancel.setVisible(False)

        self._stop_timeout_timer.stop()

    def _start_voice_thread(self) -> None:
        # 先安全清理可能残留的旧线程
        self._stop_thread("_voice_thread", "_voice_worker", stop_worker=True)

        self._voice_thread = QThread(self)
        self._voice_worker = VoiceWorker()
        self._voice_worker.moveToThread(self._voice_thread)

        self._voice_thread.started.connect(self._voice_worker.run)
        self._voice_worker.finished.connect(self._on_voice_result)
        self._voice_worker.error.connect(self._on_voice_error)

        # 异步清理，绝不阻塞主线程
        self._voice_worker.finished.connect(self._voice_thread.quit)
        self._voice_worker.error.connect(self._voice_thread.quit)
        self._voice_thread.finished.connect(self._voice_worker.deleteLater)
        self._voice_thread.finished.connect(self._voice_thread.deleteLater)

        self._voice_thread.start()

    def _start_asr_thread(self) -> None:
        self._is_asr_processing = True
        self._set_state("processing")
        self.status_changed.emit("正在转文字，请稍候...")
        self.asr_started.emit()

        self._stop_thread("_asr_thread", "_asr_worker", stop_worker=False)
        self._asr_thread = QThread(self)
        self._asr_worker = ASRWorker(self._pending_bundle.audio_path)
        self._asr_worker.moveToThread(self._asr_thread)

        self._asr_thread.started.connect(self._asr_worker.run)
        self._asr_worker.finished.connect(self._on_asr_result)
        self._asr_worker.error.connect(self._on_asr_error)
        self._asr_worker.finished.connect(self._asr_thread.quit)
        self._asr_worker.error.connect(self._asr_thread.quit)
        self._asr_thread.finished.connect(self._asr_worker.deleteLater)
        self._asr_thread.finished.connect(self._asr_thread.deleteLater)
        self._asr_thread.start()

    def _stop_thread(self, thread_attr: str, worker_attr: str, stop_worker: bool = False) -> None:
        thread = getattr(self, thread_attr, None)
        worker = getattr(self, worker_attr, None)

        # 1. 尝试通知 Worker 停止
        if stop_worker and worker:
            for m in ("stop", "cancel"):
                fn = getattr(worker, m, None)
                if callable(fn):
                    try:
                        fn()
                    except:
                        pass

        # 2. 安全清理 QThread（防 C++ 对象已删除导致的 RuntimeError）
        if thread is not None:
            try:
                if thread.isRunning():
                    thread.quit()
                    # ⚠️ 移除 thread.wait()！在主线程调用 wait() 会阻塞 UI，
                    # 依赖 finished 信号 + deleteLater() 异步清理即可。
            except RuntimeError:
                # PySide6 常见现象：deleteLater() 已调度，C++ 对象被回收
                pass
            # 同步断开 Python 引用，防止重复触发
            setattr(self, thread_attr, None)

        setattr(self, worker_attr, None)

    def _clear_pending_bundle(self) -> None:
        if self._pending_bundle:
            path = self._pending_bundle.audio_path
            if os.path.exists(path):
                try: os.remove(path)
                except: pass
        self._pending_bundle = None
        self.preview_frame.setVisible(False)
        self.lbl_preview.setText("")
        self.btn_play.setVisible(False)
        self._set_preview_buttons_enabled(True)

    def closeEvent(self, event) -> None:
        self._stop_timeout_timer.stop()
        self._stop_thread("_voice_thread", "_voice_worker", stop_worker=True)
        self._stop_thread("_asr_thread", "_asr_worker", stop_worker=False)
        super().closeEvent(event)