# app_factory.py
import logging
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import config

from schemas.enrichment import (
    MultiEnrichRequest, MultiEnrichResponse
)
# No single item import

from repositories.ae_scope_list_repository import AEScopeListRepository
from repositories.styling_guide_repository import StylingGuideRepository
from repositories.template_repository import TemplateRepository
from repositories.cached_ae_scope_list_repository import CachedAEScopeListRepository
from repositories.cached_styling_guide_repository import CachedStylingGuideRepository
from repositories.cached_template_repository import CachedTemplateRepository

from cache.cache_service import CacheService
from managers.hook_manager import HookManager
from entrypoint.task_manager import TaskManager
from entrypoint.prompt_manager import PromptManager
from entrypoint.llm_manager import LLMManager
from entrypoint.item_enricher import ItemEnricher

def create_app():
    engine = create_engine(config.DATABASE_URL, echo=False)
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    # Repositories & Cache
    styling_guide_repo = StylingGuideRepository(db_session)
    template_repo = TemplateRepository(db_session)
    ae_repo = AEScopeListRepository(db_session)

    cache_service = CacheService(config.CACHE_FQDN, 1800)
    cached_styling_repo = CachedStylingGuideRepository(styling_guide_repo, cache_service)
    cached_template_repo = CachedTemplateRepository(template_repo, cache_service)
    cached_ae_repo = CachedAEScopeListRepository(ae_repo, cache_service)

    hook_manager = HookManager(db_session)
    task_manager = TaskManager(db_session)
    prompt_manager = PromptManager(cached_styling_repo, cached_template_repo, task_manager)
    llm_manager = LLMManager(db_session)

    item_enricher = ItemEnricher(
        prompt_manager=prompt_manager,
        llm_manager=llm_manager,
        task_manager=task_manager,
        db_session=db_session,
        ae_scope_list_repo=cached_ae_repo,
        hook_manager=hook_manager
    )

    app = FastAPI(title="Gen AI Multi-Item Enrichment", version="1.0.0")

    @app.post("/enrich-items", response_model=MultiEnrichResponse)
    async def enrich_items_endpoint(request_body: MultiEnrichRequest):
        """
        Multi-item flow: entire request is in request_body.
        We call item_enricher.enrich_items() for the final result.
        """
        try:
            # Convert Pydantic model to dict
            req_dict = request_body.dict()
            # We'll call item_enricher's multi approach
            final_result = await item_enricher.enrich_items(req_dict)
            return MultiEnrichResponse(**final_result)
        except Exception as e:
            logging.error(f"Error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    return app
