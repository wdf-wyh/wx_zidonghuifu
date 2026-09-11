# Release Notes

## v1.1.0 — Open-source packaging

### Highlights

- **Docs**: 中英双语 README 主页；贡献指南与 Issue 模板
- **Security**: `config.example.py` + `.env.example`；API Key 走环境变量
- **DX**: 依赖补齐语音录制；打包说明同步
- **Ops**: GitHub Topics / Release 清单见 `docs/GITHUB_SETUP.md`

### Upgrade

1. 轮换旧 Key（若曾提交过明文）
2. `copy config.example.py config.py` 并 `copy .env.example .env`
3. `pip install -r requirements.txt`
4. 对照旧 `config.py` 合并 `name_exclude` / `audio_device_id` 等本地项

### Publish checklist

- [ ] GitHub Description / Topics 已设置（见 `docs/GITHUB_SETUP.md`）
- [ ] `docs/demo/` 放入 GIF 并在 README 引用
- [ ] `build_exe.bat` 产物上传到 Release
- [ ] 确认仓库中无明文 API Key
