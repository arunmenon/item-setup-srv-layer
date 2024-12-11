# entrypoint/llm_manager.py
import logging
from sqlalchemy.orm import Session
from models.models import ProviderConfig, GenerationTask, EvaluationTask

class LLMManager:
    def __init__(self, db_session: Session):
        """
        LLMManager initializes and stores providers (handlers) and tasks config.
        """
        self.db_session = db_session
        self.handlers = {}
        self.family_names = {}
        self.tasks = {}
        self.logger = logging.getLogger(__name__)
        self._load_providers()
        self._load_tasks()

    def _load_providers(self):
        providers = self.db_session.query(ProviderConfig).filter_by(is_active=True).all()
        from handlers.llm_handler import BaseModelHandler
        for provider in providers:
            name = provider.name
            family_name = provider.family
            provider_kwargs = {
                'provider'   : provider.provider_name,
                'model'      : provider.model,
                'max_tokens' : provider.max_tokens,
                'temperature': provider.temperature,
                'api_base'   : provider.api_base,
                'version'    : provider.version,
            }
            self.handlers[name] = BaseModelHandler(**provider_kwargs)
            self.family_names[name] = family_name
            self.logger.debug(f"Initialized handler '{name}' for family '{family_name}'.")

    def _load_tasks(self):
        generation_tasks = self.db_session.query(GenerationTask).all()
        for t in generation_tasks:
            self.tasks[(t.task_name, 'generation')] = {
                'task_type': 'generation',
                'max_tokens': t.max_tokens,
                'output_format': t.output_format
            }

        evaluation_tasks = self.db_session.query(EvaluationTask).all()
        for t in evaluation_tasks:
            self.tasks[(t.task_name, 'evaluation')] = {
                'task_type': 'evaluation',
                'max_tokens': t.max_tokens,
                'output_format': t.output_format
            }

        self.logger.info(f"Loaded {len(self.tasks)} tasks into LLMManager.")

    def get_task_config(self, task_name: str, task_type: str):
        return self.tasks.get((task_name, task_type), {})

    def get_family_name(self, handler_name: str):
        return self.family_names.get(handler_name, 'default')
