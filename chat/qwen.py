import dashscope
import random
import logging
import os
from http import HTTPStatus
from config import *

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

dashscope.api_key = qwen_apikey


def call_qwen_online(his, model_choice):
    history = his
    messages = []

    # 始终将第一条视为 system prompt（init_history[0] 固定为系统提示词）
    messages.append({'role': 'system', 'content': history[0]})
    history = history[1:]

    # 剩余消息按 assistant, user, assistant, user... 交替
    # 因为 init_history[1] 是 assistant 的回复 "我明白了"
    for i, h in enumerate(history):
        if i % 2 == 0:
            messages.append({'role': 'assistant', 'content': h})
        else:
            messages.append({'role': 'user', 'content': h})

    # debug: 打印最后3条消息
    for m in messages[-3:]:
        logger.debug(f"  [{m['role']}] {m['content'][:80]}")

    response = None
    try:
        if model_choice == "qwen_turbo":
            response = dashscope.Generation.call(
                dashscope.Generation.Models.qwen_turbo,
                messages=messages,
                seed=random.randint(1, 10000),
                result_format='message',
            )
        elif model_choice == "qwen_max":
            response = dashscope.Generation.call(
                dashscope.Generation.Models.qwen_max,
                messages=messages,
                seed=random.randint(1, 10000),
                result_format='message',
            )
        elif model_choice == "qwen_plus":
            response = dashscope.Generation.call(
                dashscope.Generation.Models.qwen_plus,
                messages=messages,
                seed=random.randint(1, 10000),
                result_format='message',
            )
        else:
            logger.error(f"Unknown model choice: {model_choice}")
            return his
    except Exception as e:
        logger.error(f"Qwen API call exception: {e}")
        return his

    if response.status_code == HTTPStatus.OK:
        reply = response['output']['choices'][0]['message']['content']
        logger.info(f"Qwen response({len(reply)}chars): {reply[:100]}")
        his.append(reply)
        return his
    else:
        logger.error(f"Qwen API call failed: status_code={response.status_code}, "
                      f"message={getattr(response, 'message', 'unknown')}")
        return his


def call_qwen_multimodal(his, image_paths, model_choice="qwen-vl-max"):
    """多模态模型调用：发送文本+图片给 VL 模型

    Args:
        his: 对话历史列表（与 call_qwen_online 格式一致）
        image_paths: 图片文件路径列表
        model_choice: VL 模型名，如 qwen-vl-max, qwen-vl-plus

    Returns:
        list: 更新后的对话历史（追加了模型回复）
    """
    # 多模态模型名映射：兼容多种写法
    model_map = {
        'qwen_vl_max': 'qwen-vl-max',
        'qwen_vl_plus': 'qwen-vl-plus',
    }
    model_choice = model_map.get(model_choice, model_choice)

    messages = []

    # 构造 system prompt
    messages.append({'role': 'system', 'content': [{'text': his[0]}]})

    # 构造对话轮次
    history = his[1:]
    for i, h in enumerate(history):
        if i % 2 == 0:
            # assistant 回复
            messages.append({'role': 'assistant', 'content': [{'text': h}]})
        else:
            # user 消息（纯文本）
            messages.append({'role': 'user', 'content': [{'text': h}]})

    # 将图片附加到最后一条 user 消息
    if image_paths:
        last_user_idx = None
        for msg in reversed(messages):
            if msg['role'] == 'user':
                last_user_idx = messages.index(msg)
                break

        if last_user_idx is not None:
            for img_path in image_paths:
                abs_path = os.path.abspath(img_path)
                if os.path.isfile(abs_path):
                    messages[last_user_idx]['content'].append(
                        {'image': f"file://{abs_path}"}
                    )
                    logger.info(f"Attached image to VL model: {abs_path}")
                else:
                    logger.warning(f"Image file not found for VL: {abs_path}")

    # debug: 打印最后3条消息
    for m in messages[-3:]:
        texts = [c.get('text', '') for c in m['content'] if 'text' in c]
        images = [c for c in m['content'] if 'image' in c]
        logger.debug(f"  [{m['role']}] text={''.join(texts)[:80]}, images={len(images)}")

    try:
        response = dashscope.MultiModalConversation.call(
            model=model_choice,
            messages=messages,
            seed=random.randint(1, 10000),
        )
    except Exception as e:
        logger.error(f"Qwen VL API call exception: {e}")
        # 模型不存在时尝试 fallback 模型
        fallback_models = ['qwen-vl-max', 'qwen-vl-plus']
        for fallback in fallback_models:
            if fallback == model_choice:
                continue
            logger.info(f"Trying fallback VL model: {fallback}")
            try:
                response = dashscope.MultiModalConversation.call(
                    model=fallback,
                    messages=messages,
                    seed=random.randint(1, 10000),
                )
                model_choice = fallback
                break
            except Exception:
                continue
        else:
            # 所有 fallback 都失败
            return his

    if response.status_code == HTTPStatus.OK:
        # VL 模型返回的 content 是 list
        reply_content = response['output']['choices'][0]['message']['content']
        if isinstance(reply_content, list):
            reply = ''.join(item.get('text', '') for item in reply_content)
        else:
            reply = str(reply_content)
        logger.info(f"Qwen VL response({len(reply)}chars): {reply[:100]}")
        his.append(reply)
        return his
    else:
        logger.error(f"Qwen VL API call failed: status_code={response.status_code}, "
                      f"message={getattr(response, 'message', 'unknown')}")
        # 模型不存在时尝试 fallback 模型
        fallback_models = ['qwen-vl-max', 'qwen-vl-plus']
        for fallback in fallback_models:
            if fallback == model_choice:
                continue
            logger.info(f"Trying fallback VL model: {fallback}")
            try:
                response = dashscope.MultiModalConversation.call(
                    model=fallback,
                    messages=messages,
                    seed=random.randint(1, 10000),
                )
                if response.status_code == HTTPStatus.OK:
                    reply_content = response['output']['choices'][0]['message']['content']
                    if isinstance(reply_content, list):
                        reply = ''.join(item.get('text', '') for item in reply_content)
                    else:
                        reply = str(reply_content)
                    logger.info(f"Qwen VL fallback response({len(reply)}chars): {reply[:100]}")
                    his.append(reply)
                    return his
            except Exception:
                continue
        return his
