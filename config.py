# 选用模型，目前只支持千问:qwen_max,qwen_turbo,qwen_plus
model = "qwen_max"

# 多模态模型（用于识别图片内容），使用通义千问 VL 系列
model_vl = "qwen-vl-max"

# 阿里通义千问的apikey，去dashscope获取
qwen_apikey = "sk-5ab5c09182f74ba986be27330288c8de"

# 你不想用ai回复的人的列表
name_exclude = []

# AI提醒词，会加在AI的回复后面提醒
warn_word = ""

# 语音消息保存目录（相对于 exe/脚本所在目录，运行时自动创建）
voice_temp_dir = "voices/temp"

# ASR 语音识别模型（使用阿里云 Paraformer）
asr_model = "paraformer-v2"

# 系统音频录音设备 ID
# [5] = DirectSound 主声音捕获（捕获所有系统音频输出）
audio_device_id = 5
