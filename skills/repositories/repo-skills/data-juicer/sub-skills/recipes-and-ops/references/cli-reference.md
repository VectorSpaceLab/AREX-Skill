# CLI reference

## Main commands
- `dj-process`: run a recipe against a dataset.
- `dj-analyze`: inspect or summarize a dataset.
- `dj-install`: inspect operator dependency hints.

## Typical usage
```bash
dj-process --config recipe.yaml
dj-analyze --config analyze.yaml
dj-install --help
```

## Utility entrypoints
Use the package helper modules when you only need one small transformation.
Examples include preprocess helpers, postprocess helpers, and format conversion helpers.

## Flags to pay attention to
- config path or inline config
- dataset source or input path
- output path and export type
- process list or operator selection
- cache and tracing toggles
- custom operator path settings

## Help-first habit
If a command fails, re-run it with `--help` or a smaller config before changing several flags at once.
