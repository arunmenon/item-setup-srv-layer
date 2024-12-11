# repositories/template_repository.py
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from models.models import ModelFamily, GenerationTask, EvaluationTask, GenerationPromptTemplate, EvaluationPromptTemplate
from jinja2 import Environment, exceptions

class TemplateRepository:
    def __init__(self, db_session: Session):
        self.db_session = db_session
        self.jinja_env = Environment()

    def get_template_text(self, task_name: str, task_type: str, model_family_name: Optional[str]) -> Optional[str]:
        if model_family_name:
            model_family = self.db_session.query(ModelFamily).filter_by(name=model_family_name).first()
            if not model_family:
                return None
            model_family_id = model_family.model_family_id
        else:
            model_family_id = None

        if task_type == 'generation':
            template_class = GenerationPromptTemplate
            task_class = GenerationTask
            task_id_field = GenerationPromptTemplate.task_id
        elif task_type == 'evaluation':
            template_class = EvaluationPromptTemplate
            task_class = EvaluationTask
            task_id_field = EvaluationPromptTemplate.task_id
        else:
            return None

        task = self.db_session.query(task_class).filter_by(task_name=task_name).first()
        if not task:
            return None

        query = self.db_session.query(template_class).filter(
            task_id_field == task.task_id,
            template_class.model_family_id == model_family_id
        ).order_by(template_class.version.desc())
        template = query.first()
        if template:
            return template.template_text
        return None

    def render_template(self, template_content: str, context: Dict[str, Any]) -> Optional[str]:
        try:
            template = self.jinja_env.from_string(template_content)
            return template.render(context)
        except exceptions.TemplateError:
            return None
