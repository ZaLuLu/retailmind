from slowapi import Limiter
from slowapi.util import get_remote_address
from .config import settings
import logging

logger = logging.getLogger(__name__)

# Use Redis storage for rate limiting if REDIS_URL is configured and reachable
storage_uri = "memory://"
if settings.REDIS_URL:
    try:
        import redis
        # Verify connection with a short timeout to prevent startup hangs
        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
        client.ping()
        storage_uri = settings.REDIS_URL
    except Exception as e:
        logger.warning(
            "Redis rate limiter store is configured but offline. "
            "Falling back to local memory rate limiting. Error: %s",
            e
        )

limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)
