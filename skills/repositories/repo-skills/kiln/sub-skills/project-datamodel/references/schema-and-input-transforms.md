# JSON schemas and input transforms

Use this reference before creating structured tasks, importing structured datasets, validating task runs, or diagnosing schema/input-transform errors.

Evidence notes: distilled from `libs/core/kiln_ai/datamodel/json_schema.py`, `input_transform.py`, `task.py`, `task_run.py`, `task_output.py`, `utils/jinja_engine.py`, and related tests.

## Schema fields on `Task`

`Task` has two schema string fields:

| Field | Accepted schema shape | Used for |
|---|---|---|
| `input_json_schema` | Any valid JSON Schema dictionary; object and array schemas are allowed. | Validates `TaskRun.input` when a run is created or edited with a parent task. |
| `output_json_schema` | Valid JSON Schema dictionary with `type: "object"` and `properties`. | Validates `TaskOutput.output` when a run is created or edited with a parent task. |

Both fields store JSON strings, not Python dictionaries. Use `json.dumps()` when building tasks in code.

```python
import json
from kiln_ai.datamodel import Task

input_schema = {
    "type": "object",
    "properties": {"ticket": {"type": "string"}},
    "required": ["ticket"],
}
output_schema = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["account", "billing", "technical"]},
        "reason": {"type": "string"},
    },
    "required": ["category", "reason"],
    "additionalProperties": False,
}

task = Task(
    name="Classify Ticket",
    instruction="Classify the ticket and explain briefly.",
    input_json_schema=json.dumps(input_schema),
    output_json_schema=json.dumps(output_schema),
)
print(task.input_schema())
print(task.output_schema())
```

## Standalone schema validation helpers

```python
import json
from kiln_ai.datamodel.json_schema import (
    close_object_schemas,
    schema_from_json_str,
    single_string_field_name,
    strip_numeric_bounds,
    validate_schema,
    validate_schema_with_value_error,
)

schema_dict = schema_from_json_str(task.output_json_schema)
validate_schema({"category": "account", "reason": "Password reset"}, task.output_json_schema)

try:
    validate_schema_with_value_error(
        {"category": "unknown"},
        task.output_json_schema,
        "Output does not match task output schema.",
    )
except ValueError as exc:
    print(exc)

closed = close_object_schemas(schema_dict, strict=True)
wire_schema = strip_numeric_bounds(closed)
maybe_single = single_string_field_name(schema_dict)
```

Helper behavior:

- `schema_from_json_str()` parses a schema string and validates the schema itself.
- `validate_schema()` raises `jsonschema.exceptions.ValidationError` when a value fails validation.
- `validate_schema_with_value_error()` wraps validation failures as `ValueError` and includes the bad JSON instance in the message.
- `close_object_schemas()` recursively adds `additionalProperties: false` to object nodes when absent; with `strict=True`, it also marks every property required.
- `strip_numeric_bounds()` recursively removes numeric-bound keywords from integer/number schemas for provider wire-format compatibility without changing Kiln's local validation semantics.
- `single_string_field_name()` returns the one property name only when a schema has exactly one string property.

## Task-run validation lifecycle

`TaskRun.input` and `TaskOutput.output` are strings. If the parent task has schemas, Kiln parses these strings as JSON and validates the parsed values.

```python
import json
from kiln_ai.datamodel import TaskRun, TaskOutput

run = TaskRun(
    parent=task,
    input=json.dumps({"ticket": "I cannot log in"}),
    output=TaskOutput(
        output=json.dumps({"category": "account", "reason": "Login failure"}),
    ),
)
run.save_to_file()
```

Validation details:

- New or edited runs validate input when `task.input_json_schema` is set.
- New or edited outputs validate output when `task.output_json_schema` is set.
- Loading existing runs from disk skips the expensive schema check during the load operation; editing the loaded object can validate the changed field.
- If `TaskRun.trace` ends with an assistant message waiting for client tool calls, output validation is skipped for that pending state because the output may be intentionally empty or partial.
- Repaired outputs must not have ratings, and `repair_instructions` and `repaired_output` must be provided together.

