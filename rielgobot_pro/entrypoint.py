import datetime as dt
import logging
import re
import time

import playwright.sync_api

from rielgobot_pro.bot import send_message
from rielgobot_pro.settings import (
    MAX_ERRORS_IN_A_ROW,
    SOURCE_TELEGRAM_CHAT_WEB_URL,
    SOURCE_TELEGRAM_LOCAL_STORAGE_SETUP,
)
from rielgobot_pro.tasks import grab_info, send_error

logger = logging.getLogger(__name__)


def main_loop():  # noqa: C901
    with open(SOURCE_TELEGRAM_LOCAL_STORAGE_SETUP, "r") as fd:
        evaluate_script = fd.read()

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

                full_text_locator = page.locator(".bubble-content").last.locator(".message")
                last_link_locator = full_text_locator.locator("a").last

                href = last_link_locator.get_attribute("href")
                if old_href == href:
                    continue
                old_href = href

                source = last_link_locator.text_content().strip().lower()

                full_text = full_text_locator.text_content().replace(" ", " ")
                rooms = int(re.findall(r"Кол-во комнат: (\d+)", full_text)[0])
                area = float(re.findall(r"Площадь: (\d+\.?\d*)", full_text)[0])
                price = re.findall(r"Стоимость: ([^Д]+)", full_text)[0].strip()

                grab_info.send_with_options(
                    args=(source, href, {"rooms": rooms, "area": area, "price": price}),
                    on_failure=send_error,
                )

                total_errors = 0

            except KeyboardInterrupt:
                break

            except Exception as ex:
                logger.exception(ex)
                total_errors += 1
                send_message(f"Ooops, ошибочка:\n{ex}"[:512])

            finally:
                print(dt.datetime.now())
                time.sleep(1)
                page.reload(wait_until="networkidle")

        if total_errors >= MAX_ERRORS_IN_A_ROW:
            send_message("Что-то мне поплохело, отдохну немного")

        browser.close()
