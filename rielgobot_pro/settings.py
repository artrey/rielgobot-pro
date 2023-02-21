import os

MAX_MEDIA_GROUP = int(os.getenv("MAX_MEDIA_GROUP", 10))
MAX_ERRORS_IN_A_ROW = int(os.getenv("MAX_ERRORS_IN_A_ROW", 3))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHAT_ID = os.getenv("TARGET_CHAT_ID")
SOURCE_TELEGRAM_CHAT_WEB_URL = os.getenv("SOURCE_TELEGRAM_CHAT_WEB_URL")
SOURCE_TELEGRAM_LOCAL_STORAGE_SETUP = os.getenv("SOURCE_TELEGRAM_LOCAL_STORAGE_SETUP")
ALLOWED_LOCATION_GEOJSON = os.getenv("ALLOWED_LOCATION_GEOJSON")
BS4_PARSER = os.getenv("BS4_PARSER", "html.parser")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
MIN_AREA = float(os.getenv("MIN_AREA", 20))
MAX_AREA = float(os.getenv("MAX_AREA", 100))
