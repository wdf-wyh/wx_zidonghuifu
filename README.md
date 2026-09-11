# AI-Operating-Wechat

<p align="center">
  <strong>Windows 微信 AI 自动回复</strong> · Text / Image / Voice · 通义千问<br/>
  <sub>WeChat auto-reply agent on Windows · Qwen · UI Automation</sub>
</p>

<p align="center">
  <a href="#-中文">中文</a> ·
  <a href="#-english">English</a>
</p>

<p align="center">
  <a href="./LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-blue.svg" alt="license"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.9+-3776AB.svg" alt="python"></a>
  <a href="#-快速开始"><img src="https://img.shields.io/badge/os-Windows-0078D6.svg" alt="windows"></a>
  <a href="https://github.com/wdf-wyh/wx_zidonghuifu/stargazers"><img src="https://img.shields.io/github/stars/wdf-wyh/wx_zidonghuifu?style=social" alt="stars"></a>
  <a href="https://github.com/wdf-wyh/wx_zidonghuifu/issues"><img src="https://img.shields.io/github/issues/wdf-wyh/wx_zidonghuifu" alt="issues"></a>
</p>

<p align="center">
  <a href="#-效果演示">Demo</a> ·
  <a href="#-功能">Features</a> ·
  <a href="#-快速开始">Quick Start</a> ·
  <a href="TROUBLESHOOTING.md">Troubleshooting</a> ·
  <a href="CONTRIBUTING.md">Contributing</a>
</p>

---

## 🇨🇳 中文

微信消息回不过来？用大模型 + UI 自动化，在 **Windows 微信客户端**上自动读未读、理解上下文、回复文字 / 看图说话 / 语音转写。

