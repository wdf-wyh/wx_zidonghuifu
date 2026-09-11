"""复制为 config.py 后按需修改。API Key 推荐放环境变量 / .env，不要提交真实密钥。"""
import os

# 文本 / 多模态模型（通义千问）
model = os.environ.get("LLM_MODEL", "qwen_max")
model_vl = os.environ.get("LLM_MODEL_VL", "qwen-vl-max")

# 优先：DASHSCOPE_API_KEY / QWEN_API_KEY 环境变量
qwen_apikey = (
    os.environ.get("DASHSCOPE_API_KEY")
    or os.environ.get("QWEN_API_KEY")
    or ""
)

# 不自动回复的会话名（联系人 / 群）
name_exclude = ["文件传输助手"]

# AI 回复后缀提示（可留空）
warn_word = ""

# 语音临时目录（相对脚本 / exe 目录）
voice_temp_dir = "voices/temp"

# ASR 模型（DashScope Paraformer）
asr_model = "paraformer-v2"

# 系统音频捕获设备 ID（可用 check_audio_capture.py 查看）
audio_device_id = 5
