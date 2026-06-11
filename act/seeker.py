import time
import os
import logging
import uiautomation as auto
import win32gui
import mss
from PIL import Image
from act.tools import *
from config import warn_word


def find_wechat_hwnd():
    """查找微信主窗口句柄"""
    def enum_callback(hwnd, hwnd_list):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title == "微信":
                hwnd_list.append(hwnd)
        return True

    hwnd_list = []
    win32gui.EnumWindows(enum_callback, hwnd_list)
    if not hwnd_list:
        raise Exception("未检测到微信进程！请确保微信已登录")
    return hwnd_list[0]


def get_window():
    hwnd = find_wechat_hwnd()
    window = auto.ControlFromHandle(hwnd)
    window.SetActive()
    return window


def get_chat_list_panel(window):
    """获取会话列表面板（适配新版微信 mmui 结构）"""
    session_list = window.GroupControl(ClassName='mmui::ChatSessionList')
    return session_list.ListControl(ClassName='mmui::XTableView')


def extract_chat_name(chat_item):
    """从会话项中提取联系人名称（新版微信 Name 包含状态信息）"""
    import re
    name = chat_item.Name
    # 移除常见状态后缀
    name = re.sub(r'\d+\s*条未读.*$', '', name)
    name = re.sub(r'\d+\s*条新消息.*$', '', name)
    name = re.sub(r'\s*已置顶\s*', '', name)
    name = re.sub(r'\s*他刚刚\s*', '', name)
    name = re.sub(r'\s*他们刚刚\s*', '', name)
    name = re.sub(r'\s*\([^)]*\)\s*', '', name)
    # 移除末尾的时间（如 16:24）和状态
    name = re.sub(r'\s+\d+:\d+$', '', name)
    name = re.sub(r'\s+(离开|手机在线|电脑在线|微信在线)$', '', name)
    return name.strip()


def get_my_name(window):
    sidebar = window.ToolBarControl(Name="导航")
    children = sidebar.GetChildren()
    return children[0].Name


def get_friends(window):
    name_list = []
    msg = window.ButtonControl(Name="聊天信息")
    time.sleep(0.2)
    msg.Click()
    more = window.ButtonControl(Name="查看更多")
    if more.Exists(0, 0):
        time.sleep(0.2)
        more.Click()
    member_list = window.ListControl(Name="聊天成员")
    for listItem, d in auto.WalkControl(member_list, maxDepth=1):
        if not isinstance(listItem, auto.ListItemControl):
            continue
        if not listItem.Name or listItem.Name in ("添加", "删除"):
            continue
        name_list.append(listItem.Name)
    return name_list


def get_chat_text(window):
    chat_list = get_chat_lines(window)
    text = ""
    for tu in chat_list:
        t = __to_text(tu)
        if t is not None:
            t = t.replace(warn_word,"")
            text = text + "\n" + t
    return text


def get_chat_lines(window):
    chat_list = []
    try:
        chat_lines = window.ListControl(Name='消息').GetChildren()
    except:
        chat_lines = window.ListControl(Name='会话').GetChildren()
    for chat_line in chat_lines:
        chat_list.append(__classify_chat_type(chat_line))
    if len(chat_list) > 1:
        chat_list = chat_list[1:]
    return chat_list


def get_chat_images(window):
    """从当前聊天中提取所有图片消息控件

    Args:
        window: 微信主窗口控件

    Returns:
        list: 图片消息的 chat_line 控件列表，以及对应的屏幕截图区域
            每个元素为 (chat_line, bbox)
    """
    images = []
    try:
        msg_list = window.ListControl(Name='消息')
        chat_lines = msg_list.GetChildren()
    except:
        chat_lines = window.ListControl(Name='会话').GetChildren()
        msg_list = None

    # 跳过第一条（通常是标题行）
    if len(chat_lines) > 1:
        chat_lines = chat_lines[1:]

    for chat_line in chat_lines:
        cn = chat_line.ClassName or ""
        name = chat_line.Name or ""

        is_image = (
            'ChatBubbleReferItemView' in cn
            or 'Image' in cn
            or 'Picture' in cn
            or '图片' in name
            or '[图片]' in name
        )

        if not is_image:
            continue

        images.append(chat_line)

    logger = logging.getLogger(__name__)
    logger.info(f"Found {len(images)} image(s) in chat")
    return images


