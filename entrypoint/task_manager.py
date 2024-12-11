# entrypoint/task_manager.py
import logging
from typing import Dict,Any,List
from sqlalchemy.orm import Session
from models.models import GenerationTask, EvaluationTask, TaskExecutionConfig

class TaskManager:
    def __init__(self, db_session: Session):
        """
        Manages task configurations and provides default/conditional tasks.
        """
        self.db_session = db_session
        self.tasks_config: Dict[(str,str),Dict[str,Any]] = {}
        self.task_execution: Dict[str,Any] = {}
        self.logger = logging.getLogger(__name__)
        self._load_tasks()
        self._load_task_execution_config()

    def _load_tasks(self):
        generation_tasks = self.db_session.query(GenerationTask).all()
        for t in generation_tasks:
            self.tasks_config[(t.task_name, 'generation')] = {
                'task_type': 'generation',
                'description': t.description,
                'max_tokens': t.max_tokens,
                'output_format': t.output_format
            }
        evaluation_tasks = self.db_session.query(EvaluationTask).all()
        for t in evaluation_tasks:
            self.tasks_config[(t.task_name, 'evaluation')] = {
                'task_type': 'evaluation',
                'description': t.description,
                'max_tokens': t.max_tokens,
                'output_format': t.output_format
            }
        self.logger.info(f"Loaded {len(self.tasks_config)} tasks.")

    def _load_task_execution_config(self):
        config = self.db_session.query(TaskExecutionConfig).order_by(TaskExecutionConfig.config_id.desc()).first()
        if config:
            self.task_execution = {
                'default_tasks': config.default_tasks,
                'conditional_tasks': config.conditional_tasks
            }
            self.logger.info("Loaded task execution config.")
        else:
            self.logger.error("No task execution config found.")
            raise ValueError("No task execution config found.")

    def get_default_tasks(self, task_type: str) -> List[str]:
        return self.task_execution.get('default_tasks', {}).get(task_type, [])

    def get_conditional_tasks(self, task_type: str) -> Dict[str,str]:
        return self.task_execution.get('conditional_tasks', {}).get(task_type, {})

    def is_task_defined(self, task_name: str, task_type: str) -> bool:
        return (task_name, task_type) in self.tasks_config

    def get_task_config(self, task_name: str, task_type: str) -> Dict[str,Any]:
        return self.tasks_config.get((task_name, task_type), {})
