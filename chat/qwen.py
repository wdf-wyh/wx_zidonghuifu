import dashscope
import random
import logging
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
