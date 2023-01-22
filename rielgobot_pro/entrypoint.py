import datetime as dt
import re
import time

import geopandas as gpd
import playwright.sync_api
from shapely.geometry import Point
from telegram import ParseMode
from telegram.error import RetryAfter

from rielgobot_pro.bot import send_message
from rielgobot_pro.grabbers import GRABBERS
from rielgobot_pro.models import FlatInfo
from rielgobot_pro.settings import (
    ALLOWED_LOCATION_GEOJSON,
    MAX_ERRORS_IN_A_ROW,
    MAX_MEDIA_GROUP,
    SOURCE_TELEGRAM_CHAT_WEB_URL,
    SOURCE_TELEGRAM_LOCAL_STORAGE_SETUP,
)


def prepare_message(info: FlatInfo) -> str:
    lines = []

    if len(info.images) > MAX_MEDIA_GROUP:
        lines.append(f"<i>Должны быть еще фото (всего: {len(info.images)}</i>")
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


def main_loop():  # noqa: C901
    with open(SOURCE_TELEGRAM_LOCAL_STORAGE_SETUP, "r") as fd:
        evaluate_script = fd.read()

    allowed_location_df = gpd.read_file(ALLOWED_LOCATION_GEOJSON)

    with playwright.sync_api.sync_playwright() as p:
        browser_type = p.chromium
        browser = browser_type.launch(timeout=10000)
        page = browser.new_page()

        page.goto(SOURCE_TELEGRAM_CHAT_WEB_URL)
        page.evaluate(evaluate_script, [])
        page.goto(SOURCE_TELEGRAM_CHAT_WEB_URL, wait_until="networkidle")

        total_errors = 0
        old_href = None
        while total_errors < MAX_ERRORS_IN_A_ROW:
            try:
                try:
                    page.locator(".icon-arrow-down").locator("..").click(timeout=1000)
                except playwright.sync_api.TimeoutError:
                    pass

                full_text_locator = page.locator(".message-content").last.locator(".text-content")
                last_link_locator = full_text_locator.locator("a")

                href = last_link_locator.get_attribute("href")
                if old_href == href:
                    continue
                old_href = href

                source = last_link_locator.text_content().strip().lower()
                if source not in GRABBERS:
                    send_message(f"O_o Какой-то неизвестный источник: {source}")
                    continue

                full_text = full_text_locator.text_content().replace(" ", " ")
                rooms = int(re.findall(r"Кол-во комнат: (\d+)", full_text)[0])
                area = float(re.findall(r"Площадь: (\d+\.?\d*)", full_text)[0])
                price = re.findall(r"Стоимость: ([^Д]+)", full_text)[0].strip()

                grabber = GRABBERS[source]
                try:
                    info = grabber(href)
                except Exception as ex:
                    send_message(f"Не удалось забрать данные:\n{href}\n\n{ex}"[:512])
                    continue

                if info.location:
                    if not allowed_location_df.geometry.contains(
                        Point(info.location.longitude, info.location.latitude)
                    )[0]:
                        continue

                info.rooms = info.rooms or rooms
                info.area = info.area or area
                info.price = info.price or price

                images = info.images
                send_message(
                    text=prepare_message(info) + f"\n<a href='{href}'>{source.upper()}</a>",
                    images=images[:MAX_MEDIA_GROUP],
                    parse_mode=ParseMode.HTML,
                )
                images = images[MAX_MEDIA_GROUP:]

                while images:
                    time.sleep(1.5)  # telegram limitation: maximum 1 message per sec
                    send_message(
                        "_Продолжение_",
                        images=images[:MAX_MEDIA_GROUP],
                        disable_notification=True,
                        parse_mode=ParseMode.MARKDOWN_V2,
                    )
                    images = images[MAX_MEDIA_GROUP:]

                total_errors = 0

            except KeyboardInterrupt:
                break

            except RetryAfter as rae:
                print(str(rae))
                time.sleep(rae.retry_after)

            except Exception as ex:
                total_errors += 1
                send_message(f"Ooops, ошибочка:\n{ex}"[:512])

            finally:
                print(dt.datetime.now())
                time.sleep(1)
                page.reload(wait_until="networkidle")

        if total_errors >= MAX_ERRORS_IN_A_ROW:
            send_message("Что-то мне поплохело, отдохну немного")

        browser.close()
