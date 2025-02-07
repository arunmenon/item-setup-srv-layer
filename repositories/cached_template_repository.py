import config
from typing import Optional

class CachedTemplateRepository:
    def __init__(self, inner_repo, cache_service):
        """
        Args:
            inner_repo: The original TemplateRepository (DB-based).
            cache_service: A memcache service with get/set.
        """
        self.inner_repo = inner_repo
        self.cache_service = cache_service

    def get_template_text(self, task_name: str, task_type: str, model_family_name: Optional[str]) -> Optional[str]:
        """
        Returns the template text for (task_name, task_type, model_family_name).
        """
        if not config.USE_CACHE:
            return self.inner_repo.get_template_text(task_name, task_type, model_family_name)

        # Flatten to a single cache key
        family_key = model_family_name or "default"
        key = f"prompt_template_{task_name}_{task_type}_{family_key}"

        cached_val = self.cache_service.get(key)
        if cached_val is not None:
            return cached_val

        # Miss -> query DB, then set
        template_text = self.inner_repo.get_template_text(task_name, task_type, model_family_name)
        if template_text:
            self.cache_service.set(key, template_text)
        return template_text

    def render_template(self, template_content: str, context: dict) -> Optional[str]:
        """
        Typically not cached because rendering can be context-specific.
        """
        return self.inner_repo.render_template(template_content, context)
