# CLI and API operation

This reference covers request surfaces, argument normalization, endpoint form fields, pipeline routing, and response handling for Sparrow's LLM engine.

## Surface map

| Surface | Use when | Invocation shape | Notes |
| --- | --- | --- | --- |
| `sparrow.sh` | You are operating locally from the LLM service directory. | `./sparrow.sh '<query>' --pipeline sparrow-parse ...` | The wrapper verifies Python `3.12.10`, then dispatches to the Typer engine command. If the first positional token is `assistant`, it shifts that token and dispatches to the assistant command instead. |
| Typer engine command | You need exact CLI flags without the shell wrapper. | `python engine.py '<query>' --pipeline ...` | The command function is `run(query, file_path=None, hints_file_path=None, pipeline='sparrow-parse', options=None, crop_size=None, instruction=False, validation=False, ocr=False, markdown=False, table=False, table_template=None, page_type=None, debug_dir=None, debug=False)`. |
| Document API | You need HTTP document extraction, file upload, table mode, markdown mode, or page-type classification. | `POST /api/v1/sparrow-llm/inference` | Uses `multipart/form-data`; saves uploaded files to a temporary request directory before calling the same engine flow. |
| Instruction API | You need instruction/payload text processing without a document upload. | `POST /api/v1/sparrow-llm/instruction-inference` | Uses form fields only and calls the instruction-only engine helper. |
| API docs | You need Swagger/OpenAPI introspection. | `/api/v1/sparrow-llm/docs` and `/api/v1/sparrow-llm/openapi.json` | Default server port is `8002`; `python api.py --port <port>` overrides it. |

The FastAPI application also exposes `/` with a simple service message. The README mentions a health check, but this LLM service implementation defines the root route and the versioned docs/OpenAPI paths above.

## CLI arguments

The Typer engine command accepts one required positional `query` plus these options:

| CLI flag | Type | Meaning |
| --- | --- | --- |
| `--pipeline` | string | Pipeline name. Use `sparrow-parse` for document/schema extraction and `sparrow-instructor` for instruction/payload text processing. |
| `--file-path` | path | Local document path for `sparrow-parse`. Omit for instruction-only requests. |
| `--hints-file-path` | path | Optional JSON hints file. Invalid or missing JSON is silently ignored by query preparation. |
| `--options` | repeated string | Backend/mode options. Repeat this flag once per list entry. The first two entries are backend method and model/space; later entries are mode toggles. |
| `--crop-size` | integer | Border crop size passed into document/table extraction. |
| `--instruction` | flag | Treat a non-wildcard query as an instruction prompt for document processing. |
| `--validation` | flag | Treat a non-wildcard query as a field-presence validation prompt. |
| `--ocr` | flag | Enables the OCR callback hook inside the document pipeline; OCR service internals belong to `../ocr-service/SKILL.md`. |
| `--markdown` | flag | Uses the markdown extraction wrapper before an instructor extraction pass. |
| `--table` | flag | Uses the table extraction wrapper and table templates. |
| `--table-template` | string | Table template module basename, such as `sparrow_generic_table`. |
| `--page-type` | repeated string | Candidate page types. Repeat this flag for CLI requests. |
| `--debug-dir` | path | Debug output directory used by the engine and extraction helpers. |
| `--debug` | flag | Enables debug prints and JSON response prints. |

### CLI option list rule

For CLI, do **not** comma-join the backend options. Repeat `--options`:

```bash
./sparrow.sh '[{"field_name":"str", "amount":0}]' \
  --pipeline sparrow-parse \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --options validation_off \
  --file-path document.pdf
```

For page types, repeat `--page-type`:

```bash
./sparrow.sh '*' \
  --pipeline sparrow-parse \
  --options mlx \
  --options mlx-community/Qwen3.6-35B-A3B-8bit \
  --page-type invoice \
  --page-type table \
  --file-path multi-page.pdf
```

## Pipeline factory routing

The engine calls a pipeline factory before dispatching work:

- `sparrow-parse` routes to the document/schema pipeline.
- `sparrow-instructor` routes to the instruction/payload text pipeline.
- `stocks` routes to the assistant stock example and is not the normal LLM API path.
- Any other pipeline name raises `Unknown pipeline: <name>`.

After the factory returns a pipeline instance, engine routing is:

1. `--markdown` / `markdown=true`: run markdown extraction, then route markdown content through `sparrow-instructor` for structured extraction.
2. `--table` / `table=true`: run table extraction and table templates.
3. Otherwise: call the selected pipeline's `run_pipeline(...)` directly.

`/api/v1/sparrow-llm/inference` follows the same three branches after storing uploaded files and hints files in temporary request storage. `/instruction-inference` bypasses document flags and calls `sparrow-instructor` with no file.

## Document API form fields

Endpoint: `POST /api/v1/sparrow-llm/inference`

