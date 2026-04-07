# UI/components/info/StreamSignals.py
"""跨线程流式信号容器，供所有流式输出组件复用。"""

from PySide6.QtCore import QObject, Signal


class StreamSignals(QObject):
    chunk_received = Signal(str)   # 新 token 到达
    stream_done    = Signal()      # 流结束（正常）
    stream_error   = Signal(str)   # 流结束（异常），携带错误信息