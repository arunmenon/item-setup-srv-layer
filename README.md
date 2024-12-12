# Gen AI Item Enrichment Serving Layer

## Overview

This repository provides a configurable and extensible serving layer for enhancing product-related data (e.g., titles, attributes) using LLM-based generation and evaluation tasks. The serving layer orchestrates:

1. Retrieving and preparing item data.
2. Generating prompts based on styling guides and templates.
3. Invoking configured LLM providers.
4. Parsing and validating responses using guardrails.
5. Integrating attribute inclusion logic for certain tasks (like attribute extraction).

All configurations—tasks, templates, guardrails, providers—are stored in a database, making the system highly dynamic and adaptable without code changes.

## Key Components

### Data Layer and Models

- **Database:**  
  Stores all configurations and resources: tasks, templates, styling guides, LLM providers, and attribute inclusion lists.
  
- **SQLAlchemy ORM and Models (in `models/`):**  
  Defines ORM models such as:
  - `GenerationTask` and `EvaluationTask` for task definitions.
  - `ModelFamily`, `ProviderConfig` for model/provider configuration.
  - `StylingGuide` for editorial constraints.
  - `AEInclusionList` for certified attributes.
  - `TaskExecutionConfig` for default/conditional tasks.
  
- **Repositories (in `repositories/`):**  
  Encapsulate data access and business logic. For example:
  - `StylingGuideRepository` fetches styling guides.
  - `TemplateRepository` fetches templates.
  - `AEInclusionListRepository` fetches certified attributes for attribute extraction tasks.

### Managers

- **TaskManager:**  
  - Loads task configurations (both generation and evaluation).
  - Provides default and conditional tasks to run based on item attributes or conditions.
  - Offers easy retrieval of task-related metadata (max_tokens, output_format).
  
- **PromptManager:**  
  - Uses `StylingGuideRepository` and `TemplateRepository` to generate prompts.
  - Interprets item data and tasks to produce prompts tailored to the LLM and the `task_type`.
  - Considers `TaskExecutionConfig` to determine which tasks to run.

- **LLMManager:**  
  - Loads and configures LLM providers (from `ProviderConfig`)—these can be OpenAI, local models, etc.
  - Initializes `BaseModelHandler` instances for each provider.
  - Maps model families to providers and tasks, enabling the system to dynamically select the correct LLM backend.

- **ItemEnricher:**  
  - The central orchestrator that:
    1. Preprocesses item data if needed (e.g., filtering attributes via `AEInclusionListRepository`).
    2. Uses `PromptManager` to generate prompts for specified tasks.
    3. Invokes the LLMs through `LLMManager` and gathers responses.
    4. Applies guardrails to validate and filter responses as per the configured tasks.
  - Returns processed, validated LLM responses.

### Adapters and Formatters

- **LLMRequestAdapter:**  
  Adapts raw incoming HTTP request bodies to the internal `item` dictionary and `task_type` format that `ItemEnricher` expects. If the input schema changes, you update or replace the adapter.

- **DefaultJSONResponseFormatter:**  
  Formats the final results into a JSON structure suitable for the API response. If the output schema changes, swap or modify this formatter.

### Guardrails

- While the current codebase does not show direct integration of guardrails as a separate repository or config table, the `ItemEnricher` includes a placeholder `_apply_guardrails` step:
  - If a generation task requires guardrails (like profanity checks, bias checks), you would:
    1. Insert guardrail configuration in a database table.
    2. `ItemEnricher` loads and applies these validators after receiving LLM responses.
  
  By default, there might not be any guardrails if not configured. If added in the future, the code can dynamically load guardrail classes and apply them to responses.

### AE Inclusion Logic

For attribute extraction tasks, we often need a certified attribute list:

- **AEInclusionListRepository:**
  - If `attributes_list` is in the input item, filter it to only certified attributes.
  - If `attributes_list` not provided, assign all certified attributes from the AE inclusion list.
  
This ensures the LLM only works with a validated subset of attributes, improving result quality.

## Workflow Summary

1. **Incoming Request**:  
   A request comes in (e.g., `POST /enrich-item`) with JSON containing item details and a `task_type`.

2. **Request Adaptation**:  
   `LLMRequestAdapter` transforms the raw request body into `(item, task_type)` that the system can handle.

3. **ItemEnricher Execution**:  
   - **Preprocessing (Attributes)**: If `AEInclusionListRepository` is configured and the task relates to attributes, filter or set `item['attributes_list']`.
   - **Prompt Generation**:  
     `PromptManager` uses styling guides and templates to build prompts for each task determined by `TaskManager`.  
     `TaskManager` checks `task_execution_config` to figure out which tasks to run.
   - **LLM Invocation**:  
     `LLMManager` finds appropriate providers and sends prompts. `ItemEnricher` awaits responses, collecting them by `(task, handler)`.
   - **Guardrails (If Configured)**:  
     If guardrails are defined for a generation task, the `ItemEnricher` applies them to ensure output quality and safety.
   
4. **Response Parsing**:  
   The system uses `ParserFactory` (not shown in detail here) to parse LLM responses according to `output_format`.
   
5. **Response Formatting**:  
   The final structured results are then passed to `DefaultJSONResponseFormatter`, returning a clean JSON response to the client.

## Configuration and Extension

### Adding a New Task

1. Insert a row into `generation_tasks` or `evaluation_tasks` defining `task_name`, `max_tokens`, `output_format`.
2. Insert corresponding `prompt_template` rows in `generation_prompt_templates` or `evaluation_prompt_templates`.
3. Update `task_execution_config` to include the new task in default or conditional tasks if needed.

### Changing Models or Providers

- Add or update rows in `providers` and `model_families` tables.
- `LLMManager` loads these automatically at startup, no code change needed.

### Integrating Guardrails

- Once the guardrail configuration table and logic are in place, simply add a row mapping a `generation_task` to the guardrail class and parameters.
- `ItemEnricher` will dynamically load and apply them after LLM responses are retrieved.

### Adjusting Input/Output Schemas

- Update `LLMRequestAdapter` to handle new fields in the input request body.
- Update `DefaultJSONResponseFormatter` if output fields or structure need changing.

### Attribute Extraction Tuning

- Insert rows in `ae_inclusion_list` for the desired `product_type`.
- Set `certified=1` for attributes you want to include. Optionally specify `attribute_precision_level`.
- `ItemEnricher` will automatically apply this logic when dealing with tasks that relate to attributes.

## Performance and Scaling

- Connection pooling and indexing at the DB layer.
- Horizontal scaling by running multiple app instances behind a load balancer.
- Add caching layers if prompt generation or style guides retrieval become bottlenecks.

## Conclusion

This serving layer is flexible, data-driven, and highly configurable. By storing configurations in the database and using adapters and managers, you can easily evolve tasks, templates, models, guardrails, and attributes logic without modifying the core code.