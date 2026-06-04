from slowapi import Limiter
from slowapi.util import get_remote_address
from .config import settings

# Use Redis storage for rate limiting if REDIS_URL is configured
storage_uri = settings.REDIS_URL if settings.REDIS_URL else "memory://"

limiter = Limiter(key_func=get_remote_address, storage_uri=storage_uri)
