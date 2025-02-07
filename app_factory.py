# app_factory.py
import logging
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import sessionmaker
from models.database import engine

from schemas.enrichment import EnrichItemRequest, EnrichItemResponse
from managers.hook_manager import HookManager
from repositories.ae_scope_list_repository import AEScopeListRepository
from repositories.styling_guide_repository import StylingGuideRepository
from repositories.template_repository import TemplateRepository
from entrypoint.task_manager import TaskManager
from entrypoint.prompt_manager import PromptManager
from entrypoint.llm_manager import LLMManager
from entrypoint.item_enricher import ItemEnricher

def create_app():
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    # Repositories
    styling_guide_repo = StylingGuideRepository(db_session)
    template_repo = TemplateRepository(db_session)
    ae_scope_list_repo = AEScopeListRepository(db_session)
    hook_manager = HookManager(db_session)

    # Managers
    task_manager = TaskManager(db_session)
    prompt_manager = PromptManager(styling_guide_repo, template_repo, task_manager)
    llm_manager = LLMManager(db_session)
    item_enricher = ItemEnricher(
        prompt_manager,
        llm_manager,
        task_manager,
        db_session,
        ae_scope_list_repo,
        hook_manager
    )

    app = FastAPI(title="Gen AI Item Enrichment API", version="1.0.0")

    @app.post("/enrich-item", response_model=EnrichItemResponse)
    async def enrich_item_endpoint(request_body: EnrichItemRequest):
        """
        Endpoint to enrich an item. Returns
          - title_enrichment
          - short_desc_enrichment
          - long_desc_enrichment
          - attributes_enrichment (list of attribute-value pairs)
        """
        try:
            item_dict = request_body.dict()
            task_type = item_dict.pop("task_type")  # 'generation' if not supplied

            # Now call the item_enricher. 
            # We'll assume the item_enricher internally returns a dict like:
            # {
            #   "title_enrichment": "...",
            #   "short_desc_enrichment": "...",
            #   "long_desc_enrichment": "...",
            #   "attributes_enrichment": [
            #       { "name": "color", "value": "red" }, ...
            #   ]
            # }
            enrichment_results = await item_enricher.enrich_item(item_dict, task_type)

            return EnrichItemResponse(**enrichment_results)

        except Exception as e:
            logging.error(f"Error in /enrich-item: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    return app
