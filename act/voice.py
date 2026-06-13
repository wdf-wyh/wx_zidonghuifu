"""
语音消息处理模块：双击播放微信语音 → 录制系统音频 → 保存 WAV

使用 DirectSound 主声音捕获设备 [5] 录制系统音频输出。
"""

import time
import re
import os
import logging
import wave
import uiautomation as auto

logger = logging.getLogger(__name__)

try:
    import sounddevice as sd
    import numpy as np
    _has_recording = True
except ImportError:
    sd = None
    np = None
    _has_recording = False

from config import audio_device_id


def record_audio(duration_seconds):
    """录制系统音频

    Args:
        duration_seconds: 录制时长（秒）

    Returns:
        numpy.ndarray: 单声道 float32 [-1,1]，失败返回 None
    """
    if not _has_recording:
        logger.error("sounddevice not installed")
        return None

    try:
        dev = sd.query_devices(audio_device_id)
        sr = int(dev.get('default_samplerate', 44100))
        ch = min(dev['max_input_channels'], 2)
        frames = int(duration_seconds * sr)

        logger.info(f"Recording {duration_seconds:.1f}s via [{audio_device_id}] {dev['name']}")
        raw = sd.rec(frames, samplerate=sr, channels=ch,
                     device=audio_device_id, dtype='float32', blocking=True)

        if ch > 1:
            audio = raw.mean(axis=1)
        else:
            audio = raw.flatten()
        return np.clip(audio, -1.0, 1.0)
    except Exception as e:
        logger.error(f"Recording failed: {e}")
        return None


def save_wav(audio_data, filepath, samplerate=16000):
    """保存 WAV 文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    audio_int16 = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(audio_int16.tobytes())
    logger.info(f"Saved WAV: {filepath} ({os.path.getsize(filepath)} bytes)")


def _save_silent_wav(filepath, duration=3, samplerate=16000):
    """生成一个静音 WAV 文件（录音不可用时占位）"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    # 16-bit PCM 静音 = 全零数据
    num_samples = int(duration * samplerate)
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(b'\x00\x00' * num_samples)
    logger.info(f"Silent WAV (placeholder): {filepath} ({os.path.getsize(filepath)} bytes)")


def _parse_duration_to_seconds(duration_str):
    """解析语音时长"""
    if not duration_str:
        return 3
    nums = re.findall(r'\d+', duration_str)
    return int(nums[0]) if nums else 3


def play_and_capture_voice(voice_control, duration_str, save_path):
    """双击播放语音消息 → 录制系统音频 → 保存 WAV

    策略：先启动录音（非阻塞），再双击触发播放，确保不丢失音频开头。

    Args:
        voice_control: 微信语音消息控件
        duration_str: 语音时长（如 '3"秒'）
        save_path: WAV 输出路径

    Returns:
        str: WAV 路径（始终返回，即使静音或失败也保存文件供排查）
    """
    # 确保保存目录存在
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    if not _has_recording:
        logger.error("sounddevice not installed. Run: pip install sounddevice numpy")
        # 保存一个静音文件供排查
        _save_silent_wav(save_path)
        return save_path

    seconds = _parse_duration_to_seconds(duration_str)
    # 录音时长 = 语音时长 + 1s 前置 padding + 1s 后置 padding
    record_duration = seconds + 2.0

    logger.info(f"Playing+recording: {seconds}s, output={save_path}")

    # 获取录音参数
    try:
        dev = sd.query_devices(audio_device_id)
        sr = int(dev.get('default_samplerate', 44100))
        ch = min(dev['max_input_channels'], 2)
        frames = int(record_duration * sr)
    except Exception as e:
        logger.error(f"Device query failed: {e}")
        _save_silent_wav(save_path, duration=seconds)
        return save_path

    # 1. 先启动录音（非阻塞）
    logger.info(f"Starting recording ({record_duration:.1f}s) via [{audio_device_id}]...")
    raw_recording = sd.rec(frames, samplerate=sr, channels=ch,
                           device=audio_device_id, dtype='float32', blocking=False)

    # 2. 等待 0.3s 让录音缓冲就绪，然后双击播放
    time.sleep(0.3)
    try:
        rect = voice_control.BoundingRectangle
        if rect:
            cx, cy = (rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2
            voice_control.Click(simulateMove=False, waitTime=0.1)
            time.sleep(0.15)
            auto.Click(cx, cy, waitTime=0.1)
            auto.Click(cx, cy, waitTime=0.1)
            logger.info(f"Double-clicked at ({cx},{cy})")
    except Exception as e:
        logger.warning(f"Double-click failed: {e}")

    # 3. 等待录音完成
    sd.wait()
    logger.info("Recording finished")

    # 4. 处理音频
    if ch > 1:
        audio = raw_recording.mean(axis=1)
    else:
        audio = raw_recording.flatten()
    audio = np.clip(audio, -1.0, 1.0)

    max_amp = np.max(np.abs(audio))
    rms = np.sqrt(np.mean(audio.astype(np.float64) ** 2))
    logger.info(f"Audio stats: max_amp={max_amp:.6f}, rms={rms:.6f}")

    # 5. 始终保存 WAV 文件（供排查用）
    save_wav(audio, save_path)
    file_size = os.path.getsize(save_path)

    if max_amp < 0.001:
        logger.warning(f"[VOICE] {save_path} — 静音 (max_amp={max_amp:.6f})")
    else:
        logger.info(f"[VOICE] {save_path} — 有声音 ✓ (max_amp={max_amp:.6f})")

    return save_path
