#!/usr/bin/env python
"""
语音功能诊断脚本
验证修复后 VoiceWorker 和 VoiceRecorder 的正确性
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加当前路径到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("语音功能诊断测试")
print("=" * 60)

# 1. 检查依赖
print("\n[1] 检查依赖...")
try:
    import numpy as np
    print("  ✓ numpy")
    import sounddevice as sd
    print("  ✓ sounddevice")
    import requests
    print("  ✓ requests")
    from dotenv import load_dotenv
    print("  ✓ python-dotenv")
except ImportError as e:
    print(f"  ✗ 依赖缺失：{e}")
    sys.exit(1)

# 2. 检查环境变量
print("\n[2] 检查环境配置...")
load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY", "")
if api_key:
    print(f"  ✓ DASHSCOPE_API_KEY 已配置 (长度: {len(api_key)})")
else:
    print("  ✗ DASHSCOPE_API_KEY 未配置（必需）")

# 3. 检查 VoiceRecorder
print("\n[3] 检查 VoiceRecorder 实现...")
try:
    from service.voice import VoiceRecorder, RECORD_CONFIG
    
    print(f"  ✓ VoiceRecorder 导入成功")
    print(f"    - 采样率: {RECORD_CONFIG['samplerate']} Hz")
    print(f"    - 声道数: {RECORD_CONFIG['channels']}")
    print(f"    - 数据类型: {RECORD_CONFIG['dtype']}")
    
    # 检查 temp_dir
    recorder = VoiceRecorder()
    print(f"    - 临时目录: {recorder.temp_dir}")
    print(f"    - 目录存在: {os.path.exists(recorder.temp_dir)}")
    
except Exception as e:
    print(f"  ✗ VoiceRecorder 初始化失败：{e}")
    sys.exit(1)

# 4. 检查 VoiceWorker
print("\n[4] 检查 VoiceWorker 实现...")
try:
    from UI.interview_panel import VoiceWorker
    from PySide6.QtCore import QCoreApplication
    
    # 创建 QApplication（必需用于信号/槽）
    if not QCoreApplication.instance():
        app = QCoreApplication.instance() or QCoreApplication([])
    
    worker = VoiceWorker()
    print(f"  ✓ VoiceWorker 创建成功")
    
    # 检查信号是否存在
    print(f"    - finished 信号: {hasattr(worker, 'finished')}")
    print(f"    - error 信号: {hasattr(worker, 'error')}")
    print(f"    - stop_requested 信号: {hasattr(worker, 'stop_requested')}")
    print(f"    - cancel_requested 信号: {hasattr(worker, 'cancel_requested')}")
    
    # 检查方法
    print(f"    - stop() 方法: {hasattr(worker, 'stop')}")
    print(f"    - cancel() 方法: {hasattr(worker, 'cancel')}")
    print(f"    - run() 方法: {hasattr(worker, 'run')}")
    
except Exception as e:
    print(f"  ✗ VoiceWorker 初始化失败：{e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. 检查麦克风设备
print("\n[5] 检查音频设备...")
try:
    devices = sd.query_devices()
    default_input = sd.default.device[0]
    print(f"  ✓ 找到 {len(devices)} 个设备")
    print(f"    - 默认输入设备: {default_input}")
    
    if isinstance(default_input, int) and default_input >= 0:
        device_info = sd.query_devices(default_input)
        print(f"    - 设备名称: {device_info.get('name', 'Unknown')}")
        print(f"    - 输入声道: {device_info.get('max_input_channels', 0)}")
    else:
        print("    - ⚠ 未能识别默认输入设备")
        
except Exception as e:
    print(f"  ⚠ 检查设备失败：{e}")

# 6. 检查 temp_audio 目录
print("\n[6] 检查临时目录...")
temp_dir = os.path.join(os.getcwd(), "temp_audio")
try:
    os.makedirs(temp_dir, exist_ok=True)
    test_file = os.path.join(temp_dir, ".test")
    with open(test_file, 'w') as f:
        f.write("test")
    os.remove(test_file)
    print(f"  ✓ 临时目录可写")
    print(f"    - 路径: {temp_dir}")
except Exception as e:
    print(f"  ✗ 临时目录无法写入：{e}")

# 7. 代码检查：验证关键修复
print("\n[7] 代码修复验证...")
try:
    with open("UI/interview_panel.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    checks = [
        ("stop_requested -> stop 连接", "stop_requested.connect(self._voice_worker.stop)"),
        ("cancel_requested -> cancel 连接", "cancel_requested.connect(self._voice_worker.cancel)"),
        ("VoiceWorker.record() 诊断日志", "[DEBUG] 录音完成"),
        ("文件大小检查", "file_size < 1000"),
        ("API 诊断日志", "[DEBUG] API 识别成功"),
    ]
    
    for check_name, keyword in checks:
        if keyword in content:
            print(f"  ✓ {check_name}")
        else:
            print(f"  ✗ {check_name} - 未找到关键代码")

except Exception as e:
    print(f"  ✗ 代码检查失败：{e}")

print("\n" + "=" * 60)
print("诊断完成！")
print("=" * 60)
print("\n建议：")
print("1. 检查麦克风连接和系统权限")
print("2. 检查 DASHSCOPE_API_KEY 是否正确配置")
print("3. 运行程序时观察 [DEBUG] 日志了解执行流程")
print("4. 如果仍有问题，查看控制台的详细错误信息")
