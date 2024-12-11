# entrypoint/item_enricher.py
import logging
from typing import Dict, Any

class ItemEnricher:
    def __init__(self, prompt_manager, llm_manager, ae_inclusion_list_repo=None):
        """
        Orchestrates item enrichment by generating prompts (PromptManager) and invoking LLMs (LLMManager).

        Args:
            prompt_manager: Instance of PromptManager for generating prompts.
            llm_manager: Instance of LLMManager for invoking language models.
            ae_inclusion_list_repo: Optional repository to fetch allowed attributes for items.
        """
        self.prompt_manager = prompt_manager
        self.llm_manager = llm_manager
        self.ae_inclusion_list_repo = ae_inclusion_list_repo
        self.logger = logging.getLogger(__name__)

    async def enrich_item(self, item: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """
        Enriches the given item by generating prompts and calling LLMs.

        Steps:
        1. Preprocess attributes (filter or set them if not present).
        2. Generate prompts per family.
        3. Invoke LLMs and process responses.

        Args:
            item (Dict[str, Any]): A dictionary containing product details (title, desc, product_type, etc.).
            task_type (str): The type of tasks to run ('generation' or 'evaluation').

        Returns:
            Dict[str, Any]: The processed LLM responses structured by tasks and handlers.
        """
        self.logger.info(f"Processing {task_type} tasks for product type: '{item.get('product_type','unknown')}'")

        # Step 1: Process item attributes if AEInclusionListRepo is available
        if self.ae_inclusion_list_repo:
            self._process_attributes(item)

        # Step 2: Generate prompts per model family
        family_names = set(self.llm_manager.family_names.values())
        prompts_per_family = {}
        for family_name in family_names:
            prompts = self.prompt_manager.generate_prompts(item, family_name=family_name, task_type=task_type)
            prompts_per_family[family_name] = prompts
            self.logger.debug(f"Generated {len(prompts)} prompts for family '{family_name}'.")

        # Prepare a unified list of prompt tasks with provider_name attached
        prompts_tasks = self._prepare_prompts_tasks(prompts_per_family)

        # Create a mapping from task_name to output_format
        task_to_format = self._get_task_format_map(prompts_per_family)

        # Step 3: Invoke LLMs and process results
        results = await self._invoke_llms(prompts_tasks)
        processed_results = self._process_results(results, task_to_format)
        return processed_results

    def _process_attributes(self, item: Dict[str, Any]):
        """
        Processes attributes for the given item:
        - If item already has 'attributes_list', filter it using the AEInclusionListRepo.
        - If not, fetch the full inclusion list from the repo and set it.

        Args:
            item (Dict[str, Any]): Item dictionary containing product information.
        """
        product_type = item.get('product_type', 'unknown')
        included_attrs = self.ae_inclusion_list_repo.get_included_attributes(product_type)

        if 'attributes_list' in item:
            # Filter existing attributes to the allowed subset
            original_attrs = item['attributes_list']
            filtered_attrs = [a for a in original_attrs if a.lower() in included_attrs]
            item['attributes_list'] = filtered_attrs
            self.logger.debug(f"Filtered attributes for product_type='{product_type}'. "
                              f"Original={original_attrs}, Filtered={filtered_attrs}")
        else:
            # No attributes_list provided, assign the full inclusion list as the default
            full_attrs = list(included_attrs)  # convert set to list if needed
            item['attributes_list'] = full_attrs
            self.logger.debug(f"No attributes_list provided. Assigned full inclusion list: {full_attrs}")

    def _prepare_prompts_tasks(self, prompts_per_family):
        prompts_tasks = []
        for handler_name, handler in self.llm_manager.handlers.items():
            family_name = self.llm_manager.get_family_name(handler_name)
            prompts = prompts_per_family.get(family_name, [])
            for prompt_task in prompts:
                pt_copy = prompt_task.copy()
                pt_copy['provider_name'] = handler_name
                prompts_tasks.append(pt_copy)
        return prompts_tasks

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
            # Determine if generation or evaluation task to get max_tokens
            task_config = self.llm_manager.get_task_config(task_name, 'generation') or self.llm_manager.get_task_config(task_name, 'evaluation')
            max_tokens = task_config.get('max_tokens', 150)
            response = await handler.invoke(request={"prompt": prompt, "parameters": {"max_tokens": max_tokens}}, task=task_name)
            return task_name, handler_name, {'response': response.get('response'), 'error': None}
        except Exception as e:
            self.logger.error(f"Error invoking handler '{handler_name}' for task '{task_name}': {e}", exc_info=True)
            return task_name, handler_name, {'response': None, 'error': str(e)}

    def _get_task_format_map(self, prompts_per_family):
        # We'll collect a task->format mapping from any available prompts
        format_map = {}
        for prompts in prompts_per_family.values():
            for p in prompts:
                format_map[p['task']] = p['output_format']
        return format_map

    def _process_results(self, results, task_to_format):
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

    def _process_single_response(self, handler_name, task, response, output_format, parser_factory):
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
