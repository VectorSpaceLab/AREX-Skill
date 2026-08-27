# Export and Pagination

## Choose the right history method

- `run.history(samples=..., keys=..., pandas=True)` returns sampled history and is best for quick previews or plotting.
- `run.scan_history(keys=..., page_size=..., min_step=..., max_step=...)` iterates unsampled history and is best for reproducible exports.
- If a task asks for complete metric rows, prefer `scan_history`; if it asks for a quick representative view, prefer `history`.

```python
run = wandb.Api(timeout=120).run("entity/project/run_id")
rows = run.history(samples=200, keys=["loss", "accuracy"], pandas=False)
for row in run.scan_history(keys=["loss"], page_size=1000, max_step=10000):
    ...
```

## Large export strategy

1. Ask for or infer a bounded metric list; exporting every key can be very large.
2. Start with `--dry-run`, `--max-rows`, or `max_step` to estimate shape.
3. Stream rows to disk; do not build a full list for large runs.
4. Use JSONL when keys vary by row; use CSV when a stable column set is needed.
5. Include `_step` and timestamps if downstream joins or ordering matter.
6. Document whether sampled or unsampled data was exported.

## Bundled helper script

The sub-skill includes `scripts/export_run_history.py`, a self-contained helper that uses only public `wandb.Api` calls.

```bash
python scripts/export_run_history.py \
  --entity ENTITY \
  --project PROJECT \
  --run RUN_ID \
  --out history.jsonl \
  --format jsonl \
  --keys _step loss accuracy \
  --page-size 1000 \
  --max-rows 50000
```

Options:

- `--entity`, `--project`, `--run`: form `entity/project/run_id` safely without relying on API defaults.
- `--out`: output file path; parent directories are created if needed.
- `--format csv|jsonl`: CSV writes a header from discovered rows; JSONL streams one JSON object per line.
- `--keys`: optional metric keys for `scan_history(keys=...)`; omit to export all available keys.
- `--min-step`, `--max-step`: bound the `_step` range. `max_step` is exclusive in the SDK.
- `--page-size`: page size passed to `scan_history`; default is conservative.
- `--max-rows`: hard client-side row cap for safe exploration.
- `--timeout`: `wandb.Api(timeout=...)` value.
- `--base-url`: optional W&B server URL, passed through `overrides={"base_url": ...}`.
- `--dry-run`: prints the resolved run and export plan without writing rows.

## Pagination patterns

`api.runs`, `api.reports`, `run.files`, `api.automations`, and integration list methods return lazy paginator-like iterables. Iterate them directly instead of assuming a materialized list:

```python
for run in api.runs("entity/project", per_page=100):
    process(run)
```

For automation listing, the iterator exposes a cursor after partial iteration. This supports resumable reads:

```python
from itertools import islice

paginator = api.automations(entity="entity", per_page=25)
first_batch = list(islice(paginator, 25))
cursor = paginator.cursor
if cursor:
    remaining = api.automations(entity="entity", per_page=25, start=cursor)
```

## Files export

```python
run = api.run("entity/project/run_id")
for file in run.files(pattern="%.json", per_page=50):
    file.download(root="downloads", replace=False)
```

- Use `names=[...]` for exact filenames or `pattern="%.ext"` for SQL-LIKE pattern matching; do not pass both.
- Confirm overwrite behavior before setting `replace=True`.
- Keep downloads out of the skill runtime tree unless the task explicitly asks to create skill assets.

## CSV vs JSONL guidance

- CSV is convenient for spreadsheets and stable scalar metrics. Missing fields become empty cells.
- JSONL preserves sparse metric rows, nested values, and heterogeneous keys better.
- If media/table objects appear in history, export metadata only unless the user specifically requests file or artifact downloads.
