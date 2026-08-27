# YAML and Export Reference

## Load and save

`Flow`, `Deployment`, and `Executor` configurations are JAML-compatible.

```python
from jina import Flow
f = Flow.load_config("flow.yml")
f.save_config("flow-out.yml")
```

The installed baseline supports these load arguments:

- `allow_py_modules`
- `substitute`
- `context`
- `uses_with`
- `uses_metas`
- `uses_requests`
- `extra_search_paths`
- `py_modules`
- `runtime_args`
- `uses_dynamic_batching`
- `needs`
- `include_gateway`
- `noblock_on_start`

## Variables

Use these variable forms in YAML:

- `${{ ENV.VAR }}` for environment variables.
- `${{ CONTEXT.VAR }}` for explicit context values.
- Relative variable references for fields within the same object.

## Export commands

- `jina export schema --schema-path ... --yaml-path ... --json-path ...`
- `jina export docker-compose flow.yml docker-compose.yml`
- `jina export kubernetes flow.yml ./config`
- `jina export flowchart flow.yml` when a visual overview is needed.

## Development pattern

Use a tiny YAML file to validate topology before deploying a heavier runtime. The exported YAML should be self-contained and not depend on the original repository checkout.
