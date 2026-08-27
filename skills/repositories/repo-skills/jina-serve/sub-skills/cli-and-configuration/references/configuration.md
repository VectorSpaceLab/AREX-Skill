# Configuration Reference

## Common YAML shapes

Deployment YAML:

```yaml
jtype: Deployment
with:
  uses: MyExecutor
  py_modules:
    - executor.py
  port: 12345
  timeout_ready: -1
```

Flow YAML:

```yaml
jtype: Flow
version: '1'
gateway:
  protocol: [grpc, http, websocket]
  port: [54321, 54322, 54323]
executors:
  - name: encoder
    uses: encoder/config.yml
  - name: indexer
    uses: indexer/config.yml
```

Executor YAML:

```yaml
jtype: MyExecutor
py_modules:
  - executor.py
with:
  model_name: tiny-model
metas:
  name: my-executor
requests:
  /index: index
  /search: search
```

## Variables and substitution

- Use `${{ ENV.VAR_NAME }}` to read an environment variable.
- Use `${{ CONTEXT.name }}` for a context dictionary passed to `load_config(..., context={...})`.
- Use `${{this.some.path}}` style references for relative variables within the same YAML object.

Example:

```yaml
jtype: Flow
with:
  name: ${{ CONTEXT.flow_name }}
executors:
  - name: encoder
    uses: encoder/config.yml
    env:
      JINA_LOG_LEVEL: ${{ ENV.JINA_LOG_LEVEL }}
```

## Overrides

Jina config loading supports overrides such as:

- `uses_with={...}` to override Executor constructor kwargs.
- `uses_metas={...}` to override metadata such as name/description.
- `uses_requests={...}` to map endpoints to methods.
- `py_modules=[...]` and `extra_search_paths=[...]` to locate classes.

Prefer explicit `py_modules` in YAML when a class lives in a local file. For production, keep Flow/Deployment YAML independent from inline Python definitions.

## Schema completion

Jina can export schemas for IDE completion:

```bash
jina export schema --schema-path schemas/latest.json --yaml-path flow.yml
```

Bind the schema URL or generated file to `*.jina.yml`, `*.jaml`, or your chosen suffix in your editor.
