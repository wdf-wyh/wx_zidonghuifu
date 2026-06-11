"""生成默认图片资源到 images/ 目录

运行方式：
    python setup_images.py

使用 Pillow 生成简单的占位图片，供 AI 发送图片功能使用。
用户可自行替换 images/ 目录下的图片为真实图片。
"""
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    logger.error("请先安装 Pillow: pip install Pillow")
    raise

IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
IMAGE_SIZE = (200, 200)
FONT_SIZE = 28
BG_COLOR = (255, 255, 255)


def _try_load_font():
    """尝试加载中文字体，失败则使用默认字体"""
    font_paths = [
        "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
        "C:/Windows/Fonts/simhei.ttf",      # 黑体
        "C:/Windows/Fonts/msyhbd.ttc",      # 微软雅黑粗体
    ]
    for fp in font_paths:
        if os.path.isfile(fp):
            try:
                return ImageFont.truetype(fp, FONT_SIZE)
            except Exception:
                continue
    logger.warning("未找到中文字体，使用默认字体（中文可能显示为方框）")
    return ImageFont.load_default()


def _create_image(filename, bg_color, text, text_color=(50, 50, 50)):
    """创建一张带文字和背景色的方形占位图片"""
    img = Image.new("RGB", IMAGE_SIZE, bg_color)
    draw = ImageDraw.Draw(img)
    font = _try_load_font()

    # 文字居中
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (IMAGE_SIZE[0] - tw) // 2
    y = (IMAGE_SIZE[1] - th) // 2
    draw.text((x, y), text, fill=text_color, font=font)

    filepath = os.path.join(IMAGE_DIR, filename)
    img.save(filepath, "PNG")
    logger.info(f"已生成: {filepath}")


def main():
    os.makedirs(IMAGE_DIR, exist_ok=True)

    images = [
        ("smile.png",       (255, 235, 200), "微笑",   (200, 80, 60)),
        ("ok.png",          (200, 240, 200), "好的",   (30, 120, 30)),
        ("thank_you.png",   (255, 220, 220), "谢谢",   (180, 40, 40)),
        ("sad.png",         (220, 225, 240), "难过",   (60, 60, 120)),
        ("celebrate.png",   (255, 230, 180), "恭喜",   (200, 100, 20)),
        ("default.png",     (230, 230, 230), "图片",   (100, 100, 100)),
    ]

    for filename, bg_color, text, text_color in images:
        _create_image(filename, bg_color, text, text_color)

    logger.info(f"共生成 {len(images)} 张默认图片到 {IMAGE_DIR}")
    logger.info("你可以随时替换 images/ 目录下的图片为真实图片（保持文件名一致）")


if __name__ == "__main__":
    main()
