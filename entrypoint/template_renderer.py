# entrypoint/template_renderer.py

import logging
from typing import Optional, Dict, Any
from repositories.template_repository import TemplateRepository
from jinja2 import Environment, exceptions

class TemplateRenderer:
    def __init__(self, template_repo: TemplateRepository):
        """
        Initializes the TemplateRenderer with a TemplateRepository for fetching templates
        and a Jinja2 environment for rendering.

        Args:
            template_repo (TemplateRepository): Repository for fetching template texts from DB.
        """
        self.template_repo = template_repo
        self.jinja_env = Environment()
        self.logger = logging.getLogger(self.__class__.__name__)

    def render(self, task_name: str, task_type: str, family_name: Optional[str], context: Dict[str, Any]) -> Optional[str]:
        """
        Renders a template for the given task_name, task_type, and model family using Jinja2.
        It fetches the template text from the repository and then applies rendering with the provided context.

        Args:
            task_name (str): The name of the task.
            task_type (str): The type of the task ('generation' or 'evaluation').
            family_name (Optional[str]): The model family name for template selection.
            context (Dict[str, Any]): The context dictionary for rendering the template.

        Returns:
            Optional[str]: The rendered template as a string, or None if template not found or rendering fails.
        """
        template_content = self.template_repo.get_template_text(task_name, task_type, family_name)
        if not template_content:
            self.logger.error(f"No template found for task='{task_name}', task_type='{task_type}', family='{family_name}'")
            return None

        try:
            template = self.jinja_env.from_string(template_content)
            return template.render(context)
        except exceptions.TemplateError as e:
            self.logger.error(f"Error rendering template for task='{task_name}': {e}")
            return None
