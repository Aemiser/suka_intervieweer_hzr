import base64
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
import wave

import numpy as np
import requests
import sounddevice as sd
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, validator

load_dotenv()

RECORD_CONFIG = {
    "samplerate": 16000,
    "channels": 1,
    "dtype": "int16",
    "format": "wav",  
}

ALIYUN_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
ALIYUN_API_URL = "https://bailian.aliyuncs.com/v1/audio/speech/recognition"

VALID_EMOTIONS = {"自信", "紧张", "迟疑", "流畅", "混乱"}


class VoiceResult(BaseModel):
    transcript: str
    emotion: str
    emotion_detail: str = ""

    @validator("emotion")
    def validate_emotion(cls, v):
        if v not in VALID_EMOTIONS:
            raise ValueError(f"情绪标签必须是：{', '.join(sorted(VALID_EMOTIONS))}, 但得到：{v}")
        return v


class VoiceRecorder:
    """音频录制类，支持最长 60 秒、取消、立即发送（中断）"""

    def __init__(self):
        self.temp_dir = os.path.abspath(os.path.join(os.getcwd(), "temp_audio"))
        os.makedirs(self.temp_dir, exist_ok=True)
        self.temp_file = None

        self._frames = []
        self._recording = False
        self._stop_event = threading.Event()
        self._cancel_event = threading.Event()

    def record(self, duration: int = 60) -> str:
        """录制语音最长60秒，可在外部调用 stop() 立即结束。"""
        if duration <= 0 or duration > 60:
            raise ValueError("录音时长必须在1-60秒之间")

        self._frames = []
        self._stop_event.clear()
        self._cancel_event.clear()
        out_wav = os.path.join(self.temp_dir, f"rec_{uuid.uuid4()}.wav")

        self._recording = True

        def callback(indata, frames, time_info, status):
            if status and not status == sd.CallbackFlags.none:
                # 忽略偶发状态
                pass

            if self._cancel_event.is_set():
                raise sd.CallbackAbort
            if self._stop_event.is_set():
                raise sd.CallbackStop

            self._frames.append(indata.copy())

        try:
            with sd.InputStream(
                samplerate=RECORD_CONFIG["samplerate"],
                channels=RECORD_CONFIG["channels"],
                dtype=RECORD_CONFIG["dtype"],
                callback=callback,
            ):
                start = time.time()
                while time.time() - start < duration:
                    if self._cancel_event.is_set():
                        break
                    if self._stop_event.is_set():
                        break
                    time.sleep(0.05)
                self._stop_event.set()
        except sd.CallbackAbort:
            self._recording = False
            raise RuntimeError("录音已取消")
        except Exception as e:
            self._recording = False
            raise RuntimeError("麦克风录制失败，请检查设备是否连接：" + str(e))

        self._recording = False

        if self._cancel_event.is_set():
            raise RuntimeError("录音已取消")

        if not self._frames:
            raise RuntimeError("未获取到录音数据，请重试")

        audio_data = np.concatenate(self._frames, axis=0)

        # 自动检测录音音量
        rms = np.sqrt(np.mean(audio_data.astype('float64') ** 2))
        if rms < 0.01:
            raise RuntimeError("录音音量太低，请靠近麦克风重试")

        with wave.open(out_wav, "wb") as wf:
            wf.setnchannels(RECORD_CONFIG["channels"])
            wf.setsampwidth(2)
            wf.setframerate(RECORD_CONFIG["samplerate"])
            wf.writeframes((audio_data * 32767).astype('int16').tobytes())

        self.temp_file = out_wav
        return self.temp_file

    def _try_convert_wav_to_mp3(self, wav_path: str, mp3_path: str) -> bool:
        try:
            from pydub import AudioSegment

            audio = AudioSegment.from_wav(wav_path)
            audio.export(mp3_path, format="mp3")
            return True
        except Exception:
            # 尝试本地 ffmpeg
            if shutil.which("ffmpeg"):
                try:
                    subprocess.run(
                        [
                            "ffmpeg",
                            "-y",
                            "-i",
                            wav_path,
                            "-codec:a",
                            "libmp3lame",
                            "-qscale:a",
                            "2",
                            mp3_path,
                        ],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    return True
                except Exception:
                    return False
    def stop(self):
        if self._recording:
            self._stop_event.set()

    def cancel(self):
        if self._recording:
            self._cancel_event.set()

    def clean_temp(self):
        """清理临时音频文件，异常不中断程序流程"""
        # 清理当前会话的临时文件
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.remove(self.temp_file)
                self.temp_file = None
            except OSError as e:
                # 日志记录但不抛出异常，防止影响程序流
                pass

        # 清理临时目录中的旧文件（超过50个或超过1小时未修改的文件）
        try:
            if os.path.exists(self.temp_dir):
                files = [
                    os.path.join(self.temp_dir, f)
                    for f in os.listdir(self.temp_dir)
                    if f.startswith("rec_") and f.endswith(".wav")
                ]
                
                # 如果文件过多，删除最旧的文件
                if len(files) > 50:
                    files_with_time = [
                        (f, os.path.getmtime(f)) for f in files
                    ]
                    files_with_time.sort(key=lambda x: x[1])
                    # 保留最新的50个文件
                    for f, _ in files_with_time[:-50]:
                        try:
                            os.remove(f)
                        except OSError:
                            pass
                
                # 删除超过1小时未修改的文件
                current_time = time.time()
                for f in files:
                    try:
                        if current_time - os.path.getmtime(f) > 3600:  # 1小时
                            os.remove(f)
                    except OSError:
                        pass
        except Exception:
            # 目录清理失败不影响程序
            pass


class STTClient:
    """阿里云百炼ASR API调用客户端，集成情绪分析"""

    def __init__(self):
        if not ALIYUN_API_KEY:
            raise RuntimeError("缺少环境变量：DASHSCOPE_API_KEY")

        self.headers = {
            "Authorization": f"Bearer {ALIYUN_API_KEY}",
            "Content-Type": "application/json",
        }

    def _call_asr_api(self, audio_path: str) -> dict:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"音频文件不存在：{audio_path}")

        with open(audio_path, "rb") as f:
            audio_bytes = f.read()

        # 直接使用 WAV 格式
        audio_format = "wav"
        audio_content = base64.b64encode(audio_bytes).decode("utf-8")

        payload = {
            "model": "qwen3-asr-flash",
            "input": {
                "audio_format": audio_format,
                "audio_content": audio_content,
            },
            "parameters": {
                "enable_emotion_analysis": True,
                "emotion_categories": list(VALID_EMOTIONS),
            },
        }

        resp = requests.post(ALIYUN_API_URL, headers=self.headers, json=payload, timeout=15)
        resp.raise_for_status()

        try:
            raw = resp.json()
        except json.JSONDecodeError as e:
            raise RuntimeError("语音识别 API 返回结果解析失败：" + str(e))

        # 检查 API 返回结果是否有效
        if not isinstance(raw, dict):
            raise RuntimeError("语音识别 API 返回结果格式错误：非字典类型")

        # 检查是否有输出内容
        output = raw.get("output", {})
        text = output.get("text", "").strip() if "output" in raw else raw.get("text", "").strip() or raw.get("transcript", "").strip()

        if not text:
            raise RuntimeError("语音识别 API 返回的识别结果为空，请检查音频质量或重试")

        return raw

    def analyze(self, audio_path: str) -> VoiceResult:
        raw = self._call_asr_api(audio_path)

        # 支持多种可能结构，容错解析
        def pick_text(obj):
            if not isinstance(obj, dict):
                return ""
            return (
                obj.get("text", "")
                or obj.get("transcript", "")
                or obj.get("result", "")
                or obj.get("content", "")
            )

        transcript = ""
        emotion = ""
        detail = ""

        if isinstance(raw, dict):
            # 首选 output.text
            output = raw.get("output") or raw.get("data") or raw.get("result")
            if isinstance(output, dict):
                transcript = pick_text(output).strip()
                emotion_obj = output.get("emotion") or raw.get("emotion") or {}
                if isinstance(emotion_obj, dict):
                    emotion = emotion_obj.get("main", "") or emotion_obj.get("label", "")
                    detail = emotion_obj.get("detail", "") or emotion_obj.get("desc", "")
            else:
                transcript = pick_text(raw).strip()
                emotion = raw.get("emotion", "") or raw.get("emotion_main", "")
                detail = raw.get("emotion_detail", "") or raw.get("emotion_desc", "")

        # 兼容多个 key 路径
        if not transcript:
            for key in ["output", "data", "result"]:
                candidate = raw.get(key)
                if isinstance(candidate, dict):
                    transcript = pick_text(candidate).strip()
                    if transcript:
                        break

        if not transcript:
            raise RuntimeError("语音识别结果为空，请重试")

        if emotion not in VALID_EMOTIONS:
            # 当 API 返回未知情绪时，按默认感知映射
            emotion = "自信" if "自信" in VALID_EMOTIONS else next(iter(VALID_EMOTIONS))

        try:
            return VoiceResult(transcript=transcript, emotion=emotion, emotion_detail=detail)
        except ValidationError as e:
            raise RuntimeError("语音结果验证失败：" + str(e))


def record_and_stt(duration: int = 8) -> VoiceResult:
    recorder = VoiceRecorder()
    try:
        audio_path = recorder.record(duration)
        client = STTClient()
        return client.analyze(audio_path)
    except Exception as e:
        raise RuntimeError("语音处理失败：" + str(e))
    finally:
        recorder.clean_temp()


def transcribe(mp3_path: str) -> VoiceResult:
    client = STTClient()
    return client.analyze(mp3_path)
