def is_notify(chat_shot):
    """新版微信：通过 Name 中的 '条未读' 来判断是否有未读消息"""
    return '条未读' in chat_shot.Name or '条新消息' in chat_shot.Name


def is_notify_with_text(chat_shot):
    """新版微信：通过 Name 中的 '条未读' 来判断是否有未读消息"""
    return '条未读' in chat_shot.Name or '条新消息' in chat_shot.Name
