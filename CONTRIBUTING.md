# Contributing / 贡献指南

Thanks for interest in **AI-Operating-Wechat** (`wx_zidonghuifu`).  
感谢关注本仓库。欢迎 Issue / PR。

## 优先方向 / Good first areas

- 新版本微信 UI 适配（请附 `debug_ui.py` 控件树片段）
- 语音录制设备兼容、ASR 失败排查
- 文档、演示 GIF、英文润色
- 稳定性与日志可读性

## 开发环境 / Setup

```bash
pip install -r requirements.txt
copy config.example.py config.py
copy .env.example .env
# 编辑 .env 填入 DASHSCOPE_API_KEY
python main.py
```

请勿提交真实 API Key、`.env`、含隐私的聊天截图。

Do **not** commit real API keys, `.env`, or private chat screenshots.

## PR 建议 / PR tips

1. 改动尽量小、可回滚；说明「为什么」  
2. 涉及微信控件：写明微信版本与复现步骤  
3. 新增配置项：同步 `config.example.py` 与 README 速查表  
4. Keep Windows + Chinese WeChat as the primary path

## 行为准则 / Conduct

讨论对事不对人。涉及账号安全、绕过登录、批量骚扰的需求一律不接受。  
Be respectful. Requests about account abuse, login bypass, or mass spam will be closed.
