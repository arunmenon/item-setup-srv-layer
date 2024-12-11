# app_factory.py
import logging
from fastapi import FastAPI, HTTPException
from sqlalchemy.orm import sessionmaker
from models.database import engine
from entrypoint.task_manager import TaskManager
from entrypoint.prompt_manager import PromptManager
from entrypoint.llm_manager import LLMManager
from entrypoint.item_enricher import ItemEnricher
from adapters.request_adapter import LLMRequestAdapter
from adapters.response_formatter import DefaultJSONResponseFormatter
from repositories.styling_guide_repository import StylingGuideRepository
from repositories.template_repository import TemplateRepository

def create_app():
    """
    Factory function to create and configure the FastAPI application.
    """
    SessionLocal = sessionmaker(bind=engine)
    db_session = SessionLocal()

    # Initialize repositories
    styling_guide_repo = StylingGuideRepository(db_session)
    template_repo = TemplateRepository(db_session)

    # Initialize core managers
    task_manager = TaskManager(db_session)
    prompt_manager = PromptManager(styling_guide_repo, template_repo, task_manager)
    llm_manager = LLMManager(db_session)
    # Instantiate ItemEnricher with (prompt_manager, llm_manager)
    item_enricher = ItemEnricher(prompt_manager, llm_manager)

    # Adapters and Formatters
    request_adapter = LLMRequestAdapter()
    response_formatter = DefaultJSONResponseFormatter()

    app = FastAPI(title="Gen AI Item Enrichment API", version="1.0.0")

    @app.post("/enrich-item")
    async def enrich_item_endpoint(request_body: dict):
        """
        Endpoint to enrich an item using configured LLM tasks.
        The request_body is adapted to item and task_type by LLMRequestAdapter.
        """
        try:
            item, task_type = request_adapter.adapt(request_body)
            results = await item_enricher.enrich_item(item, task_type)
            formatted_results = response_formatter.format(results)
            return formatted_results
        except HTTPException as he:
            raise he
        except Exception as e:
            logging.error(f"Error in /enrich-item: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error")

    return app
