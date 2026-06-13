import sys
import os
import logging
from act.Entry import *
from act.voice import play_and_capture_voice
from chat.Entry import *
from chat.qwen import transcribe_speech
from config import *
from datetime import datetime

logger = logging.getLogger(__name__)

# 获取程序所在目录（exe 或脚本所在位置）
if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

auto.uiautomation.SetGlobalSearchTimeout(1)

# 延迟初始化（在 execute("0") 中才真正获取微信控件）
window = None
chat_list_panel = None
chat_list = []
notify_list = []
name = None
chat_shot = None
history = init_history
chat_text = ""
captured_images = []  # 当前对话中截取的图片路径列表
captured_voices = []  # 当前对话中捕获的语音文件路径列表

# 图片临时目录
IMAGE_TEMP_DIR = os.path.join(APP_DIR, 'images', 'temp')

# 语音临时目录
VOICE_TEMP_DIR = os.path.join(APP_DIR, voice_temp_dir)


def execute(num):
    global window
    global chat_list_panel
    global chat_list
    global notify_list
    global name
    global chat_shot
    global history
    global chat_text
    global captured_images
    global captured_voices
    if num == "0":
        # 重新获得新消息
        time.sleep(1)
        try:
            window = get_window()
            chat_list_panel = get_chat_list_panel(window)
            chat_list = chat_list_panel.GetChildren()
            notify_list = []
            for chat_shot in chat_list:
                if is_notify_with_text(chat_shot):
                    name = extract_chat_name(chat_shot)
                    if name in name_exclude:
                        continue
                    notify_list.append(chat_shot)
        except Exception as e:
            logger.warning(f"State 0: 查找微信窗口失败: {e}")
            return "0"
        if len(notify_list) == 0:
            return "0"
        else:
            return "1"
    elif num == "1":
        # 点击chat_shot
        try:
            for chat_shot_inner in notify_list:
                name = extract_chat_name(chat_shot_inner)
                if name in name_exclude:
                    continue
                chat_shot = chat_shot_inner
                return "2"
        except Exception as e:
            logger.warning(f"State 1: 处理聊天列表失败: {e}")
            notify_list = []
            return "0"
        notify_list = []
        return "0"
    elif num == "2":
        history = init_history
        new_message_coming_prompt = new_message_coming_prompt_tp.format(name, name)
        history.append(new_message_coming_prompt)
        try:
            history = do_chat_until_status(model, history)
        except RuntimeError as e:
            logger.error(f"State 2 model call failed: {e}")
            return "0"
        status = history[-1]
        return status
    elif num == "3":
        try:
            chat_shot.Click(simulateMove=False, waitTime=1)
            try:
                window.EditControl(Name=name)
            except:
                # 退回状态2
                logger.warning(f"State 3: EditControl '{name}' not found, fallback to state 2")
                return "2"
            chat_text = get_chat_text(window)
            logger.info(f"State 3: chat_text ({len(chat_text)}chars): {chat_text[:200]}")

            # 截取聊天中的图片
            captured_images.clear()
            image_lines = get_chat_images(window)
            if image_lines:
                logger.info(f"State 3: found {len(image_lines)} image(s), capturing...")
                os.makedirs(IMAGE_TEMP_DIR, exist_ok=True)
                for idx, img_line in enumerate(image_lines):
                    save_path = os.path.join(IMAGE_TEMP_DIR, f"{name}_{idx}.png")
                    result = capture_chat_image(img_line, save_path)
                    if result:
                        captured_images.append(result)
                    # 每张图片之间留间隔，避免操作过快
                    time.sleep(0.3)
                logger.info(f"State 3: captured {len(captured_images)} image(s) to temp dir")

            # 捕获聊天中的语音消息 → 双击播放 → 录制系统音频 → ASR 转文字
            captured_voices.clear()
            voice_lines = get_chat_voices(window)
            if voice_lines:
                logger.info(f"State 3: found {len(voice_lines)} voice message(s), processing...")
                os.makedirs(VOICE_TEMP_DIR, exist_ok=True)

                # 获取聊天行列表，过滤掉 None 项，匹配语音消息的文本位置
                chat_lines = [cl for cl in get_chat_lines(window) if cl is not None]

                for idx, voice_line in enumerate(voice_lines):
                    # 找到对应的语音消息元组
                    voice_info = None
                    for line_type, sender, content in chat_lines:
                        if line_type == "voice":
                            voice_info = (line_type, sender, content)
                            break

                    if voice_info is None:
                        continue

                    line_type, voice_sender, voice_duration = voice_info

                    # 1. 双击播放 + 录制系统音频（始终保存 WAV 文件）
                    wav_path = os.path.join(VOICE_TEMP_DIR, f"{name}_{idx}.wav")
                    logger.info(f"Voice [{idx}]: playing and recording (sender='{voice_sender}', duration='{voice_duration}')...")
                    recorded_path = play_and_capture_voice(voice_line, voice_duration, wav_path)

                    # 2. 文件已保存，尝试 ASR 语音转文字
                    if recorded_path and os.path.isfile(recorded_path) and asr_model:
                        transcribed_text = transcribe_speech(recorded_path, asr_model)
                        if transcribed_text:
                            # 3. 将转文字结果替换到 chat_text 中
                            original_text = __to_text((line_type, voice_sender, voice_duration))
                            if voice_sender:
                                replacement = f"{voice_sender} 发送了一条语音（转文字：{transcribed_text}）"
                            else:
                                replacement = f"发送了一条语音（转文字：{transcribed_text}）"
                            chat_text = chat_text.replace(original_text, replacement, 1)
                            captured_voices.append(recorded_path)
                            logger.info(f"Voice [{idx}] transcribed: '{transcribed_text}'")
                        else:
                            logger.warning(f"Voice [{idx}] ASR failed (silent or unrecognized)")
                            captured_voices.append(recorded_path)
                    else:
                        logger.warning(f"Voice [{idx}] ASR disabled, file saved for inspection")

                    # 每处理一条语音后等待一下，避免操作过快
                    time.sleep(0.5)
        except Exception as e:
            logger.error(f"State 3: 处理聊天内容异常: {e}")
            return "0"

            logger.info(f"State 3: processed {len(captured_voices)} voice message(s)")
            logger.info(f"State 3: chat_text after voice transcription ({len(chat_text)}chars): {chat_text[:300]}")
        return "4"
    elif num == "4":
        # 语音转文字已嵌入到 chat_text 中，直接使用
        if captured_images:
            history_message_prompt = history_message_prompt_vl_tp.format(name, datetime.now(),
                                                                        chat_text, name)
            logger.info(f"State 4: using VL prompt (no image-send option)")
        else:
            history_message_prompt = history_message_prompt_tp.format(name, datetime.now(),
                                                                     chat_text, name, name)
        history.append(history_message_prompt)

        if captured_images:
            # 有图片：使用多模态模型，让 AI 看到图片后决策
            logger.info(f"State 4: using VL model with {len(captured_images)} image(s)")
            try:
                history = do_chat_multimodal_until_status(model_vl, history, captured_images)
            except RuntimeError as e:
                logger.error(f"State 4 VL model call failed: {e}")
                return "0"
            # 清理临时图片
            _cleanup_temp_images()
        else:
            # 纯文本决策
            try:
                history = do_chat_until_status(model, history)
            except RuntimeError as e:
                logger.error(f"State 4 model call failed: {e}")
                return "0"

        status = history[-1]
        return status
    elif num == "5":
        if captured_images:
            input_prompt = vl_input_prompt_tp
            logger.info(f"State 5: using VL model with {len(captured_images)} image(s) for text reply")
        else:
            input_prompt = input_prompt_tp
        history.append(input_prompt)

        if captured_images:
            try:
                history = call_qwen_multimodal(history, captured_images, model_vl)
            except Exception as e:
                logger.error(f"State 5 VL model call failed: {e}")
                try:
                    history = do_chat(model, history)
                except RuntimeError as e2:
                    logger.error(f"State 5 fallback text call failed: {e2}")
                    return "0"
        else:
            try:
                history = do_chat(model, history)
            except RuntimeError as e:
                logger.error(f"State 5 model call failed: {e}")
                return "0"
        # 重新激活窗口，确保 EditControl 可定位
        try:
            window.SetActive()
            time.sleep(0.5)
        except:
            pass
        try:
            send_msg(name, window, history[-1])
        except:
            return "0"
        if len(notify_list) <= 1:
            notify_list = []
            try:
                for item in chat_list:
                    if '文件传输助手' in extract_chat_name(item):
                        item.Click(simulateMove=False, waitTime=1)
                        break
            except:
                pass
            return "0"
        else:
            notify_list = notify_list[1:]
            return "1"

    elif num == "6":
        # AI 决定发送图片
        image_prompt = image_prompt_tp
        history.append(image_prompt)
        try:
            history = do_chat(model, history)
        except RuntimeError as e:
            logger.error(f"State 6 model call failed: {e}")
            return "0"

        image_choice = history[-1].strip().lower()
        logger.info(f"State 6: AI chose image '{image_choice}'")

        # 安全构建图片路径，防止目录穿越
        image_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
        image_path = None

        # 按优先级尝试匹配：精确名称 → 默认图片
        for ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif']:
            candidate = os.path.normpath(os.path.join(image_dir, f"{image_choice}{ext}"))
            # 安全检查：确保路径仍在 images 目录内
            if candidate.startswith(image_dir) and os.path.isfile(candidate):
                image_path = candidate
                break

        if image_path is None:
            # 尝试用 default 图片
            default_candidate = os.path.normpath(os.path.join(image_dir, "default.png"))
            if default_candidate.startswith(image_dir) and os.path.isfile(default_candidate):
                image_path = default_candidate
                logger.warning(f"State 6: image '{image_choice}' not found, using default")

        if image_path is not None:
            try:
                # 重新激活窗口
                window.SetActive()
                time.sleep(0.5)
                send_image(name, window, image_path)
                history.append(end_prompt_tp)
                logger.info(f"State 6: sent image '{image_path}' to '{name}'")
            except Exception as e:
                logger.error(f"State 6 send_image failed: {e}")
                return "0"
        else:
            # 没有可用图片，回退到文字回复
            logger.warning(f"State 6: no image available, falling back to text reply")
            history.append(input_prompt_tp)
            try:
                history = do_chat(model, history)
            except RuntimeError as e:
                logger.error(f"State 6 fallback text call failed: {e}")
                return "0"
            try:
                send_msg(name, window, history[-1])
            except:
                return "0"

        # 同 State 5 的清理逻辑
        if len(notify_list) <= 1:
            notify_list = []
            try:
                for item in chat_list:
                    if '文件传输助手' in extract_chat_name(item):
                        item.Click(simulateMove=False, waitTime=1)
                        break
            except:
                pass
            return "0"
        else:
            notify_list = notify_list[1:]
            return "1"


def _cleanup_temp_images():
    """清理本次对话中截取的临时图片文件"""
    # 注释掉清理逻辑，保留截图以便查看
    # global captured_images
    # for img_path in captured_images:
    #     try:
    #         if os.path.isfile(img_path):
    #             os.remove(img_path)
    #             logger.debug(f"Cleaned up temp image: {img_path}")
    #     except Exception as e:
    #         logger.warning(f"Failed to clean up temp image {img_path}: {e}")
    # captured_images.clear()
    pass