> **相对上游**：本仓库在 [ethanhwang1024/AI-Operating-Wechat](https://github.com/ethanhwang1024/AI-Operating-Wechat) 基础上增强了多模态看图、语音消息 ASR、打包脚本与问题排查文档，面向微信 4.x（中文客户端）。

### ✨ 功能

| 能力 | 说明 |
|------|------|
| 未读驱动回复 | 扫描会话列表未读角标，跳过免打扰 |
| 文字对话 | 通义千问理解上下文后口语化回复 |
| 看图理解 | `qwen-vl` 识别聊天图片再决策 / 回复 |
| 发送表情图 | 可从 `images/` 选择预设图发送 |
| 语音消息 | 播放语音 → 录制系统音频 → Paraformer ASR 转写 |
| 黑名单 | `name_exclude` 跳过指定联系人 / 群 |
| 一键打包 | `build_exe.bat` 产出可分发目录 |

### 🎬 效果演示

上游演示视频（流程相同）：

https://github.com/ethanhwang1024/AI-Operating-Wechat/assets/89822193/3e62bd19-88e7-4dda-b98a-fdd22de0f1a0

本地录屏请放到 [`docs/demo/`](docs/demo/)，并在此处引用 GIF。

### ⚠️ 使用须知

- **仅 Windows + 中文微信客户端**；需保持微信主窗口完整可见
- 依赖 UI Automation，微信大版本升级可能导致控件失效 → 先看 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- 请勿用于骚扰、冒充或未授权代聊；API Key **不要提交到 Git**
- 若仓库历史中曾出现过明文 Key，请到 [DashScope 控制台](https://dashscope.aliyun.com/) **立刻轮换**

### 🚀 快速开始

**1. 克隆**

```bash
git clone https://github.com/wdf-wyh/wx_zidonghuifu.git
cd wx_zidonghuifu
```

**2. 安装依赖**

```bash
pip install -r requirements.txt
```

**3. 配置 API Key**

```bash
copy config.example.py config.py
copy .env.example .env
```

编辑 `.env`（推荐）或 `config.py`：

```env
DASHSCOPE_API_KEY=sk-你的密钥
```

密钥在 [DashScope](https://dashscope.aliyun.com/) 申请。

**4. 准备微信**

1. 打开电脑微信，窗口完整可见  
2. 将「文件传输助手」置顶（程序空闲时会点回此处）  
3. 按需修改 `config.py` 中的 `name_exclude`、人设相关 prompt（`chat/prompt.py`）

**5. 运行**

```bash
python main.py
```

管理员权限通常更稳（UI 自动化）。

**6. 可选：打包 exe**

```bat
build_exe.bat
```

产物目录内含 `config.py`，改 Key 无需重新打包。详见 [docs/RELEASE_NOTES.md](docs/RELEASE_NOTES.md)。

### ⚙️ 配置速查

| 项 | 位置 | 说明 |
|----|------|------|
| `DASHSCOPE_API_KEY` | `.env` / 环境变量 | 通义 API Key |
| `model` / `model_vl` | `config.py` | 文本 / 多模态模型名 |
| `name_exclude` | `config.py` | 不自动回复的会话名 |
| `asr_model` | `config.py` | 语音识别模型，如 `paraformer-v2` |
| `audio_device_id` | `config.py` | 系统录音设备 ID（默认 `5`） |
| `warn_word` | `config.py` | 追加在 AI 回复后的提示后缀 |
| 人设 / 决策 prompt | `chat/prompt.py` | 口语风格与状态机话术 |

查设备 ID：`python check_audio_capture.py`

### 📁 目录结构

```
wx_zidonghuifu/
├── main.py              # 入口
├── agent.py             # 状态机：读未读 → 理解 → 回复
├── config.example.py    # 配置模板（复制为 config.py）
├── act/                 # 微信 UI 操作 / 截图 / 语音录制
├── chat/                # Prompt + 通义千问调用
├── images/              # 可发送的预设图片
├── docs/demo/           # 演示 GIF（自行放入）
├── TROUBLESHOOTING.md   # 问题排查
└── build_exe.bat        # PyInstaller 打包
```

### 🤝 贡献

欢迎 Issue / PR：新版本微信适配、稳定性、文档与演示素材。见 [CONTRIBUTING.md](CONTRIBUTING.md)。

### 📣 致谢

灵感来自 [self-operating-computer](https://github.com/OthersideAI/self-operating-computer) 与上游 [AI-Operating-Wechat](https://github.com/ethanhwang1024/AI-Operating-Wechat)。

### 📄 License

[GNU GPLv3](./LICENSE)

---

## 🇬🇧 English

Too many WeChat messages? Run a **Qwen-powered agent** on the **Windows WeChat desktop client**: unread-driven replies, vision for chat images, and ASR for voice messages.

> **Fork note**: Built on [ethanhwang1024/AI-Operating-Wechat](https://github.com/ethanhwang1024/AI-Operating-Wechat) with multimodal vision, voice ASR, packaging scripts, and troubleshooting docs. **Chinese WeChat client on Windows only.**

### Features

| Feature | Description |
|---------|-------------|
| Unread-driven loop | Scan chat list badges; skip muted chats |
| Text replies | Qwen contextual, colloquial replies |
| Vision | `qwen-vl` understands images in the thread |
| Send stickers/images | Pick files from `images/` |
| Voice messages | Play → capture system audio → Paraformer ASR |
| Blocklist | `name_exclude` skips contacts/groups |
| One-click build | `build_exe.bat` ships a redistribute folder |

### Demo

Upstream demo (same flow):

https://github.com/ethanhwang1024/AI-Operating-Wechat/assets/89822193/3e62bd19-88e7-4dda-b98a-fdd22de0f1a0

Add your own GIFs under [`docs/demo/`](docs/demo/).

### Disclaimer

- Windows + **Chinese** WeChat desktop only; keep the main window fully visible  
- UI Automation breaks when WeChat upgrades — see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)  
- Do not use for spam, impersonation, or unauthorized chatting  
- Never commit API keys; rotate any key that was ever exposed

### Quick start

```bash
git clone https://github.com/wdf-wyh/wx_zidonghuifu.git
cd wx_zidonghuifu
pip install -r requirements.txt
copy config.example.py config.py
copy .env.example .env
```

Set `DASHSCOPE_API_KEY` in `.env` ([DashScope](https://dashscope.aliyun.com/)), pin **File Transfer** in WeChat, then:

```bash
python main.py
```

Optional: run `build_exe.bat` for a portable folder.

### Config cheat sheet

| Key | Where | Purpose |
|-----|--------|---------|
| `DASHSCOPE_API_KEY` | `.env` | Tongyi / DashScope API key |
| `model` / `model_vl` | `config.py` | Text / vision model ids |
| `name_exclude` | `config.py` | Sessions to skip |
| `asr_model` | `config.py` | Speech model (e.g. `paraformer-v2`) |
| `audio_device_id` | `config.py` | Loopback/capture device id |
| Prompts | `chat/prompt.py` | Persona & agent state prompts |

List audio devices: `python check_audio_capture.py`

### Contributing

Issues and PRs welcome — WeChat UI adapters, reliability, docs, demos. See [CONTRIBUTING.md](CONTRIBUTING.md).

### Thanks

Inspired by [self-operating-computer](https://github.com/OthersideAI/self-operating-computer) and upstream [AI-Operating-Wechat](https://github.com/ethanhwang1024/AI-Operating-Wechat).

### License

[GNU GPLv3](./LICENSE)
