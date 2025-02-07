# **Gen AI Item Enrichment API - README**

## **Table of Contents**

1. [High-Level Overview](#high-level-overview)  
2. [Item Enricher Flow](#item-enricher-flow)  
3. [Prompt Manager & Template Flow](#prompt-manager--template-flow)  
4. [Caching (Megacache) Details](#caching-megacache-details)  
   - [Key Hierarchies](#key-hierarchies)  
   - [Cache Wrappers](#cache-wrappers)  
   - [Examples of Cache Usage](#examples-of-cache-usage)  
5. [Database Toggle (SQLite vs. Azure SQL)](#database-toggle-sqlite-vs-azure-sql)  
6. [Design Rationale (Pros & Cons)](#design-rationale-pros--cons)  
7. [Getting Started](#getting-started)

---

## **1. High-Level Overview**

This API enriches item data by:

1. **Fetching** product attributes/specs (AE scope data), style guides, and prompt templates from a database (SQLite in dev or Azure SQL in prod).  
2. **Optionally retrieving** them from **Megacache** (memcached) if `USE_CACHE=True`.  
3. **Generating** prompts via `PromptManager` and an LLM (OpenAI, etc.).  
4. **Applying** post-processing hooks or validations (guardrails).  
5. **Returning** the final enriched result.

Core modules:
- **ItemEnricher**: Orchestrates the entire process.  
- **PromptManager**: Builds a Jinja2 prompt context (including style guides, attribute definitions).  
- **TemplateRepository**: Fetches template text from the DB (or cache).  
- **Megacache**: Speeds up repeated lookups for AE data, style guides, templates, etc.

---

## **2. Item Enricher Flow**

The **`ItemEnricher`** is where everything **comes together**. A typical call (e.g., via `/enrich-item`) looks like this:

1. **Load AE Data**  
   - `ItemEnricher` calls `ae_scope_list_repo.get_certified_attributes(product_type)` to find all relevant attributes.  
   - It also calls `get_attribute_spec(product_type, attr)` for each attribute to retrieve a dictionary with fields like `closed_list`, `multi_select`, etc.  
   - **Caching**: The repository might check Megacache first (e.g., key = `spec_<product_type>_<attr_name>`). If `USE_CACHE=False`, it hits the DB directly.  
   - The loaded data is stored in `item["attributes_list"]` and `item["attribute_spec_list"]`.

2. **Generate Prompts**  
   - Next, `ItemEnricher` calls `PromptManager.generate_prompts(...)`.  
   - The `PromptManager` in turn fetches:
     - **Style Guides** (via `styling_guide_repo.get_styling_guide(product_type, task)` → possibly cached).  
     - **Templates** (via `template_repo.get_template_text(task_name, ... )` → possibly cached).  
   - Using these, the `PromptManager` builds a **Jinja2** context (including `attribute_definition_list` or a subset of the specs) and renders the final prompt strings.

3. **Invoke LLMs**  
   - The prompts are sent to LLM providers concurrently.  
   - `ItemEnricher._invoke_llms()` calls each provider with the final prompt.

4. **Apply Hooks** (Post-processing)  
   - If hooks (like guardrails) are defined for certain tasks, `ItemEnricher._apply_postprocess_hooks()` runs them on the JSON output.  
   - Example: If `closed_list` is `True`, a guardrail might verify the LLM’s extracted value is in `acceptable_values`.

5. **Return Enriched Result**  
   - A structured dictionary with fields like `title_enrichment`, `attributes_enrichment`, etc., is returned to the client.

**Why This Flow?**  
- We keep all steps in **one** place (`ItemEnricher`) so it’s easy to see how data is fetched, processed, and validated.

---

## **3. Prompt Manager & Template Flow**

**`PromptManager`** is responsible for:

1. Deciding **which tasks** to run (based on `TaskManager`).  
2. **Fetching style guides** for `(product_type, task)` from `StylingGuideRepository`.  
3. **Fetching prompt templates** from `TemplateRepository`.  
4. **Building context** (including `item["attributes_list"]`, partial specs, etc.) and rendering the final Jinja2 prompt.

A typical chain is:

1. `PromptManager.generate_prompts(item, family_name, task_type)`  
2. For each task:
   - Calls `styling_guide_repo.get_styling_guide(...)` -> might check the cache key `style_guide_{task}_{pt}`.  
   - Calls `template_repo.get_template_text(task_name, task_type, family_name)` -> might check the cache key `prompt_template_{task}_{task_type}_{family_name}`.  
   - **Combines** them in `_prepare_context()`, which can also incorporate a minimal `attribute_definition_list` from `item["attribute_spec_list"]`.  
   - Renders the final prompt string using Jinja2.

**Pros**:  
- Clear separation of “where we get data from” (repos) vs. “how we assemble context” (PromptManager).  
- The template repository is similarly cached, so each unique `(task, type, model_family)` fetch is quick.

---

## **4. Caching (Megacache) Details**

### **4.1 Key Hierarchies**

We store data in **memcache** using flattened string keys. Examples:

1. **AE Scope** (attributes & specs)  
   - `spec_<pt>` -> list of attributes for `<pt>`.  
   - `spec_<pt>_<attr>` -> the full spec for a single attribute.  
   - E.g., `spec_Athletic|Shoes_color` might store a JSON dict with `closed_list`, `acceptable_values`, etc.

2. **Style Guides**  
   - `style_guide_<task>_<pt>` -> the textual guide.  
   - E.g., `style_guide_desc_generation_Athletic|Shoes`.

3. **Templates**  
   - `prompt_template_<task_name>_<task_type>_<model_family>` -> the actual prompt text.  
   - E.g., `prompt_template_desc_generation_default_defaultFamily`.

**Why Flatten?**  
- Memcache is a **flat key-value store**. We replace spaces with `|` or `_` to keep it consistent.

### **4.2 Cache Wrappers**

For each repository, we have a **cached** wrapper:

- **CachedAEScopeListRepository** → tries keys like `spec_<pt>_<attr>`.  
- **CachedStylingGuideRepository** → tries keys like `style_guide_{task}_{pt}`.  
- **CachedTemplateRepository** → tries keys like `prompt_template_{task_name}_{task_type}_{family}`.

Each wrapper:

1. Checks `config.USE_CACHE`. If `False`, skip the cache.  
2. If `True`, does `cache_service.get(key)` first.  
3. On a **miss**, calls the original DB-based repo, then `cache_service.set(key, data)`.

### **4.3 Examples of Cache Usage**

**During `_process_attributes()`** in ItemEnricher:  
```python
attrs = ae_scope_list_repo.get_certified_attributes(pt)  
# -> tries key: spec_<pt> in Megacache

for attr in attrs:
    spec = ae_scope_list_repo.get_attribute_spec(pt, attr)
    # -> tries key: spec_<pt>_<attr>
```
**During PromptManager**:  
```python
style_guide = styling_guide_repo.get_styling_guide(pt, task)
# -> key: style_guide_{task}_{pt}

template_text = template_repo.get_template_text(task_name, task_type, family_name)
# -> key: prompt_template_{task_name}_{task_type}_{family_name}
```

---

## **5. Database Toggle (SQLite vs. Azure SQL)**

We rely on a single **`DATABASE_URL`** in `config.py`. For example:

- **Local Dev** (default):  
  ```
  DATABASE_URL="sqlite:///results.db"
  ```
- **Azure SQL** (Staging/Prod):  
  ```
  DATABASE_URL="mssql+pyodbc://username:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+17+for+SQL+Server"
  ```

When the app boots, we call `create_engine(config.DATABASE_URL)`. Everything else (like repository calls, `ItemEnricher`, caching) stays the same. We can seamlessly switch between DBs by changing the environment variable—**no code changes** required.

---

## **6. Design Rationale (Pros & Cons)**

### **Caching Strategy**

- **Pros**:
  - Speeds up repeated lookups (especially for large sets of attribute specs).  
  - Easy on/off toggle (`USE_CACHE`).  
  - Minimal changes to the main code flow, just wrap the repositories.
- **Cons**:
  - If data updates often, risk of stale cache if not invalidated quickly.  
  - Must carefully define keys (flattening PT, tasks, etc.).

### **Database Toggle**

- **Pros**:
  - Single codebase for dev (SQLite) vs. prod (Azure).  
  - No branching logic or environment-specific classes.  
- **Cons**:
  - Must install the correct ODBC driver & handle potential T-SQL differences.  
  - Must ensure both DBs have the same schema.

### **PromptManager & Templates**

- **Pros**:
  - Clear separation: fetch style guides/templates in one place, build a Jinja2 context, and render.  
  - Easy to add new tasks or placeholders.  
- **Cons**:
  - Another layer for devs to learn (context building, Jinja templates).

### **ItemEnricher Flow**

- **Pros**:
  - Single orchestrator that’s easy to trace: from AE data fetching to LLM calls.  
  - Hooks allow flexible post-processing.  
- **Cons**:
  - If the flow grows more complex, might need to break out specialized pipelines or sub-steps.

---

## **7. Getting Started**

1. **Clone** the repository and install dependencies (`pip install -r requirements.txt`).  
2. **Local Dev**:
   - If no environment variable is set, we default to `sqlite:///results.db`.  
   - `USE_CACHE` can be `False` to debug caching logic.  
   - Run `uvicorn main:app --reload` and test at http://127.0.0.1:8000/docs.
3. **Staging/Prod**:
   - Set `DATABASE_URL` to your Azure SQL connection string.  
   - `export USE_CACHE=true` if you want caching.  
   - Deploy the same code; no other modifications needed.

**Flow**:
- Send a `POST /enrich-item` with a JSON body containing `title`, `short_desc`, `long_desc`, `product_type`, etc.  
- The response includes enriched fields (`title_enrichment`, etc.), possibly referencing style guides and attribute specs from the DB or cache.

**That’s it!** Junior devs can now see exactly how the **ItemEnricher** retrieves AE data from Megacache/DB, uses **PromptManager** to render templates, and returns the final results. If you have any questions on key naming or hooking in new data sources, you can follow the same patterns in the **cached wrappers** or the **managers**.