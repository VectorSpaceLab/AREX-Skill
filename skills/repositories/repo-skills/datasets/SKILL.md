---
name: datasets
description: "Use this skill when working with Hugging Face Datasets: loading
  local or Hub datasets, defining Features schemas, processing/streaming
  datasets, converting formats, sharing to the Hub, managing cache/offline
  behavior, or using datasets-cli."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Hugging Face Datasets

Use this repo skill for practical work with the `datasets` Python package. It is self-contained guidance distilled from the Datasets source, docs, tests, and verified public API surface.

## Start Here

- Install the package with `pip install datasets`; add extras only for workflows that need them, such as `datasets[audio]`, `datasets[vision]`, `datasets[pdfs]`, `datasets[nibabel]`, or ML framework packages.
- Run `python -c "from datasets import Dataset, load_dataset; print(Dataset.from_dict({'x':[1]}))"` for a minimal import/API smoke check.
- Use `load_dataset(...)` for Hub datasets, local files, local dataset repositories, and packaged format builders.
- Use `Dataset.from_dict`, `Dataset.from_list`, `Dataset.from_pandas`, or `Dataset.from_generator` when data already exists in Python.

## Route by Task

- Load datasets from the Hub, local files/directories, Python objects, generators, packaged modules, or disk snapshots with `sub-skills/loading-local-hub/SKILL.md`.
- Transform, filter, batch, split, shuffle, stream, format, combine, or convert datasets with `sub-skills/processing-streaming/SKILL.md`.
- Define `Features`, cast columns, troubleshoot schemas, and work with CSV/JSON/Parquet/Arrow/text/image/audio/video/PDF/NIfTI/mesh formats with `sub-skills/features-formats/SKILL.md`.
- Push datasets to the Hub, create dataset cards, use `datasets-cli`, manage cache/offline mode, or diagnose filesystem/storage issues with `sub-skills/sharing-cli-cache/SKILL.md`.

## Shared References and Scripts

- Read `references/api-surface.md` for the verified top-level API map and the most important signatures.
- Read `references/troubleshooting.md` for cross-cutting install, import, optional dependency, auth, cache, and workflow routing failures.
- Read `references/repo-provenance.md` when checking whether this skill is stale relative to a Datasets checkout.
- Run `scripts/datasets_api_smoke.py --help` for a safe local smoke helper that verifies import, core APIs, tiny in-memory processing, and CLI availability.

## Common Decisions

- Prefer explicit `data_files`, `split`, and `features` when automatic local file inference would be ambiguous.
- Use `streaming=True` for large or remote data that should not be fully downloaded; route downstream iterable semantics to `processing-streaming`.
- Use `decode=False` for media columns when optional decoders are unavailable or when you only need paths/bytes metadata.
- Do not put tokens in code, logs, dataset cards, or generated examples; pass tokens through normal Hugging Face auth mechanisms.
- Treat `delete_from_hub` and `push_to_hub` as state-changing operations; dry-run the plan and confirm repo IDs/config names before running them.

## Validation Pattern

1. Confirm the package imports and the relevant optional dependency is installed.
2. Build or load a tiny representative dataset first.
3. Declare `Features` when schema inference is risky.
4. Run the intended map/filter/cast/format operation on a tiny subset.
5. Save, reload, or push only after the local smoke path behaves as expected.
