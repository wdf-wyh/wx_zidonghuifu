# GitHub 仓库设置（冲星清单）

仓库：https://github.com/wdf-wyh/wx_zidonghuifu

## About

- **Description**: `Windows 微信 AI 自动回复｜文字/图片/语音 ASR｜通义千问`
- **Website**:（可选）演示视频链接
- **Topics**: `wechat` `ai-agent` `qwen` `rpa` `uiautomation` `windows` `auto-reply` `asr`

English description suggestion: `AI WeChat auto-reply on Windows — text, vision, voice ASR — powered by Qwen`

## Releases

1. 打 tag（如 `v1.1.0`）
2. 运行 `build_exe.bat`，压缩产物目录
3. 上传到 Release，正文参考 `docs/RELEASE_NOTES.md`

## Discussions

可发一篇：「相对上游 ethanhwang1024/AI-Operating-Wechat 多了什么」

## 安全

若历史 commit 含过明文 Key：在 DashScope 控制台吊销并轮换；必要时用 `git filter-repo` 清理历史（需 force push，谨慎操作）。