Common validation errors:

| Symptom | Likely cause | Fix |
|---|---|---|
| `Invalid JSON` while assigning `input_json_schema` or `output_json_schema` | Schema string is not valid JSON. | Build the schema as a dict and pass `json.dumps(schema)`. |
| `JSON schema must be an object with properties` | `output_json_schema` is missing `type: "object"` or `properties`. | Use object schema for outputs. Arrays are only accepted for inputs. |
| `Input is not a valid JSON object` | Parent task has an input schema, but `TaskRun.input` is not JSON. | Store a JSON string matching the input schema. |
| `Output is not a valid JSON object` | Parent task has an output schema, but `TaskOutput.output` is not JSON. | Store a JSON object string matching the output schema. |
| `The error from the schema check was: ...` | JSON parsed successfully but failed JSON Schema validation. | Compare the parsed value with required fields, types, enums, and `additionalProperties`. |

## Array input schemas

`input_json_schema` can be an array schema. `output_json_schema` cannot.

```python
import json
from kiln_ai.datamodel import Task, TaskRun, TaskOutput

array_input_task = Task(
    name="Summarize Items",
    instruction="Summarize every item.",
    input_json_schema=json.dumps({
        "type": "array",
        "items": {"type": "string"},
    }),
    output_json_schema=json.dumps({
        "type": "object",
        "properties": {"summary": {"type": "string"}},
        "required": ["summary"],
    }),
)

TaskRun(
    parent=array_input_task,
    input=json.dumps(["first", "second"]),
    output=TaskOutput(output=json.dumps({"summary": "Two items"})),
)
```

If you call `validate_schema()` directly on an array schema, pass `require_object=False`.

## Input transforms

`JinjaInputTransform` stores a Jinja template that renders a task input into the first user message. The template is compiled during pydantic validation.

```python
from pydantic import TypeAdapter
from kiln_ai.datamodel.input_transform import InputTransform, JinjaInputTransform
from kiln_ai.utils.jinja_engine import render_input_transform

transform = JinjaInputTransform(
    template="Ticket: {{ input.ticket }}\nCustomer tier: {{ input.tier | default('unknown') }}"
)
message = render_input_transform(transform, {"ticket": "Cannot log in", "tier": "pro"})
print(message)

adapter = TypeAdapter(InputTransform)
restored = adapter.validate_python({
    "type": "jinja",
    "template": "Ticket: {{ input.ticket }}",
})
```

Input-transform behavior:

- Current discriminated-union type is `type: "jinja"`.
- A missing or unknown transform `type` raises a pydantic validation error.
- Malformed Jinja syntax raises `ValueError` through pydantic validation with an `Invalid Jinja2 template` message.
- Rendering always exposes one variable named `input`.
- If the task input passed to rendering is a string, the renderer tries `json.loads()` first; if parsing fails, `input` is the raw string.
- The template environment uses `StrictUndefined`, so missing fields referenced directly in templates fail instead of silently becoming empty text.

## Practical workflow for structured datasets

1. Define schemas as Python dictionaries.
2. Validate schemas with `schema_from_json_str(json.dumps(schema))` before creating many records.
3. Create or load a `Task` with those schemas.
4. Create `TaskRun` records with JSON-string inputs and outputs.
5. Let the datamodel raise validation errors early; do not catch and discard them during import.
6. Save runs only after construction succeeds.
7. If importing historical files, load them first, inspect failures, then rewrite only records you intentionally repair.

```python
import json
from kiln_ai.datamodel import TaskRun, TaskOutput

for item in incoming_rows:
    run = TaskRun(
        parent=task,
        input=json.dumps(item["input"]),
        output=TaskOutput(output=json.dumps(item["output"])),
    )
    run.save_to_file()
```

If a batch import mixes valid and invalid rows, keep an error report outside the project directory and only save validated `TaskRun` objects.
