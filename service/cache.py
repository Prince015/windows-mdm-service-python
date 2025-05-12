import time
from typing import Any, Optional


class CacheEntry:
    def __init__(self, value: Any, ttl: Optional[int]):
        self.value = value
        self.expiry = time.time() + ttl if ttl else None

    def is_expired(self) -> bool:
        return self.expiry is not None and time.time() > self.expiry


class Cache:
    def __init__(self):
        self._store = {}

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Store a value with an optional TTL in seconds."""
        self._store[key] = CacheEntry(value, ttl)

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a value if it's not expired. Returns None otherwise."""
        entry = self._store.get(key)
        if entry:
            if entry.is_expired():
                del self._store[key]
                return None
            return entry.value
        return None

    def delete(self, key: str):
        """Manually remove an item from cache."""
        if key in self._store:
            del self._store[key]

    def cleanup(self):
        """Remove all expired items."""
        keys_to_delete = [k for k, v in self._store.items() if v.is_expired()]
        for k in keys_to_delete:
            del self._store[k]

    def clear(self):
        """Clear all cache entries."""
        self._store.clear()

    def __contains__(self, key: str):
        """Check if a key exists and is not expired."""
        return self.get(key) is not None
