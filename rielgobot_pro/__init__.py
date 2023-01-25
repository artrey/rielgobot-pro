import dramatiq
from dramatiq.brokers.redis import RedisBroker

from rielgobot_pro import settings

redis_broker = RedisBroker(host=settings.REDIS_HOST)
dramatiq.set_broker(redis_broker)
