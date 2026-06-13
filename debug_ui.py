"""
Scan image and voice message controls in WeChat chat area.

Steps:
1. Click on a chat that HAS image/voice messages (so they are visible)
2. Run this script
"""
import uiautomation as auto
import win32gui
import time

auto.uiautomation.SetGlobalSearchTimeout(2)


def list_audio_devices():
    """列出系统所有音频设备，帮助用户配置 WASAPI loopback"""
    try:
        import sounddevice as sd
        hostapis = sd.query_hostapis()
        devices = sd.query_devices()

        print("\n" + "=" * 80)
        print("AUDIO DEVICES (for WASAPI loopback voice recording)")
        print("=" * 80)
        for i, dev in enumerate(devices):
            ha_name = hostapis[dev['hostapi']]['name']
            is_input = dev['max_input_channels'] > 0
            is_loopback = 'loopback' in dev['name'].lower() if is_input else False
            marker = " [LOOPBACK]" if is_loopback else ""
            io_type = "INPUT" if is_input else "OUTPUT"
            print(f"  [{i:2d}] {dev['name']:50s} | {io_type:6s} | {ha_name}{marker}")

        print("\nTip: Set config.audio_device_id to the [ID] of a WASAPI INPUT device")
        print("Tip: If no loopback device, enable 'Stereo Mix' in Windows sound settings")
        print("=" * 80 + "\n")
    except ImportError:
        print("\n[AUDIO DEVICES: install sounddevice to query: pip install sounddevice]\n")
    except Exception as e:
        print(f"\n[AUDIO DEVICES query failed: {e}]\n")


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


def try_get_accessible_name(ctrl):
    """尝试通过多种方式获取控件的辅助功能名称"""
    try:
        legacy = ctrl.GetLegacyIAccessiblePattern()
        if legacy:
            return f"name='{legacy.Name}', role={legacy.Role}, state={legacy.State}, defaultAction='{legacy.DefaultAction}'"
    except:
        pass
    try:
        invoke = ctrl.GetInvokePattern()
        if invoke:
            return "Has InvokePattern (clickable)"
    except:
        pass
    try:
        expand = ctrl.GetExpandCollapsePattern()
        if expand:
            return "Has ExpandCollapsePattern"
    except:
        pass
    try:
        toggle = ctrl.GetTogglePattern()
        if toggle:
            return "Has TogglePattern"
    except:
        pass
    return ""


def dump_control_deep(ctrl, depth=0, max_depth=8):
    """Recursively dump control info with max depth limit"""
    if depth > max_depth:
        return
    indent = "  " * depth
    cn = ctrl.ClassName or ""
    name = ctrl.Name or ""
    r = ctrl.BoundingRectangle
    rect = f"({r.left},{r.top},{r.right},{r.bottom})" if r else "None"
    accessible_info = try_get_accessible_name(ctrl)
    extra = f" | accessible=({accessible_info})" if accessible_info else ""
    print(f"{indent}{ctrl.ControlTypeName} | cn='{cn}' | name='{name}' | rect={rect}{extra}")
    try:
        children = ctrl.GetChildren()
        for child in children:
            dump_control_deep(child, depth + 1, max_depth)
    except:
        pass


if __name__ == '__main__':
    # 首先列出音频设备，方便配置 WASAPI loopback
    list_audio_devices()

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
        dump_control_deep(window)
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

        # 语音关键词列表（用于检测语音消息）
        voice_keywords = ['Voice', 'Audio', '语音', '录音', 'voice', 'audio']

        # Check if it's an image message
        is_image = 'ChatBubbleReferItemView' in cn or 'Image' in cn or 'Picture' in cn or name == '图片' or '[图片]' in name

        # Check if it's a voice message
        is_voice = any(kw in cn or kw in name for kw in voice_keywords)

        if is_image:
            print(f"       >>> IMAGE MESSAGE <<<")
            print(f"       Children (all levels):")
            dump_control_deep(msg, depth=2, max_depth=6)

        if is_voice:
            print(f"       >>> VOICE MESSAGE <<<")
            # 额外信息：获取 LegacyIAccessible 模式属性
            try:
                legacy_pattern = msg.GetLegacyIAccessiblePattern()
                if legacy_pattern:
                    print(f"       LegacyIAccessible: name='{legacy_pattern.Name}', role={legacy_pattern.Role}, state={legacy_pattern.State}, defaultAction='{legacy_pattern.DefaultAction}'")
            except:
                pass
            # 获取所有可用属性
            for attr in ['AutomationId', 'FrameworkId', 'IsEnabled', 'IsOffscreen', 'ProcessId', 'NativeWindowHandle', 'IsKeyboardFocusable']:
                try:
                    val = getattr(msg, attr, None)
                    if val is not None:
                        print(f"       {attr}={val}")
                except:
                    pass
            print(f"       Children (all levels, max_depth=8):")
            dump_control_deep(msg, depth=2, max_depth=8)

            # 尝试右键菜单看是否有"转文字"选项
            try:
                rect = msg.BoundingRectangle
                if rect:
                    cx = (rect.left + rect.right) // 2
                    cy = (rect.top + rect.bottom) // 2
                    auto.RightClick(cx, cy, waitTime=0.5)
                    time.sleep(0.3)
                    print(f"       >>> RIGHT-CLICK CONTEXT MENU (if any):")
                    # 查找可能出现的菜单
                    for menu_name in ('Menu', 'ContextMenu', '菜单', '右键菜单'):
                        try:
                            ctx_menu = window.MenuControl(Name=menu_name)
                            if ctx_menu.Exists(0, 0):
                                dump_control_deep(ctx_menu, depth=2, max_depth=3)
                                break
                        except:
                            continue
                    # 点击其他地方关闭菜单
                    auto.Click(cx - 100, cy, waitTime=0.2)
                    time.sleep(0.2)
            except Exception as e:
                print(f"       [Right-click test failed: {e}]")

            # 尝试单击语音消息，看是否触发"转文字"按钮出现
            try:
                rect = msg.BoundingRectangle
                if rect:
                    cx = (rect.left + rect.right) // 2
                    cy = (rect.top + rect.bottom) // 2
                    msg.Click(simulateMove=False, waitTime=0.3)
                    time.sleep(0.5)
                    print(f"       >>> AFTER CLICK - New controls near voice bubble:")
                    # 重新获取语音控件，看看是否有新增子控件（转文字按钮）
                    refreshed_msg = window.ListControl(Name='消息').GetChildren()[idx] if idx < len(window.ListControl(Name='消息').GetChildren()) else None
                    if refreshed_msg:
                        dump_control_deep(refreshed_msg, depth=2, max_depth=8)
                    # 也检查是否有浮层/弹出窗口
                    for popup_name in ('转文字', 'Transcribe', '转换为文字', '语音转文字'):
                        try:
                            popup_btn = window.ButtonControl(Name=popup_name)
                            if popup_btn.Exists(0, 0):
                                print(f"       >>> FOUND TRANSCRIBE BUTTON: '{popup_name}'")
                                print(f"           Bounds: {popup_btn.BoundingRectangle}")
                        except:
                            continue
            except Exception as e:
                print(f"       [Click test failed: {e}]")

    print("\n[Done]")
