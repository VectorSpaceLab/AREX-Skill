# Configuration guide

## Core fields
- `dataset_path`: simple local input path.
- `dataset`: structured dataset description when one path is not enough.
- `process`: ordered operator list.
- `export_path`: destination path for processed output.
- `export_type`: output format such as JSONL or parquet.
- `text_keys`: text columns to use when an operator needs text input.
- `validators`: optional checks before or after processing.
- `use_cache`: reuse intermediate results when safe.
- `open_tracer`: enable tracing only when you need per-operator debugging.

## Local recipe rules
- Prefer the smallest valid dataset description.
- Use explicit shard / split settings only when the output format needs them.
- If one operator depends on another field, make that field available in the dataset config.
- Keep cache and tracing off unless you are actively debugging.

## Format notes
- JSONL is the easiest starting point.
- Lenient JSONL loading helps when individual rows are malformed or too large for a strict parser.
- Parquet is useful for compact export, but it is less forgiving than JSONL.

## Custom operators
- Add custom operator paths only when the recipe truly needs them.
- Avoid reusing the same operator name in multiple places unless the implementation is meant to be shared.

## When to stop and simplify
If a config has too many moving parts, reduce it to:
1. one dataset source
2. one or two operators
3. one export target
4. one optional validator
