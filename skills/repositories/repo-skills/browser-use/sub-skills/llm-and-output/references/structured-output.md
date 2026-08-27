# Structured Output

Use structured output when a Browser Use run must return data that downstream code can validate. Browser Use expects Pydantic v2 model classes for internal action schemas and final structured output.

## Minimal Pattern

```python
import asyncio
from pydantic import BaseModel
from browser_use import Agent, ChatBrowserUse

class Listing(BaseModel):
    title: str
    url: str
    price: str | None = None

class Listings(BaseModel):
    items: list[Listing]

async def main():
    agent = Agent(
        task=(
            "Go to the target page, extract the first 3 listings, "
            "and finish with only the requested structured fields."
        ),
        llm=ChatBrowserUse(),
        output_model_schema=Listings,
    )
    history = await agent.run(max_steps=30)
    result = history.structured_output
    if result is None:
        result = Listings.model_validate_json(history.final_result() or "{}")
    print(result.model_dump())

asyncio.run(main())
```

## What Browser Use Does

When `output_model_schema=MyModel` is passed to `Agent`:

- Browser Use adds a structured final `done` action using the Pydantic schema.
- The task text is enhanced with the expected output schema.
- If `extraction_schema` is not explicitly set, Browser Use bridges `output_model_schema.model_json_schema()` into `extraction_schema`.
- The returned `AgentHistoryList` can expose `history.structured_output` when it retains the schema.

If `Tools(output_model=...)` is also provided and differs from `Agent(output_model_schema=...)`, the Agent-level schema wins.

## Schema Design Rules

Use simple, explicit Pydantic models:

```python
from pydantic import BaseModel, Field

class Company(BaseModel):
    name: str = Field(description="Company display name")
    website: str | None = None
    confidence: float = Field(ge=0, le=1)
```

Prefer:

- `str`, `int`, `float`, `bool`, `list[...]`, nested `BaseModel`, and nullable fields.
- Short field names with field descriptions only where ambiguity matters.
- Optional fields for data that might not appear on the page.
- Small lists when the task can bound the count: “first 5 products,” not “all products.”

Avoid:

- Huge nested schemas for broad crawling tasks.
- Regex-heavy or provider-specific schema constraints when a prompt instruction is sufficient.
- Arbitrary dictionaries unless the page truly has unknown keys.
- Relying on model-generated JSON outside Browser Use’s final `done` path.

## Parsing Final Results

Prefer `history.structured_output` when available:

```python
result = history.structured_output
```

If the schema was not retained or you need explicit validation, parse the final result:

```python
raw = history.final_result()
if not raw:
    raise RuntimeError("Agent did not return a final result")
parsed = MyModel.model_validate_json(raw)
```

If a sandbox or beta path returns a generic history object, use the history helper if available:

```python
parsed = history.get_structured_output(MyModel)
```

## Task Prompting for Reliable Structured Output

Include the schema goal in the task even though Browser Use also injects the schema:

```python
task = """
Go to https://example.com/pricing.
Extract exactly the plan name, monthly price, and one-sentence feature summary for the first 3 plans.
If a field is missing, use null for optional fields.
Finish with the structured output only.
"""
```

Good structured-output prompts specify:

- Target URL or search path.
- Exact count or stopping rule.
- Required fields and optional fallback values.
- Whether currency, units, dates, or URLs must be normalized.
- What to do if data is absent.

## Extraction Schema Interaction

`output_model_schema` automatically supplies an extraction schema only when `extraction_schema` is absent. Use an explicit `extraction_schema` only when extraction data differs from the final answer shape.

Example: extract broad rows, then finish with a summarized schema.

```python
agent = Agent(
    task="Extract product rows, then return the cheapest in stock item.",
    llm=ChatBrowserUse(),
    output_model_schema=BestProduct,
    extraction_schema={
        "type": "object",
        "properties": {
            "rows": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "price": {"type": "string"},
                        "stock": {"type": "string"},
                    },
                },
            }
        },
    },
)
```

If the user asks for extraction-tool behavior or custom extraction actions, route custom tool implementation to `../../tools-and-actions/SKILL.md`.

## Provider-Specific Structured Output Notes

- `ChatBrowserUse` sends the Pydantic JSON schema as `output_format` to the Browser Use LLM API.
- `ChatOpenAI` has flags such as `dont_force_structured_output`, `add_schema_to_system_prompt`, `remove_min_items_from_schema`, and `remove_defaults_from_schema` for provider compatibility.
- `ChatGoogle` has `supports_structured_output`; set it to `False` if native JSON mode fails and prompt-based fallback is acceptable.
- `ChatMistral` strips unsupported JSON schema keywords before sending structured schemas.
- Some local or gateway models may return text that requires fallback parsing or schema simplification.

## Validation Repair Workflow

When users hit `ValidationError`, do not immediately change providers. Debug in this order:

1. Print the final text shape without secrets:

   ```python
   print(history.final_result())
   ```

2. Validate explicitly:

   ```python
   MyModel.model_validate_json(history.final_result() or "{}")
   ```

3. Simplify the model: remove nested unions, make uncertain fields optional, add clear descriptions.
4. Tighten the task: exact count, exact fields, null behavior, and “finish with the structured output only.”
5. Cap `max_steps` and test on a deterministic page.
6. If using a non-native provider, try `ChatBrowserUse()` or the provider’s compatibility flags.

## Common Errors

### `ValidationError` after `model_validate_json`

Likely causes:

- The agent did not finish with a structured `done` action.
- The model returned prose around JSON.
- Required fields were missing.
- Field types were too strict for page text.

Fixes:

- Use `output_model_schema=MyModel`, not just a prompt asking for JSON.
- Make fields optional when pages may omit values.
- Add task instructions for nulls and exact counts.
- Inspect `history.errors()` and `history.action_names()` to confirm the run reached `done`.

### `history.structured_output` is `None`

Likely causes:

- The run did not complete successfully.
- The history object does not retain `_output_model_schema`.
- No `output_model_schema` was passed.

Fixes:

- Parse `history.final_result()` with `MyModel.model_validate_json(...)`.
- Use `history.get_structured_output(MyModel)` if available.
- Confirm `history.is_done()` and `history.is_successful()`.

### Model rejects schema

Likely causes:

- Provider does not support part of the JSON schema.
- Schema is too large or uses unsupported keywords.

Fixes:

- Simplify model fields.
- For OpenAI adapter, try schema compatibility flags.
- For Google adapter, try `supports_structured_output=False`.
- For Mistral, rely on built-in schema keyword stripping but still keep schemas simple.
