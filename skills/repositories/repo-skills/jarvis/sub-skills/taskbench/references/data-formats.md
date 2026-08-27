# TaskBench data formats

TaskBench stores each domain as a directory containing tool descriptions, a tool graph, data JSONL, user-request JSONL, and optional alignment ids. A future agent should validate the directory before inference or evaluation because the native evaluator assumes normalized field names.

## Domain layout

Expected files:

```text
DATA_DIR/
  tool_desc.json
  graph_desc.json
  data.json
  user_requests.json
  alignment_ids.json        # optional, required only for alignment subsets
  predictions/              # produced by inference
  metrics/                  # produced by evaluation
```

Built-in domain mapping:

| Domain directory name | Dependency type | Tool schema |
| --- | --- | --- |
| `data_huggingface` | `resource` | tools have `input-type` and `output-type` lists |
| `data_multimedia` | `resource` | tools have `input-type` and `output-type` lists |
| `data_dailylifeapis` | `temporal` | APIs have request `parameters` |

Do not infer dependency type from benchmark name alone when using a custom directory. Inspect the first tool record: resource tools have `input-type`/`output-type`; temporal APIs have `parameters`.

## `tool_desc.json`

Top-level shape:

```json
{
  "nodes": [
    {"id": "Tool or API name", "desc": "Human-readable description"}
  ]
}
```

Resource tool node fields:

```json
{
  "id": "Image-to-Image",
  "desc": "Transforms an input image into another image.",
  "input-type": ["image"],
  "output-type": ["image"]
}
```

Temporal API node fields:

```json
{
  "id": "send_sms",
  "desc": "Send an sms to a phone number",
  "parameters": [
    {"name": "phone_number", "type": "string", "desc": "Destination phone number"},
    {"name": "content", "type": "string", "desc": "Message body"}
  ]
}
```

Validation expectations:

- `nodes` is a non-empty list.
- `id` values are unique strings.
- Resource nodes contain list-valued `input-type` and `output-type`.
- Temporal nodes contain list-valued `parameters`; each parameter should have at least `name` and `type`, with `desc` recommended.

## `graph_desc.json`

Top-level shape:

```json
{
  "nodes": [
    {"id": "Tool or API name", "desc": "..."}
  ],
  "links": [
    {"source": "Source tool", "target": "Target tool", "type": "resource-or-complete"}
  ]
}
```

Resource graphs:

- Nodes mirror resource tool records.
- A link means the source tool can provide a resource type consumed by the target tool.
- Link `type` is usually one shared resource type such as `text`, `image`, `audio`, `video`, or `url`.
- Native graph generation links every ordered pair where `source.output-type` intersects `target.input-type`.

Temporal graphs:

- Nodes mirror API records with `parameters`.
- Links represent possible invocation order rather than resource flow.
- Native temporal graph generation creates complete directed links between distinct APIs with link `type` equal to `complete`.

## `user_requests.json`

JSONL file; each line is one object:

```json
{"id": "13590101", "user_request": "I want to watch the movie titled 'Example Movie'"}
```

Validation expectations:

- Every line is valid JSON.
- `id` is a string or number that can be compared with `data.json` and prediction ids.
- `user_request` is a non-empty string.

## `data.json`

The native evaluator expects normalized TaskBench records. Some released data files use legacy field names and JSON-encoded strings; validate and normalize before evaluation if necessary.

### Normalized evaluator schema

```json
{
  "id": "77532649",
  "seed": 813407,
  "type": "single",
  "n_tools": 1,
  "user_request": "I want to watch the movie titled 'Inception'",
  "task_steps": ["Step 1: Invoke play_movie_by_title with title 'Inception'."],
  "task_nodes": [
    {"task": "play_movie_by_title", "arguments": [{"name": "title", "value": "Inception"}]}
  ],
  "task_links": []
}
```

Required normalized fields for evaluation:

- `id`: sample id.
- `type`: split label, usually `single`, `chain`, or `dag`.
- `n_tools`: number of tools in the invocation graph.
- `user_request`: natural-language instruction.
- `task_steps`: list of step strings or step-like objects.
- `task_nodes`: list of tool/API invocation nodes.
- `task_links`: list of dependency links. Empty for single-node records; required for temporal workflows.

Resource `task_nodes`:

```json
{"task": "Image Captioning", "arguments": ["example.jpg"]}
```

Resource arguments are strings or simple values. References to prior tool outputs use `<node-0>`, `<node-1>`, and so on. Native evaluation derives resource links from these references.

Temporal `task_nodes`:

```json
{
  "task": "send_sms",
  "arguments": [
    {"name": "phone_number", "value": "1234567890"},
    {"name": "content", "value": "Running late"}
  ]
}
```

Temporal `task_links` explicitly lists invocation order:

```json
[{"source": "get_weather", "target": "send_sms"}]
```

### Legacy released-data schema

Observed legacy records use:

- `instruction` instead of `user_request`.
- `tool_steps` instead of `task_steps`.
- `tool_nodes` instead of `task_nodes`.
- `tool_links` instead of `task_links`.
- Several list fields stored as JSON strings rather than arrays.

Legacy rows can be used as provenance and fixtures, but the native evaluator reads normalized names. Convert legacy rows in a temporary copy of `data.json` before using `evaluate.py`, or validate with a tool that explicitly accepts legacy mode.

## Prediction JSONL

Native inference writes one JSON object per line. Minimal schema:

```json
{
  "id": "sample-id",
  "user_request": "Original request text",
  "result": {
    "task_steps": ["Step 1: ..."],
    "task_nodes": [
      {"task": "Tool or API name", "arguments": []}
    ],
    "task_links": []
  }
}
```

Resource predictions may omit `task_links`; links are inferred from `<node-j>` argument references during evaluation. Temporal predictions must include `task_links` because the link metric reads it directly.

Malformed prediction cases to catch before evaluation:

- A JSONL line is not valid JSON.
- `result` is a raw string or markdown block instead of an object.
- `task_nodes` is missing, not a list, or uses a tool/API name not present in `tool_desc.json`.
- Temporal arguments are strings instead of `{name, value}` objects.
- Temporal `task_links` is missing or names nodes not used by the prediction.

Use `--reformat true` during inference or a separate recovery pass when model output is malformed.

## `alignment_ids.json`

Alignment subsets are optional. The observed shape is an object with keys such as:

- `node_alignment_id`
- `link_alignment_id`
- `both_node_link_alignment_id`
- `self-check_alignment_id`
- `all_alignment_id`

Each value maps split names (`single`, `chain`, `dag`) to id lists. Native evaluation flattens a selected alignment subset before filtering labels.
