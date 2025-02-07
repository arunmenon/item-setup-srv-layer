# app_factory.py
import logging
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import sessionmaker
from models.database import engine

# Pydantic schemas
from schemas.enrichment import EnrichItemRequest, EnrichItemResponse

# Original Repositories
from repositories.ae_scope_list_repository import AEScopeListRepository
from repositories.styling_guide_repository import StylingGuideRepository
from repositories.template_repository import TemplateRepository

# Cached Wrappers
from repositories.cached_ae_scope_list_repository import CachedAEScopeListRepository
from repositories.cached_styling_guide_repository import CachedStylingGuideRepository
from repositories.cached_template_repository import CachedTemplateRepository

# Cache Service
from cache.cache_service import CacheService

# Managers / Entry Points
from managers.hook_manager import HookManager
from entrypoint.task_manager import TaskManager
from entrypoint.prompt_manager import PromptManager
from entrypoint.llm_manager import LLMManager
from entrypoint.item_enricher import ItemEnricher

# Configuration
import config  # Make sure config has USE_CACHE, CACHE_FQDN, etc.

def create_app():
    """
    Factory function to create and configure the FastAPI application.
    """
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    # Original Repositories
    styling_guide_repo = StylingGuideRepository(db_session)
    template_repo = TemplateRepository(db_session)
    ae_scope_list_repo = AEScopeListRepository(db_session)

    # Cache Service
    cache_service = CacheService(cache_fqdn=config.CACHE_FQDN, default_ttl=1800)

    # Wrap Repositories with Cached Versions
    cached_styling_guide_repo = CachedStylingGuideRepository(styling_guide_repo, cache_service)
    cached_template_repo = CachedTemplateRepository(template_repo, cache_service)
    cached_ae_scope_list_repo = CachedAEScopeListRepository(ae_scope_list_repo, cache_service)

    # Managers
    hook_manager = HookManager(db_session)
    task_manager = TaskManager(db_session)
    prompt_manager = PromptManager(
        styling_guide_repo=cached_styling_guide_repo,  # use cached styling guide
        template_repo=cached_template_repo,            # use cached template
        task_manager=task_manager
    )
    llm_manager = LLMManager(db_session)

    # ItemEnricher uses the cached AE scope repo
    item_enricher = ItemEnricher(
        prompt_manager=prompt_manager,
        llm_manager=llm_manager,
        task_manager=task_manager,
        db_session=db_session,
        ae_scope_list_repo=cached_ae_scope_list_repo,  # cached AE repo
        hook_manager=hook_manager
    )

    app = FastAPI(title="Gen AI Item Enrichment API", version="1.0.0")

    @app.post("/enrich-item", response_model=EnrichItemResponse)
    async def enrich_item_endpoint(request_body: EnrichItemRequest):
        """
        Endpoint to enrich an item. Returns an EnrichItemResponse containing:
          - title_enrichment
          - short_desc_enrichment
          - long_desc_enrichment
          - attributes_enrichment (list of attribute-value pairs)
        """
        try:
            item_dict = request_body.dict()
            task_type = item_dict.pop("task_type", "generation")  # default to 'generation' if omitted

            # The item_enricher returns a dict like:
            # {
            #   "title_enrichment": "...",
            #   "short_desc_enrichment": "...",
            #   "long_desc_enrichment": "...",
            #   "attributes_enrichment": [ ... ]
            # }
            enrichment_results = await item_enricher.enrich_item(item_dict, task_type)
            return EnrichItemResponse(**enrichment_results)

        except Exception as e:
            logging.error(f"Error in /enrich-item: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    return app
