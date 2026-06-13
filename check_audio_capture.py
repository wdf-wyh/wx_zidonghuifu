"""
WASAPI Loopback 录音兼容性检测工具（单文件版）

无需安装 Python，双击运行即可。
检测当前电脑能否录制系统音频（用于微信语音转文字）。

原理：
  1. 播放测试音 → 用每个录音设备录制
  2. 分析音频振幅 → 判断是否能捕获系统声音
"""

import sys
import os
import time
import wave
import tempfile


def main():
    print(f"\n{'='*56}")
    print(f"   WASAPI 录音兼容性检测")
    print(f"{'='*56}")
    print(f"  系统: {sys.platform}")
    print(f"  时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 导入依赖
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as e:
        print(f"  ❌ 依赖缺失: {e}")
        print(f"\n  请先安装:")
        print(f"    pip install sounddevice numpy")
        print(f"\n  或将此文件发给已装 Python 的电脑运行")
        input("\n  按 Enter 退出...")
        return

    # 1. 获取设备信息
    devices = sd.query_devices()
    hostapis = sd.query_hostapis()

    print(f"  {'─'*50}")
    print(f"  默认输出: {sd.query_devices(sd.default.device[1])['name']}")
    print(f"  默认输入: {sd.query_devices(sd.default.device[0])['name']}")
    print()

    record_devices = []
    for i, dev in enumerate(devices):
        if dev['max_input_channels'] <= 0:
            continue
        ha = hostapis[dev['hostapi']]['name']
        sr = dev.get('default_samplerate', 0)
        record_devices.append((i, dev['name'], ha, int(sr), dev['max_input_channels']))

        name_display = dev['name'][:48]
        print(f"  [{i:2d}] {name_display:48s} {ha:20s} {int(sr):5d}Hz")

    if not record_devices:
        print("\n  ❌ 未找到录音设备！")
        input("\n  按 Enter 退出...")
        return

    # 2. 测试每个设备
    print(f"\n  {'─'*50}")
    print(f"  正在测试录音能力...（将播放短暂测试音）")
    print(f"  {'─'*50}")
    print()

    passed = []
    for dev_id, dev_name, api, sr, ch in record_devices:
        # 跳过 WDM-KS（PortAudio 不支持）
        if 'WDM-KS' in api:
            print(f"  [{dev_id:2d}] ⏭️  {dev_name[:40]:40s} WDM-KS 跳过")
            continue

        name_display = dev_name[:40]
        print(f"  [{dev_id:2d}] 🔄 {name_display:40s} ", end='', flush=True)

        try:
            dev_info = sd.query_devices(dev_id)
            sr = int(dev_info.get('default_samplerate', 44100))
            channels = min(dev_info['max_input_channels'], 2)
            duration = 2.0
            frames = int(duration * sr)

            # 播放测试音
            t = np.linspace(0, duration * 0.8, int(sr * duration * 0.8))
            test_tone = (np.sin(2 * np.pi * 440 * t) * 0.3).astype(np.float32)
            sd.play(test_tone, sr, blocking=False)

            # 录音
            raw = sd.rec(frames, samplerate=sr, channels=channels,
                         device=dev_id, dtype='float32', blocking=True)
            sd.stop()

            if channels > 1:
                audio = raw.mean(axis=1)
            else:
                audio = raw.flatten()
            audio = np.clip(audio, -1.0, 1.0)

            max_amp = np.max(np.abs(audio))
            noise_floor = np.max(np.abs(audio[:int(sr * 0.1)])) if len(audio) > int(sr * 0.1) else 0.0001
            snr = max_amp / noise_floor if noise_floor > 0 else 1

            if max_amp > 0.01:
                print(f" ✅ PASS  (amp={max_amp:.4f})")
                passed.append((dev_id, dev_name))
            else:
                print(f" ❌ FAIL  (amp={max_amp:.4f})")

        except Exception as e:
            print(f" ❌ 异常 ({str(e)[:30]})")

    # 3. 结论
    print(f"\n  {'='*56}")
    if passed:
        print(f"  ✅ 此电脑支持录制系统音频！")
        print(f"  {'─'*56}")
        print(f"  推荐设备:")
        for dev_id, dev_name in passed:
            print(f"    [{dev_id}] {dev_name}")
        print()
        print(f"  配置方法:")
        print(f"    在 config.py 中设置:")
        print(f"      audio_device_id = {passed[0][0]}  # {passed[0][1]}")
    else:
        print(f"  ❌ 此电脑无法录制系统音频")
        print(f"  {'─'*56}")
        print(f"  可能原因:")
        print(f"    - 立体声混音 (Stereo Mix) 未启用")
        print(f"    - 音频驱动为 WDM-KS 格式（不支持）")
        print(f"    - VoiceMeeter 未设为默认设备")
        print()
        print(f"  建议尝试:")
        print(f"    1. 启用立体声混音（Windows 声音设置）")
        print(f"    2. 安装 VoiceMeeter 并设为默认")
        print(f"    3. 安装 pyaudiowpatch: pip install pyaudiowpatch")
        print(f"    4. 换台电脑试试")

    print(f"\n  {'='*56}")
    input("\n  按 Enter 退出...")


if __name__ == '__main__':
    main()
