import functools

from telegram import Bot, InputMediaPhoto

from rielgobot_pro.constants import TARGET_CHAT_ID, TELEGRAM_BOT_TOKEN


@functools.lru_cache(maxsize=None)
def bot() -> Bot:
    return Bot(TELEGRAM_BOT_TOKEN)


def send_message(text, images=None, disable_notification=None, **kwargs):
    if images:
        media = [
            InputMediaPhoto(media=url, caption=text if idx == 0 else None, **kwargs) for idx, url in enumerate(images)
        ]
        return bot().send_media_group(chat_id=TARGET_CHAT_ID, media=media, disable_notification=disable_notification)
    else:
        bot().send_message(chat_id=TARGET_CHAT_ID, text=text, disable_notification=disable_notification, **kwargs)
