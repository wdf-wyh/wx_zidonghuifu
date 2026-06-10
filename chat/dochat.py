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
        if not his[-1].isdigit():
            retries += 1
            logger.warning(f"do_chat_until_status: response '{his[-1]}' is not a digit, retry {retries}/{MAX_RETRIES}")
            time.sleep(2)
            continue
        return his
    logger.error(f"do_chat_until_status failed after {MAX_RETRIES} retries")
    raise RuntimeError(f"Failed to get valid status response after {MAX_RETRIES} retries")
