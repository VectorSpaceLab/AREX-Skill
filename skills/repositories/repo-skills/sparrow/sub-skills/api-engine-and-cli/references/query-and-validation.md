# Query preparation and validation

This reference explains how the engine turns CLI/API fields into prompts, how backend option flags affect validation, and how Sparrow parses returned JSON.

## Query mode precedence

The document pipeline prepares the query in this order:

1. If `query == "*"` and `page_type` is provided, Sparrow prepares a page-type classification query and does **not** treat the request as an all-data extraction.
2. If `query == "*"` and `page_type` is not provided, Sparrow treats the request as a generic all-data extraction and bypasses schema validation.
3. For non-wildcard queries, `instruction=True` prepares an instruction prompt.
4. For non-wildcard queries, `validation=True` prepares a field-presence validation prompt.
5. For non-wildcard queries, `markdown=True` prepares the grounding prompt used by the markdown wrapper.
6. Otherwise, Sparrow expects `query` to be valid JSON and prepares a JSON-schema extraction prompt.

Avoid mixing `query="*"` with `instruction`, `validation`, or `markdown` unless you deliberately want wildcard behavior; the wildcard branch is checked first.

## Standard JSON-schema extraction

For a normal document extraction query:

```json
[{"instrument_name":"str", "valuation":0}]
```

Sparrow first checks that the query string is valid JSON. If it is not valid JSON, query preparation raises:

```text
Invalid query. Please provide a valid JSON query.
```

A valid query is embedded into an extraction instruction equivalent to:

- retrieve data based on the provided JSON schema;
- return the response in JSON format;
- strictly follow the provided schema;
- return `null` when a field is not visible or cannot be found;
- do not guess, infer, or generate values for missing fields.

If `hints_file_path` or API `hints_file` is provided and it is a readable JSON file, its JSON content is appended under an `Additional Hints` section. Missing files, invalid JSON, and non-JSON paths contribute no hints and do not fail the request.

## Wildcard extraction and page-type classification

`query="*"` means one of two different things:

| Request | Prepared query | Validation behavior | Typical use |
| --- | --- | --- | --- |
| `query="*"` without `page_type` | `None` / generic all-data mode | schema validation bypassed because there is no example schema | ask the VLM backend to return all detected content |
| `query="*"` with page types | `detect page type based on this list of types - <types>. return response in JSON format` | schema validation bypassed because this is classification output | classify pages as one of the supplied types |

For CLI, supply page types as repeated flags:

```bash
./sparrow.sh '*' --pipeline sparrow-parse \
  --options mlx --options model-name \
  --page-type invoice --page-type table \
  --file-path document.pdf
```

For API, supply `page_type=invoice,table` and include `options=...`; this implementation only splits the API `page_type` field when `options` is also present.

## Instruction and validation prompt modes

### Document instruction mode

With `--instruction` or `instruction=true`, a non-wildcard document query is rewritten as:

```text
<query>. response must be short, with values to answer the question, no need to provide other values. return response in JSON format
```

Because the answer is expected to be task-specific rather than schema-shaped, post-schema validation is disabled.

### Field-presence validation mode

With `--validation` or `validation=true`, a non-wildcard query such as:

```text
tax_id,shipment_code,total_gross_worth
```

is rewritten as:

```text
validate if listed fields - tax_id,shipment_code,total_gross_worth are present in the document. format response with field name and boolean value. return response in JSON format
```

This is **not** the same as post-schema JSON validation. It asks the model to return a boolean field-presence map, so post-schema validation is disabled.

### Instruction-only endpoint

The instruction pipeline expects the text query itself to contain both markers:

```text
instruction: summarize the payload, payload: <content>
```

If either `instruction:` or `payload:` is absent, the pipeline returns:

```json
{"error": "Invalid query format. Query must contain both 'instruction:' and 'payload:' fields."}
```

## Backend options and validation flags

The document backend option list must have at least two entries:

1. backend method: `huggingface`, `mlx`, `ollama`, `vllm`, or `mistral`;
2. model name or hosted space;
3. optional flags from the remaining entries.

Recognized optional flags are case-insensitive and are checked only from entry index `2` onward:

| Option flag | Effect |
| --- | --- |
| `tables_only` | asks the document extractor to return table-only results |
| `validation_off` | disables post-schema JSON validation |
| `apply_annotation` | requests annotation/bounding-box style output where supported and disables post-schema JSON validation |

A verified backend configuration example:

```python
_configure_inference_backend(['ollama', 'mistral-small', 'tables_only'])
# -> ({'method': 'ollama', 'model_name': 'mistral-small'}, True, False, False)
```

Unsupported backend methods print an unsupported-method message and return no backend config; too few options raise `Invalid options provided for inference backend configuration.`

## Post-schema validation

When validation is enabled, the pipeline constructs a JSON schema from the query example and validates the model's returned JSON against it.

Supported example-schema value tokens include:

- `"str"`, `"int"`, `"float"`;
- `"str or null"`, `"int or null"`, `"float or null"`;
- numeric examples such as `0`, `0.0`, and nullable numeric string variants such as `"0 or null"` or `"0.0 or null"`;
- nested objects;
- arrays of objects;
- simple arrays using the first array element as the element schema.

Unsupported type strings raise an error during schema construction.

The validator normalizes one common shape mismatch:

- if the schema expects an array but the model returns one object, it wraps the object in an array;
- if the schema expects an object but the model returns an array, it validates the first array element.

## Validation result annotation

For a single-page response with validation enabled:

- if model output parses as JSON and validation passes, Sparrow adds `"valid": "true"`;
- if validation fails, Sparrow adds `"valid": "<schema validation error>"`;
- if model output is not JSON, Sparrow returns `{"message": "Invalid JSON format in LLM output", "valid": <validation_result>}`.

For multi-page responses, each page is processed similarly and then receives a `page` field. When validation is bypassed and markdown is not active, multi-page output is still parsed as JSON where possible; parse failures become `{"message": "Invalid JSON format in LLM output", "valid": "false"}`.

## Validation is bypassed by design when outputs are not schema-shaped

The document pipeline explicitly turns `validation_off` on for these cases:

- `page_type` is provided;
- `apply_annotation` backend option is present;
- `instruction=True`;
- `validation=True`;
- `markdown=True`;
- backend option `validation_off` is present;
- wildcard all-data extraction (`query="*"`) because there is no query schema.

This means the absence of a `valid` key is expected for page-type classification, annotation output, instruction-mode answers, field-presence validation answers, markdown intermediary output, and all-data wildcard extraction.