| Form field | Required | Type | Notes |
| --- | --- | --- | --- |
| `query` | yes | string | JSON example schema, `*`, instruction text, validation field list, or markdown/table schema depending on flags. |
| `pipeline` | yes | string | Usually `sparrow-parse`; `sparrow-instructor` is supported but instruction-only work should prefer `/instruction-inference`. |
| `options` | no, but required by inference backends | comma-separated string | Split on commas and stripped. Needs at least backend and model/space for normal inference. |
| `crop_size` | no | string integer or empty | Empty/omitted becomes `None`; invalid text returns HTTP `422`. |
| `instruction` | no | bool form value | Changes non-wildcard query preparation and disables post-schema validation. |
| `validation` | no | bool form value | Creates a field-presence validation prompt and disables post-schema validation. |
| `ocr` | no | bool form value | Enables the OCR callback path. |
| `markdown` | no | bool form value | Enables markdown wrapper flow. |
| `table` | no | bool form value | Enables table-template flow. |
| `table_template` | no | string | Use `sparrow_generic_table` for the implemented generic template. |
| `page_type` | no | comma-separated string | Split into page-type candidates only when `options` is also provided by this implementation. |
| `debug_dir` | no | string | Debug output target. |
| `debug` | no | bool form value | Prints JSON response in server logs. |
| `sparrow_key` | only when protected access is enabled | string | Used by config-key or database-key validation. |
| `client_ip` | no | string | Defaults to `127.0.0.1`; logged when database logging is enabled. |
| `country` | no | string | Defaults to `Unknown`; logged when database logging is enabled. |
| `file` | no | upload | Required for document extraction. If PDF, page count is estimated before inference logging. |
| `hints_file` | no | upload | Optional JSON hints file for schema extraction. |

Example API request:

```bash
curl -X POST 'http://localhost:8002/api/v1/sparrow-llm/inference' \
  -H 'Content-Type: multipart/form-data' \
  -F 'query=[{"field_name":"str", "amount":0}]' \
  -F 'pipeline=sparrow-parse' \
  -F 'options=mlx,mlx-community/Qwen2.5-VL-72B-Instruct-4bit' \
  -F 'file=@document.pdf'
```

## Instruction API form fields

Endpoint: `POST /api/v1/sparrow-llm/instruction-inference`

| Form field | Required | Type | Notes |
| --- | --- | --- | --- |
| `query` | yes | string | Must contain both `instruction:` and `payload:` for `sparrow-instructor`. |
| `pipeline` | yes | string | Usually `sparrow-instructor`. |
| `options` | no, but required by inference backends | comma-separated string | Split on commas and stripped; needs backend and model/space. |
| `debug_dir` | no | string | Debug output target. |
| `debug` | no | bool form value | Prints response in server logs. |
| `sparrow_key` | only when protected access is enabled | string | Same protected-access gate as document API. |
| `client_ip` | no | string | Defaults to `127.0.0.1`. |
| `country` | no | string | Defaults to `Unknown`. |

Example:

```bash
curl -X POST 'http://localhost:8002/api/v1/sparrow-llm/instruction-inference' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'query=instruction: do arithmetic, payload: 2+2=' \
  -d 'pipeline=sparrow-instructor' \
  -d 'options=mlx,mlx-community/Qwen3.6-35B-A3B-8bit'
```

## Convert a curl extraction request into CLI options

API `options=` is comma-separated; CLI `--options` is repeated. API `page_type=` is comma-separated; CLI `--page-type` is repeated.

Given this curl body:

```bash
-F 'query=[{"field_name":"str", "amount":0}]' \
-F 'pipeline=sparrow-parse' \
-F 'options=mlx,mlx-community/Qwen2.5-VL-72B-Instruct-4bit,validation_off' \
-F 'crop_size=60' \
-F 'page_type=invoice,table' \
-F 'file=@document.pdf'
```

The CLI equivalent is:

```bash
./sparrow.sh '[{"field_name":"str", "amount":0}]' \
  --pipeline sparrow-parse \
  --options mlx \
  --options mlx-community/Qwen2.5-VL-72B-Instruct-4bit \
  --options validation_off \
  --crop-size 60 \
  --page-type invoice \
  --page-type table \
  --file-path document.pdf
```

Use `python scripts/sparrow_cli_request.py --from-curl-file request.txt --surface cli` to perform this normalization safely without sending a request.

## Response parsing and HTTP behavior

- CLI prints `Sparrow response:` and then the raw pipeline answer.
- `/inference` tries to parse string/bytes answers with `json.loads`. If parsing fails, it returns HTTP `418` with the raw answer as `detail`.
- `/instruction-inference` also tries `json.loads`, but leaves non-JSON text unchanged when parsing fails.
- Engine `ValueError` exceptions become HTTP `418` responses.
- Invalid `crop_size` text becomes HTTP `422` with `crop_size must be a valid integer or empty`.
- Missing or invalid protected-access keys become HTTP `403`.
