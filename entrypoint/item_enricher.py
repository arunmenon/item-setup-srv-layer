# entrypoint/item_enricher.py
import logging
import asyncio
from typing import Dict, Any
from builders.attribute_instruction_builder import AttributeInstructionBuilder
from utils.dynamic_import import dynamic_import

class ItemEnricher:
    """
    Orchestrates item enrichment by generating prompts (via PromptManager),
    invoking LLMs, and applying postprocess hooks.

    Now includes the integrated 'AttributeInstructionBuilder' but does not
    rely on prompt_manager for attribute logic, preventing spaghetti.
    
    --------------------------------------------------------------------------
    Additional Note (Multi-Item Context):
    This class can also be used when processing multiple product items
    by looping over them externally (e.g. in /enrich-items). Each single item
    is handled via `enrich_item(...)`.
    --------------------------------------------------------------------------
    """
    def __init__(self, prompt_manager, llm_manager, task_manager, db_session, ae_scope_list_repo=None, hook_manager=None):
        self.prompt_manager = prompt_manager
        self.llm_manager = llm_manager
        self.task_manager = task_manager
        self.db_session = db_session
        self.ae_scope_list_repo = ae_scope_list_repo
        self.hook_manager = hook_manager
        self.logger = logging.getLogger(__name__)
        self.attribute_builder = AttributeInstructionBuilder()

    async def enrich_item(self, item: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """
        Enriches the given item by:
          1. Loading certified attributes + specs from AE Scope List Repo
          2. Generating advanced instructions (via AttributeInstructionBuilder) if needed
          3. Generating prompts per model family (PromptManager)
          4. Invoking LLMs concurrently
          5. Applying postprocess hooks
          6. Parsing + returning final JSON
        
        Additional Note (No Overwrite):
        - This method still respects the original docstring's structure.
        - The logic remains consistent whether we handle a single item
          or loop over multiple items externally (for a multi-item request).
        """
        self.logger.info(f"Processing {task_type} tasks for product type: '{item.get('product_type', 'unknown')}'")

        # Step 1: Load attributes + specs
        self._process_attributes(item)

        # Step 2 (Optional advanced instructions):
        # Already integrated in `_process_attributes` if you want to store them

        # Step 3: Generate prompts per model family.
        family_names = set(self.llm_manager.family_names.values())
        prompts_per_family = {}
        for family_name in family_names:
            prompts = self.prompt_manager.generate_prompts(item, family_name=family_name, task_type=task_type)
            prompts_per_family[family_name] = prompts
            self.logger.debug(f"Generated {len(prompts)} prompts for family '{family_name}'.")

        # Step 4: Prepare a unified list of prompt tasks with provider_name attached.
        prompts_tasks = self._prepare_prompts_tasks(prompts_per_family)

        # Create a mapping from task_name to output_format
        task_to_format = self._get_task_format_map(prompts_per_family)

        # Step 5: Invoke LLMs concurrently
        results = await self._invoke_llms(prompts_tasks)

        # Step 6: Apply postprocess hooks (all tasks output JSON by default)
        results = self._apply_postprocess_hooks(results)

        # Step 7: Process & parse LLM responses into final structure
        processed_results = self._process_results(results, task_to_format)
        return processed_results

    def _process_attributes(self, item: Dict[str, Any]):
        """
        Loads the certified attribute list for the item's product_type
        and also loads the specification for each attribute. The item is updated in-place:
        
          - item['attributes_list'] = [ 'color', 'size', ... ]
          - item['attribute_spec_list'] = { 'color': {...}, 'size': {...}, ... }

        We can also build advanced instructions for each attribute here using
        'self.attribute_builder' if we want them in the item data.

        --------------------------------------------------------------------------
        Appendix (No Overwrite):
        The integrated attribute builder `create_attribute_prompt(...)` is used
        to create more descriptive instructions for each attribute spec, which
        can later be consumed by the prompt manager or output logic.
        --------------------------------------------------------------------------
        """
        product_type = item.get('product_type', 'unknown')
        certified_attrs = self.ae_scope_list_repo.get_certified_attributes(product_type=product_type)
        item['attributes_list'] = list(certified_attrs)

        specs = {}
        instructions = {}

        for attr in certified_attrs:
            spec_data = self.ae_scope_list_repo.get_attribute_spec(product_type, attr)
            specs[attr] = spec_data
            # Create a more advanced attribute prompt/instruction
            instructions[attr] = self.attribute_builder.create_attribute_prompt(spec_data)

        item["attribute_spec_list"] = specs
        item["attribute_instructions"] = instructions

        self.logger.debug(f"Loaded certified attributes for product_type='{product_type}': {certified_attrs}")

    def _prepare_prompts_tasks(self, prompts_per_family):
        """
        Prepares a unified list of prompt tasks by attaching provider_name
        to each prompt record, enabling concurrent invocation of LLMs.
        """
        tasks = []
        for handler_name, handler in self.llm_manager.handlers.items():
            family_name = self.llm_manager.get_family_name(handler_name)
            prompts = prompts_per_family.get(family_name, [])
            for prompt_task in prompts:
                pt_copy = prompt_task.copy()
                pt_copy['provider_name'] = handler_name
                tasks.append(pt_copy)
        return tasks

    async def _invoke_llms(self, prompts_tasks):
        """
        Invokes the LLM handlers concurrently for each prompt task.
        Groups responses by task_name -> provider_name -> result dict.
        """
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

        task_results = await asyncio.gather(*tasks_list, return_exceptions=False)
        results = {}
        for task_name, handler_name, handler_response in task_results:
            if task_name not in results:
                results[task_name] = {}
            results[task_name][handler_name] = handler_response

        self.logger.info("LLM invocation completed.")
        return results

    async def _invoke_single_llm(self, task_name: str, prompt: str, handler_name: str, handler):
        """
        Invokes a single LLM handler (like openai or gemini).
        Uses 'task_config' for max_tokens, etc.
        """
        try:
            task_config = self.llm_manager.get_task_config(task_name, 'generation') \
                           or self.llm_manager.get_task_config(task_name, 'evaluation')
            max_tokens = task_config.get('max_tokens', 150)
            response = await handler.invoke(request={
                "prompt": prompt,
                "parameters": {"max_tokens": max_tokens}
            }, task=task_name)
            return task_name, handler_name, {'response': response.get('response'), 'error': None}
        except Exception as e:
            self.logger.error(f"Error invoking handler '{handler_name}' for task '{task_name}': {e}", exc_info=True)
            return task_name, handler_name, {'response': None, 'error': str(e)}

    def _get_task_format_map(self, prompts_per_family):
        """
        For each generated prompt, collects the 'output_format'
        so we know how to parse the LLM result.
        """
        format_map = {}
        for prompts in prompts_per_family.values():
            for p in prompts:
                format_map[p['task']] = p.get('output_format', 'json')
        return format_map

    def _apply_postprocess_hooks(self, results):
        """
        Applies postprocessing hooks for all tasks. 
        Since all tasks output JSON, hooks are applied uniformly.
        
        We do not overwrite existing logic; just clarifying that
        it remains the same for multi-item or single-item usage.
        """
        for task_name, handlers_map in results.items():
            if not self.task_manager.is_task_defined(task_name, 'generation'):
                continue
            hooks = self.task_manager.get_postprocess_hooks(task_name)
            if not hooks:
                continue

            for handler_name, resp in handlers_map.items():
                if resp.get('error'):
                    continue
                content = resp.get('response')
                if not content:
                    continue
                for hook_def in hooks:
                    hook_type = hook_def['hook_type']
                    class_path = hook_def['class_path']
                    params = hook_def['parameters']
                    cls = dynamic_import(class_path)
                    hook_instance = cls(**params)
                    try:
                        if hook_type == 'guardrail':
                            hook_instance.validate(content)
                        else:
                            content = hook_instance.apply(content)
                            resp['response'] = content
                    except Exception as e:
                        self.logger.error(f"Postprocess hook failed for task '{task_name}': {e}", exc_info=True)
                        resp['error'] = str(e)
                        break
        return results

    def _process_results(self, results, task_to_format):
        """
        Converts the raw LLM results from each task/provider into
        a final, structured format. Each key is a task, value is a provider's
        parsed response. The final shape can be adapted for your needs.
        """
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
        """
        Actually parse each provider's raw LLM text.
        If an error is present, pass it along.
        """
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
