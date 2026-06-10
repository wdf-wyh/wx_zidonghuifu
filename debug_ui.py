"""
探测输入框位置 — 先手动点击输入框后再运行此脚本
步骤：
1. 用鼠标点击聊天输入框（确保光标在输入框中闪烁）
2. 然后按 Enter 运行此脚本
"""
import uiautomation as auto
import win32gui
import time

auto.uiautomation.SetGlobalSearchTimeout(2)


def find_wechat_hwnd():
    def enum_callback(hwnd, hwnd_list):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title == "微信":
                hwnd_list.append(hwnd)
        return True
    hwnd_list = []
    win32gui.EnumWindows(enum_callback, hwnd_list)
    if not hwnd_list:
        print("❌ 未找到微信窗口！")
        return None
    return hwnd_list[0]


def get_focused_control_info():
    """获取当前焦点控件的详细信息"""
    focused = auto.GetFocusedControl()
    if focused:
        bounds = focused.BoundingRectangle
        rect = f"({bounds.left},{bounds.top},{bounds.right},{bounds.bottom})" if bounds else ""
        print(f"焦点控件: {focused.ControlTypeName}")
        print(f"  Name: '{focused.Name}'")
        print(f"  ClassName: '{focused.ClassName}'")
        print(f"  Bounds: {rect}")
        print(f"  Depth: {focused.Depth}")
        
        # 打印父链
        print(f"  父链:")
        p = focused
        d = 0
        while p and d < 5:
            try:
                p = p.GetParentControl()
                if p:
                    print(f"    depth={d}: {p.ControlTypeName} | Name='{p.Name}' | ClassName='{p.ClassName}'")
                d += 1
            except:
                break
        return focused
    else:
        print("❌ 没有获取到焦点控件")
        return None


def get_cursor_pos():
    """获取当前鼠标位置（模拟点击输入框后有用）"""
    import pyautogui
    x, y = pyautogui.position()
    print(f"当前鼠标位置: ({x}, {y})")
    return x, y


if __name__ == '__main__':
    hwnd = find_wechat_hwnd()
    if not hwnd:
        exit(1)

    window = auto.ControlFromHandle(hwnd)
    print(f"微信窗口句柄: {hwnd}")
    
    # 先获取信息
    print("\n=== 当前焦点控件（请确保光标在输入框中）===")
    time.sleep(1)
    focused = get_focused_control_info()
    
    print("\n=== 鼠标当前位置 ===")
    get_cursor_pos()
    
    # 也获取消息区域的坐标用于推算
    try:
        msg_list = window.ListControl(Name='消息')
        bounds = msg_list.BoundingRectangle
        print(f"\n消息区域: ({bounds.left},{bounds.top})-({bounds.right},{bounds.bottom})")
        print(f"=> 输入框预估在 y={bounds.bottom} 至 y={bounds.bottom + 200} 之间")
    except:
        pass

    # 尝试在深度 6-8 找所有控件的类型分布
    print("\n=== 所有 CustomControl / PaneControl (depth≤6) ===")
    try:
        for ctrl, depth in auto.WalkControl(window, maxDepth=6):
            if ctrl.ControlTypeName in ('CustomControl', 'PaneControl'):
                name = ctrl.Name[:50] if ctrl.Name else "(unnamed)"
                print(f"  depth={depth} | {ctrl.ControlTypeName} | Name='{name}' | ClassName='{ctrl.ClassName}'")
    except:
        pass

    print("\n✅ 探测完成")
