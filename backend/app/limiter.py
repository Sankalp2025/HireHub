import os

from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable rate limiting in tests so integration tests stay deterministic.
limiter = Limiter(
    key_func=get_remote_address,
    enabled=os.environ.get("ENVIRONMENT") != "test",
)