def capture_chat_image(chat_line, save_path):
    """获取聊天中的图片

    使用 mss 直接截取图片控件所在屏幕区域（支持多显示器）。
    不点击、不打开任何窗口，完全不影响微信状态。

    Args:
        chat_line: 图片消息控件 (ListItemControl)
        save_path: 截图保存路径

    Returns:
        str: 保存的文件路径，失败返回 None
    """
    logger = logging.getLogger(__name__)
    try:
        rect = chat_line.BoundingRectangle
        if not rect or rect.right <= rect.left or rect.bottom <= rect.top:
            logger.warning("capture_chat_image: invalid bounding rect")
            return None

        # 用 mss 截取控件区域（支持多显示器虚拟坐标）
        padding = 4
        monitor = {
            "left": rect.left - padding,
            "top": rect.top - padding,
            "width": (rect.right - rect.left) + padding * 2,
            "height": (rect.bottom - rect.top) + padding * 2,
        }
        logger.info(f"capture_chat_image: mss grab region={monitor}")

        with mss.mss() as sct:
            sct_img = sct.grab(monitor)
            screenshot = Image.frombytes("RGB", sct_img.size, sct_img.rgb)

        logger.info(f"capture_chat_image: got image size={screenshot.size}")

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        screenshot.save(save_path, 'PNG')
        file_size = os.path.getsize(save_path)
        logger.info(f"capture_chat_image: saved to {save_path} ({screenshot.size}, {file_size} bytes)")
        return save_path

    except Exception as e:
        logger.error(f"capture_chat_image failed: {e}")
        return None


def __to_text(tu):
    if tu is None:
        return None
    if tu[0] == "time":
        return "当前时间：" + tu[1]
    elif tu[0] == "nudge":
        return tu[1] + " 拍了拍我"
    elif tu[0] == "recall":
        return tu[1] + " 撤回了一条消息"
    elif tu[0] == "chat":
        if tu[1]:  # 有发送者
            return tu[1] + " 说 " + tu[2]
        else:  # 无发送者（新版 1on1 直接显示内容）
            return tu[2]
    elif tu[0] == "image":
        # 图片消息，表示发送者发了一张图片
        if tu[1]:  # 有发送者
            return tu[1] + " 发送了一张图片"
        else:
            return "发送了一张图片"
    return None


def __classify_chat_type(chat_line):
    children = chat_line.GetChildren()
    cn = chat_line.ClassName or ""

    # WeChat 4.x (Electron 版) 控件结构
    if cn == 'mmui::ChatTextItemView':
        content = chat_line.Name.strip()
        sender = ""
        for child in children:
            if child.ControlTypeName in ('ButtonControl', 'TextControl') and child.Name:
                sender = child.Name.strip()
                break
        return "chat", sender, content

    if cn == 'mmui::ChatItemView':
        if len(children) == 1 and children[0].ControlTypeName == 'TextControl':
            return "time", children[0].Name, None
        for child in children:
            if any(text in child.Name for text in ["拍了拍", "tickled"]):
                return "nudge", child.Name, None
        for child in children:
            if any(text in child.Name for text in ["撤回了一条消息", "recalled a message"]):
                return "recall", child.Name, None
        return None

    # WeChat 4.x 图片消息：ClassName='mmui::ChatBubbleReferItemView'
    if 'ChatBubbleReferItemView' in cn:
        sender = ""
        for child in children:
            if child.ControlTypeName in ('ButtonControl', 'TextControl') and child.Name:
                sender = child.Name.strip()
                break
        return "image", sender, None

    # 旧版 WeChat 兼容
    if len(children) == 1 and children[0].ControlTypeName == 'TextControl':
        return "time", children[0].Name, None
    elif find_control_with_text_list(chat_line, ["拍了拍", "tickled"]) is not None:
        return "nudge", find_control_with_text_list(chat_line, ["拍了拍", "tickled"]).Name, None
    elif find_control_with_text_list(chat_line, ["撤回了一条消息", "recalled a message"]) is not None:
        return "recall", find_control_with_text_list(chat_line, ["撤回了一条消息", "recalled a message"]).Name, None
    elif find_control_with_control_type(chat_line, "ButtonControl") is not None:
        return "chat", find_control_with_control_type(chat_line, "ButtonControl").Name, chat_line.Name

    name = chat_line.Name or ""
    if '图片' in name or 'Image' in name or '[图片]' in name:
        sender = ""
        for child in children:
            if child.ControlTypeName in ('ButtonControl', 'TextControl') and child.Name:
                sender = child.Name.strip()
                break
        return "image", sender, None

    return None
