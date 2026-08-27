# Troubleshooting CLI and API requests

Use this guide after confirming the request surface and pipeline routing in [cli-and-api.md](cli-and-api.md).

## Server port, docs, and route checks

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| Swagger docs are missing. | Wrong port or server not running. | Start with `python api.py` for port `8002`, or `python api.py --port <port>`. Visit `http://localhost:<port>/api/v1/sparrow-llm/docs`. |
| OpenAPI schema is missing. | Wrong path. | Use `/api/v1/sparrow-llm/openapi.json`. |
| Root path works but extraction path fails. | Server is alive but request body, protected access, backend options, or pipeline failed. | Move to the form-field, option, and response sections below. |
| A README-style `/health` check fails. | The LLM service implementation defines `/` and versioned docs paths; it does not define a dedicated `/health` route in the inspected API. | Use `/` for a basic message and docs/OpenAPI paths for service introspection. |

## Form-field parsing issues

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| API request ignores file upload. | Wrong content type or wrong field name. | Use `/inference` with `multipart/form-data` and field `file=@document.pdf`. `/instruction-inference` does not accept files. |
| API request ignores hints. | Wrong upload field or invalid JSON. | Use field `hints_file=@hints.json`. Hints are used only when the file is readable JSON; invalid/missing JSON is silently ignored. |
| Boolean flags do not take effect. | Form booleans were encoded unexpectedly. | Send explicit values such as `-F 'table=true'`, `-F 'debug=true'`, `-F 'instruction=true'`. |
| `page_type` seems ignored by the API. | The API only splits `page_type` when `options` is not `None`. | Include `options=backend,model` whenever sending `page_type=...`, or use CLI repeated `--page-type`. |
| Instruction-only request returns an error dict. | Query lacks required markers. | Use `instruction: ...` and `payload: ...` in the `query` field for `sparrow-instructor`. |

## Option comma parsing and backend setup

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| CLI backend setup says options are invalid. | Used one comma-joined `--options` value instead of repeated CLI flags. | CLI must repeat flags: `--options mlx --options model-name --options validation_off`. |
| API backend setup says options are invalid. | `options` field has fewer than two comma-separated entries. | API needs `options=backend,model-name` at minimum. |
| `tables_only`, `validation_off`, or `apply_annotation` is ignored. | Flag is in the wrong list position. | These flags are read from entries after backend/model: `options=mlx,model,tables_only`. |
| Table mode fails in the table/OCR pass. | Only one backend/model pair was supplied. | In table mode, supply two pairs: `options=form_backend,form_model,table_backend,table_model`. |
| Unsupported backend message appears. | Backend method is not one of the supported names. | Use `huggingface`, `mlx`, `ollama`, `vllm`, or `mistral`. |
| Config object returned but answer says backend not set up. | Unsupported method returned no config. | Correct the first option entry and retry. |

## `crop_size` integer parsing

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| API returns HTTP `422` with `crop_size must be a valid integer or empty`. | `crop_size` form field is non-empty text that cannot be parsed as an integer. | Omit it, send an empty value, or send a base-10 integer string such as `60`. |
| CLI rejects `--crop-size`. | Typer could not parse the value as an integer. | Use `--crop-size 60`, not `--crop-size sixty`. |

## Invalid JSON schema and validation errors

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| `Invalid query. Please provide a valid JSON query.` | Normal extraction query is not syntactically valid JSON. | Quote the schema carefully. Use single quotes around the shell argument and double quotes inside JSON. |
| `Unsupported type: ...` | Example-schema value uses an unsupported type string. | Use `str`, `int`, `float`, nullable variants such as `str or null`, or numeric examples such as `0` / `0.0`. |
| `Invalid JSON format in LLM output`. | The backend returned text or malformed JSON. | Confirm the prompt mode asks for JSON, inspect raw model output, try a simpler schema, or use `/instruction-inference` if text output is expected. |
| `Schema validation error: ...` appears in the `valid` field. | Model JSON parsed but does not conform to the generated schema. | Check numeric/string/null type expectations and whether the model returned object vs array. The validator wraps/unwraps one level, but fields remain required. |

