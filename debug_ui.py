"""
Scan image message controls in WeChat chat area.

Steps:
1. Click on a chat that HAS image messages (so images are visible)
2. Run this script
"""
import uiautomation as auto
import win32gui
import time

auto.uiautomation.SetGlobalSearchTimeout(2)


def find_wechat_hwnd():
    def enum_callback(hwnd, hwnd_list):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title == "WeChat" or title == "微信":
                hwnd_list.append(hwnd)
        return True
    hwnd_list = []
    win32gui.EnumWindows(enum_callback, hwnd_list)
    if not hwnd_list:
        print("[WeChat window not found!]")
        return None
    return hwnd_list[0]


def dump_control(ctrl, depth=0):
    """Recursively dump control info"""
    indent = "  " * depth
    cn = ctrl.ClassName or ""
    name = ctrl.Name or ""
    r = ctrl.BoundingRectangle
    rect = f"({r.left},{r.top},{r.right},{r.bottom})" if r else "None"
    print(f"{indent}{ctrl.ControlTypeName} | cn='{cn}' | name='{name}' | rect={rect}")
    try:
        children = ctrl.GetChildren()
        for child in children:
            dump_control(child, depth + 1)
    except:
        pass


if __name__ == '__main__':
    hwnd = find_wechat_hwnd()
    if not hwnd:
        exit(1)

    window = auto.ControlFromHandle(hwnd)
    print(f"HWND: {hwnd}")
    window.SetActive()
    window.SetTopmost()
    time.sleep(1)

    # Try to find the message list
    msg_list = None
    for name in ('消息', 'Message', '会话'):
        try:
            msg_list = window.ListControl(Name=name)
            if msg_list.Exists(0, 0):
                break
        except:
            continue

    if msg_list is None:
        print("[Message list not found!]")
        print("[Dumping top-level controls...]")
        dump_control(window)
        exit(1)

    bounds = msg_list.BoundingRectangle
    rect = f"({bounds.left},{bounds.top},{bounds.right},{bounds.bottom})" if bounds else "None"
    print(f"\nMessage list: {rect}")

    children = msg_list.GetChildren()
    print(f"\nTotal message items: {len(children)}")

    for idx, msg in enumerate(children):
        cn = msg.ClassName or ""
        name = msg.Name or ""
        r = msg.BoundingRectangle
        rect_str = f"({r.left},{r.top},{r.right},{r.bottom})" if r else "None"
        print(f"\n  [{idx}] type={msg.ControlTypeName} | cn='{cn}' | name='{name}' | rect={rect_str}")

        # Check if it's an image message
        is_image = 'ChatBubbleReferItemView' in cn or 'Image' in cn or 'Picture' in cn or name == '图片' or '[图片]' in name
        if is_image:
            print(f"       >>> IMAGE MESSAGE <<<")
            print(f"       Children (all levels):")
            dump_control(msg, depth=2)

    print("\n[Done]")
