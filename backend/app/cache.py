from cachetools import TTLCache
from functools import wraps
import json

# 20 minutes = 1200 seconds
# maxsize = 512 items
global_cache = TTLCache(maxsize=512, ttl=1200)

def with_cache(func):
    """Decorator to cache function results using cachetools TTLCache."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a deterministic key from func name and args
        key_parts = [func.__name__]
        key_parts.extend([str(a) for a in args])
        key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
        key = "|".join(key_parts)
        
        if key in global_cache:
            return global_cache[key]
            
        result = func(*args, **kwargs)
        global_cache[key] = result
        return result
    return wrapper
