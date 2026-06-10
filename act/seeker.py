import time
import uiautomation as auto
import win32gui
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
    window.SetTopmost()
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
    return None


def __classify_chat_type(chat_line):
    children = chat_line.GetChildren()
    cn = chat_line.ClassName or ""

    # WeChat 4.x (Electron 版) 控件结构
    if cn == 'mmui::ChatTextItemView':
        # 文本消息：chat_line.Name 即为消息内容
        content = chat_line.Name.strip()
        # 尝试从子控件中提取发送者
        sender = ""
        for child in children:
            if child.ControlTypeName in ('ButtonControl', 'TextControl') and child.Name:
                sender = child.Name.strip()
                break
        return "chat", sender, content

    if cn == 'mmui::ChatItemView':
        # 系统消息/时间/拍一拍/撤回等
        if len(children) == 1 and children[0].ControlTypeName == 'TextControl':
            return "time", children[0].Name, None
        # 检测"拍了拍"
        for child in children:
            if any(text in child.Name for text in ["拍了拍", "tickled"]):
                return "nudge", child.Name, None
        # 检测撤回
        for child in children:
            if any(text in child.Name for text in ["撤回了一条消息", "recalled a message"]):
                return "recall", child.Name, None
        return None

    # 旧版 WeChat 兼容
    if len(children) == 1 and children[0].ControlTypeName == 'TextControl':
        return "time", children[0].Name, None
    elif find_control_with_text_list(chat_line, ["拍了拍", "tickled"]) is not None:
        return "nudge", find_control_with_text_list(chat_line, ["拍了拍", "tickled"]).Name, None
    elif find_control_with_text_list(chat_line, ["撤回了一条消息", "recalled a message"]) is not None:
        return "recall", find_control_with_text_list(chat_line, ["撤回了一条消息", "recalled a message"]).Name, None
    elif find_control_with_control_type(chat_line, "ButtonControl") is not None:
        return "chat", find_control_with_control_type(chat_line, "ButtonControl").Name, chat_line.Name

    return None
