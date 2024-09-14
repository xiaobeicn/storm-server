import redis
from app.core.config import settings

redis_client = redis.StrictRedis.from_url(settings.REDIS_URI.__str__())
