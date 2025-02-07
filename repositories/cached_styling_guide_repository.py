import config

class CachedStylingGuideRepository:
    def __init__(self, inner_repo, cache_service):
        """
        Args:
            inner_repo: The original StylingGuideRepository (DB-based).
            cache_service: A memcache service (get/set).
        """
        self.inner_repo = inner_repo
        self.cache_service = cache_service

    def get_styling_guide(self, product_type: str, task: str) -> str:
        """
        Returns the styling guide text for (product_type, task).
        """
        if not config.USE_CACHE:
            return self.inner_repo.get_styling_guide(product_type, task)

        # Flatten into a single key
        key = f"style_guide_{task.lower()}_{product_type.lower().replace(' ', '|')}"
        cached_guide = self.cache_service.get(key)
        if cached_guide is not None:
            return cached_guide

        # Miss
        guide = self.inner_repo.get_styling_guide(product_type, task)
        if guide:
            self.cache_service.set(key, guide)
        return guide

    def fetch_active_styling_guides(self):
        """
        If you also want to cache the entire dict of active styling guides (optional).
        """
        if not config.USE_CACHE:
            return self.inner_repo.fetch_active_styling_guides()

        # Key name is arbitrary; up to you
        key = "all_active_styling_guides"
        cached_data = self.cache_service.get(key)
        if cached_data is not None:
            return cached_data

        data = self.inner_repo.fetch_active_styling_guides()
        if data:
            self.cache_service.set(key, data)
        return data
