from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config.settings import settings

# Keyed by client IP. default_limits applies to every route as a baseline
# DoS guard; routes with @limiter.limit(...) (login, register, ...) get a
# stricter, more specific limit on top of it.
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT_DEFAULT])
