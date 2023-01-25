import math
import time

import dramatiq
import geopandas as gpd
from shapely.geometry import Point
from telegram import ParseMode
from telegram.error import RetryAfter

from .bot import send_message
from .grabbers import GRABBERS
from .models import FlatInfo
from .settings import ALLOWED_LOCATION_GEOJSON, MAX_MEDIA_GROUP

allowed_location_df = gpd.read_file(ALLOWED_LOCATION_GEOJSON)

MAX_ATTEMPTS = 7


def prepare_message(info: FlatInfo, page: int = 1) -> str:
    lines = []

    if len(info.images) > MAX_MEDIA_GROUP:
        pages = int(math.ceil(len(info.images) / MAX_MEDIA_GROUP))
        lines.append(f"<i>Часть сообщения <b>{page}/{pages}</b> (всего {len(info.images)} фото)</i>")
    if info.location:
        lines.append(
            "<a href='https://www.google.com/maps/search/"
            f"?api=1&query={info.location.latitude},{info.location.longitude}'>Карта</a>"
        )
    if info.rooms:
        lines.append(f"Кол-во комнат: {info.rooms}")
    if info.area:
        lines.append(f"Площадь: {info.area}")
    if info.price:
        lines.append(f"Стоимость: {info.price}")

    return "\n".join(lines)


@dramatiq.actor(max_retries=2)
def send_error(message_data, exception_data):
    if message_data.get("options", {}).get("retries", 1) > MAX_ATTEMPTS:
        source, url, initial_info = message_data.get("args") or [None, None, None]
        if url:
            send_message(f"Не удалось забрать данные: {url}")


@dramatiq.actor(max_retries=MAX_ATTEMPTS, min_backoff=3000, max_backoff=60000)
def grab_info(source: str, url: str, initial_info: dict):
    grabber = GRABBERS.get(source)
    if not grabber:
        send_message(f"O_o вот это поворот - появился новый неизвестный источник: {source}")
        return

    info = grabber(url)

    if (
        info.location
        and not allowed_location_df.geometry.contains(Point(info.location.longitude, info.location.latitude))[0]
    ):
        return

    info.rooms = info.rooms or initial_info.get("rooms")
    info.area = info.area or initial_info.get("area")
    info.price = info.price or initial_info.get("price")

    images = info.images
    page = 1
    while images:
        try:
            send_message(
                text=prepare_message(info, page) + f"\n<a href='{url}'>{source.upper()}</a>",
                images=images[:MAX_MEDIA_GROUP],
                parse_mode=ParseMode.HTML,
            )
            images = images[MAX_MEDIA_GROUP:]
            page += 1

        except RetryAfter as rae:
            print(str(rae))
            time.sleep(rae.retry_after)
