# entrypoint/prompt_manager.py
import logging
from typing import Dict, Any, Optional, List

class PromptManager:
    def __init__(self, styling_guide_repo, template_repo, task_manager):
        """
        Manages prompt generation logic.

        Args:
            styling_guide_repo: Repository for fetching styling guides.
            template_repo: Repository for fetching templates.
            task_manager: Manages task configuration.
        """
        self.styling_guide_repo = styling_guide_repo
        self.template_repo = template_repo
        self.task_manager = task_manager
        self.logger = logging.getLogger(__name__)

    def generate_prompts(self, item: Dict[str,Any], family_name: Optional[str], task_type: str) -> List[Dict[str,Any]]:
        product_type = item.get('product_type','unknown').lower()
        self.logger.info(f"Generating prompts for product_type='{product_type}', task_type='{task_type}'")

        prompts_tasks = []
        default_tasks = self.task_manager.get_default_tasks(task_type)
        self.logger.debug(f"Default tasks: {default_tasks}")
        self._handle_tasks(family_name, item, product_type, prompts_tasks, default_tasks, task_type, False)

        conditional_tasks = self.task_manager.get_conditional_tasks(task_type)
        for t_name, cond_key in conditional_tasks.items():
            if cond_key and item.get(cond_key):
                self._handle_tasks(family_name, item, product_type, prompts_tasks, [t_name], task_type, True)

        return prompts_tasks

    def _handle_tasks(self, family_name, item, product_type, prompts_tasks, tasks, task_type, is_conditional):
        for task_name in tasks:
            if not self.task_manager.is_task_defined(task_name, task_type):
                self.logger.warning(f"Task '{task_name}' not defined.")
                continue

            task_config = self.task_manager.get_task_config(task_name, task_type)
            output_format = task_config.get('output_format','json')
            max_tokens = task_config.get('max_tokens',150)

            styling_guide = self.styling_guide_repo.get_styling_guide(product_type, task_name)
            if not styling_guide:
                self.logger.warning(f"No styling guide for '{product_type}', '{task_name}'. Skipping.")
                continue

            context = self._prepare_context(item, product_type, styling_guide)
            template_content = self.template_repo.get_template_text(task_name, task_type, family_name)
            if not template_content:
                self.logger.error(f"No template for task='{task_name}', family='{family_name}', type='{task_type}'.")
                continue

            prompt = self.template_repo.render_template(template_content, context)
            if not prompt:
                self.logger.error(f"Failed to render template for task='{task_name}'.")
                continue

            prompts_tasks.append({
                'task': task_name,
                'prompt': prompt,
                'output_format': output_format,
                'max_tokens': max_tokens
            })

    def _prepare_context(self, item, product_type, styling_guide):
        context = {
            'styling_guide': styling_guide,
            'original_title': item.get('item_title',''),
            'original_short_description': item.get('short_description',''),
            'original_long_description': item.get('long_description',''),
            'product_type': product_type,
            'image_url': item.get('image_url',''),
            'attributes_list': item.get('attributes_list',[]),
            'output_format': 'json'
        }
        return {k:v for k,v in context.items() if v}
