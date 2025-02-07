import config

class CachedAEScopeListRepository:
    def __init__(self, inner_repo, cache_service):
        """
        Args:
            inner_repo: The original AEScopeListRepository instance (DB-based).
            cache_service: A wrapper providing 'get(key)' and 'set(key, value)' for memcache.
        """
        self.inner_repo = inner_repo
        self.cache_service = cache_service

    def get_certified_attributes(self, product_type: str):
        """Returns a list of certified attribute names, first checking the cache if USE_CACHE is True."""
        if not config.USE_CACHE:
            return self.inner_repo.get_certified_attributes(product_type)

        cache_key = f"spec_{product_type.replace(' ', '|')}"
        cached_list = self.cache_service.get(cache_key)
        if cached_list is not None:
            return cached_list

        # Cache miss -> fetch from DB
        attrs = self.inner_repo.get_certified_attributes(product_type)
        if attrs:
            self.cache_service.set(cache_key, attrs)
        return attrs

    def get_attribute_spec(self, product_type: str, attribute_name: str):
        """Returns the spec for a given (product_type, attribute_name)."""
        if not config.USE_CACHE:
            return self.inner_repo.get_attribute_spec(product_type, attribute_name)

        cache_key = f"spec_{product_type.replace(' ', '|')}_{attribute_name}"
        cached_spec = self.cache_service.get(cache_key)
        if cached_spec is not None:
            return cached_spec

        # Cache miss
        spec_data = self.inner_repo.get_attribute_spec(product_type, attribute_name)
        if spec_data:
            self.cache_service.set(cache_key, spec_data)
        return spec_data
