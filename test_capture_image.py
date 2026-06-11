"""
测试图片获取 — 从当前微信聊天窗口截图/Ctrl+C 保存图片到 temp 目录

使用方法：
1. 在微信中打开一个包含图片消息的聊天窗口
2. 确保图片在可视区域内（滚动到能看到图片的位置）
3. 运行: python test_capture_image.py
"""
import os
import sys
import time
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from act.seeker import get_window, get_chat_images, capture_chat_image

IMAGE_TEMP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images', 'temp')


def main():
    print("=" * 60)
    print("图片获取测试脚本")
    print("=" * 60)
    print(f"图片保存目录: {IMAGE_TEMP_DIR}")
    print()

    # 1. 获取微信窗口
    print("[1] 获取微信窗口...")
    window = get_window()
    print(f"    OK - 窗口已激活")
    print()

    # 2. 获取图片消息控件
    print("[2] 扫描聊天中的图片消息...")
    images = get_chat_images(window)
    print(f"    找到 {len(images)} 张可见图片")
    print()

    if not images:
        print("[!] 没有在可视区域内找到图片。请确保：")
        print("    1. 打开了一个包含图片的聊天窗口")
        print("    2. 图片在聊天区域可见（没有滚走）")
        print("    3. 点击聊天窗口让它获得焦点")
        return

    # 3. 逐个获取图片
    os.makedirs(IMAGE_TEMP_DIR, exist_ok=True)

    for idx, img_line in enumerate(images):
        save_path = os.path.join(IMAGE_TEMP_DIR, f"test_capture_{idx}.png")
        print(f"[3-{idx}] 正在获取图片 {idx + 1}/{len(images)} ...")
        print(f"      控件: cn='{img_line.ClassName}', name='{img_line.Name}'")
        result = capture_chat_image(img_line, save_path)
        if result:
            file_size = os.path.getsize(result)
            print(f"      ✅ 成功! 保存到: {result}")
            print(f"         文件大小: {file_size / 1024:.1f} KB")
        else:
            print(f"      ❌ 获取失败")
        print()

    # 4. 打印结果
    print("=" * 60)
    print("所有图片文件:")
    for f in sorted(os.listdir(IMAGE_TEMP_DIR)):
        fp = os.path.join(IMAGE_TEMP_DIR, f)
        size = os.path.getsize(fp)
        print(f"  {f:40s} {size / 1024:>8.1f} KB")
    print("=" * 60)


if __name__ == '__main__':
    main()