Use `python scripts/json_validation_smoke.py` to run offline fixtures before sending a live request.

## Validation bypass surprises

| Symptom | Explanation | Check/fix |
| --- | --- | --- |
| No `valid` field is present. | Post-schema validation is disabled for wildcard extraction, `page_type`, `apply_annotation`, `instruction`, `validation`, `markdown`, and explicit `validation_off`. | This is expected when output is not intended to match the extraction schema. |
| `--validation` did not validate the schema. | `--validation` means field-presence prompt mode, not JSON-schema post-validation. | Use normal schema extraction without `--validation` to get post-schema validation. |
| `query="*"` plus page types returned classification output only. | Wildcard with `page_type` is a special page-type detection mode. | Remove `page_type` for all-data extraction, or use a JSON schema for data extraction with validation. |
| `apply_annotation` changed validation behavior. | Annotation/bounding-box output is not schema-shaped, so validation is disabled. | Do not use `apply_annotation` when you require a `valid` result for the original schema. |

## Protected access and `sparrow_key`

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| HTTP `403`: `Sparrow key is required for protected access.` | `protected_access=true` and no `sparrow_key` form field was sent. | Add `-F 'sparrow_key=<SPARROW_KEY>'` or disable protected access for local open testing. |
| HTTP `403`: protected pipeline not allowed. | Config-key validation is active and the key value is not configured. | Check `[keys]` values and usage limits. |
| HTTP `403`: invalid/disabled/usage limit exceeded. | Database-key validation is active or config-key limit is exceeded. | Confirm whether `use_database` is true. Check the backing key store and usage counters. |
| Key works once and then fails. | Usage limit is low and usage count is incremented on accepted requests. | Raise the limit or reset usage count in the configured backing store. |

Do not embed real key values in reusable examples. Use placeholders.

## Database disabled/enabled behavior

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| No inference logs appear. | `use_database=false`. | This is expected; logging functions no-op when database is disabled. |
| API startup shows database pool errors. | `use_database=true` but database driver, network, credentials, service name, or schema function is unavailable. | Fix the database settings and Oracle driver/runtime, or set `use_database=false` for local inference without analytics. |
| Protected access rejects every key after enabling database. | Database validation is now used instead of config keys. | Add/enable keys in the database key table/function expected by the service, or disable database-backed validation. |
| Config keys are not incrementing. | Database-backed validation is active. | With `use_database=true`, usage increments happen in the database flow rather than the config file. |

## Response JSONDecode failures

| Symptom | Surface | Meaning | Check/fix |
| --- | --- | --- | --- |
| HTTP `418` with raw answer in `detail`. | `/inference` | The endpoint expected JSON but `json.loads(answer)` failed. | Check model prompt, query mode, and whether instruction-like text should use `/instruction-inference`. |
| Plain text response is returned. | `/instruction-inference` | Non-JSON instruction output is accepted and returned as text. | This can be correct for instruction tasks; require JSON in the prompt if structured output is needed. |
| CLI prints non-JSON after `Sparrow response:`. | CLI | CLI does not enforce JSON parsing at the boundary. | Debug the backend output and query mode directly. |

## Table-template failures

| Symptom | Likely cause | Check/fix |
| --- | --- | --- |
| Empty table response with generic template. | No table blocks, no headers, unsupported query key, or no matching columns. | Use `query="*"` to auto-detect all columns, or use a query key exactly `items`. |
| Empty response with invoice template. | The invoice template is a placeholder in the inspected implementation. | Use `sparrow_generic_table` unless a refreshed implementation is available. |
| Template import error. | `table_template` name does not resolve. | Use a known template basename such as `sparrow_generic_table`. |
| Missing method error. | Template lacks `fetch_table_data` or `fetch_form_data`. | Choose an implemented template or add the required methods in the application code. |

Use `python scripts/table_template_smoke.py` for an offline generic-template sanity check before sending a live table request.
