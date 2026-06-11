import time
import logging

from chat.qwen import *

logger = logging.getLogger(__name__)

MAX_RETRIES = 5


def do_chat(model_choice, his):
    retries = 0
    while retries < MAX_RETRIES:
        if "qwen" in model_choice:
            size = len(his)
            his = call_qwen_online(his, model_choice)
            if size == len(his):
                retries += 1
                logger.warning(f"Qwen API returned no response, retry {retries}/{MAX_RETRIES}")
                time.sleep(2)
                continue
            return his
    logger.error(f"do_chat failed after {MAX_RETRIES} retries")
    raise RuntimeError(f"Qwen model call failed after {MAX_RETRIES} retries")


def _extract_status_digit(response):
    """从模型响应中提取状态数字 (3/5/6)

    模型有时会输出额外文字（如 "5\\n\\n回复内容"），此函数尝试提取首位合法状态数字。

    Returns:
        str: 提取的状态数字，或 None
    """
    text = response.strip()
    # 直接是纯数字
    if text.isdigit() and text in ('3', '5', '6'):
        return text
    # 从开头提取数字
    for line in text.split('\n'):
        line = line.strip()
        if line.isdigit() and line in ('3', '5', '6'):
            return line
        # 处理 "5、回复" 或 "5.回复" 格式
        if line and line[0].isdigit() and line[0] in ('3', '5', '6'):
            return line[0]
    return None


def do_chat_until_status(model_choice, his):
    retries = 0
    while retries < MAX_RETRIES:
        size = len(his)
        his = do_chat(model_choice, his)
        if size == len(his):
            retries += 1
            logger.warning(f"do_chat_until_status: do_chat returned no new content, retry {retries}/{MAX_RETRIES}")
            time.sleep(2)
            continue

        status = _extract_status_digit(his[-1])
        if status is not None:
            # 替换为干净的数字
            his[-1] = status
            logger.info(f"do_chat_until_status: extracted status '{status}' from response")
            return his

        retries += 1
        logger.warning(f"do_chat_until_status: cannot extract status from '{his[-1]}', retry {retries}/{MAX_RETRIES}")
        time.sleep(2)
        continue

    logger.error(f"do_chat_until_status failed after {MAX_RETRIES} retries")
    raise RuntimeError(f"Failed to get valid status response after {MAX_RETRIES} retries")


def do_chat_multimodal_until_status(model_choice, his, image_paths):
    """使用多模态模型进行状态决策（AI 看到图片后决定回复/发图）

    Args:
        model_choice: 多模态模型名
        his: 对话历史
        image_paths: 已截取的图片路径列表

    Returns:
        list: 更新后的对话历史，最后一条是状态数字

    Raises:
        RuntimeError: 超过最大重试次数
    """
    retries = 0
    while retries < MAX_RETRIES:
        size = len(his)
        his = call_qwen_multimodal(his, image_paths, model_choice)
        if size == len(his):
            retries += 1
            logger.warning(f"do_chat_multimodal: no new content, retry {retries}/{MAX_RETRIES}")
            time.sleep(2)
            continue

        status = _extract_status_digit(his[-1])
        if status is not None:
            his[-1] = status
            logger.info(f"do_chat_multimodal_until_status: extracted status '{status}'")
            return his

        retries += 1
        logger.warning(f"do_chat_multimodal: cannot extract status from '{his[-1]}', retry {retries}/{MAX_RETRIES}")
        time.sleep(2)
        continue

    logger.error(f"do_chat_multimodal_until_status failed after {MAX_RETRIES} retries")
    raise RuntimeError(f"Failed to get valid multimodal status after {MAX_RETRIES} retries")
