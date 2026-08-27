# Template resolution and conditions

SAM workflows pass data between workflow input, node outputs, map/loop context, conditions, and final output with `{{...}}` templates. This reference captures the behavior exercised by the installed workflow implementation and unit tests.

## Template locations

Templates are commonly used in:

- `workflow.output_mapping`
- `agent` and `workflow` node `input`
- `agent` and `workflow` node `instruction`
- `agent` and `workflow` node `when`
- `switch.cases[].condition` / `switch.cases[].when`
- `loop.condition`
- map item expressions such as `items: "{{fetch.output.items}}"`

Templates can be scalar strings or nested inside dicts/lists. Non-template literal values pass through unchanged.

## Basic references

| Expression | Meaning |
| --- | --- |
| `{{workflow.input}}` | Entire workflow input object. |
| `{{workflow.input.field}}` | Field from workflow input. Nested paths are supported, e.g. `{{workflow.input.customer.id}}`. |
| `{{workflow.parameters.field}}` | Argo-compatible alias for `{{workflow.input.field}}`. |
| `{{node_id.output}}` | Entire output object from a completed node. |
| `{{node_id.output.field}}` | Field from a completed node output. Nested paths are supported. |
| `{{_map_item}}` | Current map item in a map target input mapping. |
| `{{_map_item.field}}` | Field from the current map item in a map target input mapping. |
| `{{item}}`, `{{item.field}}` | Argo-compatible aliases for map item templates. |
| `{{_map_index}}` | Zero-based map iteration index. |
| `{{_loop_iteration}}` | Zero-based loop iteration count. |
| `{{workflow.status}}`, `{{workflow.error}}`, `{{workflow.output}}` | Workflow-level completion context, most useful in exit-handler nodes. |

Example input mapping:

```yaml
- id: process
  type: agent
  agent_name: Processor
  depends_on: [validate]
  input:
    original_request: "{{workflow.input.request}}"
    clean_payload: "{{validate.output.cleaned_payload}}"
    labels:
      - "{{validate.output.category}}"
      - manual-review
```

## Missing values and errors

The resolver distinguishes between missing nodes and missing fields:

- A missing workflow input object is an error.
- A missing workflow input field resolves to `null`/`None`; this enables `coalesce` fallbacks.
- A missing node reference in a plain value resolver can resolve to `null`/`None`; this enables branch output coalescing where skipped branches have no result.
- A missing field inside an existing node output is an error because it usually means the template path is wrong.
- Conditional expressions are stricter: referencing a node that has not completed or a missing path usually raises a conditional evaluation error; switch cases catch evaluation failures and move to the next case/default.

Use `coalesce` when a branch may be skipped:

```yaml
output_mapping:
  response:
    coalesce:
      - "{{billing.output.response}}"
      - "{{technical.output.response}}"
      - "{{general.output.response}}"
```

## Operators in value mappings

### `coalesce`

Returns the first non-null resolved value. The argument must be a list.

```yaml
input:
  customer_id:
    coalesce:
      - "{{lookup.output.customer_id}}"
      - "{{workflow.input.customer_id}}"
      - anonymous
```

### `concat`

Resolves each list item, skips `null`, converts non-string values to strings, and concatenates them.

```yaml
input:
  message:
    concat:
      - "Ticket "
      - "{{workflow.input.ticket_id}}"
      - " classified as "
      - "{{classify.output.kind}}"
```

The `concat` argument must be a list.

## Conditions

`switch`, `loop`, and `when` expressions use a safe expression evaluator. Supported syntax includes:

- Comparisons: `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`
- Boolean operators: `and`, `or`, `not`
- Parentheses for grouping
- Literals: strings, numbers, booleans (`true`/`false`, any case), and null/none (`null`, `none`, `None`)

Quote string templates inside conditions so the resolved expression remains valid:

```yaml
cases:
  - condition: "'{{classify.output.kind}}' == 'billing'"
    node: billing_path
  - condition: "'high' in '{{classify.output.tags}}'"
    node: priority_path
```

Numeric and boolean templates usually should not be quoted:

```yaml
when: "{{score.output.value}} >= 0.8 and {{score.output.ready}} == true"
```

A switch evaluates cases top-to-bottom and selects the first true case. Failed condition evaluation is logged and treated like no match for that case. A loop runs once before evaluating its condition for the next iteration.

## Map templates

Map nodes resolve their item source, then execute the target node once per item.

```yaml
nodes:
  - id: load_items
    type: agent
    agent_name: ItemLoader

  - id: process_items
    type: map
    depends_on: [load_items]
    items: "{{load_items.output.items}}"
    node: process_one
    concurrencyLimit: 3

  - id: process_one
    type: agent
    agent_name: ItemProcessor
    input:
      id: "{{_map_item.id}}"
      raw_item: "{{_map_item}}"
      index: "{{_map_index}}"
```

The target node can also use Argo aliases in input mappings:

```yaml
input:
  id: "{{item.id}}"
```

Caution for `when`/condition expressions inside map targets: condition evaluation follows path resolution through the workflow state. If `{{item.field}}` fails in a condition, use the wrapped form `{{item.output.field}}` and validate the config. Input mappings use the unwrapped `{{_map_item.field}}`/`{{item.field}}` form.

Map output shape:

```yaml
output_mapping:
  processed_items: "{{process_items.output.results}}"
```

The `results` list preserves item order.

## Loop templates

Loop nodes expose `_loop_iteration` to their target node input. The first iteration has value `0`.

```yaml
nodes:
  - id: poll
    type: loop
    node: check_status
    condition: "{{check_status.output.ready}} == false"
    maxIterations: 5
    delay: 2s

  - id: check_status
    type: agent
    agent_name: StatusChecker
    input:
      task_id: "{{workflow.input.task_id}}"
      iteration: "{{_loop_iteration}}"

output_mapping:
  ready: "{{check_status.output.ready}}"
  iterations: "{{poll.output.iterations_completed}}"
```

Loop stop reasons include `condition_false` and `max_iterations`.

## Workflow nesting templates

A `workflow` node passes input to another workflow and receives output like an agent node.

```yaml
- id: validate_data
  type: workflow
  workflow_name: ValidationWorkflow
  input:
    dataset: "{{workflow.input.dataset}}"

- id: summarize
  type: agent
  agent_name: Summarizer
  depends_on: [validate_data]
  input:
    validation: "{{validate_data.output}}"
```

Avoid direct self-recursion. Use `max_call_depth`/`maxCallDepth` on the parent workflow definition to bound nested calls.

## Template dependency checklist

When authoring a node input or condition:

1. Identify every `{{node_id.output...}}` reference.
2. Ensure the referenced node id exists.
3. Ensure the current node has `depends_on` covering those producers, unless the reference is intentionally optional and guarded by `coalesce`.
4. For switch branch handlers, depend on the switch node, not only the classifier node.
5. For final `output_mapping`, use `coalesce` for mutually exclusive branch outputs.
6. Run [../scripts/validate_workflow_config.py](../scripts/validate_workflow_config.py) for static references and package model checks.
