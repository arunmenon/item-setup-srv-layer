# repositories/cached_ae_scope_list_repository.py
import config

class CachedAEScopeListRepository:
    def __init__(self, inner_repo, cache_service):
        """
        Args:
            inner_repo: The original AEScopeListRepository instance (DB-based).
            cache_service: A memcache wrapper (get(key), set(key, value)).
        """
        self.inner_repo = inner_repo
        self.cache_service = cache_service

    def get_certified_attributes(self, product_type: str):
        if not config.USE_CACHE:
            return self.inner_repo.get_certified_attributes(product_type)

        cache_key = f"spec_{product_type.replace(' ', '|')}"
        cached_list = self.cache_service.get(cache_key)
        if cached_list is not None:
            return cached_list

        attrs = self.inner_repo.get_certified_attributes(product_type)
        if attrs:
            self.cache_service.set(cache_key, attrs)
        return attrs

    def get_attribute_spec(self, product_type: str, attribute_name: str):
        if not config.USE_CACHE:
            return self.inner_repo.get_attribute_spec(product_type, attribute_name)

        cache_key = f"spec_{product_type.replace(' ', '|')}_{attribute_name}"
        cached_spec = self.cache_service.get(cache_key)
        if cached_spec is not None:
            return cached_spec

        # Miss
        spec_data = self.inner_repo.get_attribute_spec(product_type, attribute_name)
        if spec_data:
            self.cache_service.set(cache_key, spec_data)
        return spec_data
