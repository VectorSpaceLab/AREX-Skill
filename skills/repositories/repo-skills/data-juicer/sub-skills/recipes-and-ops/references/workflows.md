# Local recipe workflows

## Minimal processing flow
1. Prepare a recipe config with the dataset source, process list, and export target.
2. Run the processor:

```bash
dj-process --config recipe.yaml
```

3. Inspect the output dataset or run a follow-up analysis:

```bash
dj-analyze --config analyze.yaml
```

## Common pattern
- `dataset_path` is for a simple local input.
- Structured dataset configs are better when a dataset is split across files, shards, or mixed sources.
- Keep the process list small first, then add operators once the config is valid.

## Utility helpers
Use the helper modules when you need a focused transformation instead of a full recipe:
- preprocess helpers for input cleanup and splitting
- postprocess helpers for output cleanup
- format conversion helpers for moving between text, JSONL, parquet, and similar formats

## Dependency checks
If a recipe fails because an operator is missing an optional dependency:
1. Check the operator documentation or error message.
2. Use `dj-install` to inspect the dependency hint when available.
3. Prefer a smaller recipe or a local fallback operator until the missing package is installed.

## Good troubleshooting habit
When a config fails, separate the problem into:
- input path / dataset shape
- process list syntax
- export target and shard settings
- optional dependency or cache/tracing toggle
