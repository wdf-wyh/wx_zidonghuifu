# AI-Operating-Wechat 问题排查手册

## 1. 千问模型调用返回"嗨，有啥事？"等无关回复

### 现象
模型始终回复"嗨，有啥事儿？"（AI生成），而不是根据聊天内容正常回复。

### 原因 A：角色分配反转（历史问题，已修复）
`chat/qwen.py` 中 `call_qwen_online` 构造 `messages` 时，`user` 和 `assistant` 角色完全颠倒。

```python
# ❌ 错误（旧代码）
if count % 2 == 1:
    messages.append({'role': 'user', 'content': h})   # 应该是 assistant
else:
    messages.append({'role': 'assistant', 'content': h}) # 应该是 user
```

`init_history` 的正确结构是：
```
[system, assistant, user, assistant, user, assistant, ...]
#  index:     0          1      2          3      4          5
```

- `history[0]` → `system`
- `history[1]`(assistant 回复) → **从 0 开始，偶数位** `assistant`
- `history[2]`(user 输入) → **奇数位** `user`

#### 修复
```python
# ✅ 正确
messages.append({'role': 'system', 'content': history[0]})
history = history[1:]
for i, h in enumerate(history):
    if i % 2 == 0:
        messages.append({'role': 'assistant', 'content': h})
    else:
        messages.append({'role': 'user', 'content': h})
```

**相关文件**: [chat/qwen.py](file:///e:/Users/MSN/Desktop/工程/AI-Operating-Wechat/chat/qwen.py)

### 原因 B：聊天记录读取为空
模型收到的 `history_message_prompt` 中聊天记录为空，模型不知道要回复什么。

#### 排查步骤
1. 在 `agent.py` state 3 添加日志，查看 `chat_text` 内容
2. 运行 `debug_ui.py` 探测消息列表控件结构

#### 检查清单
- [ ] 微信是否已点击某个聊天会话（右侧有消息内容）
- [ ] 消息列表控件是否能被 uiautomation 找到

#### 修复（WeChat 4.x）
微信 4.x (Electron 版) 的控件结构变化：
- 文本消息: `ListItemControl(ClassName='mmui::ChatTextItemView')`，内容在 `Name`
- 时间/系统消息: `ListItemControl(ClassName='mmui::ChatItemView')`，内容在 `Name`
- ❌ 不再有 `ButtonControl` 子控件

修改 `act/seeker.py` 中 `__classify_chat_type`，按 `ClassName` 判断控件类型：
```python
cn = chat_line.ClassName or ""
if cn == 'mmui::ChatTextItemView':
    return "chat", sender, chat_line.Name.strip()
if cn == 'mmui::ChatItemView':
    # 系统消息/时间/拍一拍等
```

**相关文件**: [act/seeker.py](file:///e:/Users/MSN/Desktop/工程/AI-Operating-Wechat/act/seeker.py#L119-L134)

---

## 2. API 调用失败（status 400）

### 现象
```
status: 400, message: Access denied, please make sure your account is in good standing.
```

### 原因
阿里云 Dashscope 账户问题：
1. **账户欠费** — 最常见原因
2. API Key 过期或被吊销
3. 账户被风控

### 解决方案
1. 访问 [Dashscope 控制台](https://dashscope.aliyun.com/) 检查账户余额
2. 欠费则充值
3. 生成新 API Key 并更新 `config.py`
4. **安全提醒**: 旧 Key 应立即在阿里云控制台吊销

**相关文件**: [config.py](file:///e:/Users/MSN/Desktop/工程/AI-Operating-Wechat/config.py)

---

## 3. 模型无限重试（死循环）

### 现象
`do_chat` 或 `do_chat_until_status` 无限循环，程序卡住。

### 原因
原代码是 `while True` 无退出条件的死循环，API 失败时会一直重试。

### 修复
添加最大重试次数限制：
```python
MAX_RETRIES = 5
while retries < MAX_RETRIES:
    ...
retries += 1
raise RuntimeError("Model call failed after N retries")
```

同时 `agent.py` 中捕获异常，安全回退到扫描状态：
```python
try:
    history = do_chat_until_status(model, history)
except RuntimeError as e:
    logger.error(f"State X model call failed: {e}")
    return "0"  # 回到重新扫描
```

**相关文件**: [chat/dochat.py](file:///e:/Users/MSN/Desktop/工程/AI-Operating-Wechat/chat/dochat.py), [agent.py](file:///e:/Users/MSN/Desktop/工程/AI-Operating-Wechat/agent.py)

---

## 4. 发送消息失败

### 现象
`send_msg` 抛出异常，程序无法正常回复。

### 原因 A：输入框控件找不到
微信 4.x 输入框为 `EditControl(ClassName='mmui::ChatInputField')`，Name 是**聊天对象名**（动态值）。

#### 修复
直接用 `window.EditControl(Name=name)` 查找即可，与代码一致。

### 原因 B：发送按钮找不到
微信 4.x (Electron 版) 没有 `ButtonControl(Name='发送(S)')`，通过 `Ctrl+V` 粘贴后按 `Enter` 发送。

#### 修复
```python
edit.SendKeys('{Ctrl}v', waitTime=0.1)
edit.SendKeys('{Enter}', waitTime=0.3)  # 代替找发送按钮
```

**相关文件**: [act/writer.py](file:///e:/Users/MSN/Desktop/工程/AI-Operating-Wechat/act/writer.py)

---

## 5. 调试工具

### 探测 UI 控件结构
使用 `debug_ui.py`（在项目根目录）：
```powershell
python debug_ui.py
```
该脚本会输出微信窗口的完整控件树，包括：
- 消息列表控件及子项
- 输入框控件及坐标
- 发送按钮控件

**相关文件**: [debug_ui.py](file:///e:/Users/MSN/Desktop/工程/AI-Operating-Wechat/debug_ui.py)

---

## 6. 微信版本兼容性速查

| 功能 | 旧版 WeChat | 4.x (Electron 版) |
|------|-----------|-------------------|
| 消息文本控件 | `ButtonControl` | `ListItemControl(ClassName='mmui::ChatTextItemView')`，Name=内容 |
| 时间/系统消息 | `TextControl` | `ListItemControl(ClassName='mmui::ChatItemView')`，Name=内容 |
| 输入框 | `EditControl(Name='聊天对象名')` | `EditControl(Name='聊天对象名', ClassName='mmui::ChatInputField')` |
| 发送按钮 | `ButtonControl(Name='发送(S)')` | **不存在**，需用 `{Enter}` 发送 |
| 会话列表 | `ListControl(ClassName='mmui::XTableView')` | 同上 |

---

## 快速排查流程

当程序异常时，按以下顺序排查：

1. **看控制台日志**
   - 有 `ERROR` 日志？→ 检查 API 或 UI 错误
   - 只有 `INFO` 但回复不对？→ 检查模型调用上下文

2. **检查 API 调用**
   - 日志中是否有 `Qwen response`？→ 确认模型被调用
   - 是否有 `status: 4xx`？→ Dashscope 账户问题

3. **检查消息读取**
   - 日志中 `State 3: chat_text (Nchars)` 是否为 0？
   - 是 → 运行 `debug_ui.py` 探测控件结构
   - 否 → 检查模型上下文构造逻辑

4. **检查发送**
   - `send_msg` 是否抛出异常？
   - 检查输入框控件是否能被定位
