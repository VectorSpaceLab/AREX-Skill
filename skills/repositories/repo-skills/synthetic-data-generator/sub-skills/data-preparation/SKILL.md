---
name: data-preparation
description: "Prepare SDGX tabular inputs with connectors, DataLoader caching,
  Metadata inspection, processors, relationships, and plugin registration before
  synthesis."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SDGX Data Preparation

Use this sub-skill when a task is about getting tabular data ready for SDGX synthesis: CSV/DataFrame/generator connectors, `DataLoader`, metadata inference, datetime/PII/fixed-combination handling, cache behavior, relationship metadata, or custom plugin registration.

Route to [../single-table-synthesis/SKILL.md](../single-table-synthesis/SKILL.md) when the user primarily wants to fit/sample a model or use `sdgx fit`/`sample`. Route to [../llm-synthesis/SKILL.md](../llm-synthesis/SKILL.md) for GPT-backed generation.

## Core workflow

1. Select data access: `CsvConnector` for CSV paths, `DataFrameConnector` for in-memory pandas data, and `GeneratorConnector` for repeated chunk generators.
2. Wrap in `DataLoader` when needed: `DataLoader(connector, chunksize=..., cacher=..., cacher_kwargs=...)` provides chunking, slicing, and cache-backed access.
3. Infer metadata with `Metadata.from_dataframe(df)` or `Metadata.from_dataloader(loader, max_chunk=...)`.
4. Validate and customize metadata: primary keys, column types, `datetime_format`, `specific_combinations`, categorical encoders, and relationship metadata.
5. Confirm processors: default `Synthesizer` processors handle combinations, missing/outlier values, PII, integer/datetime formatting, constants, positive/negative filters, empty columns, and column order.
6. Persist artifacts if useful: save metadata JSON or combiner directories with package APIs, not ad-hoc pickle files.

For concrete API patterns, read [references/connectors-loaders-metadata.md](references/connectors-loaders-metadata.md). For processors/inspectors, read [references/processors-and-inspectors.md](references/processors-and-inspectors.md). For custom plugins, read [references/extensions.md](references/extensions.md).

## Bundled helper

Run [scripts/inspect_metadata.py](scripts/inspect_metadata.py) to inspect a CSV and emit SDGX metadata JSON:

```bash
python sub-skills/data-preparation/scripts/inspect_metadata.py data.csv --output metadata.json --check
```

## Decision points

- Prefer `DataFrameConnector` for tiny tests and avoid disk cache by default.
- Prefer `CsvConnector` plus `DataLoader` for real CSV files and chunked reads.
- Use `GeneratorConnector` only with a cache-backed `DataLoader`; it is not random-access by itself.
- Add `specific_combinations` manually for semantic column groups such as `("education", "educational-num")` when automatic fixed-combination inference is not enough.
- Set `metadata.datetime_format` for every datetime column you want preserved; missing formats can cause datetime columns to be removed by `DatetimeFormatter`.
- Treat PII generators as replacement/masking processors, not privacy certification.

## Troubleshooting

Read [references/troubleshooting.md](references/troubleshooting.md) for `MetadataInvalidError`, generator/cache failures, datetime removal, fixed-combination over-detection, PII inference, and plugin registration issues.
