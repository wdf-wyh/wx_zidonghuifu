import uiautomation as auto
import logging
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
