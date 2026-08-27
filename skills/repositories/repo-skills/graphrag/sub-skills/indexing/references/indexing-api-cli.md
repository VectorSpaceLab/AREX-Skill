# Indexing API and CLI

## CLI Entrypoints

GraphRAG exposes indexing through `graphrag init`, `graphrag index`, and `graphrag update`.

```bash
graphrag init --root <project-root>
graphrag index --root <project-root> --method standard --dry-run
graphrag index --root <project-root> --method fast --verbose
graphrag update --root <project-root> --method standard
```

Important options:

- `--root <project-root>` points to the GraphRAG project directory containing settings and input/output locations.
- `--method standard|fast` selects the base indexing method. `update` derives the corresponding update pipeline.
- `--dry-run` is available for `index`, validates and logs config, then exits before pipeline execution.
- `--cache/--no-cache` controls LLM cache use for `index`; disabling cache sets the cache type to noop for that run.
- `--skip-validation` bypasses preflight config-name validation. Use carefully, mainly for no-LLM/custom-workflow cases where standard validation is too strict.
- `--verbose` enables more detailed logging and console workflow callbacks.

## Python API

Use `graphrag.config.load_config.load_config` with `graphrag.api.build_index`.

```python
import asyncio
from graphrag.api import build_index
from graphrag.config.load_config import load_config

config = load_config(root_dir="<project-root>")
results = asyncio.run(build_index(config, method="standard"))
errors = [result for result in results if result.error]
if errors:
    raise RuntimeError(errors[0].error)
```

Verified signature:

```python
build_index(
    config,
    method="standard",
    is_update_run=False,
    callbacks=None,
    additional_context=None,
    verbose=False,
    input_documents=None,
)
```

Behavioral notes:

- `method` accepts an `IndexingMethod` enum value or string.
- When `is_update_run=True`, GraphRAG appends `-update` to the base method before selecting a pipeline.
- `callbacks` can receive pipeline and workflow lifecycle events. The CLI uses console callbacks.
- `additional_context` is merged into pipeline state under `additional_context` and is not persisted to `context.json`.
- `input_documents` can bypass file loading; the pipeline writes the DataFrame as the `documents` table and removes the load workflow.

## Lifecycle

`build_index` initializes logging, creates callbacks, selects a pipeline via `PipelineFactory.create_pipeline`, then iterates `run_pipeline`. Each workflow returns a `PipelineRunResult` with `workflow`, `result`, `state`, and `error`.

`run_pipeline` creates input storage, output storage, table provider, and cache from config. On standard runs it writes directly to output storage. On update runs it creates timestamped update storage with `delta` and `previous` providers, copies previous output tables, and runs the update pipeline against delta/previous context.

## Error Handling

The pipeline catches workflow exceptions and yields a result whose `error` is set. The CLI exits nonzero if any result has an error. API callers should inspect every result, not only the final one.

## Safe Patterns

- Always start with `graphrag index --dry-run` after changing settings.
- For costly runs, verify model IDs, rate limits, cache location, and vector dimensions before indexing.
- For custom workflows, confirm every workflow name is registered and every expected source table already exists.
- For updates, validate the current output directory before running `graphrag update`.
