import uiautomation as auto
import logging
import os
from uiautomation.uiautomation import Bitmap
from config import warn_word

logger = logging.getLogger(__name__)


def send_msg(edit_name, window, content, msg_type=1):
    content = content + warn_word
    # WeChat 4.x: 输入框的 Name 即为聊天对象名
    edit = window.EditControl(Name=edit_name)

    if msg_type:
        auto.SetClipboardText(content)
    else:
        auto.SetClipboardBitmap(Bitmap.FromFile(content))

    edit.Click(simulateMove=False, waitTime=0.6)
    edit.SendKeys('{Ctrl}v', waitTime=0.1)

    # WeChat 4.x (Electron版) 没有传统的发送按钮，按 Enter 发送
    edit.SendKeys('{Enter}', waitTime=0.3)
    logger.info(f"Sent message to '{edit_name}': {content[:50]}...")


def send_image(edit_name, window, image_path):
    """发送图片文件到微信聊天窗口

    安全地将本地图片文件通过剪贴板发送到微信。

    Args:
        edit_name: 聊天对象名（输入框 Name）
        window: 微信主窗口控件
        image_path: 图片文件的绝对路径

    Raises:
        FileNotFoundError: 图片文件不存在
        ValueError: 路径不安全（目录穿越检测）
        Exception: 其他发送失败异常
    """
    # 路径安全检查：禁止目录穿越
    abs_path = os.path.abspath(image_path)
    allowed_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'images')
    allowed_dir = os.path.abspath(allowed_dir)

    if not abs_path.startswith(allowed_dir):
        raise ValueError(f"Security: image path '{image_path}' is outside allowed directory")

    if not os.path.isfile(abs_path):
        raise FileNotFoundError(f"Image file not found: {abs_path}")

    edit = window.EditControl(Name=edit_name)
    auto.SetClipboardBitmap(Bitmap.FromFile(abs_path))
    edit.Click(simulateMove=False, waitTime=0.6)
    edit.SendKeys('{Ctrl}v', waitTime=0.1)
    edit.SendKeys('{Enter}', waitTime=0.3)
    logger.info(f"Sent image to '{edit_name}': {abs_path}")
