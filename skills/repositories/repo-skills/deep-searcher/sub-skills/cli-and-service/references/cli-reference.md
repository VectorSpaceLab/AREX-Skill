# CLI Reference

## Purpose

Use this reference for the exact `deepsearcher` command-line surface in the inspected checkout.

## Command layout

The console entry point is `deepsearcher = deepsearcher.cli:main`.

### Query

```bash
deepsearcher query <query> [--max_iter MAX_ITER]
```

- Positional argument: `query`
- Optional flag: `--max_iter` (default: `3`)

### Load

```bash
deepsearcher load <load_path> [<load_path> ...] [--batch_size BATCH_SIZE] [--collection_name COLLECTION_NAME] [--collection_desc COLLECTION_DESC] [--force_new_collection FORCE_NEW_COLLECTION]
```

- Positional argument: one or more local paths or URLs
- Optional flags:
  - `--batch_size` (default: `256`)
  - `--collection_name`
  - `--collection_desc`
  - `--force_new_collection`

## Deprecated forms

The inspected CLI still detects these legacy forms and exits with a deprecation warning:

```bash
deepsearcher --query ...
deepsearcher --load ...
```

Use the `query` and `load` subcommands instead.

## Help caveat

The CLI initializes `Configuration()` and `init_config(config)` before it finishes parsing subcommands. In this checkout, that means even `--help` can fail if the default provider stack is not ready. Use `scripts/check_cli_help.py` for a temp-cwd probe that makes the failure mode explicit.

## What the help output shows

- Root parser with `query` and `load` subcommands.
- `query` positional `query` plus `--max_iter`.
- `load` positional `load_path` plus `--batch_size`, `--collection_name`, `--collection_desc`, and `--force_new_collection`.

## When to use the service helper instead

If the user wants an HTTP surface, read [service reference](service-reference.md) and use `scripts/serve_deepsearcher_api.py` instead of invoking the console command directly.
