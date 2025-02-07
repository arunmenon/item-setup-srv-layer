# cache_service.py
import logging
import json
from pymemcache.client.base import Client

class CacheService:
    """
    A simple wrapper around a pymemcache Client for storing and retrieving JSON data.
    
    Usage:
      - Initialize with cache_fqdn (e.g., "meghacache.dev.ae-cache-dev.ms-df-cache.stg-gcp-uscentral1-1.gcp.us.walmart.net").
      - Call .get(key) to retrieve data (automatically JSON-deserialized).
      - Call .set(key, value, ttl=None) to store data (serialized as JSON).
    
    By default, there's a 30-minute TTL unless overridden in .set().
    """
    def __init__(self, cache_fqdn: str, default_ttl: int = 1800):
        """
        Args:
            cache_fqdn: The FQDN or host:port string for your memcached server(s).
            default_ttl: Default time-to-live (in seconds) for cached items. Defaults to 30 minutes.
        """
        self.cache_fqdn = cache_fqdn
        self.default_ttl = default_ttl
        self.client = self._create_client()

    def _create_client(self) -> Client:
        """
        Attempts to create a pymemcache client. Logs errors if it fails.
        """
        try:
            # If you have multiple comma-separated servers, you'd parse and pass them as a list of tuples.
            # For a single FQDN, just pass it directly.
            return Client(self.cache_fqdn)
        except Exception as ex:
            logging.error(f"Failed to create memcache client for {self.cache_fqdn}: {ex}", exc_info=True)
            return None

    def get(self, key: str):
        """
        Retrieves the JSON-deserialized value stored at 'key'.
        Returns None if key does not exist or on error.
        """
        if not self.client:
            return None  # If client creation failed, return None.

        try:
            raw_data = self.client.get(key)
            if raw_data is None:
                return None  # Cache miss
            return json.loads(raw_data)
        except Exception as ex:
            logging.error(f"Error reading cache key={key}: {ex}", exc_info=True)
            return None

    def set(self, key: str, value, ttl: int = None):
        """
        Stores 'value' (JSON-serialized) at 'key', with optional TTL (defaults to self.default_ttl).
        
        Args:
            key: The cache key to store under.
            value: The Python object to store (will be converted to JSON).
            ttl: Optional override for the time-to-live (in seconds).
        """
        if not self.client:
            return  # If client is unavailable, do nothing.

        expire = ttl if ttl is not None else self.default_ttl
        try:
            serialized = json.dumps(value)
            self.client.set(key, serialized, expire=expire)
        except Exception as ex:
            logging.error(f"Error writing cache key={key}: {ex}", exc_info=True)
