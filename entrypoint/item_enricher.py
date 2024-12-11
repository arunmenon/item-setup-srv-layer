# entrypoint/item_enricher.py
import logging
from typing import Dict, Any
from fastapi import HTTPException

class ItemEnricher:
    def __init__(self, prompt_manager, llm_manager):
        """
        Orchestrates item enrichment by generating prompts (PromptManager) and invoking LLMs (LLMManager).

        Args:
            prompt_manager: Instance of PromptManager for generating prompts.
            llm_manager: Instance of LLMManager for invoking language models.
        """
        self.prompt_manager = prompt_manager
        self.llm_manager = llm_manager
        self.logger = logging.getLogger(__name__)

    async def enrich_item(self, item: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """
        Enriches the given item by generating prompts and calling LLMs.

        Args:
            item (Dict[str, Any]): A dictionary containing product details.
            task_type (str): The type of tasks ('generation' or 'evaluation').

        Returns:
            Dict[str, Any]: The processed LLM responses.
        """
        self.logger.info(f"Processing {task_type} tasks for product type: '{item.get('product_type','unknown')}'")

        # Collect unique family names from llm_manager
        family_names = set(self.llm_manager.family_names.values())

        # Generate prompts per family
        prompts_per_family = {}
        for family_name in family_names:
            prompts = self.prompt_manager.generate_prompts(item, family_name=family_name, task_type=task_type)
            prompts_per_family[family_name] = prompts
            self.logger.debug(f"Generated {len(prompts)} prompts for family '{family_name}'.")

        # Associate prompts with handlers
        prompts_tasks = []
        for handler_name, handler in self.llm_manager.handlers.items():
            family_name = self.llm_manager.get_family_name(handler_name)
            prompts = prompts_per_family.get(family_name, [])
            for prompt_task in prompts:
                pt_copy = prompt_task.copy()
                pt_copy['provider_name'] = handler_name
                prompts_tasks.append(pt_copy)

        # Map task to format
        task_to_format = {pt['task']: pt['output_format'] for pt in prompts_tasks}

        # Invoke LLMs
        results = await self._invoke_llms(prompts_tasks)

        # Process responses
        processed_results = self._process_results(results, task_to_format)
        return processed_results

    async def _invoke_llms(self, prompts_tasks):
        import asyncio

        tasks_list = []
        for pt in prompts_tasks:
            task_name = pt['task']
            prompt = pt['prompt']
            provider_name = pt['provider_name']
            handler = self.llm_manager.handlers.get(provider_name)
            if not handler:
                self.logger.error(f"Handler '{provider_name}' not found for task '{task_name}'.")
                continue
            tasks_list.append(self._invoke_single_llm(task_name, prompt, provider_name, handler))

        task_results = await asyncio.gather(*tasks_list)

        results = {}
        for task_name, handler_name, handler_response in task_results:
            if task_name not in results:
                results[task_name] = {}
            results[task_name][handler_name] = handler_response

        self.logger.info("LLM invocation completed.")
        return results

    async def _invoke_single_llm(self, task_name: str, prompt: str, handler_name: str, handler) -> (str, str, Dict[str,Any]):
        try:
            # Determine if task is generation or evaluation from llm_manager tasks
            # If not found as generation, try evaluation
            task_config = self.llm_manager.get_task_config(task_name, 'generation')
            if not task_config:
                task_config = self.llm_manager.get_task_config(task_name, 'evaluation')
            max_tokens = task_config.get('max_tokens', 150)
            response = await handler.invoke(request={"prompt": prompt, "parameters": {"max_tokens": max_tokens}}, task=task_name)
            return task_name, handler_name, {'response': response.get('response'), 'error': None}
        except Exception as e:
            self.logger.error(f"Error invoking handler '{handler_name}' for task '{task_name}': {e}", exc_info=True)
            return task_name, handler_name, {'response': None, 'error': str(e)}

    def _process_results(self, results: Dict[str,Any], task_to_format: Dict[str,str]) -> Dict[str,Any]:
        from parsers.parser_factory import ParserFactory

        processed_results = {}
        for task, handler_responses in results.items():
            output_format = task_to_format.get(task, 'json')
            task_results = {}
            for handler_name, response in handler_responses.items():
                parsed = self._process_single_response(handler_name, task, response, output_format, ParserFactory)
                task_results[handler_name] = parsed
            processed_results[task] = task_results
        return processed_results

    def _process_single_response(self, handler_name: str, task: str, response: Dict[str,Any], output_format: str, parser_factory) -> Dict[str,Any]:
        if response.get('error'):
            return {'handler_name': handler_name, 'error': response['error']}

        response_content = response.get('response', '')
        parser = parser_factory.get_parser(output_format)

        try:
            parsed_response = parser.parse(response_content)
            return {'handler_name': handler_name, 'response': parsed_response}
        except Exception as e:
            self.logger.error(f"Parsing failed for task '{task}', handler '{handler_name}': {e}", exc_info=True)
            return {'handler_name': handler_name, 'error': 'Parsing failed'}
